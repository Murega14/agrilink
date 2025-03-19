from flask import (
    Blueprint,
    session,
    request,
    jsonify,
    make_response,
    current_app,
    url_for
)
from ..models import db, Farmer, Buyer
from datetime import timedelta
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request
)
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from ..extensions import mail
from ..wrappers import login_is_required
import re
from sqlalchemy.exc import SQLAlchemyError
import logging
from email_validator import validate_email, EmailNotValidError
from itsdangerous import SignatureExpired, BadSignature

authentication = Blueprint('authentication', __name__)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):  # Reduced to 1 hour
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token, 
            salt='password-reset-salt',
            max_age=expiration
        )
        return email
    except (SignatureExpired, BadSignature) as e:
        logger.warning(f"Invalid reset token: {str(e)}")
        return None

def validate_password(password):
    """
    Validate password meets security requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains number
    - Contains special character
    """
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def validate_phone_number(phone_number):
    if not re.search(r"\d{10}$", phone_number):
        return False
    return True


@authentication.route('/api/v1/signup/farmer', methods=['POST'])
def signup_farmer():
    try:
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        
        if not all([first_name, last_name, phone_number, email, password]):
            return jsonify({"error": "all fields are required"}), 400
        
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({"error": "invalid email format"}), 400
        
        try:
            validate_phone_number(phone_number)
        except ValueError:
            return jsonify({"error": "invalid phone number format"}), 400
        
        try:
            validate_password(password)
        except ValueError:
            return jsonify({"error": "password must contain 8 letters, 1 uppercase, lowercase, 1 digit and 1 special character"}), 400
        
        if Farmer.query.filter((Farmer.email == email) or (Farmer.phone_number == phone_number)).first():
            return jsonify({"error": "phone number or email exists"}), 400
        
        try:
            new_farmer = Farmer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number
            )
            new_farmer.hash_password(password)
            db.session.add(new_farmer)
            db.session.commit()
            
            identity = {
                'id': new_farmer.id,
                'role': 'farmer'
            }
            expires = timedelta(hours=2)
            access_token = create_access_token(identity=identity, expires_delta=expires)
            
            response = jsonify({
                "success": True,
                "message": "Account created",
                "access_token": access_token
            })
            return response, 201
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to create farmer account",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
        
@authentication.route('/api/v1/signup/buyer', methods=['POST'])
def signup_buyer():
    try:
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        if not ([first_name, last_name, email, phone_number, password]):
            return jsonify({"error": "all fields are required"}), 400
        
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({"error": "invalid email format"}), 400
        
        try:
            validate_phone_number(phone_number)
        except ValueError:
            return jsonify({"error": "invalid phone number"}), 400
        
        try:
            validate_password(password)
        except ValueError:
            return jsonify({"error": "password must contain 8 letters, 1 uppercase, lowercase letter, 1 digit and i special character"}), 400
        
        if Buyer.query.filter((Buyer.email == email) or (Buyer.phone_number == phone_number)).first():
            return jsonify({"error": "email or phone number exists"}), 400
        
        try:
            new_buyer = Buyer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number
            )
            new_buyer.hash_password(password)
            db.session.add(new_buyer)
            db.session.commit()
            
            identity = {
                'id': new_buyer.id,
                'role': 'buyer'
            }
            expires = timedelta(hours=2)
            access_token = create_access_token(identity=identity, expires_delta=expires)
            
            response = jsonify({
                "success": True,
                "message": "Buyer account created",
                "access_token": access_token
            })
            
            return response, 201
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to create buyer account",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500

@authentication.route('/api/v1/login/farmer', methods=['POST'])
def login_farmer():
    try:
       
        data = request.get_json()
        identifier = data.get('identifier')
        password = data.get('password')
        
        if not all([identifier, password]):
            return jsonify({"error": "missing required fields"}), 400
        
        try:
            farmer = Farmer.query.filter((Farmer.email==identifier) or (Farmer.phone_number==identifier)).first()
            
            if not farmer or not farmer.check_password(password):
                return jsonify({"error": "invalid login credentials"}),401
            
            identity = {
                'id': farmer.id,
                'role': 'farmer'
            }
            expires = timedelta(hours=1)
            access_token = create_access_token(identity=identity, expires_delta=expires)
            refresh_token = create_refresh_token(identity=identity)
            
            response = jsonify({
                "success": True,
                "message": "login successful",
                "token": access_token,
                "refresh_token": refresh_token
            })
            response.set_cookie(
                "session_token",
                access_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=7200
            )
            
            return response, 200
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            return jsonify({
                "message": "database error, failed to login user",
                "error": str(e)
            }), 400
            
        except Exception as e:
            logger.error(f"an error occured while logging in: {str(e)}")
            return jsonify({
                "message": "an error occured when logging in",
                "error": str(e)
            }), 400
    
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500

@authentication.route('/api/v1/login/buyer', methods=['POST'])
def login_buyer():
    try:
        
        data = request.get_json()
        identifier = data.get('identifier')
        password = data.get('password')
        
        if not all([identifier, password]):
            return jsonify({"error": "missing fields required"}), 400
        
        try:
            buyer = Buyer.query.filter((Buyer.email==identifier) or (Buyer.phone_number==identifier)).first()
            
            if not buyer or not buyer.check_password(password):
                return jsonify({"error": "invalid login credentials"}), 401
            
            identity = {
                'id': buyer.id,
                'role': 'farmer'
            }
            expires = timedelta(hours=1)
            access_token = create_access_token(identity=identity, expires_delta=expires)
            refresh_token = create_refresh_token(identity=identity)
            
            response = jsonify({
                "success": True,
                "message": "login successful",
                "token": access_token,
                "refresh_token": refresh_token,
            })
            response.set_cookie(
                "session_token",
                access_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=7200
            )
            
            return response, 200
        
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            return jsonify({
                "message": "database error, failed to login",
                "error": str(e)
            }), 400
            
        except Exception as e:
            logger.error(f"an error occured logging in: {str(e)}")
            return jsonify({
                "message": "an error occured while logging in",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "Error": str(e)
        }), 500

@authentication.route('/api/v1/logout', methods=['POST'])
@login_is_required
def logout():
    try:
        session.clear()
        response = jsonify({
            "success": True,
            "message": "logged out successfully"
        })
        response.set_cookie('session_token', '', expires=0)
        
        return response, 200
    
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "failed to logout",
            "error": str(e)
        }), 500

@authentication.route('/api/v1/farmer/change_password', methods=['PATCH'])
@login_is_required
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = Farmer.query.get_or_404(user_id)
        
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not all([old_password, new_password]):
            return jsonify({"error": "missing fields required"}), 400
        
        if not user.check_password(old_password):
            return jsonify({"error": "incorrect password"}), 400
        
        try:
            validate_password(new_password)
        except ValueError:
            return jsonify({"Error": "password must contain atleast 8 characters, 1 uppercase, lowercase letter, 1 number and 1 special digit"}), 400
        
        if old_password == new_password:
            return jsonify({"error": "old password cannot be the same as the new password"}), 400
        
        try:
            hashed_password = user.hash_password(new_password)
            user.password_hash = hashed_password
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "password updated successfully"
            }), 200
            
        except SQLAlchemyError as e:
            logger.error(f"database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                "message": "failed to update password",
                "error": str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500

@authentication.route('/api/v1/forgot_password', methods=['GET'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({"error": "email is required"})
        
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({"error": "invalid email format"}), 400
        
        token = generate_reset_token(email)
        reset_url = url_for('authentication.reset_password', token=token, _external=True)
        
        farmer = Farmer.query.filter_by(email=email).first()
        if not farmer:
            try:
                buyer = Buyer.query.filter_by(email=email).first()
                if buyer:
                    try:
                        msg = Message(
                            subject="Password Reset Request",
                            sender=current_app.config['MAIL_USERNAME'],
                            recipients=[email],
                            body=f"""
                            Hello,
                            
                            You have requested to reset your password. Please click the link below:
                            
                            {reset_url}
                            
                            If you did not request this, please ignore this email.
                            
                            This link will expire in 1 hour.
                            
                            Best regards,
                            AgriLink Team
                            """
                        )
                        mail.send(msg)
                        return jsonify({
                            "success": True,
                            "message": "password reset link sent to email"
                        }), 200
                        
                    except Exception as e:
                        logger.error(f"failed to send email to buyer: {str(e)}")
                        return jsonify({
                            "message": "failed to send email to buyer",
                            "error": str(e)
                        }), 400
                        
            except:
                return jsonify({"error": "user not found"}), 400

        if farmer:
            try:
                msg = Message(
                    subject="Password Reset Request",
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[email],
                    body=f"""
                    Hello,
                    
                    You have requested to reset your password. Please click the link below:
                    
                    {reset_url}
                    
                    If you did not request this, please ignore this email.
                    
                    This link will expire in 1 hour.
                    
                    Best regards,
                    AgriLink Team
                    """
                )
                mail.send(msg)
                return jsonify({
                    "success": True,
                    "message": "password resent link sent to email"
                }), 200
            except Exception as e:
                logger.error(f"failed to send email for farmer: {str(e)}")
                return jsonify({
                    "message": "failed to send reset link to farmer's email",
                    "error": str(e)
                }), 400
                
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
            

@authentication.route('/api/v1/reset_password/<token>', methods=['PATCH'])
def reset_password(token):
    try:
        email = verify_reset_token(token)
        if not email:
            return jsonify({"error": "invalid or expired token"})
        
        data = request.get_json()
        password = data.get('password')
        
        try:
            validate_password(password)
        except ValueError:
            return jsonify({"error": "password must contain atleast 8 characters, 1 lowercase, uppercase, a number and a special character"}), 400
        
        buyer = Buyer.query.filter_by(email=email).first()
        if not buyer:
            try:
                farmer = Farmer.query.filter_by(email=email).first()
                if farmer:
                    try:
                        hashed_password = farmer.hash_password(password)
                        farmer.password_hash = hashed_password
                        db.session.commit()
                        return jsonify({
                            "success": True,
                            "message": "farmer password reset"
                        }), 200
                        
                    except SQLAlchemyError as e:
                        logger.error(f"farmer, database error: {str(e)}")
                        db.session.rollback()
                        return jsonify({
                            "message": "failed to reset farmer password",
                            "error": str(e)
                        }), 400
            except:
                return jsonify({"error": "user does not exist"}), 404
        
        if buyer:
            try:
                hashed_password = buyer.hash_password(password)
                buyer.password_hash = hashed_password
                db.session.commit()
                return jsonify({
                    'success': True,
                    "message": "password reset successfully"
                }), 200
                
            except SQLAlchemyError as e:
                logger.error(f"buyer, database error: {str(e)}")
                db.session.rollback()
                return jsonify({
                    "message": "failed to reset buyer password",
                    "error": str(e)
                })
                
    except Exception as e:
        logger.error(f"endpoint error: {str(e)}")
        return jsonify({
            "message": "internal server error",
            "error": str(e)
        }), 500
