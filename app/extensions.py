from dotenv import load_dotenv
from flask_mail import Mail
import logging
from flask_caching import Cache
from flask_jwt_extended import get_jwt_identity
from .models import Farmer, Buyer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

mail = Mail()
cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': 'redis-12843.c73.us-east-1-2.ec2.redns.redis-cloud.com',
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