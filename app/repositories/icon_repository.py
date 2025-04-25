# from app import db
from app.models import db, Icon  # 导入Icon模型
# from sqlalchemy import or_, and_, distinct
from sqlalchemy.sql import func

class IconRepository:
    """使用Flask-SQLAlchemy的CRUD操作类"""
    @staticmethod
    def get(icon_id):
        """
        通过ID获取单个Icon记录
        :param icon_id: ID
        :return: Icon对象或None
        """
        return Icon.query.get(icon_id)

    @staticmethod
    def create(icon_data):
        """创建新包记录"""
        icon = Icon(**icon_data)
        db.session.add(icon)
        db.session.commit()
        return icon

    @staticmethod
    def get_id_by_name(name):
        """
        通过 name 查找对应的 id
        :param name: Icon 的 name（唯一约束）
        :return: id（如果找到）或 None（如果没找到）
        """
        icon = Icon.query.filter_by(name=name).first()  # 查询第一条记录
        return icon.id if icon else None  # 返回 id 或 None