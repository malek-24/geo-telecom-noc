import jwt
from functools import wraps
from flask import request, jsonify, g
from utils.globals import JWT_SECRET

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header else ""
        if not token:
            return jsonify({"error": "Token manquant"}), 401
        try:
            g.current_user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expiré"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalide"}), 401
    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.get("role") != "administrateur":
            return jsonify({"error": "Accès réservé aux administrateurs"}), 403
        return f(*args, **kwargs)
    return decorated

def role_required(*roles_autorises):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user_role = g.current_user.get("role", "")
            if user_role not in roles_autorises:
                return jsonify({
                    "error": f"Accès refusé. Rôles autorisés : {', '.join(roles_autorises)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
