from functools import wraps
from flask import request, jsonify
from config.config import API_KEY
import hmac

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not hmac.compare_digest(api_key, API_KEY):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated
