from dotenv import load_dotenv
from flask_mail import Mail
import logging
from flask_caching import Cache
from flask_jwt_extended import get_jwt_identity
from .models import Farmer, Buyer
import os
from typing import Dict, Any
import re
from decimal import Decimal

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

mail = Mail()
cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL'),
    'CACHE_DEFAULT_TIMEOUT': 300
})

def get_current_user():
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        user_id = identity['id']
        role = identity['role']
        
        if role == 'farmer':
            return Farmer.query.get(user_id)
        elif role == 'buyer':
            return Buyer.query.get(user_id)
        
    return None

def get_current_user_id():
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity['id']
    return None

def validate_phone_number(phone_number):
    if not re.search(r"\d{10}$", phone_number):
        return False
    return True

def validate_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    validate a products data
    returns a dictionary with validated data or raises an exception
    """
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price_per_unit = data.get('price_per_unit')
    amount_available = data.get('amount_available')
    category = data.get('category', '').strip().lower()
    
    if not all([name, description, price_per_unit, category]):
        return ValueError("All fields are required")
    
    try:
        price_per_unit = Decimal(str(price_per_unit))
        amount_available = int(amount_available)
    except (ValueError, TypeError):
        raise ValueError("Invalid price or amount")
    
    if price_per_unit <= 0 or amount_available < 0:
        raise ValueError("Price and amount must be greater than or equal to 0")
    
    return {
        "name": name,
        "description": description,
        "price_per_unit": price_per_unit,
        "amount_available": amount_available,
        "category": category
    }
    