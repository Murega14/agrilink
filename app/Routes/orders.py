from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import (db,
                      Buyer,
                      Order,
                      Product,
                      FarmerOrder,
                      OrderItem,
                      Farmer)
from decimal import Decimal

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
        "order_date": order.created_at,
        "delivery_date": order.delivery_date,
        "status": order.status
    } for order in orders]
    
    return jsonify(order_list), 200

@orders.route('/api/v1/orders/create', methods=['POST'])
@jwt_required()
def make_order():
    try:
        user_id = get_jwt_identity()
        buyer = Buyer.query.get(user_id)
        
        if not buyer:
            return jsonify({'error': 'Buyer not found'}), 404
            
        data = request.get_json()
        
        
        new_order = Order(
            buyer_id=user_id,
            total_amount=0,
            status='pending'
        )
        db.session.add(new_order)
        db.session.flush()
        
        if not new_order.id:
            db.session.rollback()
            return jsonify({'error': 'Failed to create order'}), 500
        
        farmer_orders = {}
        total_amount = Decimal('0')
        
        for item in data.get('items', []):
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return jsonify({'error': f'Product {product_id} not found'}), 404
                
            if quantity > product.amount_available:
                db.session.rollback()
                return jsonify({'error': f'Insufficient quantity for product {product_id}'}), 400
            
            if product.farmer_id not in farmer_orders:
                farmer_order = FarmerOrder(
                    order_id=new_order.id,
                    farmer_id=product.farmer_id,
                    subtotal_amount=Decimal('0')
                )
                db.session.add(farmer_order)
                db.session.flush()
                
                if not farmer_order.id:
                    db.session.rollback()
                    return jsonify({'error': 'Failed to create farmer order'}), 500
                    
                farmer_orders[product.farmer_id] = farmer_order
            
            order_item = OrderItem(
                order_id=new_order.id,
                farmer_order_id=farmer_orders[product.farmer_id].id,
                product_id=product.id,
                quantity=quantity,
                price_per_unit=product.price_per_unit
            )
            db.session.add(order_item)
            
            product.amount_available -= quantity
            item_total = Decimal(str(quantity)) * product.price_per_unit
            total_amount += item_total
            farmer_orders[product.farmer_id].subtotal_amount += item_total
        
        new_order.total_amount = total_amount
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': new_order.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@orders.route('/api/v1/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    try:
        user_id = get_jwt_identity()
        buyer = Buyer.query.get(user_id)
        
        if not buyer:
            return jsonify({"error": "user not found"}), 404
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "order not found"}), 404
        
        if order.buyer_id != user_id:
            return jsonify({"error": "unauthorized"}), 401
        
        order_details = {
            "order_id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "delivery_date": order.delivery_date,
            "order_date": order.created_at,
            "items": []
        }
        
        for item in order.order_items:
            product = item.product
            sub_total = float(item.quantity * item.price_per_unit)
            
            item_detail = {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": item.quantity,
                "price_per_unit": float(item.price_per_unit),
                "subtotal": sub_total,
                "farmer_name": product.farmer.full_name
            }
            order_details["items"].append(item_detail)
            
        return jsonify(order_details), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@orders.route('/api/v1/farmer/orders', methods=['GET'])
@jwt_required()
def get_farmer_orders():
    try:
        user_id = get_jwt_identity()
        farmer = Farmer.query.get(user_id)
        
        if not farmer:
            return jsonify({"error": "user not found"}), 404
        
        farmer_orders = FarmerOrder.query.filter_by(farmer_id=user_id).all()
        
        if not farmer_orders:
            return jsonify({"error": "No orders found"}), 200
        
        orders_list = []
        for farmer_order in farmer_orders:
            order = farmer_order.order
            
            items = []
            for item in farmer_order.order_items:
                items.append({
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "price_per_unit": float(item.price_per_unit),
                    "subtotal": float(item.calculate_item_total)
                })
                
            order_detail = {
                "order_id": order.id,
                "order_date": order.created_at,
                "buyer_name": order.buyer.full_name,
                "status": farmer_order.status,
                "subtotal": float(farmer_order.subtotal_amount),
                "items": items
            }
            orders_list.append(order_detail)
            
        return jsonify({"orders": orders_list}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500