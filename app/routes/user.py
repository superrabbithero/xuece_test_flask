from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from ..repositories.user_repository import UserRepository
from ..models import User
from functools import wraps
import os
from app.utils.auth import  generate_token, token_required,TOKEN_EXPIRE_HOURS

user_bp = Blueprint('user', __name__, url_prefix='/api/users')



@user_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    ---
    tags:
      - 用户管理
    consumes:
      - application/json
    parameters:
      - in: body
        name: user
        description: 用户注册信息
        required: true
        schema:
          type: object
          required:
            - user_name
            - password
          properties:
            user_name:
              type: string
              description: 用户名
              example: "testuser"
            password:
              type: string
              description: 密码
              example: "testpassword"
    responses:
      201:
        description: 注册成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User registered successfully"
            user_id:
              type: integer
              example: 1
      400:
        description: 无效请求
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Username already exists"
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        user_name = data.get('user_name')
        password = data.get('password')

        if not user_name or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # 检查用户名是否已存在
        if UserRepository.get_by_user_name(user_name):
            return jsonify({'error': 'Username already exists'}), 400

        # 密码哈希处理
        hashed_password = generate_password_hash(password)

        # 创建用户
        user_data = {
            'user_name': user_name,
            'password': hashed_password,
            'created_at': datetime.now()
        }

        user_id = UserRepository.create(user_data)
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201

    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    ---
    tags:
      - 用户管理
    consumes:
      - application/json
    parameters:
      - in: body
        name: credentials
        description: 用户登录凭证
        required: true
        schema:
          type: object
          required:
            - user_name
            - password
          properties:
            user_name:
              type: string
              description: 用户名
              example: "testuser"
            password:
              type: string
              description: 密码
              example: "testpassword"
    responses:
      200:
        description: 登录成功
        schema:
          type: object
          properties:
            token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            expires_in:
              type: integer
              example: 86400
      401:
        description: 登录失败
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid credentials"
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        user_name = data.get('user_name')
        password = data.get('password')
        print(user_name,password)
        if not user_name or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # print("@@@")
        # 验证用户
        user = UserRepository.get_by_user_name(user_name)
        # print(user)
        if not user:
            return jsonify({'error': f'用户名不存在'}), 404
        if not check_password_hash(user.password, password):
            return jsonify({'error': f'密码错误'}), 402
        # 生成JWT Token
        token = generate_token(user.id)

        return jsonify({
            'token': token,
            'expires_in': TOKEN_EXPIRE_HOURS * 3600
        }), 200

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    获取用户信息
    ---
    tags:
      - 用户管理
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: 用户ID
    responses:
      200:
        description: 用户信息
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
            user_name:
              type: string
              example: "testuser"
            created_at:
              type: string
              example: "2023-01-01T00:00:00"
      404:
        description: 用户不存在
    """
    user = UserRepository.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user_id': user.id,
        'user_name': user.user_name,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }), 200



@user_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """
    修改用户密码
    ---
    tags:
      - 用户管理
    security:
      - BearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - old_password
            - new_password
          properties:
            old_password:
              type: string
              description: 旧密码
            new_password:
              type: string
              description: 新密码
    responses:
      200:
        description: 密码修改成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Password updated successfully"
      401:
        description: 认证失败
      403:
        description: 旧密码错误
    """
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not all([old_password, new_password]):
            return jsonify({"error": "必须提供旧密码和新密码"}), 400

        # 获取当前用户
        user = UserRepository.get(request.current_user_id)
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        # 验证旧密码
        if not check_password_hash(user.password, old_password):
            return jsonify({"error": f"旧密码不正确{old_password}{user.password}"}), 403

        # 更新为新密码（自动加盐哈希）
        new_hashed_password = generate_password_hash(new_password)
        if not UserRepository.update_password(user.id, new_hashed_password):
            raise Exception("密码更新失败")

        return jsonify({"message": "密码修改成功"}), 200

    except Exception as e:
        current_app.logger.error(f"修改密码错误: {str(e)}")
        return jsonify({"error": str(e)}), 500