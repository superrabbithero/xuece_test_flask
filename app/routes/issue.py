from flask import Blueprint, request, jsonify
from app.repositories.issue_repository import IssueRepository, DingTalkRepository

# 初始化蓝图
# url_prefix 设置为 /api/issues，后续路由都会自动加上这个前缀
issue_bp = Blueprint('issue', __name__, url_prefix="/api/issues")

@issue_bp.route('', methods=['GET'])
def list_issues():
    """
    获取问题列表（支持筛选）
    对应前端：issueApi.getIssues
    """
    # 从 URL 参数中获取筛选条件
    filters = {}
    
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    status = request.args.get('status')

    if start_time:
        filters['start_time'] = start_time
    if end_time:
        filters['end_time'] = end_time
    if status and status != 'all': # 前端可能传 'all'，后端库可能不需要过滤
        filters['status'] = status

    issues = IssueRepository.get_issues(filters)
    # 假设 Model 类有 to_dict() 方法，如果没有需要自行序列化
    return jsonify([issue.to_dict() for issue in issues])

@issue_bp.route('/<int:issue_id>', methods=['GET'])
def get_issue(issue_id):
    """
    获取单个问题详情
    对应前端：issueApi.getIssueById
    """
    issue = IssueRepository.get_issue_by_id(issue_id)
    if not issue:
        return jsonify({"error": "Issue not found"}), 404
    return jsonify(issue.to_dict())


@issue_bp.route('/<int:issue_id>', methods=['DELETE'])
def delete_issue(issue_id):
    try:
        # 调用 Repository 删除 issue
        deleted_issue = IssueRepository.delete_issue(issue_id)

        if deleted_issue:
            # 删除成功，返回成功信息
            return jsonify({
                "success": True,
                "message": f"Issue {issue_id} 已成功删除",
                "deleted_issue_id": issue_id
            }), 200  # 或者 204 No Content（如果不想返回内容）
        else:
            # 未找到对应 Issue
            return jsonify({
                "success": False,
                "message": f"Issue {issue_id} 不存在"
            }), 404

    except Exception as e:
        # 捕获未知异常，避免服务崩溃，返回 500
        return jsonify({
            "success": False,
            "message": f"删除 Issue 时发生错误：{str(e)}"
        }), 500


@issue_bp.route('', methods=['POST'])
def create_issue():
    """
    手动创建新问题
    对应前端：issueApi.createIssue
    """
    data = request.json
    if not data or not data.get('content'):
        return jsonify({"error": "Content is required"}), 400

    # 获取前端传来的参数
    content = data.get('content')
    images = data.get('images', [])
    # 如果有登录系统，这里应该从 current_user 获取 submitter 信息
    # 这里暂时假设前端可以传，或者留空
    submitter_id = data.get('submitter_id') 
    submitter_name = data.get('submitter_name')

    issue = IssueRepository.create_issue(
        content=content,
        images=images,
        submitter_id=submitter_id,
        submitter_name=submitter_name
    )
    
    return jsonify(issue.to_dict()), 201

@issue_bp.route('/<int:issue_id>/status', methods=['PUT'])
def update_issue_status(issue_id):
    """
    更新问题状态
    对应前端：issueApi.updateIssueStatus
    """
    data = request.json
    required_fields = ['status', 'operator_id', 'operator_name']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    issue = IssueRepository.update_issue_status(
        issue_id=issue_id,
        new_status=data['status'],
        operator_id=data['operator_id'],
        operator_name=data['operator_name'],
        gitee_url=data.get('gitee_url'),       # 可选
        ignore_reason=data.get('ignore_reason') # 可选
    )
    
    if not issue:
        return jsonify({"error": "Issue not found"}), 404
        
    return jsonify(issue.to_dict())

@issue_bp.route('/fetch', methods=['POST'])
def fetch_issues():
    """
    批量主动获取/导入问题
    对应前端：issueApi.fetchIssues
    """
    data = request.json
    items = data.get('items', [])
    
    results = []
    for item in items:
        # 根据实际业务逻辑调整字段映射
        issue = IssueRepository.create_issue(
            content=item.get('description'),
            images=item.get('images', []),
            # 如果是爬虫抓取的，可能没有具体的提交人
            submitter_name=item.get('source', 'System Fetch')
        )
        results.append(issue.to_dict())
    
    return jsonify({"data": results, "count": len(results)}), 201

# app/routes.py (修改 dingtalk_webhook 部分)

@issue_bp.route('/dingtalk/webhook', methods=['POST'])
def dingtalk_webhook():
    """
    钉钉机器人回调接口
    接收群消息 -> 解析 -> 存库 -> 返回回复消息
    """
    # 1. 获取钉钉 POST 过来的数据
    payload = request.json
    
    # 打印日志方便调试
    print("收到钉钉消息:", payload) 
    
    # 2. 安全校验与数据提取
    # 钉钉的消息内容在 'text' -> 'content' 中
    raw_content = payload.get('text', {}).get('content', '').strip()
    
    # 获取发送者信息 (senderId 是加密的用户ID，senderNick 是昵称)
    sender_id = payload.get('senderId')
    sender_nick = payload.get('senderNick')
    
    # 3. 简单的逻辑处理
    # 虽然钉钉后台设置了关键字，但为了保险，代码里再判断一次
    if not raw_content or not raw_content.startswith('%bug'):
        return jsonify({"message": "ignored"}), 200
    
    # 4. 调用 Service/Repository 层处理数据
    try:
        # 解析内容，去掉 %bug 前缀
        # 例如 "%bug 登录报错" -> "登录报错"
        parsed_data = DingTalkRepository.parse_bug_report(raw_content, sender_id, sender_nick)
        
        # 创建 Issue
        issue = IssueRepository.create_issue(
            content=parsed_data['content'],
            submitter_id=parsed_data['submitter_id'],
            submitter_name=parsed_data['submitter_name']
        )
        
        # 5. 【关键】构造返回给钉钉的响应
        # 如果你返回这个 JSON，机器人就会在群里把这句话发出来
        response_msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": "Bug已记录",
                "text": f"### 🐛 Bug 已记录\n\n"
                        f"**ID:** #{issue.id}\n"
                        f"**提交人:** @{sender_nick}\n"
                        f"**内容:** {issue.content}\n\n"
                        f"> 状态: 待处理"
            },
            "at": {
                "atUserIds": [sender_id], # @发送者
                "isAtAll": False
            }
        }
        return jsonify(response_msg)
        
    except Exception as e:
        print(f"Error processing dingtalk msg: {e}")
        # 出错时也可以回复机器人
        return jsonify({
             "msgtype": "text",
             "text": { "content": "系统错误，Bug 提交失败" }
        })