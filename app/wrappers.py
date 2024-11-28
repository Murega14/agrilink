from functools import wraps
from flask import session, abort
import asyncio
import time

def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "id" not in session:
            return abort(401)
        else:
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

class AsyncTTLCache:
    def __init__(self, maxsize=128, ttl=300):
        self._cache = {}
        self._maxsize = maxsize
        self._ttl = ttl
        
    def get(self, key):
        if key in self._cache:
            item, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return item
            else:
                del self._cache[key]
                
        return None
    
    def set(self, key, value):
        if len(self._cache) >= self._maxsize:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
            
        self._cache[key] = (value, time.time())
        
    def clear(self, key=None):
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
        
def cache_result(cache_object):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            #generating a unique cache key 
            cache_key = str(args) + str(kwargs)
            #checking cache
            cached_result = cache_object.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = await func(*args, **kwargs)
            cache_object.set(cache_key, result)
            
            return result
        return wrapper
    return decorator