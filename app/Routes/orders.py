from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, Buyer, Order

orders = Blueprint('orders', __name__)

@orders.route('/api/v1/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    user = Buyer.query.get(user_id)
    
    if not user:
        return jsonify({"error": "user not found"}), 404
    
    orders = Order.query.filter_by(buyer_id=user_id).all()
    
    order_list = [{
        "id": order.id,
        "amount": order.total_amount,
        "delivery_date": order.delivery_date,
        "status": order.status
    } for order in orders]
    
    return jsonify(order_list), 200
    
    