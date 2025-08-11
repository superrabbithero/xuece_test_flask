from typing import List
from app.models import db, doc_tag, Documents, Tags

class DocTagRepository:
    
    @staticmethod
    def get_tags_for_document(doc_id: int) -> List[Tags]:
        """获取文档的所有标签"""
        return Tags.query.join(doc_tag, Tags.id == doc_tag.tag_id)\
                        .filter(doc_tag.doc_id == doc_id)\
                        .all()
    
    @staticmethod
    def get_documents_for_tag(tag_id: int) -> List[Documents]:
        """获取拥有该标签的所有文档"""
        return Documents.query.join(doc_tag, Documents.id == doc_tag.doc_id)\
                             .filter(doc_tag.tag_id == tag_id)\
                             .all()
    
    @staticmethod
    def get_all_relations() -> List[doc_tag]:
        """获取所有文档-标签关系"""
        return doc_tag.query.all()
    
    @staticmethod
    def delete_relations_for_document(doc_id: int) -> int:
        """删除文档的所有标签关系"""
        count = doc_tag.query.filter_by(doc_id=doc_id).delete()
        db.session.commit()
        return count