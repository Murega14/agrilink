from functools import wraps
from flask import session, abort,jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def farmer_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if not isinstance(identity, dict) or identity.get('role') != 'farmer':
            return jsonify({"error": "Farmer access required"}),403
        return function(*args, **kwargs)
    return wrapper

def buyer_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity.get('role') != 'buyer':
            return jsonify({"error": "buyer access required"}), 403
        return function(*args, **kwargs)
    return wrapper

def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "id" not in session:
            return abort(401)
        else:
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper

