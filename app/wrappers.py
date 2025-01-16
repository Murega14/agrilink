from functools import wraps
from flask import session, abort,jsonify
import asyncio
import time
import inspect
from flask_jwt_extended import get_jwt_identity


def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "id" not in session:
            return abort(401)
        else:
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper

