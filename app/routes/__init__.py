def init_routes(app):
    """集中注册所有蓝图"""
    from .package import package_bp
    app.register_blueprint(package_bp, url_prefix='/api/packages')

    from .oss import oss_bp
    app.register_blueprint(oss_bp, url_prefix='/api/oss')

    from .user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')

    from .xuece import xuece_bp
    app.register_blueprint(xuece_bp, url_prefix='/api/xuece')

    from .bailian import bailian_bp
    app.register_blueprint(bailian_bp, url_prefix='/api/bailian')

    from .documents import documents_bp
    app.register_blueprint(documents_bp, url_prefix='/api/documents')

    from .image import image_bp
    app.register_blueprint(image_bp, url_prefix='/api/images')

