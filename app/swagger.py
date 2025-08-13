# app/swagger.py
from datetime import datetime

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    # —— 统一的 definitions 放这里 ——
    "definitions": {
        "DocumentCreate": {
            "type": "object",
            "required": ["user_id", "short_content", "oss_key"],
            "properties": {
                "user_id": {"type": "integer"},
                "short_content": {"type": "string"},
                "oss_key": {"type": "string"},
                "category_id": {"type": "integer"},
                "tags_id": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            }
        },
        "Envelope_Error": {
            "type": "object",
            "properties": {
                "code": {"type": "integer", "example": 1},
                "msg":  {"type": "string",  "example": "参数错误"},
                "data": {"type": "object",  "example": {}}
            }
        },
        "ImageReserve": {
            "type": "object",
            "properties": {
                "id":       {"type": "integer", "example": 101},
                "oss_key":  {"type": "string",  "example": "uploads/2025-08-13/uuid.jpg"},
                "uploaded": {"type": "boolean", "example": False},
                "in_use":   {"type": "boolean", "example": False},
            }
        },
        "Envelope_ImageReserve": {
            "type": "object",
            "properties": {
                "code": {"type": "integer", "example": 0},
                "msg":  {"type": "string",  "example": "ok"},
                "data": {"$ref": "#/definitions/ImageReserve"}
            }
        },
        "BatchStatusRequest": {
            "type": "object",
            "required": ["ids"],
            "properties": {
                "ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [1, 2, 3]
                },
                "uploaded": {"type": "boolean", "description": "可选"},
                "in_use":   {"type": "boolean", "description": "可选"}
            }
        },
        "BatchStatusResult": {
            "type": "object",
            "properties": {
                "updated": {"type": "integer", "example": 3},
                "fields":  {"type": "object", "example": {"uploaded": True}}
            }
        },
        "Envelope_BatchStatusResult": {
            "type": "object",
            "properties": {
                "code": {"type": "integer", "example": 0},
                "msg":  {"type": "string",  "example": "ok"},
                "data": {"$ref": "#/definitions/BatchStatusResult"}
            }
        },
        "CleanupRequest": {
            "type": "object",
            "properties": {
                "ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "仅清理这些图片ID（可选）",
                    "example": [10, 11, 12]
                },
                "not_uploaded":  {"type": "boolean", "example": True},
                "not_in_use":    {"type": "boolean", "example": True},
                "delete_from_oss":{"type": "boolean", "example": False}
            }
        },
        "CleanupResult": {
            "type": "object",
            "properties": {
                "deleted": {"type": "integer", "example": 2},
                "ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [10, 12]
                }
            }
        },
        "Envelope_CleanupResult": {
            "type": "object",
            "properties": {
                "code": {"type": "integer", "example": 0},
                "msg":  {"type": "string",  "example": "ok"},
                "data": {"$ref": "#/definitions/CleanupResult"}
            }
        },
        "UpdateRelationsRequest": {
            "type": "object",
            "required": ["doc_id", "image_ids"],
            "properties": {
                "doc_id":    {"type": "integer", "example": 501},
                "image_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [2, 5, 8, 13]
                }
            }
        },
        "RelationsResult": {
            "type": "object",
            "properties": {
                "doc_id":         {"type": "integer", "example": 501},
                "added": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [5, 8]
                },
                "removed": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [3]
                },
                "final_image_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [2, 5, 8, 13]
                }
            }
        },
        "Envelope_RelationsResult": {
            "type": "object",
            "properties": {
                "code": {"type": "integer", "example": 0},
                "msg":  {"type": "string",  "example": "ok"},
                "data": {"$ref": "#/definitions/RelationsResult"}
            }
        },
    },
    "static_url_path": "/flasgger_static",
    "specs_route": "/apidocs/",   # 访问文档的路由
    "title": "Package Management API",
    "uiversion": 3  # 使用Swagger UI 3
}

SWAGGER_TEMPLATE = {
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT 认证格式: Bearer <token>"
        }
    }
}
