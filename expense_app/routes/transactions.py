from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Transaction, Category, Subcategory

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/', methods=['GET'])
@login_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    type_filter = request.args.get('type')
    category_id = request.args.get('category_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Transaction.query.filter_by(user_id=current_user.id)
    if type_filter:
        query = query.filter_by(type=type_filter)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(end_date))
    query = query.order_by(Transaction.date.desc())
    total = query.count()
    txns = query.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({'transactions': [t.to_dict() for t in txns], 'total': total, 'page': page, 'per_page': per_page})


@transactions_bp.route('/', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json()
    if not data or not all(k in data for k in ['amount', 'type', 'category_id']):
        return jsonify({'error': 'amount, type, and category_id are required'}), 400
    if data['type'] not in ('income', 'expense'):
        return jsonify({'error': 'type must be income or expense'}), 400
    cat = Category.query.filter_by(id=data['category_id'], user_id=current_user.id).first()
    if not cat:
        return jsonify({'error': 'Category not found'}), 404
    txn = Transaction(
        amount=float(data['amount']),
        type=data['type'],
        category_id=data['category_id'],
        subcategory_id=data.get('subcategory_id'),
        notes=data.get('notes'),
        user_id=current_user.id,
        date=datetime.fromisoformat(data['date']) if data.get('date') else datetime.utcnow()
    )
    db.session.add(txn)
    db.session.commit()
    return jsonify(txn.to_dict()), 201


@transactions_bp.route('/<int:txn_id>', methods=['PUT'])
@login_required
def update_transaction(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'amount' in data:
        txn.amount = float(data['amount'])
    if 'type' in data:
        txn.type = data['type']
    if 'category_id' in data:
        txn.category_id = data['category_id']
    if 'subcategory_id' in data:
        txn.subcategory_id = data['subcategory_id']
    if 'notes' in data:
        txn.notes = data['notes']
    if 'date' in data:
        txn.date = datetime.fromisoformat(data['date'])
    db.session.commit()
    return jsonify(txn.to_dict())


@transactions_bp.route('/<int:txn_id>', methods=['DELETE'])
@login_required
def delete_transaction(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first_or_404()
    db.session.delete(txn)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


@transactions_bp.route('/balance', methods=['GET'])
@login_required
def get_balance():
    from sqlalchemy import func
    income = db.session.query(func.sum(Transaction.amount)).filter_by(
        user_id=current_user.id, type='income').scalar() or 0.0
    expense = db.session.query(func.sum(Transaction.amount)).filter_by(
        user_id=current_user.id, type='expense').scalar() or 0.0
    return jsonify({'income': income, 'expense': expense, 'balance': income - expense})


@transactions_bp.route('/export/csv', methods=['GET'])
@login_required
def export_csv():
    import csv, io
    from flask import Response
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Category', 'Subcategory', 'Amount', 'Notes'])
    for t in txns:
        writer.writerow([
            t.date.strftime('%Y-%m-%d %H:%M'),
            t.type,
            t.category.name if t.category else '',
            t.subcategory.name if t.subcategory else '',
            t.amount,
            t.notes or ''
        ])
    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=transactions.csv'})
