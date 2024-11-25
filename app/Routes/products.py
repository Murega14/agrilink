from flask import Blueprint, jsonify, request, session, render_template
from ..models import db, Product, Farmer
from .authentication import login_is_required
from sqlalchemy import func
from ..extensions import get_db
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import os
from dotenv import load_dotenv

products = Blueprint('products', __name__)

cache = {}
category_cache = {}
name_cache = {}

@products.route('/view_products', methods=['GET'])
async def view_products():
    if 'products' in cache:
        return render_template('marketplace.html', product_list=cache['products'])
    
    async with get_db() as session:
        # The joinedload will now work because the farmer relationship is explicitly defined
        stmt = select(Product).options(joinedload(Product.farmer))
        result = await session.execute(stmt)
        products = list(result.unique().scalars().all())
        
        product_list = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}" if product.farmer else "Unknown Seller"
        } for product in products]
    
    cache['products'] = product_list    
    return render_template('marketplace.html', product_list=product_list)
# Similar fixes should be applied to other routes
@products.route('/view_products/category/<string:category>', methods=['GET'])
async def view_by_category(category):
    if category in category_cache:
        return jsonify(category_cache[category])
    
    async with get_db() as session:
        stmt = select(Product).options(joinedload(Product.farmer)).filter(func.lower(Product.category) == category.lower())
        result = await session.execute(stmt)
        products_by_category = list(result.unique().scalars().all())
        
        if not products_by_category:
            return jsonify({"error": "category not found"}), 404
        
        products = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        } for product in products_by_category]
    
    category_cache[category] = products   
    return jsonify(products)

@products.route('/view_products/<int:product_id>', methods=['GET'])
async def view_by_id(product_id):
    async with get_db() as session:
        stmt = select(Product).options(joinedload(Product.farmer)).filter(Product.id == product_id)
        result = await session.execute(stmt)
        product_by_id = result.unique().scalar_one_or_none()
        
        if not product_by_id:
            return jsonify({"error": "product not found"}), 404
        
        product_details = {
            "name": product_by_id.name,
            "description": product_by_id.description,
            "price": product_by_id.price_per_unit,
            "amount": product_by_id.amount_available,
            "seller": f"{product_by_id.farmer.first_name} {product_by_id.farmer.last_name}"
        }
    
    return jsonify(product_details)

@products.route('/view_products/name/<string:name>', methods=['GET'])
async def view_by_name(name):
    if name in name_cache:
        return jsonify(name_cache[name])
    
    async with get_db() as session:
        stmt = select(Product).options(joinedload(Product.farmer)).filter(Product.name.ilike(name))
        result = await session.execute(stmt)
        product_by_name = list(result.unique().scalars().all())
        
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
    
    name_cache[name] = product_list   
    return jsonify(product_list)