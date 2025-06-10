from flask import Blueprint, jsonify, request
from app.utils.api_utils import BaiLianAPIs

bailian_bp = Blueprint('bailian', __name__)

@bailian_bp.route('/image_generation', methods=['POST'])
def image_generation():
	data = request.get_json()

	api = BaiLianAPIs()

	rst = api.image_generation(data)

	return jsonify(rst), 200

@bailian_bp.route('/tasks/<string:task_id>', methods=['GET'])
def get_task(task_id):

	api = BaiLianAPIs()

	rst = api.get_task(task_id)

	return jsonify(rst), 200