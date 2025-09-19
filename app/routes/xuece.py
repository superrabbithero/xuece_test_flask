from flask import Blueprint, jsonify, request
from app.utils.api_utils import XueceAPIs


xuece_bp = Blueprint('xuece', __name__)

@xuece_bp.route('/get_answercard', methods=['GET'])
def get_answercard():
    """
    获取答题卡信息
    ---
    tags:
      - xuece_api
    parameters:
      - name: env
        in: query
        type: string
        required: true
      - name: card_type
        in: query
        type: string
      - name: paper_id
        in: query
        type: string
    responses:
      200:
        description: 获取答题卡信息成功
        schema:
          type: string
          example: "127.0.0.1:5000"
    """
    env = request.args.get('env', 'test1')
    card_type = request.args.get('card_type','exam')
    paper_id = request.args.get('paper_id','1')

    # print(env)
        
    xuece_api = XueceAPIs(env)

    xuece_api.login('markethuang:xctest','3a352bebcc6ac5cc2c6611d751727729')

    result = xuece_api.get_answercard(card_type, paper_id)

    # print(result)
    if result['code'] == 'SUCCESS':
      rst = {}
      if card_type == "exam":
        rst = {
          "params":result['data']['cutparamJsonstr2'],
          "name":result['data']['examPaperName'],
          "pdf_url": result['data']['pdfUrl']
        }
      else:
        rst = {
          "params":result['data']['answercard']['cutParamJsonStr'],
          "name":result['data']['classworkBaseVO']['name'],
          "pdf_url":result['data']['answercard']['pdfUrl']
        }
        
      return jsonify(rst), 200
    else:
        return jsonify({'error': result['msg']}), 500

     