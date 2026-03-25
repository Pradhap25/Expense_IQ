from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'GET':
        return render_template('auth.html', mode='register')
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'All fields required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    _seed_default_categories(user)
    login_user(user)
    return jsonify({'message': 'Registered successfully', 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'GET':
        return render_template('auth.html', mode='login')
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    user = User.query.filter_by(email=data.get('email', '')).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401
    login_user(user)
    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'}), 200


def _seed_default_categories(user):
    from models import Category, Subcategory
    defaults = [
        {'name': 'Food & Dining', 'type': 'expense', 'icon': '🍔', 'color': '#f59e0b',
         'subs': ['Restaurants', 'Groceries', 'Coffee', 'Takeaway']},
        {'name': 'Transport', 'type': 'expense', 'icon': '🚗', 'color': '#3b82f6',
         'subs': ['Fuel', 'Public Transit', 'Taxi/Uber', 'Parking']},
        {'name': 'Shopping', 'type': 'expense', 'icon': '🛍️', 'color': '#8b5cf6',
         'subs': ['Clothing', 'Electronics', 'Home', 'Personal Care']},
        {'name': 'Bills & Utilities', 'type': 'expense', 'icon': '⚡', 'color': '#ef4444',
         'subs': ['Electricity', 'Internet', 'Phone', 'Water']},
        {'name': 'Health', 'type': 'expense', 'icon': '🏥', 'color': '#10b981',
         'subs': ['Doctor', 'Pharmacy', 'Gym', 'Insurance']},
        {'name': 'Entertainment', 'type': 'expense', 'icon': '🎬', 'color': '#f97316',
         'subs': ['Movies', 'Streaming', 'Games', 'Events']},
        {'name': 'Education', 'type': 'expense', 'icon': '📚', 'color': '#06b6d4',
         'subs': ['Courses', 'Books', 'Tuition', 'Stationery']},
        {'name': 'Salary', 'type': 'income', 'icon': '💼', 'color': '#22c55e',
         'subs': ['Monthly Salary', 'Bonus', 'Overtime']},
        {'name': 'Freelance', 'type': 'income', 'icon': '💻', 'color': '#84cc16',
         'subs': ['Projects', 'Consulting', 'Design']},
        {'name': 'Investments', 'type': 'income', 'icon': '📈', 'color': '#14b8a6',
         'subs': ['Dividends', 'Interest', 'Capital Gains']},
    ]
    for d in defaults:
        cat = Category(name=d['name'], type=d['type'], icon=d['icon'], color=d['color'], user_id=user.id)
        db.session.add(cat)
        db.session.flush()
        for s in d['subs']:
            db.session.add(Subcategory(name=s, category_id=cat.id))
    db.session.commit()
