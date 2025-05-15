import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')  # 替换为高强度密钥
TOKEN_EXPIRE_HOURS = 24  # Token有效期（小时）


def generate_token(user_id: str) -> str:
    """生成JWT Token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 辅助装饰器：验证JWT并获取用户ID
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({"error": "Token缺失或格式错误"}), 401
        
        try:
            token = token[7:]  # 去掉'Bearer '
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token已过期"}), 403
        except Exception as e:
            return jsonify({"error": "Token无效"}), 403
        
        return f(*args, **kwargs)
    return decorated