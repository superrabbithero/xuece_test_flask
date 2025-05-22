from datetime import datetime
from app import db

class Package(db.Model):
    """
    软件包数据模型
    """
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    appname = db.Column(db.String(128), nullable=False, index=True, comment='应用名称')
    version = db.Column(db.String(64), nullable=False, comment='版本号')
    name = db.Column(db.String(256), nullable=False, comment='文件名')
    size = db.Column(db.BigInteger, nullable=False, comment='文件大小(字节)')
    system = db.Column(db.String(64), nullable=False, comment='适用系统')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    # status = db.Column(db.SmallInteger, default=0, nullable=False, comment='状态(0-正常)')
    is_debug = db.Column(db.Boolean, default=True, nullable=False, comment="是否为调试包")
    comment = db.Column(db.Text, default='', comment='备注信息')
    ar = db.Column(db.String(256), nullable=True, comment='架构信息')
    package_name = db.Column(db.String(256), nullable=False, comment='包名')
    oss_key = db.Column(db.String(256), nullable=False, comment='oss的key值')
    # 外键：指向 Icon 表的 id
    icon_id = db.Column(db.Integer, db.ForeignKey('icons.id'))
    
    # 关系定义：backref 可选的，用于反向访问
    icon = db.relationship('Icon', backref='packages', lazy='joined')
    # lazy='joined' 表示查询 Package 时自动联表加载 Icon
    
    def __repr__(self):
        return f'<Package {self.name}@{self.version}>'
    
    def to_dict(self):
        """
        将模型转换为字典格式
        """
        return {
            'id': self.id,
            'appname': self.appname,
            'version': self.version,
            'name': self.name,
            'size': self.size,
            'system': self.system,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'is_debug': self.is_debug,
            # 'status': self.status,
            'comment': self.comment,
            'ar': self.ar,
            'package_name': self.package_name,
            'oss_key': self.oss_key,
            'icon_id': self.icon_id,
            'icon': self.icon.to_dict() if self.icon else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建模型实例
        """
        return cls(
            id=data.get('id'),
            appname=data['appname'],
            version=data['version'],
            name=data['name'],
            size=data['size'],
            system=data['system'],
            create_time=data.get('create_time', datetime.utcnow()),
            # status=data.get('status', 0),
            is_debug=data.get('is_debug', False),
            comment=data.get('comment', ''),
            ar=data.get('ar'),
            package_name=data.get('package_name'),
            oss_key=data.get('oss_key')
        )


class OSSClient:
    """OSS 文件操作客户端"""
    
    @staticmethod
    def delete(oss_key):
        """
        删除OSS文件
        :param oss_key: OSS文件key
        :return: 是否删除成功
        """
        # 实际实现根据您使用的OSS SDK (阿里云/腾讯云/七牛等)
        try:
            # 示例: 阿里云OSS删除
            # from aliyunsdkcore.client import AcsClient
            # client = AcsClient('<access-key>', '<access-secret>', '<region>')
            # client.delete_object('<bucket-name>', oss_key)
            return True  # 假设总是成功
        except Exception as e:
            print(f"OSS删除失败: {str(e)}")
            return False

    @staticmethod
    def recover(oss_key):
        """
        恢复OSS文件(如果有回收站功能)
        :param oss_key: OSS文件key
        :return: 是否恢复成功
        """
        try:
            # 实现恢复逻辑
            return True
        except Exception as e:
            print(f"OSS恢复失败: {str(e)}")
            return False


class Icon(db.Model):
    """
    软件包数据模型
    """
    __tablename__ = 'icons'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False, comment='oss路径')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='md5名称')
    
    
    def to_dict(self):
        """
        将模型转换为字典格式
        """
        return {
            'id': self.id,
            'url': self.url,
            'name': self.name
        }

class User(db.Model):
    """
    用户模型
    """
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50),unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(255),  nullable=False, comment='密码')
    phone = db.Column(db.String(20), unique=True, nullable=True, comment='手机号')
    created_at = db.Column(db.DateTime, default=datetime.utcnow , comment='创建时间')

    
    def to_dict(self):
        """
        将模型转换为字典格式
        """
        return {
            'id': self.id,
            'user_name': self.user_name,
            'password': self.password,
            'phone': self.phone,
            'created_at': self.created_at
        }

    