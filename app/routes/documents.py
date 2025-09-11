from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from app.utils.auth import  token_required
from app.repositories import (
    DocumentRepository, 
    CategoryRepository,
    TagRepository
)

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

def ok(data=None, msg="ok"):
    return jsonify({"code": 0, "msg": msg, "data": data or {}})


def bad_request(msg="bad request", code=400):
    return jsonify({"code": 1, "msg": msg}), code

# 获取用户的文章
@documents_bp.route('', methods=['GET'])
@token_required
def get_documents():
    """
    获取文档列表
    ---
    tags:
      - 文档管理
    parameters:
      - name: user_id
        in: query
        require: true
        type: integer
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码
      - name: per_page
        in: query
        type: integer
        default: 10
        description: 每页数量
      - name: status
        in: query
        type: integer
        description: 文档状态(0-草稿/1-审核中/2-未通过/3-已发布)
      - name: title
        in: query
        type: string
        description: 标题关键词搜索
      - name: category_id
        in: query
        type: integer
        description: 分类ID筛选
      - name: tag_id
        in: query
        type: array
        items:
          type: integer
        collectionFormat: multi
        description: 标签ID(可传多个)
    responses:
      200:
        description: 文档列表
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/definitions/Document'
            total:
              type: integer
              example: 100
            pages:
              type: integer
              example: 10
            current_page:
              type: integer
              example: 1
    """
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    result = DocumentRepository.get_documents(
        user_id=user_id,
        page=page,
        per_page=per_page,
        status=request.args.get('status',type=list),
        title=request.args.get('title', ''),
        category_id=request.args.get('category_id', type=int),
        tag_ids=request.args.getlist('tag_id', type=int) or None
    )
    
    return jsonify({
        'items': [doc.to_dict() for doc in result.items],
        'total': result.total,
        'pages': result.pages,
        'current_page': result.page
    })

# 获取用户的文章
@documents_bp.route('/home', methods=['GET'])
def get_home_documents():
    """
    获取文档列表
    ---
    tags:
      - 文档管理
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码
      - name: per_page
        in: query
        type: integer
        default: 10
        description: 每页数量
      - name: title
        in: query
        type: string
        description: 标题关键词搜索
      - name: category_id
        in: query
        type: integer
        description: 分类ID筛选
      - name: tag_id
        in: query
        type: array
        items:
          type: integer
        collectionFormat: multi
        description: 标签ID(可传多个)
    responses:
      200:
        description: 文档列表
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/definitions/Document'
            total:
              type: integer
              example: 100
            pages:
              type: integer
              example: 10
            current_page:
              type: integer
              example: 1
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    result = DocumentRepository.get_documents(
        user_id=None,
        page=page,
        per_page=per_page,
        status=[3],
        title=request.args.get('title', ''),
        category_id=request.args.get('category_id', type=int),
        tag_ids=request.args.getlist('tag_id', type=int) or None
    )
    
    return jsonify({
        'items': [doc.to_dict() for doc in result.items],
        'total': result.total,
        'pages': result.pages,
        'current_page': result.page
    })


@documents_bp.route("", methods=["delete"])
@token_required
def delete_document():
    """
    获取文档详情
    ---
    tags:
      - 文档管理
    parameters:
      - name: id
        in: query
        require: true
        type: integer
    responses:
      200:
        description: 预留成功
        schema:
          $ref: '#/definitions/Envelope_ImageReserve'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/Envelope_Error'
        
    """
    doc_id = request.args.get('id')
    rst = DocumentRepository.delete(doc_id)
    return ok(rst)

@documents_bp.route("/detail", methods=["get"])
def get_doc_by_id():
    """
    获取文档详情
    ---
    tags:
      - 文档管理
    parameters:
      - name: id
        in: query
        require: true
        type: integer
    responses:
      200:
        description: 文档列表
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/definitions/Document'
            total:
              type: integer
              example: 100
            pages:
              type: integer
              example: 10
            current_page:
              type: integer
              example: 1
    """
    doc_id = request.args.get('id')
    rst = DocumentRepository.get_by_id(doc_id)
    return ok(rst.to_dict())


@documents_bp.route("/reserve", methods=["POST"])
@token_required
def reserve_oss_key():
    """
    预留一个唯一的 OSS Key，并在本地入库
    ---
    tags:
      - 文档管理
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            user_id:
              type: integer
            title:
              type: string
            short_content:
              type: string
            prefix:
              type: string
              description: OSS 目录前缀，默认 documents
              example: uploads
    responses:
      200:
        description: 预留成功
        schema:
          $ref: '#/definitions/Envelope_ImageReserve'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/Envelope_Error'
    """
    payload = request.get_json(silent=True) or {}
    prefix = payload.get("prefix") or "documents"
    user_id = int(payload.get("user_id", None))
    title = payload.get('title', '新建文章')
    short_content = payload.get('short_content', '')
    if not user_id:
        return bad_request("user_id 必须非空")

    date_str = int(datetime.now().timestamp()*1000)
    print(date_str)
    key = f"{prefix}/{user_id}/{date_str}_{uuid.uuid4().hex}.md"
    print(key)
    success = DocumentRepository.create(
      user_id=user_id,
      oss_key=key,
      title=title,
      short_content=short_content,
      status=0,
      category_id=None)

    return ok(
        success.to_dict()
    )


@documents_bp.route('', methods=['POST'])
@token_required
def create_document():
    """
    创建新文档
    ---
    tags:
      - 文档管理
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DocumentCreate'
    responses:
      201:
        description: 文档创建成功
        schema:
          $ref: '#/definitions/DocumentCreate'
      400:
        description: 参数验证失败
        schema:
          type: object
          properties:
            error:
              type: string
              example: "缺少必要字段"
    """
    data = request.get_json()

    success = DocumentRepository.create(
      user_id=data.get('user_id'),
      oss_key=data.get('oss_key'),
      short_content=data.get('short_content'),
      status=data.get('status'),
      category_id=data.get('category_id'))

    # print(success.id)

    if not success:
        return jsonify({'error': '创建文档失败'}), 404
    
    return jsonify({'message': '创建文档成功'}), 201


@documents_bp.route('', methods=['PUT'])
@token_required
def update_document():
    """
    更新文档信息
    ---
    tags:
      - 文档管理
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            id:
              type: integer
            status:
              type: integer
            category_id:
              type: integer
            title:
              type: string
    responses:
      200:
        description: 更新成功
        schema:
          $ref: '#/definitions/Envelope_ImageReserve'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/Envelope_Error'
    """
    payload = request.get_json(silent=True) or {}
    doc_id = payload.get("id", None)
    status = payload.get("status", None)
    category_id = payload.get("category_id", None)
    title = payload.get("title", None)
    print(payload,title)
    if not doc_id:
        return bad_request("doc_id 必须非空")

    success = DocumentRepository.update(
      id=doc_id,
      title=title,
      short_content='',
      status=status,
      category_id=category_id)

    return ok(
        success.to_dict()
    )

@documents_bp.route('/publish', methods=['PUT'])
@token_required
def publish_document():
    """
    更新文档信息
    ---
    tags:
      - 文档管理
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            id:
              type: integer
            status:
              type: integer
            cover_img:
              type: String
            short_content:
              type: String
    responses:
      200:
        description: 更新成功
        schema:
          $ref: '#/definitions/Envelope_ImageReserve'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/Envelope_Error'
    """
    payload = request.get_json(silent=True) or {}
    doc_id = payload.get("id", None)
    status = payload.get("status", None)
    short_content = payload.get("short_content", None)
    cover_img = payload.get("cover_img", None)
    print(payload)
    if not doc_id:
        return bad_request("doc_id 必须非空")
    if not short_content:
        return bad_request("short_content 必须非空")

    success = DocumentRepository.update(
      id=doc_id,
      short_content=short_content,
      cover_img=cover_img,
      status=status)

    return ok(
        success.to_dict()
    )



@documents_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    获取全部分类
    ---
    tags:
      - 分类管理
    responses:
      200:
        description: 分类树结构
        schema:
          type: array
          items:
            $ref: '#/definitions/Category'
    """
    return jsonify(CategoryRepository.get_tree())

@documents_bp.route('/tags', methods=['GET'])
def get_tags():
    """
    获取所有标签
    ---
    tags:
      - 标签管理
    parameters:
      - name: name
        in: query
        type: string
        description: 标签名称搜索
    responses:
      200:
        description: 标签列表
        schema:
          type: array
          items:
            $ref: '#/definitions/Tag'
    """
    name = request.args.get('name', '')
    if name:
        tags = TagRepository.search_by_name(name)
    else:
        tags = TagRepository.get_all()
    return jsonify([tag.to_dict() for tag in tags])

@documents_bp.route('/<int:doc_id>/tags', methods=['POST'])
def add_document_tag(doc_id):
    """
    添加文档标签
    ---
    tags:
      - 文档标签
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: 文档ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - tag_id
          properties:
            tag_id:
              type: integer
              example: 1
    responses:
      201:
        description: 标签添加成功
        schema:
          type: object
          properties:
            message:
              type: string
              example: "标签添加成功"
      404:
        description: 文档或标签不存在
    """
    data = request.get_json()
    if 'tag_id' not in data:
        return jsonify({'error': '缺少tag_id参数'}), 400
    
    success = DocumentRepository.add_tag(doc_id, data['tag_id'])
    if not success:
        return jsonify({'error': '文档或标签不存在'}), 404
    
    return jsonify({'message': '标签添加成功'}), 201