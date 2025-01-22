from flask import Blueprint, jsonify, request
from ..models import db, Product, Farmer
from ..wrappers import farmer_required, buyer_required
from ..extensions import get_current_user_id, cache
from sqlalchemy import func
from typing import Dict, Any
import logging
from decimal import Decimal

products = Blueprint('products', __name__)
logger = logging.getLogger(__name__)

products = Blueprint('products', __name__)

def validate_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    validate a products data
    returns a dictionary with validated data or raises an exception
    """
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price_per_unit = data.get('price_per_unit')
    amount_available = data.get('amount_available')
    category = data.get('category', '').strip().lower()
    
    if not all([name, description, price_per_unit, category]):
        return ValueError("All fields are required")
    
    try:
        price_per_unit = Decimal(str(price_per_unit))
        amount_available = int(amount_available)
    except (ValueError, TypeError):
        raise ValueError("Invalid price or amount")
    
    if price_per_unit <= 0 or amount_available < 0:
        raise ValueError("Price and amount must be greater than or equal to 0")
    
    return {
        "name": name,
        "description": description,
        "price_per_unit": price_per_unit,
        "amount_available": amount_available,
        "category": category
    }
    
@products.route('/api/v1/products/add', methods=['POST'])
@farmer_required
def add_product():
    """
    add a new product for the current farmer
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("no data provided in the request")
            return jsonify({"error": "no data provided"}), 400
        
        user_id = get_current_user_id()
        farmer = Farmer.query.get(user_id)
        if not farmer:
            logger.error(f"farmer not found: {user_id}")
            return jsonify({"error": "Farmer not found"}), 404
        
        try:
            validated_data = validate_product_data(data)
        except ValueError as e:
            logger.error(f"validation error: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
        new_product = Product(
            name=validated_data["name"],
            description=validated_data["description"],
            price_per_unit=validated_data["price_per_unit"],
            amount_available=validated_data["amount_available"],
            category=validated_data["category"],
            farmer_id=user_id
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        logger.info(f"product added successfully: {new_product.name}")
        return jsonify({
            "success": "product added successfully",
            "product_id": new_product.id
        }), 201
        
    except Exception as e:
        logger.error(f"failed to add product: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    
@products.route('/api/v1/products', methods=['GET'])
def view_products():
    """
    view a paginated list of produxts with caching and optional search filtering
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search_query = request.args.get('search', '', type=str)
        
        if page <= 0 or per_page <= 0:
            return jsonify({"error": "page and per page must be greater than 0"})
        
        # generating a unique cache key based on the request parameters
        cache_key = f"products:page:{page}:per_page{per_page}:search{search_query}"
        #check if the data exists in the cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"returning cached data for: {cache_key}")
            return jsonify(cached_data), 200
        
        #if the data does not exist we go ahead with querying the database
        query = Product.query
        
        if search_query:
            search_query = search_query.replace('%', r'\%').replace('_', r'\_')
            query = query.filter(Product.name.ilike(f'%{search_query}%'))
        
        pagination = query.paginate(page=page, per_page=per_page)
        products = pagination.items
        
        product_list = [{
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price_per_unit),
            "amount": product.amount_available,
            "category": product.category,
            "seller": product.farmer.full_name
        } for product in products]
        
        response_data = {
            "products": product_list,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total
        }
        
        #storing the response in the cache
        cache.set(cache_key, response_data, timeout=300)
        logger.info(f"data cached for; {cache_key}")
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"error fetching products: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
@products.route('/api/v1/products/update/<int:id>', methods=['PUT'])
@farmer_required
def update_product(id: int):
    """
    update an existing product for the current farmer

    Args:
        id (integer): product identifier
    """
    try:
        user_id = get_current_user_id()
        farmer = Farmer.query.get(user_id)
        if not farmer:
            logger.error("Farmer not found")
            return jsonify({"error": "farmer not found"}), 404
        
        product = Product.query.get(id)
        if not product:
            logger.error(f"product not found: {id}")
            return jsonify({"error": "product not found"}), 404
        
        if product.farmer_id != user_id:
            logger.error(f"unauthorized access to product: {id} by user: {user_id}")
            return jsonify({"error": "unauthorized"}),401
        
        data = request.get_json()
        if not data:
            logger.error("No data provided in the request")
            return jsonify({"error": "no data provided"}), 400
        
        if 'name' in data:
            product.name = data['name'].strip()
        if 'description' in data:
            product.description = data['description'].strip()
        if 'category' in data:
            product.category = data['category'].strip()
        if 'price_per_unit' in data:
            try:
                new_price = Decimal(str(data['price_per_unit']))
                if new_price <= 0:
                    return jsonify({"error": "price must be greater than 0"}), 400
                product.price_per_unit = new_price
            except (ValueError, TypeError):
                return jsonify({"error": "invalid price"}), 400
        if 'amount_available' in data:
            try:
                new_amount = int(data['amount_available'])
                if new_amount < 0:
                    return jsonify({"error": "available amount cannot be less than 0"}), 400
                product.amount_available = new_amount
            except (ValueError, TypeError):
                return jsonify({"error": "invalid amount"}), 400
        
        db.session.commit()
        logger.info(f"product updated successfully: {product.name} (ID: {product.id})")
        
        return jsonify({
            "message": "product updated successfully",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price_per_unit),
                "amount_available": product.amount_available,
                "category": product.category
            }
        }), 200
        
    except Exception as e:
        logger.error(f"error updating product: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "internal server error"}), 500
    
@products.route('/api/v1/products/category/<string:category>', methods=['GET'])
def view_by_category(category: str):
    """
    view products by category

    Args:
        category (str): product category
    """
    try:
        products = Product.query.filter(Product.category.ilike(f'%{category}%')).all()
        if not products:
            logger.error(f"no products found for category: {category}")
            return jsonify({"error": "category not found"}), 404
        
        product_list = [{
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price_per_unit),
            "amount_available": product.amount_available,
            "seller": product.farmer.full_name
        } for product in products]
        
        return jsonify(product_list), 200
    
    except Exception as e:
        logger.error(f"error fetching products by category: {str(e)}")
        return jsonify({"error": "internal server error"}), 500
        
@products.route('/api/v1/products/<int:id>', methods=['GET'])
def view_by_id(id: int):
    """
    view a single product by its ID

    Args:
        id (int): unique identifier
    """
    try:
        product = Product.query.get(id)
        if not product:
            logger.error(f"product not found: {id}")
            return jsonify({"error": "product not found"}), 404
        
        product_details = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price_per_unit),
            "amount_available": product.amount_available,
            "category": product.category,
            "seller": product.farmer.full_name
        }
        
        return jsonify(product_details), 200
    
    except Exception as e:
        logger.error(f"Failed to fetch product by id: {str(e)}")
        return jsonify({"error": "internal server error"}), 500
    
@products.route('/api/v1/products/delete/<int:id>', methods=['DELETE'])
@farmer_required
def delete_product(id: int):
    """
    delete a product for the current farmer

    Args:
        id (int): product unique identifier
    """
    try:
        user_id = get_current_user_id()
        farmer = Farmer.query.get(user_id)
        if not farmer:
            logger.error(f"farmer not found: {user_id}")
            return jsonify({"Error": "farmer not found"}), 400
        
        product = Product.query.get(id)
        if not product:
            logger.error(f"product not found: {id}")
            return jsonify({"error": "product not found"}), 404
        
        if product.farmer_id != user_id:
            logger.error(f"unauthorized access by: {user_id} for product: {id}")
            return jsonify({"error": "unauthorized"}), 401
        
        db.session.delete(product)
        db.session.commit()
        
        logger.info(f"product deleted successfully: {product.name} (ID: {product.id})")
        return jsonify({"error": f"product {product.name} has been deleted"}), 200
    
    except Exception as e:
        logger.error(f"error deleting product: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "internal server error"}), 500