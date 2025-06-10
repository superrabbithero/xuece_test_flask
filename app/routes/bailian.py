from flask import Blueprint, jsonify, request
from app.utils.api_utils import BaiLianAPIs

bailian_bp = Blueprint('bailian', __name__)

@bailian_bp.route('/image_generation', methods=['POST'])
def image_generation():
	json_info = request.get_json()
	data = json_info["data"]
	key = json_info["api_key"]

	api = BaiLianAPIs()

	rst = api.image_generation(key, data)

	return jsonify(rst), 200

@bailian_bp.route('/tasks/<string:task_id>', methods=['GET'])
def get_task(task_id):

	api = BaiLianAPIs()
	print("task_id")
	key = ""
	rst = api.get_task(key, task_id)

	return jsonify(rst), 200