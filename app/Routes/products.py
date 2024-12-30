from flask import Blueprint, jsonify, request
from ..models import db, Product, Farmer
from ..wrappers import login_is_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from typing import Dict, Any
import logging
from decimal import Decimal

products = Blueprint('products', __name__)
logger = logging.getLogger(__name__)

@products.route('/api/v1/products/add', methods=['POST'])
#@login_is_required
@jwt_required()
def add_product() -> Dict[str, Any]:
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "no data provided"}), 400
        
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "unauthorized"}), 401
        
        user = Farmer.query.get(user_id)
        if not user:
            logger.error(f"Farmer with id {user_id} not found")
            return jsonify({"error": "farmer not found"}), 404
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        price_per_unit = data.get('price_per_unit', 0)
        amount_available = data.get('amount_available', 0)
        category = data.get('category', '').strip().lower()
        
        
        if not all([name, description, price_per_unit, amount_available, category]):
            return jsonify({"error": "all fields are required"}), 400
        
        try:
            price_per_unit = Decimal(price_per_unit)
            amount_available = int(amount_available)
        except (ValueError, TypeError):
            return jsonify({"error": "invalid price or amount"}), 400
        
        if price_per_unit <= 0 or amount_available <= 0:
            return jsonify({"error": "price and amount must be greater than 0"}), 400
        
        new_product = Product(
            name=name,
            description=description,
            price_per_unit=price_per_unit,
            amount_available=amount_available,
            category=category,
            farmer_id=user_id
        )
        db.session.add(new_product)
        db.session.commit()
        
        logger.info(f"product {name} added successfully")
        return jsonify({"success": "product added successfully"}), 201
    
    except Exception as e:
        logger.error(f"error adding product: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "internal server error"}), 500
            

@products.route('/api/v1/products', methods=['GET'])
#@login_is_required
def view_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    search_query = request.args.get('search', '', type=str)
    
    query = Product.query

    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    pagination = query.paginate(page=page, per_page=per_page)
    products = pagination.items

    product_list = []
    for product in products:
        product_details = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": product.farmer.full_name
        }
        product_list.append(product_details)

    return jsonify(product_list)

@products.route('/api/v1/products/category/<string:category>', methods=['GET'])
@login_is_required
def view_by_category(category):
    products_by_category = Product.query.filter(func.lower(Product.category) == category.lower()).all()
    if not products_by_category:
        return jsonify({"error": "category not found"}), 404
    
    products = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        } for product in products_by_category]
    
        
    return jsonify(products)

@products.route('/api/v1/products/<int:product_id>', methods=['GET'])
@login_is_required
def view_by_id(product_id):
    product_by_id = Product.query.filter_by(id=product_id).first()
    if not product_by_id:
        return jsonify({"error": "product not found"}), 404
    
    product_details = [{
        "name": product_by_id.name,
        "description": product_by_id.description,
        "price": product_by_id.price_per_unit,
        "amount": product_by_id.amount_available,
        "seller": product_by_id.farmer.name
    }]
    
    return jsonify(product_details)

@products.route('/api/v1/products/name/<string:name>', methods=['GET'])
@login_is_required
def view_by_name(name):
    product_by_name = Product.query.filter(func.lower(Product.name) == name.lower()).all()
    if not product_by_name:
        return jsonify({"error": "product not found"}), 404
    
    product_list = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        } for product in product_by_name]
     
        
    return jsonify(product_list)
