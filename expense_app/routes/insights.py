from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Transaction
from sqlalchemy import func, extract
import json

insights_bp = Blueprint('insights', __name__)


def _get_monthly_data(user_id, months=6):
    """Get monthly income/expense data for the last N months"""
    now = datetime.utcnow()
    monthly = []
    for i in range(months - 1, -1, -1):
        offset_month = (now.month - i - 1) % 12 + 1
        offset_year = now.year - ((i - now.month + 1) // 12 + (1 if (i - now.month + 1) % 12 != 0 else 0))
        if now.month <= i:
            offset_month = now.month - i + 12
            offset_year = now.year - 1
        else:
            offset_month = now.month - i
            offset_year = now.year

        txns = Transaction.query.filter(
            Transaction.user_id == user_id,
            extract('month', Transaction.date) == offset_month,
            extract('year', Transaction.date) == offset_year
        ).all()
        monthly.append({
            'month': offset_month, 'year': offset_year,
            'label': datetime(offset_year, offset_month, 1).strftime('%b %Y'),
            'income': sum(t.amount for t in txns if t.type == 'income'),
            'expense': sum(t.amount for t in txns if t.type == 'expense'),
        })
    return monthly


def _get_category_monthly(user_id):
    """Get current month vs last month category breakdown"""
    now = datetime.utcnow()
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1

    def get_cat_data(month, year):
        txns = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).all()
        cats = {}
        for t in txns:
            name = t.category.name if t.category else 'Unknown'
            cats[name] = cats.get(name, 0) + t.amount
        return cats

    curr = get_cat_data(now.month, now.year)
    prev = get_cat_data(prev_month, prev_year)
    return curr, prev


@insights_bp.route('/', methods=['GET'])
@login_required
def get_insights():
    monthly = _get_monthly_data(current_user.id, 6)
    curr_cat, prev_cat = _get_category_monthly(current_user.id)
    insights = []

    # Month over month total comparison
    if len(monthly) >= 2:
        curr_exp = monthly[-1]['expense']
        prev_exp = monthly[-2]['expense']
        if prev_exp > 0:
            change = ((curr_exp - prev_exp) / prev_exp) * 100
            if change > 10:
                insights.append({
                    'type': 'warning',
                    'icon': '📈',
                    'title': 'Spending Increased',
                    'message': f'Your expenses increased by {abs(change):.1f}% compared to last month (₹{curr_exp:.0f} vs ₹{prev_exp:.0f})'
                })
            elif change < -10:
                insights.append({
                    'type': 'success',
                    'icon': '📉',
                    'title': 'Great Savings!',
                    'message': f'Your expenses decreased by {abs(change):.1f}% compared to last month. You saved ₹{prev_exp - curr_exp:.0f}!'
                })

    # Top spending category this month
    if curr_cat:
        top_cat = max(curr_cat, key=curr_cat.get)
        total_expense = sum(curr_cat.values())
        pct = (curr_cat[top_cat] / total_expense * 100) if total_expense > 0 else 0
        insights.append({
            'type': 'info',
            'icon': '🔍',
            'title': 'Top Spending Category',
            'message': f'You are spending the most on {top_cat} this month (₹{curr_cat[top_cat]:.0f}, {pct:.1f}% of total expenses)'
        })

    # Category comparisons
    for cat, amount in curr_cat.items():
        if cat in prev_cat and prev_cat[cat] > 0:
            change = ((amount - prev_cat[cat]) / prev_cat[cat]) * 100
            if change > 30:
                insights.append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': f'{cat} Spike',
                    'message': f'You are spending {change:.1f}% more on {cat} than last month (₹{amount:.0f} vs ₹{prev_cat[cat]:.0f})'
                })

    # Savings rate
    curr_income = monthly[-1]['income'] if monthly else 0
    curr_expense = monthly[-1]['expense'] if monthly else 0
    if curr_income > 0:
        savings_rate = ((curr_income - curr_expense) / curr_income) * 100
        if savings_rate >= 20:
            insights.append({'type': 'success', 'icon': '🏆', 'title': 'Excellent Savings Rate', 'message': f'You saved {savings_rate:.1f}% of your income this month. Keep it up!'})
        elif savings_rate < 0:
            insights.append({'type': 'danger', 'icon': '🚨', 'title': 'Overspending Alert', 'message': f'You spent ₹{curr_expense - curr_income:.0f} more than you earned this month!'})
        else:
            insights.append({'type': 'info', 'icon': '💡', 'title': 'Savings Tip', 'message': f'You saved {savings_rate:.1f}% of your income. Try to aim for 20% or more!'})

    # Weekend vs weekday spending
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    txns = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        Transaction.date >= start_of_month
    ).all()
    weekend_spend = sum(t.amount for t in txns if t.date.weekday() >= 5)
    weekday_spend = sum(t.amount for t in txns if t.date.weekday() < 5)
    if weekend_spend > 0 and weekday_spend > 0:
        days_count = (now - start_of_month).days + 1
        weekend_days = sum(1 for i in range(days_count) if (start_of_month + timedelta(days=i)).weekday() >= 5)
        weekday_days = days_count - weekend_days
        if weekend_days > 0 and weekday_days > 0:
            avg_weekend = weekend_spend / weekend_days
            avg_weekday = weekday_spend / weekday_days
            if avg_weekend > avg_weekday * 1.5:
                insights.append({'type': 'info', 'icon': '🎉', 'title': 'Weekend Spending Pattern', 'message': f'You spend {avg_weekend / avg_weekday:.1f}x more on weekends (₹{avg_weekend:.0f}/day) vs weekdays (₹{avg_weekday:.0f}/day)'})

    if not insights:
        insights.append({'type': 'info', 'icon': '👋', 'title': 'Add More Transactions', 'message': 'Add more income and expense transactions to get personalized AI insights!'})

    return jsonify(insights)


@insights_bp.route('/predict', methods=['GET'])
@login_required
def predict_expenses():
    """Linear regression-based expense prediction for next month"""
    monthly = _get_monthly_data(current_user.id, 12)
    expenses = [m['expense'] for m in monthly]

    # Need at least 3 data points
    data_points = [(i, v) for i, v in enumerate(expenses) if v > 0]

    if len(data_points) < 2:
        return jsonify({'prediction': None, 'message': 'Not enough data for prediction. Add at least 2 months of transactions.', 'confidence': 'low'})

    try:
        import numpy as np
        X = np.array([p[0] for p in data_points]).reshape(-1, 1)
        y = np.array([p[1] for p in data_points])

        # Simple linear regression
        n = len(X)
        x_mean = np.mean(X)
        y_mean = np.mean(y)
        numerator = np.sum((X.flatten() - x_mean) * (y - y_mean))
        denominator = np.sum((X.flatten() - x_mean) ** 2)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        next_x = len(expenses)
        prediction = slope * next_x + intercept
        prediction = max(0, prediction)

        # Confidence based on variance
        residuals = y - (slope * X.flatten() + intercept)
        r_squared = 1 - np.sum(residuals ** 2) / np.sum((y - y_mean) ** 2) if np.sum((y - y_mean) ** 2) > 0 else 0
        confidence = 'high' if r_squared > 0.7 else ('medium' if r_squared > 0.4 else 'low')

        now = datetime.utcnow()
        next_month = now.month % 12 + 1
        next_year = now.year if next_month > 1 else now.year + 1

        return jsonify({
            'prediction': round(prediction, 2),
            'month': datetime(next_year, next_month, 1).strftime('%B %Y'),
            'confidence': confidence,
            'r_squared': round(r_squared, 3),
            'trend': 'increasing' if slope > 50 else ('decreasing' if slope < -50 else 'stable'),
            'message': f'Predicted expenses for {datetime(next_year, next_month, 1).strftime("%B %Y")}: ₹{prediction:.0f}'
        })
    except Exception as e:
        return jsonify({'prediction': None, 'message': f'Prediction error: {str(e)}', 'confidence': 'low'})
