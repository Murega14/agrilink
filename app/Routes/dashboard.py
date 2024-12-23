from flask import Blueprint, session, jsonify, request
from ..models import Farmer, Order, Product, db
from datetime import datetime, timedelta
from ..wrappers import login_is_required

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/api/dashboard/stats', methods=['GET'])
@login_is_required
def view_dashboard():
    user_id = session.get('id')
    
    #get the current date and last month date for comparisons
    today = datetime.now()
    last_month = today - timedelta(days=30)
    
    #get statistics for orders
    total_orders = Order.query.filter_by(farmer_id=user_id).count()
    pending_orders = Order.query.filter_by(farmer_id=user_id, status='pending').count()
    delivered_orders = Order.query.filter_by(farmer_id=user_id, status='delivered').count()
    
    #calculate revenue
    current_month_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.farmer_id == user_id,
        Order.order_date >= last_month,
        Order.status == 'delivered'
    ).scalar() or 0
    
    #getting the products available
    active_listings = Product.query.filter_by(farmer_id=user_id, status='available').count()
    
    return jsonify({
        "products_sold": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "current_month_revenue": current_month_revenue,
        "active_listings": active_listings
    })
    
@dashboard.route('/api/dashboard/recent-orders', methods=['GET'])
@login_is_required
def get_recent_orders():
    user_id = session.get('id')
    
    recent_orders = Order.query.filter_by(farmer_id=user_id).order_by(
        Order.order_date.desc()
    ).limit(5).all()
    
    orders_list = []
    for order in recent_orders:
        orders_list.append({
            "order_id": order.id,
            "order_date": order.order_date,
            "total_amount": order.total_amount,
            "status": order.status
        })
        
    return jsonify(orders_list)

@dashboard.route('/api/dashboard/available-products', methods=['GET'])
@login_is_required
def get_available_products():
    user_id = session.get('id')
    
    products = Product.query.filter_by(farmer_id=user_id, status='available').all()
    
    products_list = []
    for product in products:
        products_list.append({
            "product_id": product.id,
            "name": product.name,
            "price": product.price_per_unit,
            "amount": product.amount_available
        })
        
    return jsonify(products_list)