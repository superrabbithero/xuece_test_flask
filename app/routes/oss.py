from flask import Blueprint, jsonify
from app.utils.oss_utils import generate_sts_token

oss_bp = Blueprint('oss', __name__)

@oss_bp.route('/sts-token', methods=['GET'])
def get_sts_token():
    """
    提供给前端的临时凭证接口
    ---
    tags:
      - oss服务
    responses:
      200:
        description: 成功返回凭证
        schema:
          type: string
          example: "127.0.0.1:5000"
    """
    result = generate_sts_token()
    if result['status'] == 'success':
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['message']}), 500
