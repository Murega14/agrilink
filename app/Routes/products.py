from flask import Blueprint, jsonify, request, session, render_template
from ..models import db, Product, Farmer
from .authentication import login_is_required

products = Blueprint('products', __name__)

@products.route('/add_product', methods=['POST'])
@login_is_required
def add_product():
    data = request.get_json()
    user_id = session.get('id')
    
    user = Farmer.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "farmer not found, can't add a product"}),404
    
    name = data.get('name')
    description = data.get('description')
    price_per_unit = data.get('price')
    amount_available = data.get('amount')
    category = data.get('category')
    
    if not all([name, description, price_per_unit, amount_available, category]):
        return jsonify({"error": "all fields are required"}), 400
    
    new_product = Product(name=name,
                          description=description,
                          price_per_unit=price_per_unit,
                          amount_available=amount_available,
                          category=category,
                          farmer_id=user.id)
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({"message": "product added successfully"}), 200

@products.route('/view_products', methods=['GET'])
#@login_is_required
def view_products():
    products = Product.query.all()
    
    product_list = []
    for product in products:
        product_details = {
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": f"{product.farmer.first_name} {product.farmer.last_name}"
        }
        
        product_list.append(product_details)
        
    return render_template('marketplace.html', product_list=product_list)

@products.route('/view_products/category/<string:category>', methods=['GET'])
@login_is_required
def view_by_category(category):
    products_by_category = Product.query.filter_by(category=category).all()
    if not products_by_category:
        return jsonify({"error": "category not found"}), 404
    
    products = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "seller": product.farmer.name
        } for product in products_by_category]
    
        
    return jsonify(products)

@products.route('/view_products/<int:product_id>', methods=['GET'])
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

@products.route('/view_products/name/<string:name>', methods=['GET'])
@login_is_required
def view_by_name(name):
    product_by_name = Product.query.filter_by(name=name).all()
    if not product_by_name:
        return jsonify({"error": "product not found"}), 404
    
    product_list = [{
            "name": product.name,
            "description": product.description,
            "price": product.price_per_unit,
            "amount": product.amount_available,
            "category": product.category,
            "seller": product.farmer.name
        } for product in product_by_name]
     
        
    return jsonify(product_list)

