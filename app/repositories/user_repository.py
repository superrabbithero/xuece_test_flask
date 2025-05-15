from app.models import db, User  
from sqlalchemy.sql import func

class UserRepository:
    """使用Flask-SQLAlchemy的CRUD操作类"""
    
    @staticmethod
    def get(user_id):
        """
        通过ID获取单个用户记录
        :param user_id: 用户ID
        :return: User对象或None
        """
        return User.query.get(user_id)  

    @staticmethod
    def create(user_data):
        """创建新用户记录"""
        new_user = User(**user_data)  
        db.session.add(new_user)
        db.session.commit()
        return new_user.id  # 返回用户ID

    @staticmethod
    def get_by_user_name(user_name):
        """
        通过用户名查找用户
        :param user_name: 用户名
        :return: User对象或None
        """
        return User.query.filter_by(user_name=user_name).first()  

    @staticmethod
    def update_password(user_id, new_hashed_password):
        """
        更新用户密码
        :param user_id: 用户ID
        :param new_hashed_password: 新密码的哈希值
        :return: 是否成功
        """
        user = User.query.get(user_id)
        if not user:
            return False
        
        user.password = new_hashed_password
        db.session.commit()
        return True