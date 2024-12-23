from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import db, Farmer, Order, Product

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/api/dashboard/stats')
@jwt_required()
def get_stats():
    current_user_id = get_jwt_identity()
    
    # Get current month dates
    today = datetime.now()
    start_of_month = datetime(today.year, today.month, 1)
    
    try:
        # Products sold this month
        products_sold = db.session.query(func.sum(Order.quantity))\
            .join(Product)\
            .filter(
                Product.farmer_id == current_user_id,
                Order.created_at >= start_of_month
            ).scalar() or 0
            
        # Current month revenue
        current_month_revenue = db.session.query(func.sum(Order.total_amount))\
            .join(Product)\
            .filter(
                Product.farmer_id == current_user_id,
                Order.created_at >= start_of_month
            ).scalar() or 0
            
        # Pending orders
        pending_orders = Order.query\
            .join(Product)\
            .filter(
                Product.farmer_id == current_user_id,
                Order.status == 'pending'
            ).count()
            
        # Active listings
        active_listings = Product.query\
            .filter(
                Product.farmer_id == current_user_id,
                Product.is_available == True
            ).count()
            
        return jsonify({
            "products_sold": products_sold,
            "current_month_revenue": float(current_month_revenue),
            "pending_orders": pending_orders,
            "active_listings": active_listings
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard.route('/api/dashboard/recent-orders')
@jwt_required()
def get_recent_orders():
    current_user_id = get_jwt_identity()
    
    try:
        recent_orders = db.session.query(Order)\
            .join(Product)\
            .filter(Product.farmer_id == current_user_id)\
            .order_by(Order.created_at.desc())\
            .limit(5)\
            .all()
            
        orders_data = [{
            "order_id": order.id,
            "order_date": order.created_at.isoformat(),
            "total_amount": float(order.total_amount),
            "status": order.status
        } for order in recent_orders]
        
        return jsonify(orders_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard.route('/api/dashboard/available-products')
@jwt_required()
def get_available_products():
    current_user_id = get_jwt_identity()
    
    try:
        products = Product.query\
            .filter(
                Product.farmer_id == current_user_id,
                Product.is_available == True
            )\
            .all()
            
        products_data = [{
            "id": product.id,
            "name": product.name,
            "amount_available": float(product.quantity),
            "price_per_unit": float(product.price_per_unit)
        } for product in products]
        
        return jsonify(products_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500