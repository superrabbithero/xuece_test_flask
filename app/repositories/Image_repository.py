from typing import List, Optional
from app.models import db, Images
from .result import RepoResult

class ImageRepository:
    
    @staticmethod
    def create(oss_key: str) -> Images:
        """创建新标签"""
        image = Images(oss_key=oss_key)
        db.session.add(image)
        db.session.commit()
        return image
    
    @staticmethod
    def update(oss_key: str, **kwargs) -> Optional[Images]:
        """更新标签信息"""

        image = Images.query.filter_by(oss_key=oss_key)[0]

        for key, value in kwargs.items():
            if hasattr(image, key):
                setattr(image, key, value)

        db.session.commit()

        return image

    @staticmethod
    def batch_update(ids: List[int], uploaded: Optional[bool] = None, in_use: Optional[bool] = None) -> RepoResult:
        # 参数校验
        if not ids:
            return RepoResult.fail("ids 不能为空")
        if uploaded is None and in_use is None:
            return RepoResult.fail("至少提供一个待更新字段：uploaded / in_use")
        if uploaded is not None and not isinstance(uploaded, bool):
            return RepoResult.fail("uploaded 必须是布尔值")
        if in_use is not None and not isinstance(in_use, bool):
            return RepoResult.fail("in_use 必须是布尔值")

        try:
            update_values = {}
            if uploaded is not None:
                update_values["uploaded"] = uploaded
            if in_use is not None:
                update_values["in_use"] = in_use

            # 批量 UPDATE，效率更高
            with db.session.begin():
                updated = Images.query.filter(Images.id.in_(ids)).update(
                    update_values, synchronize_session=False
                )

            return RepoResult.success({"updated": int(updated)})
        except SQLAlchemyError as e:
            db.session.rollback()
            return RepoResult.fail(f"数据库错误: {e}")



    
    