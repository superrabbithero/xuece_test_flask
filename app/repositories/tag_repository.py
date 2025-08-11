from typing import List, Optional
from app.models import db, Tags, doc_tag, Documents

class TagRepository:
    
    @staticmethod
    def get_all() -> List[Tags]:
        """获取全部标签"""
        return Tags.query.order_by(Tags.name).all()
    
    @staticmethod
    def get_by_id(tag_id: int) -> Optional[Tags]:
        """根据ID获取标签"""
        return Tags.query.get(tag_id)
    
    @staticmethod
    def create(name: str) -> Tags:
        """创建新标签"""
        tag = Tags(name=name)
        db.session.add(tag)
        db.session.commit()
        return tag
    
    @staticmethod
    def update(tag_id: int, name: str) -> Optional[Tags]:
        """更新标签信息"""
        tag = Tags.query.get(tag_id)
        if tag:
            tag.name = name
            db.session.commit()
        return tag
    
    @staticmethod
    def delete(tag_id: int) -> bool:
        """删除标签"""
        tag = Tags.query.get(tag_id)
        if tag:
            # 先删除关联关系
            doc_tag.query.filter_by(tag_id=tag_id).delete()
            db.session.delete(tag)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_documents_by_tag(tag_id: int, page: int = 1, per_page: int = 10):
        """获取拥有该标签的文档"""
        return Documents.query.join(doc_tag, Documents.id == doc_tag.doc_id)\
                             .filter(doc_tag.tag_id == tag_id)\
                             .order_by(Documents.created_at.desc())\
                             .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def search_by_name(name: str) -> List[Tags]:
        """按名称搜索标签"""
        return Tags.query.filter(Tags.name.ilike(f"%{name}%")).all()