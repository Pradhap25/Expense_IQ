from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Category, Subcategory

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/', methods=['GET'])
@login_required
def get_categories():
    type_filter = request.args.get('type')
    query = Category.query.filter_by(user_id=current_user.id)
    if type_filter:
        query = query.filter_by(type=type_filter)
    cats = query.order_by(Category.name).all()
    return jsonify([c.to_dict() for c in cats])


@categories_bp.route('/', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'type']):
        return jsonify({'error': 'name and type required'}), 400
    if data['type'] not in ('income', 'expense'):
        return jsonify({'error': 'type must be income or expense'}), 400
    cat = Category(
        name=data['name'], type=data['type'],
        icon=data.get('icon', '💰'),
        color=data.get('color', '#6366f1'),
        user_id=current_user.id
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@categories_bp.route('/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'name' in data:
        cat.name = data['name']
    if 'icon' in data:
        cat.icon = data['icon']
    if 'color' in data:
        cat.color = data['color']
    db.session.commit()
    return jsonify(cat.to_dict())


@categories_bp.route('/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


@categories_bp.route('/<int:cat_id>/subcategories', methods=['POST'])
@login_required
def add_subcategory(cat_id):
    cat = Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'name required'}), 400
    sub = Subcategory(name=data['name'], category_id=cat.id)
    db.session.add(sub)
    db.session.commit()
    return jsonify(sub.to_dict()), 201


@categories_bp.route('/subcategories/<int:sub_id>', methods=['DELETE'])
@login_required
def delete_subcategory(sub_id):
    sub = Subcategory.query.join(Category).filter(
        Subcategory.id == sub_id, Category.user_id == current_user.id
    ).first_or_404()
    db.session.delete(sub)
    db.session.commit()
    return jsonify({'message': 'Deleted'})
