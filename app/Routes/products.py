from flask import Blueprint, jsonify, request, session, render_template
from ..models import db, Product, Farmer
from .authentication import login_is_required
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
import os
from dotenv import load_dotenv

products = Blueprint('products', __name__)

engine = create_async_engine(os.getenv('DATABASE_URI'), echo=True)
async_session = AsyncSession(engine)

cache = []
category_cache = []
name_cache = []

@products.route('/add_product', methods=['POST'])
@login_is_required
def add_product():
    data = request.get_json()
    user_id = session.get('id')
    
    user = Farmer.query.get(user_id)
    if not user:
        return jsonify({"error": "farmer not found, can't add a product"}),404
    
    name = data.get('name')
    description = data.get('description')
    price_per_unit = data.get('price')
    amount_available = data.get('amount')
    category = data.get('category')
    
    if not all([name, description, price_per_unit, amount_available, category]):
        return jsonify({"error": "all fields are required"}), 400
    
    if not isinstance(price_per_unit, (int, float)) or price_per_unit < 0:
        return jsonify({"error": "price must be a positive number"}), 400

    if not isinstance(amount_available, int) or amount_available < 0:
        return jsonify({"error": "amount must be a non-negative integer"}), 400
    
    new_product = Product(name=name,
                          description=description,
                          price_per_unit=price_per_unit,
                          amount_available=amount_available,
                          category=category,
                          farmer_id=user.id)
    db.session.add(new_product)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"message": "product added successfully"}), 200

@products.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@products.route('/view_products', methods=['GET'])
#@login_is_required
async def view_products():
    if 'products' in cache:
        return render_template('marketplace.html', product_list=cache['products'])
    
    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
    
    product_list = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        } for product in products]
    
    cache['products'] = product_list    
    return render_template('marketplace.html', product_list=product_list)

@products.route('/view_products/category/<string:category>', methods=['GET'])
#@login_is_required
def view_by_category(category):
    if category in category_cache:
        return jsonify(category_cache[category])
    
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
    
    category_cache[category] = products   
    return jsonify(products)

@products.route('/view_products/<int:product_id>', methods=['GET'])
#@login_is_required
def view_by_id(product_id):
    product_by_id = Product.query.filter_by(id=product_id).first()
    if not product_by_id:
        return jsonify({"error": "product not found"}), 404
    
    product_details = {
        "name": product_by_id.name,
        "description": product_by_id.description,
        "price": product_by_id.price_per_unit,
        "amount": product_by_id.amount_available,
        "seller": product_by_id.farmer.name
    }
    
    return jsonify(product_details)

@products.route('/view_products/name/<string:name>', methods=['GET'])
#@login_is_required
def view_by_name(name):
    if name in name_cache:
        return jsonify(name_cache[name])
    
    product_by_name = Product.query.filter(Product.name.ilike(name)).all()
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

