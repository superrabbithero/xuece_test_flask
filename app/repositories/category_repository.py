from typing import List, Optional
from app.models import db, Categories

class CategoryRepository:
    
    @staticmethod
    def get_all() -> List[Categories]:
        """获取全部分类"""
        return Categories.query.order_by(Categories.id).all()
    
    @staticmethod
    def get_by_id(category_id: int) -> Optional[Categories]:
        """根据ID获取分类"""
        return Categories.query.get(category_id)
    
    @staticmethod
    def create(name: str, parent_id: int = None, path: str = None) -> Categories:
        """创建新分类"""
        category = Categories(
            name=name,
            parent_id=parent_id,
            path=path or f"/{name}"
        )
        db.session.add(category)
        db.session.commit()
        return category
    
    @staticmethod
    def update(category_id: int, **kwargs) -> Optional[Categories]:
        """更新分类信息"""
        category = Categories.query.get(category_id)
        if not category:
            return None
            
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        
        db.session.commit()
        return category
    
    @staticmethod
    def delete(category_id: int) -> bool:
        """删除分类"""
        category = Categories.query.get(category_id)
        if category:
            db.session.delete(category)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_children(parent_id: int) -> List[Categories]:
        """获取子分类"""
        return Categories.query.filter_by(parent_id=parent_id).all()
    
    @staticmethod
    def get_tree() -> List[dict]:
        """获取分类树形结构"""
        categories = Categories.query.all()
        tree = []
        id_to_node = {c.id: {'id': c.id, 'name': c.name, 'children': []} for c in categories}
        
        for category in categories:
            node = id_to_node[category.id]
            if category.parent_id is None:
                tree.append(node)
            else:
                parent_node = id_to_node.get(category.parent_id)
                if parent_node:
                    parent_node['children'].append(node)
        
        return tree