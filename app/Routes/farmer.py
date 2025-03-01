from flask import jsonify, Blueprint, request
from ..extensions import logger, validate_phone_number
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import SQLAlchemyError
from ..models import db, Farmer
from flask_jwt_extended import jwt_required, get_jwt_identity

farmer = Blueprint('farmer', __name__)

@farmer.route('/api/v1/farmerprofile', methods=['GET'])
@jwt_required()
def get_farmer():
    try:
        farmer_id = get_jwt_identity()
        farmer = Farmer.query.get_or_404(farmer_id)
        
        farmer_details = {
            "id": farmer.id,
            "name": farmer.full_name(),
            "email": farmer.email,
            "phone_number":  farmer.phone_number
        }
        
        response = jsonify(farmer_details)
        return response, 200
    
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "failed to fetch user details",
            "error": str(e)
        }), 500
        
@farmer.route('/api/v1/farmer/update', methods=['PUT'])
@jwt_required()
def update_farmer():
    try:
        farmer_id = get_jwt_identity()
        farmer = Farmer.query.get_or_404(farmer_id)
        
        data = request.get_json()
        try:
            if 'first_name' in data:
                farmer.first_name = data['first_name']
            if 'last_name' in data:
                farmer.last_name = data['last_name']
            if 'email' in data:
                try:
                    validate_email(data['email'])
                    farmer.email = data['email']
                except EmailNotValidError:
                    return jsonify({"error": "invalid email format"}), 400
            if 'phone_number' in data:
                try:
                    validate_phone_number(data['phone_number'])
                    farmer.phone_number = data['phone_number']
                except:
                    return jsonify({"error": "invalid phone number format"}), 400
            
            db.session.commit()
            
            response = jsonify({
                "success": True,
                "message": "farmer details updated"
            })
            return response, 200
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to update farmer details",
                "error": str(e)
            }), 400
        
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
        
@farmer.route('/api/v1/farmer/delete', methods=['DELETE'])
@jwt_required()
def delete_farmer():
    try:
        farmer_id = get_jwt_identity()
        farmer = Farmer.query.get_or_404(farmer_id)
        
        try:
            db.session.delete(farmer)
            db.session.commit()
            
            response = jsonify({
                "success": True,
                "message": "farmer profile deleted"
            })
            return response, 200
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to delete farmer account",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500