from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flasgger import Swagger

from flask_cors import CORS

from config import Config

db = SQLAlchemy()

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    CORS(app) #开发环境允许跨域
    app.config.from_object(config_class)

    # 1. 先初始化数据库和迁移
    db.init_app(app)
    migrate = Migrate(app, db)  # 注意：不需要重复初始化

    # 2. 初始化Swagger（必须在蓝图注册前）
    swagger_config = {
        "headers":[],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,  # 包含所有路由
                "model_filter": lambda tag: True,
            }
        ],
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
            }
        },
        "static_url_path": "/flasgger_static",
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

    Swagger(app, config=swagger_config, template=SWAGGER_TEMPLATE)  # 初始化

    # 3. 最后注册蓝图
    from .routes import init_routes
    init_routes(app)  # 确保所有路由在此之后添加

    return app