from typing import List
from app.models import db, doc_image, Documents, Images
from .result import RepoResult

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

    @staticmethod
    def update_doc_relations(doc_id: int, image_ids: List[int]) -> RepoResult:
        
        '''
        逻辑：
          - 删除库里多余的关联（在库中但不在 image_ids）
          - 增加库里没有的关联（在 image_ids 但库中不存在）
          - 被删除后不再关联到任何文档的图片 -> Images.in_use = False
          - 新增后被关联到文档的图片 -> Images.in_use = True
        '''
        if not isinstance(doc_id, int):
            return RepoResult.fail("doc_id 必须是整数")
        if not isinstance(image_ids, list):
            return RepoResult.fail("image_ids 必须是数组")

        try:
            if not Documents.query.get(doc_id):
                return RepoResult.fail(f"文档 {doc_id} 不存在")

            target_ids = set(int(i) for i in image_ids)

            with db.session.begin():
                # 当前已有关联
                existing_rows = doc_image.query.filter_by(doc_id=doc_id).all()
                existing_ids = {row.image_id for row in existing_rows}

                to_add = target_ids - existing_ids
                to_remove = existing_ids - target_ids

                if to_add:
                    exist_imgs = {img.id for img in Images.query.filter(Images.id.in_(list(to_add))).all()}
                    for iid in exist_imgs:
                        db.session.add(doc_image(image_id=iid, doc_id=doc_id))
                    if exist_imgs:
                        Images.query.filter(Images.id.in_(list(exist_imgs))).update(
                            {"in_use": True}, synchronize_session=False
                        )

                if to_remove:
                    doc_image.query.filter(
                        doc_image.doc_id == doc_id,
                        doc_image.image_id.in_(list(to_remove))
                    ).delete(synchronize_session=False)

                    # 检查是否还有其他文档引用；没有则 in_use=False
                    still_used_ids = {
                        row.image_id
                        for row in db.session.query(doc_image.image_id)
                        .filter(doc_image.image_id.in_(list(to_remove)))
                        .distinct()
                        .all()
                    }
                    set_false_ids = list(set(to_remove) - set(still_used_ids))
                    if set_false_ids:
                        Images.query.filter(Images.id.in_(set_false_ids)).update(
                            {"in_use": False}, synchronize_session=False
                        )

            return RepoResult.success({
                "doc_id": doc_id,
                "added": sorted(list(to_add)),
                "removed": sorted(list(to_remove)),
                "final_image_ids": sorted(list(target_ids)),
            })
        except SQLAlchemyError as e:
            db.session.rollback()
            return RepoResult.fail(f"数据库错误: {e}")