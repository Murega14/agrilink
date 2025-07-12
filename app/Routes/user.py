from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Buyer, db
from ..extensions import logger, validate_phone_number
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import SQLAlchemyError

user = Blueprint('user', __name__)

@user.route('/api/v1/userprofile', methods=['GET'])
@jwt_required()
def get_user():
    try:
        user_id = get_jwt_identity()
        
        user = Buyer.query.get_or_404(user_id.get('id'))
        
        user_data = {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number
        }  
        
        response = jsonify(user_data)
        return response, 200
    
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
        
@user.route('/api/v1/user/update', methods=['PUT'])
@jwt_required()
def update_user():
    try:
        user_id = get_jwt_identity()
        user = Buyer.query.get_or_404(user_id)
        
        data = request.get_json()
        
        try:
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                try:
                    validate_email(data['email'])
                    user.email = data['email']
                except EmailNotValidError:
                    return jsonify({"error": "invalid email format"}), 400
            if 'phone_number' in data:
                try:
                    validate_phone_number(data['phone_number'])
                    user.phone_number = data['phone_number']
                except:
                    return jsonify({"error": "invalid phone number"}), 400
            
            db.session.commit()
            response = jsonify({
                "success": True,
                "message": "profile details updated successfully"
            })
            
            return response, 200
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to update user details",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
        
@user.route('/api/v1/user/delete', methods=['DELETE'])
@jwt_required()
def delete_user():
    try:
        user_id = get_jwt_identity()
        user = Buyer.query.get_or_404(user_id)
        
        try:
            db.session.delete(user)
            db.session.commit()
            
            response = jsonify({
                "success": True,
                "message": "user account deleted"
            })
            
            return response, 200
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to delete user account",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "Error": str(e)
        }), 500
        