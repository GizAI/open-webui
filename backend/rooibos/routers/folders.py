from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS

import logging
import requests
import uuid
import time

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

@router.get("/")
async def getNoteFolder(request: Request):
    search_params = request.query_params
    userId = search_params.get("userId")  
    try:
        with get_db() as db:
            query = """
                SELECT *
                FROM rb_folder
                WHERE user_id = :userId
                  AND type = 'note'
                ORDER BY created_at ASC
            """
            params = {"userId": userId}
            result = db.execute(text(query), params)
            folders = [dict(row._mapping) for row in result.fetchall()]

        return {
            "success": True,
            "folders": folders,
            "total": len(folders)
        }
    except Exception as e:
        log.error("Failed to fetch note folders: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to fetch note folders",
                "message": str(e)
            }
        )

@router.post("/add")
async def addNoteFolder(request: Request):
    search_params = request.query_params
    userId = search_params.get("userId")  
    folder_name = request.query_params.get("name", "Untitle")
    new_id = str(uuid.uuid4())
    now = int(time.time())
    try:
        with get_db() as db:
            query = """
                INSERT INTO rb_folder (id, parent_id, user_id, "name", type, items, meta, is_expanded, created_at, updated_at)
                VALUES (:id, NULL, :userId, :name, 'note', NULL, NULL, false, :created_at, :updated_at)
                RETURNING *
            """
            params = {"id": new_id, "userId": userId, "name": folder_name, "created_at": now, "updated_at": now}
            result = db.execute(text(query), params)
            db.commit()
            folder = dict(result.fetchone())

        return {
            "success": True,
            "folder": folder
        }
    except Exception as e:
        log.error("Failed to add note folder: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to add note folder",
                "message": str(e)
            }
        )


