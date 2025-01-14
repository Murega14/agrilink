from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta
from ..models import db, Order, Product, FarmerOrder, OrderItem
import logging

dashboard = Blueprint('dashboard', __name__)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@dashboard.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    try:
        current_user_id = get_jwt_identity()
        
        # Calculate start of current month
        today = datetime.utcnow()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get total products sold (sum of quantities from order items)
        products_sold = db.session.query(func.sum(OrderItem.quantity)).join(Order).filter(
            FarmerOrder.farmer_id == current_user_id,
            FarmerOrder.status == 'delivered'
        ).scalar() or 0
        
        # Get current month revenue
        current_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            FarmerOrder.farmer_id == current_user_id,
            FarmerOrder.status == 'delivered',
            FarmerOrder.created_at >= start_of_month
        ).scalar() or 0
        
        # Get pending orders count
        pending_orders = FarmerOrder.query.filter_by(
            farmer_id=current_user_id,
            status='pending'
        ).count()
        
        # Get active listings count
        active_listings = Product.query.filter_by(
            farmer_id=current_user_id,
            status='available'
        ).count()
        
        return jsonify({
            "products_sold": float(products_sold),
            "current_month_revenue": float(current_month_revenue or 0),
            "pending_orders": pending_orders,
            "active_listings": active_listings
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_dashboard_stats: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@dashboard.route('/api/dashboard/recent-orders', methods=['GET'])
@jwt_required()
def get_recent_orders():
    try:
        current_user_id = get_jwt_identity()
        
        recent_orders = FarmerOrder.query.filter_by(farmer_id=current_user_id)\
            .order_by(Order.created_at.desc())\
            .limit(5)\
            .all()
        
        orders_data = [{
            'order_id': order.id,
            'order_date': order.created_at.isoformat(),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'buyer_name': order.buyer.full_name if order.buyer else "Unknown"
        } for order in recent_orders]
        
        return jsonify(orders_data), 200
        
    except Exception as e:
        logger.error(f"Error in get_recent_orders: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@dashboard.route('/api/dashboard/available-products', methods=['GET'])
@jwt_required()
def get_available_products():
    try:
        current_user_id = get_jwt_identity()
        
        products = Product.query.filter_by(
            farmer_id=current_user_id,
            status='available'
        ).all()
        
        products_data = [{
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'amount_available': float(product.amount_available),
            'price_per_unit': float(product.price_per_unit),
            'category': product.category
        } for product in products]
        
        return jsonify(products_data), 200
        
    except Exception as e:
        logger.error(f"Error in get_available_products: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
