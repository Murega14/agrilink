from flask import Blueprint, request, jsonify
from ..models import (db,
                      Buyer,
                      Order,
                      Product,
                      FarmerOrder,
                      OrderItem,
                      Farmer)
from decimal import Decimal
from ..wrappers import buyer_required, farmer_required
from ..extensions import get_current_user_id
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orders = Blueprint('orders', __name__)

@orders.route('/api/v1/orders', methods=['GET'])
@buyer_required
def get_orders():
    """
    Fetch all orders for the current buyer, including order items.
    """
    try:
        user_id = get_current_user_id()
        buyer = Buyer.query.get(user_id)
        
        if not buyer:
            logger.error(f"Buyer not found: {user_id}")
            return jsonify({"error": "Buyer not found"}), 404
        
        # Get pagination parameters from the request
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if page <= 0 or per_page <= 0:
            logger.error(f"Invalid pagination parameters: page={page}, per_page={per_page}")
            return jsonify({"error": "Page and per_page must be greater than 0"}), 400
        
        # Fetch orders with pagination
        orders_query = Order.query.filter_by(buyer_id=user_id)
        pagination = orders_query.paginate(page=page, per_page=per_page)
        orders = pagination.items
        
        # Build the response with order details and items
        order_list = []
        for order in orders:
            order_details = {
                "id": order.id,
                "total_amount": float(order.total_amount),
                "order_date": order.created_at.isoformat(),
                "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
                "status": order.status,
                "items": []
            }
            
            # Add order items to the order details
            for item in order.order_items:
                product = item.product
                item_details = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "price_per_unit": float(item.price_per_unit),
                    "subtotal": float(item.calculate_item_total),
                    "farmer_name": product.farmer.full_name
                }
                order_details["items"].append(item_details)
            
            order_list.append(order_details)
        
        # Return paginated response
        return jsonify({
            "orders": order_list,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500



@orders.route('/api/v1/orders/create', methods=['POST'])
@buyer_required
def make_order():
    """
    create a new order for the current buyer
    """
    try:
        user_id = get_current_user_id()
        buyer = Buyer.query.get(user_id)
        
        if not buyer:
            logger.error(f"Buyer not found: {user_id}")
            return jsonify({"error": "Buyer not found"}), 404
        
        data = request.get_json()
        if not data or 'items' not in data:
            logger.error("Invalid request data")
            return jsonify({"error": "Invalid request data"}), 400
        
        new_order = Order(buyer_id=user_id, total_amount=0, status='pending')
        db.session.add(new_order)
        db.session.flush()
        
        if not new_order.id:
            logger.error("Failed to create order")
            db.session.rollback()
            return jsonify({"error": "Failed to create order"}), 500
        
        farmer_orders = {}
        total_amount = Decimal('0')
        
        for item in data['items']:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            if not product_id or quantity <= 0:
                logger.error(f"Invalid item data: {item}")
                db.session.rollback()
                return jsonify({"error": "Invalid item data"}), 400
            
            product = Product.query.get(product_id)
            if not product:
                logger.error(f"Product not found: {product_id}")
                db.session.rollback()
                return jsonify({"error": "product not found"}), 400
            
            if quantity > product.amount_available:
                logger.error(f"Insufficient quantity only {product.amount_available} available")
                db.session.rollback()
                return jsonify({"error": "insufficient quantity for product {product_id} only {product.amount_available} available"}), 400
            
            farmer_order = farmer_orders.get(product.farmer_id)
            if not farmer_order:
                farmer_order = FarmerOrder(
                    order_id=new_order.id,
                    farmer_id=product.farmer_id,
                    subtotal_amount=Decimal('0')
                )
                db.session.add(farmer_order)
                db.session.flush()
                
                if not farmer_order.id:
                    logger.error(f"failed to create the farmer order")
                    db.session.rollback()
                    return jsonify({"error": "Failed to create farmer order"}), 500
                
                farmer_orders[product.farmer_id] = farmer_order
                
            order_item = OrderItem(
                order_id=new_order.id,
                farmer_order_id=farmer_order.id,
                product_id=product.id,
                quantity=quantity,
                price_per_unit=product.price_per_unit
            )
            db.session.add(order_item)
            
            product.amount_available -= quantity
            item_total = Decimal(str(quantity)) * product.price_per_unit
            total_amount += item_total
            farmer_order.subtotal_amount += item_total
            
        new_order.total_amount = total_amount
        db.session.commit()
        
        logger.info(f"Order created successfully: {new_order.id}")
        return jsonify({
            "message": "order created successfully",
            "order_id": new_order.id,
            "buyer_id": buyer.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    
@orders.route('/api/v1/orders/<int:order_id>', methods=['GET'])
@buyer_required
def get_order_details(order_id):
    """
    fetch details of a specific order

    Args:
        order_id (integer): unique identifier for order
    """
    try:
        user_id = get_current_user_id()
        buyer = Buyer.query.get(user_id)
        
        if not buyer:
            logger.error(f"buyer not found: {user_id}")
            return jsonify({"error": "buyer not found"}), 404
        
        order = Order.query.get(order_id)
        if not order:
            logger.error(f"order not found: {order_id}")
            return jsonify({"error": "order not found"}), 404
        
        if order.buyer_id != user_id:
            logger.error(f"unauthorized access to order: {order_id} by {user_id}")
            return jsonify({"error": "unauthorized"}), 401
        
        order_details = {
            "order_id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
            "order_date": order.created_at.isoformat(),
            "items": []
        }
        
        for item in order.order_items:
            product = item.product,
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
        logger.error(f"Error fetching order details: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
@orders.route('/api/v1/farmer/orders', methods=['GET'])
@farmer_required
def get_farmer_orders():
    """
    fetch all orders for the current farmer
    """
    try:
        user_id = get_current_user_id()
        farmer = Farmer.query.get(user_id)
        
        if not farmer:
            logger.error(f"farmer not found: {user_id}")
            return jsonify({"error": "farmer not found"}), 404
        
        farmer_orders = FarmerOrder.query.filter_by(farmer_id=user_id).all()
        if not farmer_orders:
            return jsonify({"message": "No orders found"}), 200
        
        orders_list = []
        for farmer_order in farmer_orders:
            order = farmer_order.order
            
            items= []
            for item in farmer_order.order_items:
                items.append({
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "price_per_unit": float(item.price_per_unit),
                    "subtotal": float(item.quantity * item.price_per_unit)
                })
                
            order_detail = {
                "order_id": order.id,
                "order_date": order.created_at.isoformat(),
                "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
                "buyer_name": order.buyer.full_name,
                "status": farmer_order.status,
                "subtotal": float(farmer_order.subtotal_amount),
                "items": items
            }
            orders_list.append(order_detail)
            
        return jsonify({"orders": orders_list}), 200
    
    except Exception as e:
        logger.error(f"error fetching farmer orders: {str(e)}")
        return jsonify({"error": "internal server error"}), 500
    