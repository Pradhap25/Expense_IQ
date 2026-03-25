from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Budget, Category, Transaction

budgets_bp = Blueprint('budgets', __name__)


@budgets_bp.route('/', methods=['GET'])
@login_required
def get_budgets():
    now = datetime.utcnow()
    month = request.args.get('month', now.month, type=int)
    year = request.args.get('year', now.year, type=int)
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()
    return jsonify([b.to_dict() for b in budgets])


@budgets_bp.route('/', methods=['POST'])
@login_required
def set_budget():
    data = request.get_json()
    if not data or not all(k in data for k in ['category_id', 'amount']):
        return jsonify({'error': 'category_id and amount required'}), 400
    now = datetime.utcnow()
    month = data.get('month', now.month)
    year = data.get('year', now.year)
    cat = Category.query.filter_by(id=data['category_id'], user_id=current_user.id).first_or_404()
    existing = Budget.query.filter_by(
        user_id=current_user.id, category_id=data['category_id'], month=month, year=year
    ).first()
    if existing:
        existing.amount = float(data['amount'])
    else:
        existing = Budget(
            amount=float(data['amount']), month=month, year=year,
            category_id=data['category_id'], user_id=current_user.id
        )
        db.session.add(existing)
    db.session.commit()
    return jsonify(existing.to_dict()), 201


@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


@budgets_bp.route('/alerts', methods=['GET'])
@login_required
def get_alerts():
    from sqlalchemy import func, extract
    now = datetime.utcnow()
    budgets = Budget.query.filter_by(user_id=current_user.id, month=now.month, year=now.year).all()
    alerts = []
    for b in budgets:
        d = b.to_dict()
        if d['percentage'] >= 100:
            alerts.append({'type': 'danger', 'message': f"🚨 Budget exceeded for {d['category_name']}! Spent ₹{d['spent']:.0f} of ₹{d['amount']:.0f}", 'category': d['category_name']})
        elif d['percentage'] >= 80:
            alerts.append({'type': 'warning', 'message': f"⚠️ {d['category_name']} budget is {d['percentage']}% used. Only ₹{d['remaining']:.0f} left.", 'category': d['category_name']})
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id, Transaction.type == 'income'
    ).scalar() or 0
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id, Transaction.type == 'expense'
    ).scalar() or 0
    balance = total_income - total_expense
    if balance < 0:
        alerts.append({'type': 'danger', 'message': f"🔴 Your balance is negative! Balance: ₹{balance:.0f}", 'category': 'Balance'})
    elif balance < 5000:
        alerts.append({'type': 'warning', 'message': f"⚠️ Low balance alert! Current balance: ₹{balance:.0f}", 'category': 'Balance'})
    return jsonify(alerts)
