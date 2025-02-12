from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

from rooibos.models.categories import Categories, CategoryModel
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()

############################
# Get Category by ID
############################

@router.get("/{category_id}", response_model=Optional[CategoryModel])
async def get_category_by_id(category_id: int):
    category = Categories.get_category_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

############################
# Update Category by ID
############################

class CategoryUpdateModel(BaseModel):
    data: dict
    version: int

@router.put("/{category_id}", response_model=Optional[CategoryModel])
async def update_category_by_id(
    category_id: int,
    form_data: CategoryUpdateModel,
):
    category = Categories.update_category_by_id(
        category_id, 
        form_data.data,
        form_data.version
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found or update failed")
    return category
