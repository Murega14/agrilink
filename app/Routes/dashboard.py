from flask import Blueprint, session, jsonify, request
from ..models import Farmer, Order, Product, db
from datetime import datetime, timedelta
from ..wrappers import login_is_required
from sqlalchemy import func

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/api/dashboard/stats', methods=['GET'])
@login_is_required
def view_dashboard():
    user_id = session.get('id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    today = datetime.now()
    last_month = today - timedelta(days=30)
    two_months_ago = today - timedelta(days=60)
    
    # Current month stats
    current_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.farmer_id == user_id,
        Order.order_date >= last_month,
        Order.status == 'delivered'
    ).scalar() or 0
    
    # Last month stats for comparison
    last_month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.farmer_id == user_id,
        Order.order_date.between(two_months_ago, last_month),
        Order.status == 'delivered'
    ).scalar() or 0
    
    # Calculate month-over-month change
    revenue_change = 0
    if last_month_revenue > 0:
        revenue_change = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    
    # Products sold in current month
    products_sold = Order.query.filter(
        Order.farmer_id == user_id,
        Order.order_date >= last_month,
        Order.status == 'delivered'
    ).count()
    
    # Products sold in previous month
    last_month_products = Order.query.filter(
        Order.farmer_id == user_id,
        Order.order_date.between(two_months_ago, last_month),
        Order.status == 'delivered'
    ).count()
    
    # Calculate products change percentage
    products_change = 0
    if last_month_products > 0:
        products_change = ((products_sold - last_month_products) / last_month_products) * 100
    
    stats = {
        "products_sold": {
            "value": products_sold,
            "change": round(products_change, 1)
        },
        "current_month_value": {
            "value": float(current_month_revenue),
            "change": round(revenue_change, 1)
        },
        "pending_orders": {
            "value": Order.query.filter_by(
                farmer_id=user_id, 
                status='pending'
            ).count()
        },
        "active_listings": {
            "value": Product.query.filter_by(
                farmer_id=user_id, 
                status='available'
            ).count()
        }
    }
    
    return jsonify(stats)

@dashboard.route('/api/dashboard/recent-orders', methods=['GET'])
@login_is_required
def get_recent_orders():
    user_id = session.get('id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    recent_orders = Order.query.filter_by(farmer_id=user_id).order_by(
        Order.order_date.desc()
    ).limit(5).all()
    
    return jsonify([{
        "order_id": order.id,
        "order_date": order.created_at.isoformat(),
        "total_amount": float(order.total_amount),
        "status": order.status
    } for order in recent_orders])

@dashboard.route('/api/dashboard/available-products', methods=['GET'])
@login_is_required
def get_available_products():
    user_id = session.get('id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    products = Product.query.filter_by(
        farmer_id=user_id, 
        status='available'
    ).all()
    
    return jsonify([{
        "product_id": product.id,
        "name": product.name,
        "price_per_unit": float(product.price_per_unit),
        "amount_available": product.amount_available
    } for product in products])