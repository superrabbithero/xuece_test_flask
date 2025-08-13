# image_repository.py
from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_
from datetime import datetime
import uuid


from app.repositories import (
    ImageRepository, 
    DocImageRepository,
    RepoResult
)

image_bp = Blueprint("image_repo", __name__, url_prefix="/api/images")


def ok(data=None, msg="ok"):
    return jsonify({"code": 0, "msg": msg, "data": data or {}})


def bad_request(msg="bad request", code=400):
    return jsonify({"code": 1, "msg": msg}), code


# ========== 1) 预留一个唯一的 OSS Key 并本地入库 uploaded=False, in_use=False ==========
@image_bp.route("/reserve", methods=["POST"])
def reserve_oss_key():
    """
    预留一个唯一的 OSS Key，并在本地入库 uploaded=false、in_use=false
    ---
    tags:
      - 图片管理
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
            ext:
              type: string
              description: 图片扩展名（不带点），默认 png
              example: jpg
            prefix:
              type: string
              description: OSS 目录前缀，默认 images
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
    ext = (payload.get("ext") or "png").lstrip(".")
    prefix = payload.get("prefix") or "images"

    # 生成 key：images/2025-08-13/uuid.png
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"{prefix}/{date_str}/{uuid.uuid4().hex}.{ext}"

    img = ImageRepository.create(oss_key=key)

    return ok(
        {
            "id": img.id,
            "oss_key": img.oss_key,
            "uploaded": img.uploaded,
            "in_use": img.in_use,
        }
    )


# ========== 2) 批量更新上传状态 uploaded 或使用状态 in_use ==========
@image_bp.route("/batch-status", methods=["PATCH"])
def batch_update_status():
    """
    批量更新图片的 uploaded / in_use 状态
    ---
    tags:
      - 图片管理
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/BatchStatusRequest'
    responses:
      200:
        description: 更新成功
        schema:
          $ref: '#/definitions/Envelope_BatchStatusResult'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/Envelope_Error'
    """
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        return bad_request("ids 必须是非空数组")

    rst = ImageRepository.batch_update(ids,payload.get('uploaded',None),payload.get('in_use',None))

    return ok(rst.data) if rst.ok else bad_request(rst.error)



# ========== 3) 同步更新图片与文档关联 ==========
@image_bp.route("/relations", methods=["PUT"])
def update_relations():
    """
    更新指定文档的图片关联：删除多余、增加缺失；并维护 Images.in_use
    ---
    tags:
      - 图片管理
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/UpdateRelationsRequest'
    responses:
      200:
        description: 同步结果
        schema:
          $ref: '#/definitions/Envelope_RelationsResult'
      400:
        description: 参数错误
        schema:
          $ref: '#/definitions/Envelope_Error'
      404:
        description: 文档不存在
        schema:
          $ref: '#/definitions/Envelope_Error'
    """
    payload = request.get_json(silent=True) or {}
    doc_id = payload.get("doc_id")
    image_ids = payload.get("image_ids", [])

    rst = DocImageRepository.update_doc_relations(doc_id,image_ids)

    return ok(rst.data) if rst.ok else bad_request(rst.error)


    
