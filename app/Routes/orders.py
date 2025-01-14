from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, Buyer, Order, Product, FarmerOrder, OrderItem

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

@orders.route('/api/v1/orders/create', methods=['POST'])
@jwt_required()
def make_order():
    try:
        user_id = get_jwt_identity()
        user = Buyer.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({"error": "no items provided"}), 400
        
        # creating a main order and will then add items to
        # the order items table
        new_order = Order(
            buyer_id=user_id,
            total_amount=0,
            status='pending'
        )
        db.session.add(new_order)
        db.session.flush()
        
        # tracking orders for each farmer
        farmer_orders = {}
        total_amount = 0
        
        # processing each order item
        for item in data['items']:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            if not all([product_id, quantity]):
                db.session.rollback()
                return jsonify({"error": "invalid item data"}), 400
            
            product = Product.query.get(product_id)
            if not product or product.status != 'available':
                db.session.rollback()
                return jsonify({"error": f"product {product.id} not found"}), 400
            
            if product.amount_available < quantity:
                db.session.rollback()
                return jsonify({"error": f"insufficient quantity, only {product.amount_available} available"}), 400
            
            #create a farmer order 
            if product.farmer_id not in farmer_orders:
                farmer_order = FarmerOrder(
                    order_id=new_order.id,
                    farmer_id=product.farmer_id,
                    subtotal_amount=0
                )
                db.session.add(farmer_order)
                db.session.flush()
                farmer_orders[product.farmer_id] = farmer_order
                
            #create an order item
            order_item = OrderItem(
                order_id=new_order.id,
                farmer_order_id=farmer_orders[product.farmer_id],
                product_id=product.id,
                quantity=quantity,
                price_per_unit=product.price_per_unit
            )
            db.session.add(order_item)
            
            product.amount -= quantity
            
            item_total = quantity * float(product.price_per_unit)
            total_amount += item_total
            farmer_orders[product.farmer_id].subtotal_amount += item_total
            
        new_order.total_amount = total_amount
        db.session.commit()
        
        return jsonify({
            "message": "Order created successfully",
            "order_id": new_order.id,
            "total_amount": float(new_order.total_amount)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    