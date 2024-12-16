from flask import Blueprint, session, abort, request, flash, jsonify, render_template, make_response, current_app, url_for, redirect
from functools import wraps
from ..models import db, Farmer, Buyer
from datetime import timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from ..extensions import mail
import re

authentication = Blueprint('authentication', __name__)

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=5000):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except Exception as e:
        return None
    return email


@authentication.route('/signup/farmer', methods=['POST'])
def signup_farmer():
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone_number = data.get('phone_number')
    email = data.get('email')
    password = data.get('password')
        
    if not all([first_name, last_name, phone_number, email, password]):
        return jsonify({"error": "all fields are required"}), 400
        
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "email format is invalid"}), 400
        
    if not re.match(r"^\d{10}$", phone_number):
        return jsonify({"error": "phone number must be 10 digits"}), 400
        
    if db.session.query(Farmer.id).filter((Farmer.email == email) | (Farmer.phone_number == phone_number)).first():
        return jsonify({"error": "email or phone number exists"}), 400
        
    new_farmer = Farmer(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email)
    new_farmer.hash_password(password)
    db.session.add(new_farmer)
    db.session.commit()
        
    return jsonify({"success": "farmer account created sucessfully"}), 201

@authentication.route('/signup/buyer', methods=['POST'])
def signup_buyer():
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
         
    if not all([first_name, last_name, phone_number, email, password]):
        return jsonify({"error": "all fields are required"}), 400
            
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "invalid email format"}), 400
        
    if not re.match(r"^\d{10}$", phone_number):
        return jsonify({"error": "phone number must be 10 digits"}), 400
        
    if db.session.query(Buyer.id).filter((Buyer.email == email) | (Buyer.phone_number == phone_number)).first():
        return jsonify({"error": "email or phone number exists"}), 400
        
    new_buyer = Buyer(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email)
    new_buyer.hash_password(password)
    db.session.add(new_buyer)
    db.session.commit()
        
    return jsonify({"success": "buyer account created sucessfully"}), 201


@authentication.route('/login/farmer', methods=['POST'])
def login_farmer():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
        
    if not all([identifier, password]):
        return jsonify({"error": "all fields are required"}), 401
        
    farmer = Farmer.query.filter((Farmer.email == identifier) | (Farmer.phone_number == identifier)).first()
    if farmer and farmer.check_password(password):
        expires = timedelta(hours=2)
        access_token = create_access_token(identity=farmer.id, expires_delta=expires)
        response = make_response(jsonify({
            "login": "sucess"
        })), 201
        response = jsonify({
            "success": True,
            "message": "Login successful",
            "token": access_token
            })
        response.set_cookie(
            "session_token",
            access_token,
            httponly=True,
            secure=False
        )
            
        return response
    else:
        return jsonify({"error": "we don't know you"}), 401
        

@authentication.route('/login/buyer', methods=['POST'])
def login_buyer():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
        
    if not all([identifier, password]):
        return jsonify({"error": "all fields are required"}), 401
        
    buyer = Buyer.query.filter((Buyer.phone_number == identifier) | (Buyer.email == identifier)).first()
    if buyer and buyer.check_password(password):
        expires = timedelta(hours=2)
        access_token = create_access_token(identity=buyer.id, expires_delta=expires)
        response = jsonify({
            "success": True,
            "message": "Login successful",
            "token": access_token
        })
        response.set_cookie(
            "session_token",
            access_token,
            httponly=True,
            secure=False  #remember to set to True in production
        )
            
        return response
            
    else:
        return jsonify({"error": "we don't know you"}), 401

@authentication.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = Farmer.query.filter_by(email=email).first() or Buyer.query.filter_by(email=email).first()
        
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('authentication.reset_password', token=token, _external=True)
            
            msg = Message("Password Reset Request", sender="tedmurega@gmail.com", recipients=[email])
            msg.body = f"To reset your password, click the following link: {reset_url}"
            mail.send(msg)
            
            flash("A password reset link has been sent to your email", 'info')
            return jsonify({"message": "A password reset link has been sent to your email"}), 200
        else:
            flash('Email not found.', 'warning')
            return jsonify({"error": "Email not found"}), 404

    return render_template('forgot_password.html')

           

@authentication.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        user = Farmer.query.filter_by(email=email).first() or Buyer.query.filter_by(email=email).first()
        if user:
            user.hash_password(password)
            db.session.commit()
            flash('Your password has been reset successfully.', 'success')
            return redirect(url_for('index'))
        
    return render_template('reset_password.html')

