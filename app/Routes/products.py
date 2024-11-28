from flask import Blueprint, jsonify, request, session, render_template
from ..models import db, Product, Farmer
from ..wrappers import cache_result, AsyncTTLCache, async_route
from sqlalchemy import func
from ..extensions import get_db
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from math import ceil

products = Blueprint('products', __name__)

cache = AsyncTTLCache()
category_cache = AsyncTTLCache()
name_cache = AsyncTTLCache()

@products.route('/view_products', methods=['GET'])
@cache_result(cache)
@async_route
async def view_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 16))
    
    
    async with get_db() as session:
        total_products = await session.execute(select(func.count(Product.id)))
        total_products = total_products.scalar()
        total_pages = ceil(total_products / per_page)
        
        stmt = (
                select(Product)
                .options(joinedload(Product.farmer))
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
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
    
        
    return render_template('marketplace.html', product_list=product_list, page=page, total_pages=total_pages, per_page=per_page)

@products.route('/view_products/category/<string:category>', methods=['GET'])
@cache_result(category_cache)
@async_route
async def view_by_category(category):
    async with get_db() as session:
        stmt = (
            select(Product)
            .options(joinedload(Product.farmer))
            .filter(func.lower(Product.category) == category.lower())
        )
        result = await session.execute(stmt)
        products_by_category = list(result.unique().scalars().all())
        
        if not products_by_category:
            return jsonify({"error": "Category not found"}), 404
        
        products = [{
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        } for product in products_by_category]
    
    return jsonify(products)

@products.route('/view_products/<int:product_id>', methods=['GET'])
@async_route
async def view_by_id(product_id):
    async with get_db() as session:
        stmt = select(Product).options(joinedload(Product.farmer)).filter(Product.id == product_id)
        result = await session.execute(stmt)
        product_by_id = result.unique().scalar_one_or_none()
        
        if not product_by_id:
            return jsonify({"error": "Product not found"}), 404
        
        product_details = {
            "id": product_by_id.id,
            "name": product_by_id.name,
            "description": product_by_id.description,
            "price": product_by_id.price_per_unit,
            "amount": product_by_id.amount_available,
            "category": product_by_id.category,
            "seller": f"{product_by_id.farmer.first_name} {product_by_id.farmer.last_name}"
        }
    
    return jsonify(product_details)

@products.route('/view_products/name/<string:name>', methods=['GET'])
@cache_result(name_cache)
@async_route
async def view_by_name(name):
    async with get_db() as session:
        stmt = (
            select(Product)
            .options(joinedload(Product.farmer))
            .filter(Product.name.ilike(f"%{name}%"))
        )
        result = await session.execute(stmt)
        product_by_name = list(result.unique().scalars().all())
        
        if not product_by_name:
            return jsonify({"error": "Product not found"}), 404
        
        product_list = [{
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        } for product in product_by_name]
    
    return jsonify(product_list)

@products.route('/clear_cache', methods=['POST'])
@async_route
async def clear_cache():
    cache.clear()
    category_cache.clear()
    name_cache.clear()
    return jsonify({"message": "Caches cleared successfully"}), 200