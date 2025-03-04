from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS

import logging
import json

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

@router.get("/{id}")
async def get_note(id: str):
    try:
        with get_db() as db:
            query = "SELECT * FROM rb_note WHERE id = :noteId"
            params = {"noteId": id}
            result = db.execute(text(query), params)
            row = result.fetchone()
            note = dict(row._mapping) if row else None
        return {"success": True, "note": note}
    except Exception as e:
        log.error("Failed to get note: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Failed to get note", "message": str(e)}
        )

@router.post("/add")
async def addNote(request: Request):
    search_params = request.query_params
    userId = search_params.get("userId")
    newId = search_params.get("newId")
    folderId = search_params.get("folderId", "")
    title = '새페이지'
    content = ''

    try:
        with get_db() as db:
            query = """
                INSERT INTO rb_note (id, user_id, title, content, folder_id, created_at, updated_at)
                VALUES (:newId, :userId, :title, :content, :folderId, now(), now())
                RETURNING *
            """
            params = {"newId": newId, "userId": userId, "title": title, "content": content, "folderId": folderId}
            result = db.execute(text(query), params)
            row = result.fetchone()
            if row:
                note = dict(row._mapping)
            else:
                note = None
            db.commit()

        return {
            "success": True,
            "note": note
        }
    except Exception as e:
        log.error("Failed to add note: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to add note",
                "message": str(e)
            }
        )

@router.put("/update")
async def updateNote(request: Request):
    search_params = request.query_params
    noteId = search_params.get("noteId")
    try:
        data = await request.json()
        new_title = data.get("title")
        new_content = data.get("content")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request payload")
    
    # 업데이트할 필드를 동적으로 구성합니다.
    fields_to_update = []
    params = {"noteId": noteId}
    if new_title is not None:
        fields_to_update.append("title = :new_title")
        params["new_title"] = new_title
    if new_content is not None:
        fields_to_update.append("content = :new_content")
        # 한글이 그대로 보이도록 ensure_ascii=False 옵션 사용
        # 쌍따옴표 제거: json.dumps()로 직렬화된 문자열에서 처음과 끝의 쌍따옴표 제거
        content_json = json.dumps(new_content, ensure_ascii=False)
        if content_json.startswith('"') and content_json.endswith('"'):
            content_json = content_json[1:-1]
        params["new_content"] = content_json
    
    # 업데이트할 항목이 없으면 에러 처리
    if not fields_to_update:
        raise HTTPException(status_code=400, detail="No update fields provided")
    
    set_clause = ", ".join(fields_to_update) + ", updated_at = now()"
    
    try:
        with get_db() as db:
            query = f"""
                UPDATE rb_note
                SET {set_clause}
                WHERE id = :noteId
                RETURNING *
            """
            result = db.execute(text(query), params)
            row = result.fetchone()
            note = dict(row._mapping) if row else None
            db.commit()
        return {"success": True, "note": note}
    except Exception as e:
        log.error("Failed to update note: %s", e)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Failed to update note", "message": str(e)}
        )

@router.delete("/{id}/delete")
async def delete_note(id: str):
    try:
        sql_query = """
        DELETE FROM rb_note
        WHERE id = :id
        """
        log.info(f"Executing query: {sql_query} with parameter id={id}")
        with get_db() as db:
            db.execute(text(sql_query), {"id": id})
            db.commit() 

        return {
            "success": True,
            "message": f"Note with company_id {id} has been successfully deleted."
        }
    except Exception as e:
        log.error("Delete API error: " + str(e))
        return {
            "success": False,
            "error": "Delete failed",
            "message": str(e)
        }
    



