import time
import uuid
from typing import Optional
from datetime import datetime

from open_webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, Integer, JSON, DateTime

####################
# Category DB Schema
####################

class Category(Base):
    __tablename__ = "rb_category"

    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)


class CategoryModel(BaseModel):
    id: int
    data: dict
    version: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


####################
# Category Table Operations
####################

class CategoriesTable:
    def get_category_by_id(self, id: int) -> Optional[CategoryModel]:
        with get_db() as db:
            try:
                category = db.get(Category, id)
                return CategoryModel.model_validate(category) if category else None
            except Exception:
                return None

    def update_category_by_id(
        self,
        id: int,
        data: dict,
        version: int,
    ) -> Optional[CategoryModel]:
        with get_db() as db:
            try:
                db.query(Category).filter_by(id=id).update(
                    {
                        "data": data,
                        "version": version,
                        "updated_at": datetime.now()
                    }
                )
                db.commit()
                return self.get_category_by_id(id)
            except Exception:
                return None


Categories = CategoriesTable()
