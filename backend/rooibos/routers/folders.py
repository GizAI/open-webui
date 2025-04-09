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
            # 포스트그레SQL에서 GROUP BY 문제를 해결하기 위해 서브쿼리를 사용
            query = """
                SELECT folder.*,
                    COALESCE(bookmark_counts.active_count, 0) as active_bookmark_count,
                    COALESCE(bookmark_counts.deleted_count, 0) as deleted_bookmark_count
                FROM rb_folder folder
                LEFT JOIN (
                    SELECT folder_id, 
                        COUNT(*) FILTER (WHERE is_deleted = FALSE OR is_deleted IS NULL) as active_count,
                        COUNT(*) FILTER (WHERE is_deleted = TRUE) as deleted_count
                    FROM corp_bookmark
                    WHERE user_id = :userId
                    GROUP BY folder_id
                ) bookmark_counts ON folder.id = bookmark_counts.folder_id
                WHERE folder.user_id = :userId
            """
            params = {"userId": userId}
            if folderType:
                query += " AND folder.type = :folderType"
                params["folderType"] = folderType
            
            query += " ORDER BY folder.created_at DESC"
            
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


@router.get("/{folderId}/companies")
async def getFolderCompanyList(folderId: str, request: Request):    
    search_params = request.query_params
    userId = search_params.get("userId")
    deleted_param = search_params.get("deleted", "false")
    shared_param = search_params.get("shared", "false")
    
    # 페이징 파라미터 처리 추가
    page = int(search_params.get("page", "1"))
    page_size = int(search_params.get("page_size", "100"))
    offset = (page - 1) * page_size
    
    # 대소문자 구분 없이 파라미터 처리
    deleted = deleted_param.lower() in ["true", "1", "yes", "y"]
    shared = shared_param.lower() in ["true", "1", "yes", "y"]
    
    # 폴더 ID에서 공유 폴더 특별 처리
    isSharedFolder = folderId.startswith("shared-folder-")
    if isSharedFolder:
        shared = True
    
    try:
        with get_db() as db:
            # 1. 필요한 컬럼만 선택
            # 2. LEFT JOIN 대신 INNER JOIN 사용 (조건에 맞는 데이터만 필요)
            # 3. 성능 저하 요소(타입 변환, 중복 비교) 제거
            # 4. 페이징 적용
            
            # 공통 필드 정의 (중복 코드 제거)
            common_fields = """
                f.id,
                f.created_at,
                f.updated_at,
                f.company_id,
                f.user_id,
                rf.name as folder_name
            """
            
            # 카운트 쿼리를 위한 조건 생성
            count_condition = ""
            count_params = {"userId": userId}
            
            if deleted:
                count_condition = "f.user_id = :userId AND f.is_deleted = TRUE"
            elif shared:
                count_condition = "f.user_id != :userId AND (f.access_control::jsonb -> 'write' -> 'user_ids') ? :userId"
            else:
                count_condition = "f.user_id = :userId AND f.folder_id = :folderId AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)"
                count_params["folderId"] = folderId
            
            # 전체 레코드 수 조회 (페이징을 위해)
            count_query = f"""
                SELECT COUNT(*) as total
                FROM corp_bookmark f
                WHERE {count_condition}
            """
            
            total_result = db.execute(text(count_query), count_params).fetchone()
            total_count = total_result[0] if total_result else 0
            
            # 쿼리 최적화 1: public 회사 정보
            if deleted:
                query_public = f"""
                    SELECT 
                        {common_fields},
                        rmc.master_id::text as master_id,
                        rmc.company_name,
                        rmc.address,
                        rmc.business_registration_number,
                        'public' as company_type,
                        NULL AS entity_type
                    FROM corp_bookmark f
                    JOIN rb_folder rf ON f.folder_id = rf.id
                    JOIN rb_master_company rmc
                        ON f.business_registration_number = rmc.business_registration_number
                    WHERE f.user_id = :userId AND f.is_deleted = TRUE
                """
            elif shared:
                query_public = f"""
                    SELECT 
                        {common_fields},
                        rmc.master_id::text as master_id,
                        rmc.company_name,
                        rmc.address,
                        rmc.business_registration_number,
                        'public' as company_type,
                        NULL AS entity_type
                    FROM corp_bookmark f
                    JOIN rb_folder rf ON f.folder_id = rf.id
                    JOIN rb_master_company rmc 
                        ON f.business_registration_number = rmc.business_registration_number
                    WHERE f.user_id != :userId 
                    AND (f.access_control::jsonb -> 'write' -> 'user_ids') ? :userId
                """
            else:
                query_public = f"""
                    SELECT 
                        {common_fields},
                        rmc.master_id::text as master_id,
                        rmc.company_name,
                        rmc.address,
                        rmc.business_registration_number,
                        'public' as company_type,
                        NULL AS entity_type
                    FROM corp_bookmark f
                    JOIN rb_folder rf ON f.folder_id = rf.id
                    JOIN rb_master_company rmc 
                        ON f.business_registration_number = rmc.business_registration_number
                    WHERE f.user_id = :userId 
                    AND f.folder_id = :folderId 
                    AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)
                """
            
            # 쿼리 최적화 2: private 회사 정보
            if deleted:
                query_private = f"""
                    SELECT 
                        {common_fields},
                        pci.smtp_id::text as master_id,
                        pci.company_name,
                        pci.address,
                        pci.business_registration_number,
                        'private' as company_type,
                        pci.entity_type
                    FROM corp_bookmark f
                    JOIN rb_folder rf ON f.folder_id = rf.id
                    JOIN private_entity_info pci 
                        ON f.business_registration_number = pci.business_registration_number
                    WHERE f.user_id = :userId AND f.is_deleted = TRUE
                """
            elif shared:
                query_private = f"""
                    SELECT 
                        {common_fields},
                        pci.smtp_id::text as master_id,
                        pci.company_name,
                        pci.address,
                        pci.business_registration_number,
                        'private' as company_type,
                        pci.entity_type
                    FROM corp_bookmark f
                    JOIN rb_folder rf ON f.folder_id = rf.id
                    JOIN private_entity_info pci 
                        ON f.business_registration_number = pci.business_registration_number
                    WHERE f.user_id != :userId 
                    AND (f.access_control::jsonb -> 'write' -> 'user_ids') ? :userId
                """
            else:
                query_private = f"""
                    SELECT 
                        {common_fields},
                        pci.smtp_id::text as master_id,
                        pci.company_name,
                        pci.address,
                        pci.business_registration_number,
                        'private' as company_type,
                        pci.entity_type
                    FROM corp_bookmark f
                    JOIN rb_folder rf ON f.folder_id = rf.id
                    JOIN private_entity_info pci 
                        ON f.business_registration_number = pci.business_registration_number
                    WHERE f.user_id = :userId 
                    AND f.folder_id = :folderId 
                    AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)
                """
            
            # 최종 쿼리
            final_query = f"""
            SELECT * FROM (
                {query_public}
                UNION ALL
                {query_private}
            ) AS combined_results
            ORDER BY updated_at DESC
            LIMIT :limit OFFSET :offset
            """
            
            params = {
                "userId": userId, 
                "folderId": folderId, 
                "limit": page_size, 
                "offset": offset
            }
            
            # 실행 계획 분석 (개발 환경에서만)
            if log.level <= logging.DEBUG:
                explain_query = f"EXPLAIN ANALYZE {final_query}"
                explain_result = db.execute(text(explain_query), params)
                for row in explain_result:
                    log.debug(f"EXPLAIN: {row[0]}")
            
            # 실제 쿼리 실행
            result = db.execute(text(final_query), params)
            companyList = [dict(row._mapping) for row in result.fetchall()]

        log.info(f"getFolderCompanyList - returning {len(companyList)} results (total: {total_count})")
        
        return {
            "success": True,
            "data": companyList,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total_count
        }
    except Exception as e:
        log.error(f"getFolderCompanyList - error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False, 
                "error": "Failed to fetch company list for folder",
                "message": str(e)
            }
        )

@router.get("/trash/companies")
async def getTrashCompanyList(request: Request):    
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
                    rmc.address,
                    rmc.business_registration_number
                FROM corp_bookmark f
                INNER JOIN rb_master_company rmc
                    ON f.company_id::text = rmc.master_id::text
                WHERE f.user_id = :userId
                AND f.is_deleted = TRUE
                ORDER BY f.updated_at DESC
            """
            params = {"userId": userId}
            result = db.execute(text(query), params)
            companyList = [dict(row._mapping) for row in result.fetchall()]    

        return {
            "success": True,
            "data": companyList,
            "total": len(companyList),
        }
    except Exception as e:
        log.error("Trash API error: " + str(e))
        return {
            "success": False,
            "error": "Failed to fetch trash",
            "message": str(e)
        }

@router.get("/shared/companies")
async def getSharedCompanyList(request: Request):    
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
                    f.user_id,
                    rmc.master_id,
                    rmc.company_name,
                    rmc.address,
                    rmc.business_registration_number
                FROM corp_bookmark f
                INNER JOIN rb_master_company rmc
                    ON f.company_id::text = rmc.master_id::text
                WHERE f.user_id != :userId
                AND (f.access_control::jsonb -> 'write' -> 'user_ids') ? :userId
                ORDER BY f.updated_at DESC
            """
            params = {"userId": userId}
            result = db.execute(text(query), params)
            companyList = [dict(row._mapping) for row in result.fetchall()]    

        return {
            "success": True,
            "data": companyList,
            "total": len(companyList),
        }
    except Exception as e:
        log.error("Shared Companies API error: " + str(e))
        return {
            "success": False,
            "error": "Failed to fetch shared companies",
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
                SET access_control = :access_control, updated_at = extract(epoch from now())::bigint
                WHERE id = :id 
                RETURNING access_control
            """
            result_update = db.execute(
                text(sql_update),
                {"access_control": json.dumps(current_access), "id": id}
            )

            updated_access = result_update.fetchone()[0]
            db.commit();
        
        # Get user information for the updated access control
        user_list = []
        if "user_ids" in updated_access and updated_access["user_ids"]:
            for user_id in updated_access["user_ids"]:
                user = Users.get_user_by_id(user_id)
                if user:
                    user_list.append(user)
        
        return {
            "success": True,
            "data": updated_access,
            "users": user_list
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
            
            if user_id in current_access["user_ids"]:
                current_access["user_ids"].remove(user_id)
            
            sql_update = """
                UPDATE rb_folder 
                SET access_control = :access_control, updated_at = extract(epoch from now())::bigint
                WHERE id = :id 
                RETURNING access_control
            """
            result_update = db.execute(
                text(sql_update),
                {"access_control": json.dumps(current_access), "id": id}
            )

            updated_access = result_update.fetchone()[0]
            db.commit();
        
        # Get user information for the updated access control
        user_list = []
        if "user_ids" in updated_access and updated_access["user_ids"]:
            for user_id in updated_access["user_ids"]:
                user = Users.get_user_by_id(user_id)
                if user:
                    user_list.append(user)
        
        return {
            "success": True,
            "data": updated_access,
            "users": user_list
        }
        
    except Exception as e:
        log.error("Remove user access control error: " + str(e))
        return {
            "success": False,
            "error": "Remove user failed",
            "message": str(e)
        }

@router.delete("/{id}/delete")
async def delete_folder(id: str, request: Request):
    try:
        with get_db() as db:
            # 폴더 삭제
            delete_query = """
                DELETE FROM rb_folder
                WHERE id = :id
                RETURNING id
            """
            result = db.execute(text(delete_query), {"id": id})
            deleted = result.fetchone()
            
            if not deleted:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            db.commit()
            
        return {
            "success": True,
            "message": "Folder deleted successfully"
        }
    except Exception as e:
        log.error("Failed to delete folder: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to delete folder",
                "message": str(e)
            }
        )

@router.get("/{id}")
async def get_folder_by_id(id: str, request: Request):
    try:
        with get_db() as db:
            query = """
                SELECT *
                FROM rb_folder
                WHERE id = :id
            """
            params = {"id": id}
            result = db.execute(text(query), params)
            folder = dict(result.fetchone()._mapping)
            
            if not folder:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": "Folder not found",
                        "message": "The requested folder was not found"
                    }
                )
                
            
        return {
            "success": True,
            "data": folder
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("Failed to fetch folder by ID: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to fetch folder",
                "message": str(e)
            }
        )


