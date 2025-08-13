from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flasgger import Swagger

from flask_cors import CORS

from config import Config

from .swagger import SWAGGER_TEMPLATE, SWAGGER_CONFIG


db = SQLAlchemy()

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    CORS(app) #开发环境允许跨域
    app.config.from_object(config_class)

    # 1. 先初始化数据库和迁移
    db.init_app(app)
    migrate = Migrate(app, db)  # 注意：不需要重复初始化

    # 2. 初始化Swagger（必须在蓝图注册前）

    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)  # 初始化

    # 3. 最后注册蓝图
    from .routes import init_routes
    init_routes(app)  # 确保所有路由在此之后添加

    return app