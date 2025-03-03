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
from ..extensions import logger, get_current_user_id
from sqlalchemy.exc import SQLAlchemyError

orders = Blueprint('orders', __name__)

@orders.route('/api/v1/orders', methods=['GET'])
@buyer_required
def get_orders():
    """
    fetch all orders for the current buyer

    Returns:
        Response: JSON response containing the list of orders and pagination details.
    """
    try:
        buyer_id = get_current_user_id()
        
        # set up pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 8, type=int)
        
        #fetch the orders and include pagination
        orders_query = Order.query.filter_by(buyer_id=buyer_id)
        pagination = orders_query.paginate(page=page, per_page=per_page)
        orders = pagination.items
        
        order_list = [{
            "id": order.id,
            "total_amount": float(order.total_amount),
            "order_date": order.created_at.isoformat(),
            "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
            "status": order.status,
            "items": [{
                "product_id": item.product.id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price_per_unit": float(item.price_per_unit),
                "subtotal": float(item.calculate_item_total()),
                "farmer_name": item.product.farmer.full_name if item.product.farmer else None
            } for item in order.order_items]
        } for order in orders]
        
        response = jsonify({
            "orders": order_list,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total
        })
        
        return response, 200
    
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "failed to fetch orders",
            "error": str(e)
        }), 500

@orders.route('/api/v1/orders/create', methods=['POST'])
@buyer_required    
def make_order():
    """
    Create a new order for the current buyer.

    The function expects a JSON payload with order items, validates the data, 
    and creates an order along with associated farmer orders and order items.

    Returns:
        Response: JSON response with success message or error details.
    """
    try:
        buyer_id = get_current_user_id()
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({"error": "invalid request"}), 400
        
        try:
            new_order = Order(buyer_id=buyer_id, total_amount=0, status='pending')
            db.session.add(new_order)
            db.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"database error, trying to initialize order: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to initialize order",
                "error": str(e)
            }), 400
            
        farmer_orders = {}
        total_amount = Decimal('0')
        
        try:
            for item in data['items']:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)
                
                product = Product.query.get_or_404(product_id)
                if quantity <= 0:
                    return jsonify({"error": "quantity must be greater than zero"}), 400
                
                if quantity > product.amount_available:
                    return jsonify({"message": f"only {product.amount_available} is available"}), 400
                
                farmer_order =farmer_orders.get(product.farmer_id)
                if not farmer_order:
                    try:
                        farmer_order = FarmerOrder(
                        order_id=new_order.id,
                        farmer_id=product.farmer_id,
                        subtotal_amount=0
                        )
                        db.session.add(farmer_order)
                        db.session.flush()
                    except SQLAlchemyError as e:
                        logger.error(f"failed to create farmer order: {str(e)}")
                        db.session.rollback()
                        return jsonify({
                            "message": "failed to create farmer order",
                            "error": str(e)
                        })
                    
                    farmer_orders[product.farmer_id] = farmer_order
                    
                try:
                    order_item = OrderItem(
                        order_id=new_order.id,
                        farmer_order_id=farmer_order.id,
                        product_id=product.id,
                        quantity=quantity,
                        price_per_unit=product.price_per_unit
                    )
                    db.session.add(order_item)
                    
                    product.amount_available -= quantity
                    item_total = Decimal(quantity) * product.price_per_unit
                    total_amount += item_total
                    farmer_order.subtotal_amount += item_total
                except SQLAlchemyError as e:
                    logger.error(f"failed to additems to the order: {str(e)}")
                    db.session.rollback()
                    return jsonify({
                        "message": "Failed to add order items",
                        "error": str(e)
                    }), 400
                    
            new_order.total_amount = total_amount
            db.session.commit()
            
            response = jsonify({
                "success": True,
                "message": "order created successfully"
            })
            return response, 201
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to create order",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
        

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
    