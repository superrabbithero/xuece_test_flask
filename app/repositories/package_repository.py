# from app import db
from app.models import db, Package, Icon  # 导入package模型
from sqlalchemy import or_, and_, distinct
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload

class PackageRepository:
    """使用Flask-SQLAlchemy的CRUD操作类"""
    @staticmethod
    def get(package_id):
        """
        通过ID获取单个Package记录
        :param package_id: 包ID
        :return: Package对象或None
        """
        return Package.query.get(package_id)

    @staticmethod
    def create(package_data):
        """创建新包记录"""
        package = Package(**package_data)
        db.session.add(package)
        db.session.commit()
        return package

    @staticmethod
    def update_status(package_id, status):
        """更新包状态"""
        rows_updated = Package.query.filter_by(id=package_id).update(
            {'status': status},
            synchronize_session=False
        )
        db.session.commit()
        return rows_updated

    @staticmethod
    def update_comment(package_id, comment):
        """更新包描述"""
        Package.query.filter_by(id=package_id).update(
            {'comment': comment},
            synchronize_session=False
        )
        db.session.commit()


    @staticmethod
    def update_package_info(package_id, comment=None, name=None):
        """
        更新包信息（描述或名称）
        参数:
            package_id: 要更新的包ID
            comment (可选): 新的描述，如果提供则更新
            name (可选): 新的名称，如果提供则更新
        """
        update_data = {}
        if comment is not None:
            update_data['comment'] = comment
        if name is not None:
            update_data['name'] = name

        if not update_data:
            raise ValueError("至少需要提供 comment 或 name 中的一个参数")

        Package.query.filter_by(id=package_id).update(
            update_data,
            synchronize_session=False
        )
        db.session.commit()

    @staticmethod
    def get_versions(appname, system=None):
        """获取指定应用的所有版本"""
        query = db.session.query(distinct(Package.version)).filter(
            Package.appname == appname
        )
        
        if system and system != 'all':
            query = query.filter(Package.system == system)
            
        return [v[0] for v in query.all()]

    @staticmethod
    def get_paginated_packages(appname, system=None, version=None, ar=None, page=1, per_page=10):
        """分页查询包列表"""
        query = Package.query.filter(Package.appname == appname)
        
        # 构建动态过滤条件
        filters = []
        if system and system != 'all':
            filters.append(Package.system == system)
        if version and version != '全部':
            filters.append(Package.version == version)
        if ar and ar != '全部':
            filters.append(Package.ar == ar)
            
        if filters:
            query = query.filter(and_(*filters))
        
        return query.order_by(
            Package.create_time.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def delete(package_id):
        """通过ID删除包"""
        package = Package.query.get(package_id)
        if package:
            db.session.delete(package)
            db.session.commit()
            return True
        return False

    @staticmethod
    def delete_by_packagename(packagename):
        """通过包名删除包"""
        Package.query.filter(Package.packagename == packagename).delete()
        db.session.commit()

    @staticmethod
    def get_count(appname, system=None, version=None, ar=None):
        """获取符合条件的包数量"""
        query = db.session.query(func.count(Package.id)).filter(
            Package.appname == appname
        )
        
        if system and system != 'all':
            query = query.filter(Package.system == system)
        if version and version != '全部':
            query = query.filter(Package.version == version)
        if ar and ar != '全部':
            query = query.filter(Package.ar == ar)
            
        return query.scalar()