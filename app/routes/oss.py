from flask import Blueprint, jsonify
from app.utils.oss_utils import generate_sts_token, get_download_url
from app.utils.auth import  token_required

oss_bp = Blueprint('oss', __name__)

@oss_bp.route('/sts-token', methods=['GET'])
@token_required
def get_sts_token():
    """
    提供给前端的临时凭证接口
    ---
    tags:
      - OSS服务
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

@oss_bp.route('/download/<path:oss_key>', methods=['GET'])
def download_file(oss_key):
    """
    获取OSS文件的下载URL
    ---
    tags:
      - OSS服务
    parameters:
      - name: oss_key
        in: path
        type: string
        required: true
        description: OSS文件的对象键
    responses:
      200:
        description: 返回带签名的下载URL和过期时间
        schema:
          type: object
          properties:
            url:
              type: string
              description: 带签名的下载URL
            expires:
              type: string
              format: date-time
              description: URL过期时间(ISO格式)
    """
    obj = get_download_url(oss_key)

    return jsonify(obj)
     