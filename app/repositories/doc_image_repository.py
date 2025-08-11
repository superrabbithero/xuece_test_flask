from typing import List
from app.models import db, doc_image, Documents, Images

class DocImageRepository:
    
    @staticmethod
    def get_images_for_document(doc_id: int) -> List[Images]:
        """获取文档的所有图片"""
        return Images.query.join(doc_image, Images.id == doc_image.image_id)\
                        .filter(doc_image.doc_id == doc_id)\
                        .all()
    
    @staticmethod
    def get_documents_for_tag(image_id: int) -> List[Documents]:
        """获取拥有该标签的所有文档"""
        return Documents.query.join(doc_image, Documents.id == doc_image.doc_id)\
                             .filter(doc_image.image_id == image_id)\
                             .all()
    
    @staticmethod
    def get_all_relations() -> List[doc_image]:
        """获取所有文档-标签关系"""
        return doc_image.query.all()
    
    @staticmethod
    def delete_relations_for_document(doc_id: int) -> int:
        """删除文档的所有标签关系"""
        count = doc_image.query.filter_by(doc_id=doc_id).delete()
        db.session.commit()
        return count