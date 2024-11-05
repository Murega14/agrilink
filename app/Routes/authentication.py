from flask import Blueprint, session, abort, request, flash, jsonify, render_template, make_response
from functools import wraps
from ..models import db, Farmer, Buyer
from datetime import timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


authentication = Blueprint('authentication', __name__)

def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "id" not in session:
            return abort(401)
        else:
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper

@authentication.route('/signup/farmer', methods=['GET', 'POST'])
def signup_farmer():
    if request.method == 'POST':
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        
        if not all([first_name, last_name, phone_number, email, password]):
            return jsonify({"error": "All fields are required"}), 403
        
        if Farmer.query.filter((Farmer.email == email) | (Farmer.phone_number == phone_number)).first():
            return jsonify({"error": "Phone number or email already exists"}), 403
        
        new_farmer = Farmer(first_name, last_name, phone_number, email)
        new_farmer.hash_password(password)
        db.session.add(new_farmer)
        db.session.commit()
        
        return jsonify({"message": "Farmer account created successfully"}), 201

    return render_template('signup_farmer.html')

@authentication.route('/signup/buyer', methods=['GET', 'POST'])
def signup_buyer():
    if request.method == 'POST':
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        
        if not all([first_name, last_name, phone_number, email, password]):
            return jsonify({"error": "all fields are required"}), 403
        
        if Buyer.query.filter((Buyer.email == email) | (Buyer.phone_number == phone_number)).first():
            return jsonify({"error": "email or phone number exists"}), 403
        
        new_buyer = Buyer(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email)
        new_buyer.hash_password(password)
        db.session.add(new_buyer)
        db.session.commit()
        
        return jsonify({"message": "Buyer created Successfully"}), 201
    
    return render_template('signup_buyer.html')

@authentication.route('/login/farmer', methods=['GET', 'POST'])
def login_farmer():
    if request.method == 'POST':
        data = request.get_json()
        identifier = data.get('identifier')
        password = data.get('password')
        
        if not all([identifier, password]):
            return jsonify({"error": "all fields are required"})
        
        farmer = Farmer.query.filter((Farmer.email == identifier) | (Farmer.phone_number == identifier)).first()
        if farmer and farmer.check_password(password):
            expires = timedelta(hours=2)
            access_token = create_access_token(identity=farmer.id, expires_delta=expires)
            response = make_response(jsonify({
                "login": "sucess"
            })), 201
            response.set_cookie("session_token",
                                access_token,
                                httponly=True,
                                secure=True)
            
            return jsonify(response), 200
        else:
            return jsonify({"error": "we don't know you"}), 401
        
    return render_template('login_farmer.html')

@authentication.route('/login/buyer', methods=['GET', 'POST'])
def login_buyer():
    if request.method == 'POST':
        data = request.get_json()
        identifier = data.get('identifier')
        password = data.get('password')
        
        if not all([identifier, password]):
            return jsonify({"error": "all fields are required"}), 401
        
        buyer = Buyer.query.filter((Buyer.phone_number == identifier) | (Buyer.email == identifier)).first()
        if buyer and buyer.check_password(password):
            expires = timedelta(hours=2)
            access_token = create_access_token(identity=buyer.id, expires_delta=expires)
            response = make_response(jsonify({
                "login": "success"
            })), 201
            response.set_cookie("session_token",
                                access_token,
                                httponly=True,
                                secure=True)
            
            return jsonify(response), 200
        else:
            return jsonify({"error": "we don't know you"}), 401
        
    return render_template('login_buyer.html')
    
