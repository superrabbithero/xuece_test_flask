from datetime import datetime
from typing import List, Optional
from app.models import db, Documents, Categories, Tags, doc_tag

class DocumentRepository:
    
    @staticmethod
    def get_by_id(doc_id: int) -> Optional[Documents]:
        """根据ID获取文档"""
        return Documents.query.get(doc_id)
    
    @staticmethod
    def create(user_id: int, oss_key: str, title:str = '新建文章', short_content: str = None, 
               status: int = 0, category_id: int = None) -> Documents:
        """创建新文档"""
        doc = Documents(
            user_id=user_id,
            oss_key=oss_key,
            title=title,
            short_content=short_content,
            status=status,
            category_id=category_id
        )
        db.session.add(doc)
        db.session.commit()
        # print(doc.to_dict())
        return doc
    
    @staticmethod
    def update(**kwargs) -> Optional[Documents]:
        """更新文档信息"""
        doc = Documents.query.get(kwargs.get('id'))
        if not doc:
            return None

        for key, value in kwargs.items():
            if key == 'id':
                continue
            if hasattr(doc, key) and value:
                setattr(doc, key, value)
        
        doc.updated_at = db.func.now()
        db.session.commit()
        return doc
    
    @staticmethod
    def delete(doc_id: int) -> bool:
        """删除文档"""
        doc = Documents.query.get(doc_id)
        if doc:
            db.session.delete(doc)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_user_documents(
        user_id: int,
        page: int = 1,
        per_page: int = 10,
        status: Optional[int] = None,
        title: Optional[str] = None,
        category_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None
    ):
        """
        分页获取用户文档（支持多条件筛选）
        
        :param user_id: 用户ID
        :param page: 页码
        :param per_page: 每页数量
        :param status: 文档状态筛选（可选）
        :param title: 标题关键词模糊搜索（可选）
        :param category_id: 分类ID筛选（可选）
        :param tag_ids: 标签ID列表（筛选包含任一标签的文档，可选）
        :return: Flask-SQLAlchemy Pagination对象
        """
        query = Documents.query.filter_by(user_id=user_id)
        
        print(user_id,status,title,category_id,tag_ids)
        # 状态筛选
        if status is not None:
            query = query.filter(Documents.status.in_(status))
        
        # 标题模糊搜索
        if title:
            query = query.filter(Documents.title.ilike(f'%{title}%'))
        
        # 分类筛选
        if category_id is not None:
            query = query.filter(Documents.category_id == category_id)
        
        # 标签筛选（包含任一标签）
        if tag_ids:
            query = query.join(doc_tag, Documents.id == doc_tag.doc_id)\
                         .filter(doc_tag.tag_id.in_(tag_ids))\
                         .group_by(Documents.id)\
                         .having(db.func.count(doc_tag.tag_id) >= 1)
        

        # 排序并分页
        return query.order_by(Documents.created_at.desc())\
                   .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def add_tag(doc_id: int, tag_id: int) -> bool:
        """为文档添加标签"""
        if not Documents.query.get(doc_id) or not Tags.query.get(tag_id):
            return False
            
        existing = doc_tag.query.filter_by(doc_id=doc_id, tag_id=tag_id).first()
        if existing:
            return True
            
        relation = doc_tag(doc_id=doc_id, tag_id=tag_id)
        db.session.add(relation)
        db.session.commit()
        return True
    
    @staticmethod
    def remove_tag(doc_id: int, tag_id: int) -> bool:
        """移除文档标签"""
        relation = doc_tag.query.filter_by(doc_id=doc_id, tag_id=tag_id).first()
        if relation:
            db.session.delete(relation)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_documents_by_category(category_id: int, page: int = 1, per_page: int = 10):
        """按分类获取文档"""
        return Documents.query.filter_by(category_id=category_id)\
                             .order_by(Documents.created_at.desc())\
                             .paginate(page=page, per_page=per_page, error_out=False)