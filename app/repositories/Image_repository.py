from typing import List, Optional
from app.models import db, Images

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
    
    