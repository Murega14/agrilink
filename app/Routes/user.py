from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..models import Buyer
from ..extensions import get_current_user_id

user = Blueprint('user', __name__)

@user.route('/api/v1/userprofile', methods=['GET'])
@jwt_required()
def get_user():
    user_id = get_current_user_id()
    
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
    