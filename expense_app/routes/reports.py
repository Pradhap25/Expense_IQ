from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from models import db, Transaction, Category

reports_bp = Blueprint('reports', __name__)


def _get_date_range(period, year=None, month=None, week=None):
    now = datetime.utcnow()
    if period == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'weekly':
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'monthly':
        m = month or now.month
        y = year or now.year
        start = datetime(y, m, 1)
        if m == 12:
            end = datetime(y + 1, 1, 1) - timedelta(seconds=1)
        else:
            end = datetime(y, m + 1, 1) - timedelta(seconds=1)
    elif period == 'yearly':
        y = year or now.year
        start = datetime(y, 1, 1)
        end = datetime(y, 12, 31, 23, 59, 59)
    else:
        start = now - timedelta(days=30)
        end = now
    return start, end


def _build_report(start, end):
    txns = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start,
        Transaction.date <= end
    ).all()

    income = sum(t.amount for t in txns if t.type == 'income')
    expense = sum(t.amount for t in txns if t.type == 'expense')

    cat_breakdown = {}
    for t in txns:
        cat_name = t.category.name if t.category else 'Unknown'
        cat_icon = t.category.icon if t.category else '💰'
        cat_color = t.category.color if t.category else '#6366f1'
        key = (cat_name, t.type, cat_icon, cat_color)
        cat_breakdown[key] = cat_breakdown.get(key, 0) + t.amount

    breakdown = [
        {'category': k[0], 'type': k[1], 'icon': k[2], 'color': k[3], 'amount': v}
        for k, v in cat_breakdown.items()
    ]
    breakdown.sort(key=lambda x: x['amount'], reverse=True)

    return {
        'income': income, 'expense': expense, 'balance': income - expense,
        'transaction_count': len(txns),
        'category_breakdown': breakdown,
        'start': start.isoformat(), 'end': end.isoformat()
    }


@reports_bp.route('/daily', methods=['GET'])
@login_required
def daily_report():
    start, end = _get_date_range('daily')
    return jsonify(_build_report(start, end))


@reports_bp.route('/weekly', methods=['GET'])
@login_required
def weekly_report():
    start, end = _get_date_range('weekly')
    return jsonify(_build_report(start, end))


@reports_bp.route('/monthly', methods=['GET'])
@login_required
def monthly_report():
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    start, end = _get_date_range('monthly', year=year, month=month)
    return jsonify(_build_report(start, end))


@reports_bp.route('/yearly', methods=['GET'])
@login_required
def yearly_report():
    year = request.args.get('year', type=int)
    start, end = _get_date_range('yearly', year=year)
    return jsonify(_build_report(start, end))


@reports_bp.route('/chart/monthly-trend', methods=['GET'])
@login_required
def monthly_trend():
    """Last 12 months income vs expense trend"""
    now = datetime.utcnow()
    results = []
    for i in range(11, -1, -1):
        if now.month - i <= 0:
            m = now.month - i + 12
            y = now.year - 1
        else:
            m = now.month - i
            y = now.year
        start = datetime(y, m, 1)
        end = datetime(y, m + 1, 1) - timedelta(seconds=1) if m < 12 else datetime(y + 1, 1, 1) - timedelta(seconds=1)
        txns = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start, Transaction.date <= end
        ).all()
        results.append({
            'month': start.strftime('%b %Y'),
            'income': sum(t.amount for t in txns if t.type == 'income'),
            'expense': sum(t.amount for t in txns if t.type == 'expense')
        })
    return jsonify(results)
