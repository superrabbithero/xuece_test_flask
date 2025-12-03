from flask import request, jsonify, Blueprint
from ..repositories.issue_repository import IssueRepository, DingTalkRepository
import re

# 初始化蓝图
issue_bp = Blueprint('issue', __name__, url_prefix="/api/issues")

# 主动获取接口
@issue_bp.route('/fetch', methods=['POST'])
def fetch_issues():
    data = request.json
    # 示例处理逻辑（实际需对接具体数据源）
    formatted_issues = []
    for item in data.get('items', []):
        issue = IssueRepository.create_issue(
            content=item['description'],
            images=item.get('images', [])
        )
        formatted_issues.append(issue.to_dict())
    
    return jsonify({"data": formatted_issues}), 201

# 钉钉被动获取接口
@issue_bp.route('/api/dingtalk/webhook', methods=['POST'])
def dingtalk_webhook():
    payload = request.json
    msg_content = payload.get('text', {}).get('content', '')
    
    # 验证%bug开头
    if not msg_content.startswith('%bug'):
        return jsonify({"error": "Invalid format"}), 400
    
    # 获取用户信息（需对接钉钉API）
    user_id = payload['senderId']
    user_name = payload['senderNick']
    
    # 解析内容
    parsed = DingTalkRepository.parse_bug_report(msg_content, user_id, user_name)
    
    # 创建问题
    issue = IssueRepository.create_issue(
        content=parsed['content'],
        submitter_id=parsed['submitter_id'],
        submitter_name=parsed['submitter_name']
    )
    
    return jsonify(issue.to_dict()), 201

# 问题列表查询
@issue_bp.route('', methods=['GET'])
def list_issues():
    filters = {
        'start_time': request.args.get('start_time'),
        'end_time': request.args.get('end_time'),
        'status': request.args.get('status')
    }
    issues = IssueRepository.get_issues(filters)
    return jsonify([i.to_dict() for i in issues])

# 更新问题状态
@issue_bp.route('/<int:issue_id>/status', methods=['PUT'])
def update_issue_status(issue_id):
    data = request.json
    issue = IssueRepository.update_issue_status(
        issue_id=issue_id,
        new_status=data['status'],
        operator_id=data['operator_id'],
        operator_name=data['operator_name'],
        gitee_url=data.get('gitee_url'),
        ignore_reason=data.get('ignore_reason')
    )
    
    if not issue:
        return jsonify({"error": "Issue not found"}), 404
        
    return jsonify(issue.to_dict())

