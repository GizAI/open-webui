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
    data = await request.json()
    userId = request.query_params.get("userId")  
    folder_name = data.get("name", "Untitle")
    folder_type = data.get("type")
    new_id = str(uuid.uuid4())
    now = int(time.time())
    try:
        with get_db() as db:
            query = """
                INSERT INTO rb_folder (id, parent_id, user_id, "name", type, items, meta, is_expanded, created_at, updated_at)
                VALUES (:id, NULL, :userId, :name, :folderType, NULL, NULL, false, :created_at, :updated_at)
                RETURNING *
            """
            params = {"id": new_id, "userId": userId, "name": folder_name, "folderType": folder_type, "created_at": now, "updated_at": now}
            result = db.execute(text(query), params)
            folder = dict(result.fetchone()._mapping)  # _mapping 속성 사용
            db.commit()

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

@router.get("/rename")
async def update_folder_name(request: Request):
    search_params = request.query_params
    folderId = search_params.get("folderId")
    folderName = search_params.get("folderName")
    now = int(time.time())
    try:
        with get_db() as db:
            query = """
                UPDATE rb_folder
                SET name = :folderName, updated_at = :updateAt
                WHERE id = :folderId
            """
            params = {"folderName": folderName, "folderId": folderId, "updateAt": now}
            db.execute(text(query), params)
            db.commit() 
            
        return {
            "success": True,
            "message": "success"
        }
    except Exception as e:
        log.error("Failed note folder rename : %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed note folder rename",
                "message": str(e)
            }
        )

@router.get("/{folderId}/notes")
async def getFolderNoteList(folderId: str, request: Request):    
    search_params = request.query_params
    userId = search_params.get("userId")
    try:
        with get_db() as db:
            query = """
                SELECT *
                FROM rb_note
                WHERE user_id = :userId and folder_id = :folderId
                ORDER BY updated_at ASC
            """
            params = {"userId": userId, "folderId": folderId}
            result = db.execute(text(query), params)
            notes = [dict(row._mapping) for row in result.fetchall()]

        return {
            "success": True,
            "notes": notes,
            "total": len(notes)
        }
    except Exception as e:
        log.error("Failed to fetch notes for folder: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to fetch notes for folder",
                "message": str(e)
            }
        )

@router.get("/{folderId}/companies")
async def getFolderCompanyList(folderId: str, request: Request):    
    search_params = request.query_params
    userId = search_params.get("userId")
    try:
        with get_db() as db:
            query = """
                SELECT DISTINCT
                    f.id,
                    f.created_at,
                    f.updated_at,
                    f.company_id,
                    rmc.master_id,
                    rmc.company_name,
                    rmc.address
                FROM corp_bookmark f
                INNER JOIN rb_master_company rmc
                    ON f.company_id::text = rmc.master_id::text
                WHERE f.user_id = :userId AND f.folder_id = :folderId
                ORDER BY f.updated_at DESC
            """
            params = {"userId": userId, "folderId": folderId}
            result = db.execute(text(query), params)
            companyList = [dict(row._mapping) for row in result.fetchall()]    

        return {
            "success": True,
            "data": companyList,
            "total": len(companyList),
        }
    except Exception as e:
        log.error("Search API error: " + str(e))
        return {
            "success": False,
            "error": "Search failed",
            "message": str(e)
        }

@router.post("/move")
async def moveBookmark(request: Request):
    data = await request.json()
    userId = request.query_params.get("userId")
    bookmarkId = data.get("bookmarkId")
    targetFolderId = data.get("targetFolderId")
    
    if not (userId and bookmarkId and targetFolderId):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Missing required parameters",
                "message": "userId, bookmarkId, 그리고 targetFolderId 값이 필요합니다."
            }
        )
    
    try:
        with get_db() as db:
            query = """
                UPDATE corp_bookmark
                SET folder_id = :targetFolderId, updated_at = now()
                WHERE id = :bookmarkId AND user_id = :userId
                RETURNING *
            """
            params = {
                "targetFolderId": targetFolderId,
                "bookmarkId": bookmarkId,
                "userId": userId
            }
            result = db.execute(text(query), params)
            updated = result.fetchone()
            if updated is None:
                raise Exception("해당 북마크가 존재하지 않거나 사용자 정보가 일치하지 않습니다.")
            updated_bookmark = dict(updated._mapping)
            db.commit()

        return {
            "success": True,
            "bookmark": updated_bookmark
        }
    except Exception as e:
        log.error("북마크 이동 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "북마크 이동 실패",
                "message": str(e)
            }
        )
