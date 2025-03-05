from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.users import Users

import logging
import requests
import uuid
import time
import json

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

@router.get("/")
async def getNoteFolder(request: Request):
    search_params = request.query_params
    userId = search_params.get("userId")  
    folderType = search_params.get("folderType")
    try:
        with get_db() as db:
            query = """
                SELECT *
                FROM rb_folder
                WHERE user_id = :userId
            """
            params = {"userId": userId}
            if folderType:
                query += " AND type = :folderType"
                params["folderType"] = folderType
            query += " ORDER BY created_at DESC"
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
            # Update the folder name
            update_query = """
                UPDATE rb_folder
                SET name = :folderName, updated_at = :updateAt
                WHERE id = :folderId
            """
            params = {"folderName": folderName, "folderId": folderId, "updateAt": now}
            db.execute(text(update_query), params)
            
            # Fetch the updated folder data
            select_query = """
                SELECT * FROM rb_folder
                WHERE id = :folderId
            """
            result = db.execute(text(select_query), {"folderId": folderId})
            folder = dict(result.fetchone()._mapping)
            
            db.commit() 
            
        return {
            "success": True,
            "folder": folder
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

@router.get("/{id}/accessControl/users")
async def get_access_control_users(id: str, request: Request):
    try:
        with get_db() as db:
            # folder의 access_control 필드를 조회
            sql_select = "SELECT access_control FROM rb_folder WHERE id = :id"
            result = db.execute(text(sql_select), {"id": id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Folder not found")
            current_access = row[0] or {}
            user_ids = current_access.get("user_ids", [])
            if not user_ids:
                return {"success": True, "data": []}
            
            user_list = []
            for user_id in user_ids:
                user_list.append(Users.get_user_by_id(user_id))
            
        return {"success": True, "data": user_list}
    
    except Exception as e:
        log.error("Get access control users error: " + str(e))
        return {"success": False, "error": "Get users failed", "message": str(e)}

@router.post("/{id}/accessControl/addUser")
async def add_user_access_control(id: str, request: Request):
    try:
        search_params = request.query_params
        user_id = search_params.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        with get_db() as db:
            sql_select = "SELECT access_control FROM rb_folder WHERE id = :id"
            result = db.execute(text(sql_select), {"id": id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            current_access = row[0] or {}
            
            if "user_ids" not in current_access or not isinstance(current_access["user_ids"], list):
                current_access["user_ids"] = []
            
            if user_id not in current_access["user_ids"]:
                current_access["user_ids"].append(user_id)
            
            sql_update = """
                UPDATE rb_folder 
                SET access_control = :access_control, updated_at = now() 
                WHERE id = :id 
                RETURNING access_control
            """
            result_update = db.execute(
                text(sql_update),
                {"access_control": json.dumps(current_access), "id": id}
            )
            updated_access = result_update.fetchone()[0]
            db.commit();
        
        return {
            "success": True,
            "data": updated_access
        }
        
    except Exception as e:
        log.error("Add user access control error: " + str(e))
        return {
            "success": False,
            "error": "Add user failed",
            "message": str(e)
        }


@router.post("/{id}/accessControl/removeUser")
async def remove_user_access_control(id: str, request: Request):
    try:
        search_params = request.query_params
        user_id = search_params.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        with get_db() as db:
            sql_select = "SELECT access_control FROM rb_folder WHERE id = :id"
            result = db.execute(text(sql_select), {"id": id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            current_access = row[0] or {}
            if "user_ids" not in current_access or not isinstance(current_access["user_ids"], list):
                current_access["user_ids"] = []
            
            current_access["user_ids"] = [uid for uid in current_access["user_ids"] if uid != user_id]
            
            sql_update = """
                UPDATE rb_folder 
                SET access_control = :access_control, updated_at = now() 
                WHERE id = :id 
                RETURNING access_control
            """
            result_update = db.execute(
                text(sql_update),
                {"access_control": json.dumps(current_access), "id": id}
            )
            updated_access = result_update.fetchone()[0]
            db.commit();
        
        return {
            "success": True,
            "status_code":200,
            "data": updated_access
        }
    
    except Exception as e:
        log.error("Remove user access error: " + str(e))        
        return {
            "status_code":500,
            "content":{
                "success": False,
                "error": "Remove user failed",
                "message": str(e)
            }
        }


