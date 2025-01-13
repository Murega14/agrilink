from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Buyer

user = Blueprint('user', __name__)

@user.route('/api/v1/userprofile', methods=['GET'])
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    
    user = Buyer.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    
    user_data = {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number
    }
    
    return jsonify(user_data)
    