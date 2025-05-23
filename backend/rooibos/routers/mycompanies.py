from fastapi import APIRouter, Request, HTTPException

from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.users import UserModel, Users
from open_webui.utils.access_control import has_access
from open_webui.models.groups import Groups

import json
import logging
import uuid

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

def format_parameter(param):
    if param is None:
        return "NULL"
    if isinstance(param, str):
        param = param.replace("'", "''")
        return f"'{param}'"
    return str(param)

def get_executable_query(sql_query: str, params: list) -> str:   
    executable_query = sql_query
    
    sorted_params = sorted(
        [(param, index + 1) for index, param in enumerate(params)],
        key=lambda x: -x[1]
    )
    for param, index in sorted_params:
        placeholder = f"${index}"
        formatted_param = format_parameter(param)
        executable_query = executable_query.replace(placeholder, formatted_param)
    return executable_query

@router.get("/user/{user_id}")
async def get_mycompanies(user_id: str):
    try:
        params = [user_id]
        sql_query = """
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
            WHERE f.user_id = $1
            AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)
            ORDER BY f.updated_at DESC
        """
        favorites = get_executable_query(sql_query, params)
        log.info(f"Executing query: {favorites}")

        with get_db() as db:
            result = db.execute(text(favorites))
            bookmarks = [row._mapping for row in result.fetchall()]

        return {
            "success": True,
            "data": bookmarks,
            "total": len(bookmarks),
        }
    except Exception as e:
        log.error("Search API error: " + str(e))
        return {
            "success": False,
            "error": "Search failed",
            "message": str(e)
        }

    
@router.get("/{id}")
async def get_mycompany_by_id(id: str, request: Request):
    search_params = request.query_params
    user_id = search_params.get("user_id")
    
    try:
        # 1. 기존 쿼리 최적화:
        #   - WITH 절 사용하여 파일 정보를 미리 필터링
        #   - 필요 없는 LEFT JOIN 제거 (smtp_financial_company, smtp_executives)
        #   - 주석을 추가하여 가독성 향상
        bookmark_sql_query = """
        WITH file_data AS (
            -- 파일 정보를 미리 필터링하여 메인 쿼리와 조인
            SELECT 
                file_id,
                jsonb_build_object(
                    'id', fi.id,
                    'user_id', fi.user_id,
                    'filename', fi.filename,
                    'meta', fi.meta,
                    'created_at', fi.created_at,
                    'hash', fi.hash,
                    'data', fi."data",
                    'updated_at', fi.updated_at,
                    'path', fi."path",
                    'access_control', fi.access_control
                ) AS file_info
            FROM (
                -- 북마크에서 파일 ID만 추출하는 서브쿼리
                SELECT 
                    jsonb_array_elements_text(f.data::jsonb->'file_ids') AS file_id
                FROM corp_bookmark f
                WHERE f.id = :id AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)
            ) AS file_ids
            JOIN file fi ON fi.id::text = file_ids.file_id
        )
        SELECT DISTINCT
            -- 북마크 기본 정보
            f.id as bookmark_id,
            f.created_at,
            f.updated_at,
            f.company_id, 
            f.user_id as bookmark_user_id,
            f.folder_id,
            f.data::jsonb as data_files,
            f.access_control::jsonb,
            
            -- 파일 정보를 집계 (파일이 있는 경우에만)
            CASE WHEN f.data IS NOT NULL 
                THEN jsonb_agg(fd.file_info) 
                ELSE NULL 
            END AS files,
            
            -- 회사 기본 정보
            rmc.master_id,
            rmc.company_name,
            rmc.representative,
            rmc.postal_code,
            rmc.address,
            rmc.phone_number,
            rmc.fax_number,
            rmc.website,
            rmc.email,
            rmc.business_registration_number,
            
            -- 회사 추가 정보
            rmc.company_type,
            rmc.establishment_date,
            rmc.founding_date,
            rmc.employee_count,
            rmc.industry_code1,
            rmc.industry_code2,
            rmc.industry,
            rmc.main_product,
            rmc.main_bank,
            rmc.main_branch,
            rmc.group_name,
            rmc.stock_code,
            rmc.corporate_number,
            rmc.english_name,
            rmc.trade_name,
            
            -- 재무 정보
            rmc.fiscal_month,
            rmc.sales_year,
            rmc.recent_sales,
            rmc.profit_year,
            rmc.recent_profit,
            rmc.operating_profit_year,
            rmc.recent_operating_profit,
            rmc.asset_year,
            rmc.recent_total_assets,
            rmc.debt_year,
            rmc.recent_total_debt,
            rmc.equity_year,
            rmc.recent_total_equity,
            rmc.capital_year,
            rmc.recent_capital,
            
            -- 지역 및 산업 정보
            rmc.region1,
            rmc.region2,
            rmc.industry_major,
            rmc.industry_middle,
            rmc.industry_small,
            rmc.latitude,
            rmc.longitude,
            
            -- 기타 회사 정보
            rmc.sme_type,
            rmc.research_info,
            rmc.representative_birth,
            rmc.is_family_shareholder,
            rmc.is_non_family_shareholder,
            rmc.financial_statement_year,
            rmc.total_assets,
            rmc.total_equity,
            rmc.net_income,
            rmc.venture_confirmation_type,
            rmc.venture_valid_from,
            rmc.venture_valid_until,
            rmc.confirming_authority,
            rmc.new_reconfirmation_code
        FROM corp_bookmark f
        -- 기업 정보와 조인 (타입 맞추기 위해 ::text 유지)
        JOIN rb_master_company rmc ON f.company_id::text = rmc.master_id::text
        -- 파일 정보와 LEFT JOIN (파일이 없어도 기업 정보는 반환)
        LEFT JOIN file_data fd ON f.data IS NOT NULL
        WHERE f.id = :id
        AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)           
        GROUP BY
            -- 필요한 컬럼만 GROUP BY에 포함 (JSON 타입 컬럼은 제외하거나 캐스팅)
            f.id, f.created_at, f.updated_at, f.company_id, f.user_id, f.folder_id, 
            -- JSON 컬럼을 TEXT로 변환하여 GROUP BY 가능하게 함
            f.data::text, f.access_control::text,
            rmc.master_id, rmc.company_name, rmc.representative, rmc.postal_code, rmc.address,
            rmc.phone_number, rmc.fax_number, rmc.website, rmc.email, rmc.company_type,
            rmc.establishment_date, rmc.founding_date, rmc.employee_count, rmc.industry_code1,
            rmc.industry_code2, rmc.industry, rmc.main_product, rmc.main_bank, rmc.main_branch,
            rmc.group_name, rmc.stock_code, rmc.business_registration_number, rmc.corporate_number,
            rmc.english_name, rmc.trade_name, rmc.fiscal_month, rmc.sales_year, rmc.recent_sales,
            rmc.profit_year, rmc.recent_profit, rmc.operating_profit_year, rmc.recent_operating_profit,
            rmc.asset_year, rmc.recent_total_assets, rmc.debt_year, rmc.recent_total_debt,
            rmc.equity_year, rmc.recent_total_equity, rmc.capital_year, rmc.recent_capital,
            rmc.region1, rmc.region2, rmc.industry_major, rmc.industry_middle, rmc.industry_small,
            rmc.latitude, rmc.longitude, rmc.sme_type, rmc.research_info, rmc.representative_birth,
            rmc.is_family_shareholder, rmc.is_non_family_shareholder, rmc.financial_statement_year,
            rmc.total_assets, rmc.total_equity, rmc.net_income, rmc.venture_confirmation_type,
            rmc.venture_valid_from, rmc.venture_valid_until, rmc.confirming_authority, rmc.new_reconfirmation_code
        ORDER BY f.updated_at DESC
        """
        
        stmt = text(bookmark_sql_query)
        params = {"id": id}
        
        with get_db() as db:
            # 디버그 레벨에서만 로깅
            if log.level <= logging.DEBUG:
                compiled_query = stmt.compile(dialect=db.bind.dialect, compile_kwargs={"literal_binds": True})
                log.debug(f"Query: {compiled_query}")
            
            # 실제 쿼리 실행
            bookmark_result = db.execute(stmt, params)
            bookmark_data = [row._mapping for row in bookmark_result.fetchall()]
            
            if not bookmark_data:
                return {
                    "success": False,
                    "error": "북마크를 찾을 수 없음",
                    "message": f"Bookmark with id '{id}' 를 찾을 수 없습니다."
                }
            
            bookmark_user_id = bookmark_data[0].bookmark_user_id
            access_control = bookmark_data[0].access_control
            
            if user_id and user_id != bookmark_user_id:
                
                if access_control is None:
                    return {
                        "success": False,
                        "error": "권한 없음",
                        "message": f"Bookmark with id '{id}' 에 대한 접근 권한이 없습니다."
                    }
                
                user_groups = Groups.get_groups_by_member_id(user_id)
                user_group_ids = [group.id for group in user_groups]
                
                write_permission = access_control.get("write", {})
                permitted_group_ids = write_permission.get("group_ids", [])
                permitted_user_ids = write_permission.get("user_ids", [])
                
                if not (user_id in permitted_user_ids or any(
                    group_id in permitted_group_ids for group_id in user_group_ids
                )):
                    return {
                        "success": False,
                        "error": "권한 없음",
                        "message": f"Bookmark with id '{id}' 에 대한 접근 권한이 없습니다."
                    }
            
            # Chat List 조회 - 기존 로직 유지
            conditions = []
            
            bookmark_owner_id = bookmark_data[0].bookmark_user_id            
            
            # 항상 북마크 소유자의 채팅을 가져옴
            conditions.append("user_id = " + format_parameter(bookmark_owner_id))
            conditions.append("c.business_registration_number = " + format_parameter(bookmark_data[0].business_registration_number))
            
            chat_query = "SELECT * FROM chat c WHERE " + " AND ".join(conditions)
            chat_query = get_executable_query(chat_query, [])
            
            # 디버그 레벨에서만 로깅
            if log.level <= logging.DEBUG:
                log.debug(f"Chat query: {chat_query}")
                
            chat_result = db.execute(text(chat_query))
            chat_list = [row._mapping for row in chat_result.fetchall()]
        
        return {
            "success": True,
            "bookmark": bookmark_data,
            "bookmark_total": len(bookmark_data),
            "chatList": chat_list,
            "chat_total": len(chat_list)
        }
    except Exception as e:
        log.error(f"Get mycompany by ID error: {str(e)}")
        return {
            "success": False,
            "error": "Fetch failed",
            "message": str(e)
        }



@router.delete("/{id}/delete")
async def delete_mycompany(id: str):
    try:
        sql_query = """
        DELETE FROM corp_bookmark
        WHERE id = :id
        """
        log.info(f"Executing query: {sql_query} with parameter id={id}")
        with get_db() as db:
            db.execute(text(sql_query), {"id": id})
            db.commit() 

        return {
            "success": True,
            "message": f"Bookmark with company_id {id} has been successfully deleted."
        }
    except Exception as e:
        log.error("Delete API error: " + str(e))
        return {
            "success": False,
            "error": "Delete failed",
            "message": str(e)
        }
    
@router.put("/{id}/softdelete")
async def soft_delete_mycompany(id: str):
    try:
        sql_query = """
        UPDATE corp_bookmark
        SET is_deleted = TRUE, updated_at = now()
        WHERE id = :id
        RETURNING id
        """
        
        with get_db() as db:
            log.info(f"Executing query: {sql_query} with parameter id={id}")
            result = db.execute(text(sql_query), {"id": id})
            deleted_id = result.fetchone()
            
            if not deleted_id:
                return {
                    "success": False,
                    "error": "Bookmark not found",
                    "message": f"Bookmark with id {id} not found."
                }
                
            db.commit()

        return {
            "success": True,
            "message": f"Bookmark with id {id} has been successfully soft-deleted."
        }
    except Exception as e:
        log.error("Soft Delete API error: " + str(e))
        return {
            "success": False,
            "error": "Soft delete failed",
            "message": str(e)
        }

@router.put("/{id}/restore")
async def restore_mycompany(id: str):
    try:
        sql_query = """
        UPDATE corp_bookmark
        SET is_deleted = FALSE, updated_at = now()
        WHERE id = :id
        RETURNING id
        """
        
        with get_db() as db:
            log.info(f"Executing query: {sql_query} with parameter id={id}")
            result = db.execute(text(sql_query), {"id": id})
            restored_id = result.fetchone()
            
            if not restored_id:
                return {
                    "success": False,
                    "error": "Bookmark not found",
                    "message": f"Bookmark with id {id} not found."
                }
                
            db.commit()

        return {
            "success": True,
            "message": f"Bookmark with id {id} has been successfully restored."
        }
    except Exception as e:
        log.error("Restore API error: " + str(e))
        return {
            "success": False,
            "error": "Restore failed",
            "message": str(e)
        }
    
@router.post("/add")
async def add_mycompany(request: Request):
    try:
        body = await request.json()
        user_id = body.get("userId")
        company_id = body.get("companyId")
        business_registration_number = body.get("business_registration_number")
        folder_id = body.get("folderId")

        if not user_id or not company_id:
            raise HTTPException(status_code=400, detail="Invalid input. 'userId' and 'companyId' are required.")

        with get_db() as db:
            # 중복 체크 - 이미 저장된 항목이 있는지 확인 (삭제 여부 상관없이)
            check_query = """
            SELECT id, is_deleted FROM corp_bookmark 
            WHERE user_id = :user_id AND company_id = :company_id 
            """
            log.info(f"Checking duplicate bookmark: {check_query} with parameters: user_id={user_id}, company_id={company_id}")
            result = db.execute(
                text(check_query),
                {
                    "user_id": user_id,
                    "company_id": company_id
                }
            )
            existing_bookmark = result.fetchone()
            
            if existing_bookmark:
                bookmark_id = existing_bookmark[0]
                is_deleted = existing_bookmark[1]
                
                # 삭제된 북마크가 있다면 is_deleted를 NULL로 업데이트
                if is_deleted:
                    update_query = """
                    UPDATE corp_bookmark
                    SET is_deleted = FALSE, updated_at = now()
                    WHERE id = :id
                    """
                    log.info(f"Restoring deleted bookmark: {update_query} with parameters: id={bookmark_id}")
                    db.execute(
                        text(update_query),
                        {"id": bookmark_id}
                    )
                    db.commit()
                    
                    return {
                        "success": True,
                        "message": "Deleted bookmark has been restored.",
                        "id": bookmark_id
                    }
                
                # 삭제되지 않은 북마크가 있다면 그대로 반환
                log.info(f"Bookmark already exists with id: {bookmark_id}")
                return {
                    "success": True,
                    "message": "Bookmark already exists.",
                    "id": bookmark_id
                }
            
            # 새 북마크 추가
            insert_query = """
            INSERT INTO corp_bookmark (user_id, company_id, business_registration_number, folder_id, created_at, updated_at)
            VALUES (:user_id, :company_id, :business_registration_number, :folder_id, now(), now())
            RETURNING id
            """
            log.info(
                f"Executing query: {insert_query} with parameters: user_id={user_id}, company_id={company_id}, business_registration_number={business_registration_number}, folder_id={folder_id}"
            )
            
            result = db.execute(
                text(insert_query),
                {
                    "user_id": user_id,
                    "company_id": company_id,
                    "business_registration_number": business_registration_number,
                    "folder_id": folder_id,
                }
            )
            row = result.fetchone()
            if row is None:
                raise HTTPException(status_code=500, detail="Insertion failed, no ID returned.")
            bookmark_id = row[0]
            db.commit()

        return {
            "success": True,
            "message": "Bookmark successfully added.",
            "id": bookmark_id
        }
    except Exception as e:
        log.error("Add Bookmark API error: " + str(e))
        return {
            "success": False,
            "error": "Add failed",
            "message": str(e)
        }


@router.post("/{id}/file/add")
async def add_file_to_bookmark_by_id(request: Request, id: str):
    try:
        body = await request.json()
        file_id = body.get("file_id")

        if not file_id:
            raise HTTPException(status_code=400, detail="Invalid input. 'file_id' is required.")

        check_query = """
        SELECT data FROM corp_bookmark WHERE id = :id
        """
        update_query = """
        UPDATE corp_bookmark
        SET 
            data = :new_data,
            updated_at = now()
        WHERE id = :id
        RETURNING data
        """
        log.info(f"Executing query: {check_query} with parameter id={id}")
        with get_db() as db:
            result = db.execute(text(check_query), {"id": id})
            current_row = result.fetchone()

            if current_row and current_row[0]:
                current_data = current_row[0]
                file_ids = current_data.get("file_ids", [])
                if file_id not in file_ids:
                    file_ids.append(file_id)
                new_data = {"file_ids": file_ids}
            else:
                new_data = {"file_ids": [file_id]}

            log.info(f"Executing query: {update_query} with parameters: id={id}, new_data={json.dumps(new_data)}")
            result = db.execute(
                text(update_query),
                {"id": id, "new_data": json.dumps(new_data)}
            )
            db.commit()
                        
        return {
            "success": True,
            # "data": corp_bookmark_data["data"],
            "message": "File successfully added to bookmark."
        }
    except Exception as e:
        log.error("Add File to Bookmark API error: " + str(e))
        return {
            "success": False,
            "error": "Add failed",
            "message": str(e)
        }

@router.post("/{id}/file/remove")
async def remove_file_from_bookmark_by_id(request: Request, id: str):
    try:
        body = await request.json()
        file_id = body.get("file_id")

        if not file_id:
            raise HTTPException(status_code=400, detail="Invalid input. 'file_id' is required.")

        check_query = """
        SELECT data FROM corp_bookmark WHERE id = :id
        """
        update_query = """
        UPDATE corp_bookmark
        SET 
            data = :new_data,
            updated_at = now()
        WHERE id = :id
        RETURNING data
        """
        delete_file_query = """
        DELETE FROM file WHERE id = :file_id
        """
        log.info(f"Executing query: {check_query} with parameter id={id}")
        with get_db() as db:
            result = db.execute(text(check_query), {"id": id})
            current_row = result.fetchone()

            if current_row and current_row[0]:
                current_data = current_row[0]
                file_ids = current_data.get("file_ids", [])

                if file_id in file_ids:
                    file_ids.remove(file_id)
                else:
                    raise HTTPException(status_code=404, detail="File ID not found in bookmark.")

                new_data = {"file_ids": file_ids} if file_ids else None
            else:
                raise HTTPException(status_code=404, detail="Bookmark not found.")

            log.info(f"Executing query: {update_query} with parameters: id={id}, new_data={json.dumps(new_data) if new_data else None}")
            result = db.execute(
                text(update_query),
                {"id": id, "new_data": json.dumps(new_data) if new_data else None}
            )
            updated_data = result.fetchone()[0]

            log.info(f"Executing query: {delete_file_query} with parameter file_id={file_id}")
            db.execute(
                text(delete_file_query),
                {"file_id": file_id}
            )

            db.commit()

        return {
            "success": True,
            "data": updated_data,
            "message": "File successfully removed from bookmark and deleted."
        }
    except Exception as e:
        log.error("Remove File from Bookmark API error: " + str(e))
        return {
            "success": False,
            "error": "Remove failed",
            "message": str(e)
        }

@router.post("/{id}/file/reset")
async def file_reset_mycompany_by_id(id: str):
    try:
        # corp_bookmark의 data 컬럼 초기화
        check_query = """
        SELECT data FROM corp_bookmark WHERE id = :id
        """
        update_query = """
        UPDATE corp_bookmark
        SET 
            data = NULL,
            updated_at = now()
        WHERE id = :id
        RETURNING data
        """
        delete_file_query = """
        DELETE FROM file WHERE id = :file_id
        """
        log.info(f"Executing query: {check_query} with parameter id={id}")
        with get_db() as db:
            result = db.execute(text(check_query), {"id": id})
            current_row = result.fetchone()
            db.commit()

            if current_row and current_row[0]:
                current_data = current_row[0]
                file_ids = current_data.get("file_ids", [])

                for file_id in file_ids:
                    log.info(f"Executing query: {delete_file_query} with parameter file_id={file_id}")
                    db.execute(text(delete_file_query), {"file_id": file_id})

                log.info(f"Executing query: {update_query} with parameter id={id}")
                db.execute(text(update_query), {"id": id})
                db.commit()
            else:
                raise HTTPException(status_code=404, detail="Bookmark not found.")

        return {
            "success": True,
            "message": f"All files reset and removed for bookmark {id}."
        }
    except Exception as e:
        log.error("File Reset API error: " + str(e))
        return {
            "success": False,
            "error": "Reset failed",
            "message": str(e)
        }

@router.get("/{id}/accessControl/users")
async def get_access_control_users(id: str, request: Request):
    try:
        with get_db() as db:
            # bookmark의 access_control 필드를 조회
            sql_select = "SELECT access_control FROM corp_bookmark WHERE id = :id"
            result = db.execute(text(sql_select), {"id": id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Bookmark not found")
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
            sql_select = "SELECT access_control FROM corp_bookmark WHERE id = :id"
            result = db.execute(text(sql_select), {"id": id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Bookmark not found")
            
            current_access = row[0] or {}
            
            if "user_ids" not in current_access or not isinstance(current_access["user_ids"], list):
                current_access["user_ids"] = []
            
            if user_id not in current_access["user_ids"]:
                current_access["user_ids"].append(user_id)
            
            sql_update = """
                UPDATE corp_bookmark 
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
        log.error("File Reset API error: " + str(e))
        return {
            "success": False,
            "error": "Reset failed",
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
            sql_select = "SELECT access_control FROM corp_bookmark WHERE id = :id"
            result = db.execute(text(sql_select), {"id": id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Bookmark not found")
            
            current_access = row[0] or {}
            if "user_ids" not in current_access or not isinstance(current_access["user_ids"], list):
                current_access["user_ids"] = []
            
            current_access["user_ids"] = [uid for uid in current_access["user_ids"] if uid != user_id]
            
            sql_update = """
                UPDATE corp_bookmark 
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

@router.post("/{id}/accessControl")
async def update_access_control(id: str, request: Request):
    """
    북마크의 액세스 컨트롤 설정을 업데이트합니다.
    
    요청 본문 예시:
    {
        "access_control": {
            "read": {
                "group_ids": ["group1", "group2"],
                "user_ids": ["user1", "user2"]
            },
            "write": {
                "group_ids": ["group1"],
                "user_ids": ["user1"]
            }
        }
    }
    
    또는 액세스 컨트롤을 제거하려면:
    {
        "access_control": null
    }
    """
    try:
        body = await request.json()
        access_control = body.get("access_control")
        
        log.info(f"Updating access control for bookmark {id}: {access_control}")
        
        with get_db() as db:
            # 북마크가 존재하는지 확인
            check_query = "SELECT id, access_control FROM corp_bookmark WHERE id = :id"
            result = db.execute(text(check_query), {"id": id})
            bookmark = result.fetchone()
            if not bookmark:
                log.error(f"Bookmark with id '{id}' not found")
                return {
                    "success": False,
                    "error": "Bookmark not found",
                    "message": f"Bookmark with id '{id}' does not exist."
                }
            
            log.info(f"Current access control for bookmark {id}: {bookmark[1]}")
            
            # 액세스 컨트롤 업데이트
            update_query = """
                UPDATE corp_bookmark 
                SET access_control = :access_control, 
                    updated_at = now() 
                WHERE id = :id 
                RETURNING id, access_control
            """
            
            # access_control이 None이면 NULL로 설정, 그렇지 않으면 JSON으로 변환
            access_control_param = json.dumps(access_control) if access_control is not None else None
            
            log.info(f"Setting access_control to: {access_control_param}")
            
            result = db.execute(
                text(update_query),
                {"id": id, "access_control": access_control_param}
            )
            updated = result.fetchone()
            db.commit()
            
            log.info(f"Updated access control for bookmark {id}: {updated[1]}")
            
            return {
                "success": True,
                "message": "Access control updated successfully",
                "data": {
                    "id": updated[0],
                    "access_control": updated[1]
                }
            }
            
    except Exception as e:
        log.error("Update access control error: " + str(e))
        return {
            "success": False,
            "error": "Update failed",
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
        log.error("나의 고객 이동 실패: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "나의 고객 이동 실패",
                "message": str(e)
            }
        )

@router.get("/user/find-by-email/{email}")
async def find_user_by_email(email: str, request: Request):
    try:
        # Users 모델을 사용하여 이메일로 사용자 조회
        user = Users.get_user_by_email(email.lower())
        
        if user:
            return {
                "success": True,
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name
                }
            }
        else:
            return {
                "success": False,
                "error": "User not found",
                "message": f"이메일 '{email}'에 해당하는 사용자를 찾을 수 없습니다."
            }
    except Exception as e:
        log.error("Find user by email error: " + str(e))
        return {
            "success": False,
            "error": "Find user failed",
            "message": str(e)
        }

@router.get("/user/find-by-id/{user_id}")
async def find_user_by_id(user_id: str, request: Request):
    try:
        # Users 모델을 사용하여 ID로 사용자 조회
        user = Users.get_user_by_id(user_id)
        
        if user:
            return {
                "success": True,
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name
                }
            }
        else:
            return {
                "success": False,
                "error": "User not found",
                "message": f"ID '{user_id}'에 해당하는 사용자를 찾을 수 없습니다."
            }
    except Exception as e:
        log.error("Find user by ID error: " + str(e))
        return {
            "success": False,
            "error": "Find user failed",
            "message": str(e)
        }

@router.post("/{chat_id}/share")
async def update_share_id_for_chat(chat_id: str, request: Request):
    """
    채팅 공유 ID를 생성하거나 기존 공유 ID를 반환합니다.
    """
    try:
        log.info(f"Creating or retrieving share ID for chat: {chat_id}")        
        
        # 3. 공유 ID 생성
        update_share_query = """
        UPDATE chat
        SET share_id = :share_id
        WHERE id = :chat_id
        RETURNING share_id
        """
        
        with get_db() as db:           
            
            # 새 공유 ID 생성
            share_id = str(uuid.uuid4())
            result = db.execute(
                text(update_share_query),
                {"share_id": share_id, "chat_id": chat_id}
            )
            created_share_id = result.fetchone()[0]
            db.commit()
            
            log.info(f"Created new share ID for chat {chat_id}: {created_share_id}")
            
            return {
                "success": True,
                "share_id": created_share_id
            }
            
    except Exception as e:
        log.error(f"Error creating share ID: {str(e)}")
        return {
            "success": False,
            "error": "Share ID creation failed",
            "message": str(e)
        }

@router.get("/s/{share_id}")
async def get_chat_by_share_id(share_id: str, request: Request):
    """
    공유 ID를 사용하여 채팅을 조회합니다.
    """
    try:
        sql_query = """
        SELECT * FROM chat
        WHERE share_id = :share_id
        """
        
        with get_db() as db:
            log.info(f"Executing query: {sql_query} with parameter share_id={share_id}")
            result = db.execute(text(sql_query), {"share_id": share_id})
            chat_data = result.fetchone()
            
            if not chat_data:
                return {
                    "success": False,
                    "error": "채팅을 찾을 수 없음",
                    "message": f"Share ID '{share_id}'에 해당하는 채팅을 찾을 수 없습니다."
                }
            
            chat = dict(chat_data._mapping)
            
        return {
            "success": True,
            "data": chat
        }
    except Exception as e:
        log.error("Get chat by share ID error: " + str(e))
        return {
            "success": False,
            "error": "조회 실패",
            "message": str(e)
        }

@router.post("/company/add")
async def add_private_entity_info(request: Request):
    """
    기업 정보를 private_entity_info 테이블에 저장합니다.
    """
    try:
        data = await request.json()
        company_data = data.get("company_data", {})
        customer_data = data.get("customer_data", {})
        folder_id = data.get("folder_id")
        user_id = data.get("userId")
        entity_type = data.get("entity_type", "COMPANY")  # 'COMPANY' 또는 'CUSTOMER' 값, 기본값은 'COMPANY'
        item_type = data.get("item_type", "company")
        
        # 내부 식별용 사업자등록번호 생성 (시스템 내부용)
        internal_id = f"PRIVATE-{str(uuid.uuid4())[:8]}"
        
        # smtp_id용 UUID 생성
        smtp_id = f"SMTP-{str(uuid.uuid4())}"
        
        # 필수 필드 확인
        if item_type == "company":
            if not company_data.get("company_name"):
                return {
                    "success": False,
                    "error": "필수 정보 누락",
                    "message": "회사명은 필수 입력 항목입니다."
                }
            # 사용자 ID 추가
            company_data["user_id"] = user_id
            
            # 쿼리 및 파라미터 준비
            columns = []
            placeholders = []
            values = {}
            
            for i, (key, value) in enumerate(company_data.items(), 1):
                if value is not None:
                    columns.append(key)
                    placeholders.append(f":{key}")
                    values[key] = value
        else:  # customer
            if not customer_data.get("representative"):
                return {
                    "success": False,
                    "error": "필수 정보 누락",
                    "message": "대표자는 필수 입력 항목입니다."
                }
            # 데이터 변환: 고객 데이터를 회사 데이터 형식으로 변환
            # 대표자를 회사명 필드에 저장
            customer_data["company_name"] = customer_data.get("representative", "")
            customer_data["user_id"] = user_id
            
            # 쿼리 및 파라미터 준비
            columns = []
            placeholders = []
            values = {}
            
            for i, (key, value) in enumerate(customer_data.items(), 1):
                if value is not None:
                    columns.append(key)
                    placeholders.append(f":{key}")
                    values[key] = value
                    
        # 사업자등록번호 내부용 추가
        if "business_registration_number" not in columns:
            columns.append("business_registration_number")
            placeholders.append(":business_registration_number")
            values["business_registration_number"] = internal_id
        
        # smtp_id 추가
        columns.append("smtp_id")
        placeholders.append(":smtp_id")
        values["smtp_id"] = smtp_id
        
        # entity_type 추가
        columns.append("entity_type")
        placeholders.append(":entity_type")
        values["entity_type"] = entity_type
        
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(placeholders)
        
        # 1. private_entity_info 테이블에 기업 정보 저장
        insert_query = f"""
        INSERT INTO private_entity_info ({columns_str})
        VALUES ({placeholders_str})
        RETURNING smtp_id, company_name
        """
        
        with get_db() as db:
            log.info(f"Executing query: {insert_query} with values: {values}")
            result = db.execute(text(insert_query), values)
            inserted = result.fetchone()
            
            if not inserted:
                return {
                    "success": False,
                    "error": "저장 실패",
                    "message": "기업 정보를 저장하는 데 실패했습니다."
                }
            
            inserted_smtp_id = inserted[0]
            company_name = inserted[1]
            
            # 2. 폴더 ID가 있으면 corp_bookmark 테이블에도 추가
            if folder_id:
                # corp_bookmark 테이블에 추가
                bookmark_query = """
                INSERT INTO corp_bookmark (user_id, company_id, business_registration_number, folder_id, created_at, updated_at)
                VALUES (:user_id, :company_id, :business_registration_number, :folder_id, now(), now())
                RETURNING id
                """
                
                bookmark_result = db.execute(
                    text(bookmark_query),
                    {
                        "user_id": user_id,
                        "company_id": inserted_smtp_id,  # 여기서 smtp_id를 company_id로 사용
                        "business_registration_number": internal_id,
                        "folder_id": folder_id
                    }
                )
                bookmark_row = bookmark_result.fetchone()
                if bookmark_row:
                    log.info(f"Added company to bookmark with id: {bookmark_row[0]}")
        
            db.commit()
                
            return {
                "success": True,
                "message": "기업 정보가 성공적으로 저장되었습니다.",
                "data": {
                    "smtp_id": inserted_smtp_id,
                    "company_name": company_name,
                    "user_id": user_id
                }
            }
            
    except Exception as e:
        log.error("기업 정보 저장 오류: " + str(e))
        return {
            "success": False,
            "error": "저장 실패",
            "message": str(e)
        }

@router.get("/private/{id}")
async def get_private_company_by_id(id: str, request: Request):
    search_params = request.query_params
    user_id = search_params.get("user_id")
    
    try:
        bookmark_sql_query = """
        SELECT DISTINCT
            f.id as bookmark_id,
            f.created_at,
            f.updated_at,
            f.company_id, f.user_id as bookmark_user_id,
            f.folder_id,
            f.data::jsonb as data_files,
            f.access_control::jsonb,
            jsonb_agg(DISTINCT
                CASE
                    WHEN f.data IS NOT NULL
                    THEN jsonb_build_object(
                        'id', fi.id,
                        'user_id', fi.user_id,
                        'filename', fi.filename,
                        'meta', fi.meta,
                        'created_at', fi.created_at,
                        'hash', fi.hash,
                        'data', fi."data",
                        'updated_at', fi.updated_at,
                        'path', fi."path",
                        'access_control', fi.access_control
                    )
                    ELSE NULL
                END
            ) FILTER (WHERE f.data IS NOT NULL) AS files,
            pci.smtp_id as master_id,
            pci.company_name,
            pci.representative,
            pci.postal_code,
            pci.address,
            pci.phone_number,
            pci.fax_number,
            pci.website,
            pci.email,
            pci.company_type,
            pci.establishment_date,
            pci.founding_date,
            pci.employee_count,
            pci.industry_code1,
            pci.industry_code2,
            pci.industry,
            pci.main_product,
            pci.main_bank,
            pci.main_branch,
            pci.group_name,
            pci.stock_code,
            pci.business_registration_number,
            pci.corporate_number,
            pci.english_name,
            pci.trade_name,
            pci.fiscal_month,
            pci.region1,
            pci.region2,
            pci.industry_major,
            pci.industry_middle,
            pci.industry_small,
            pci.latitude,
            pci.longitude,
            'private' as company_type
        FROM corp_bookmark f
        INNER JOIN private_entity_info pci ON f.business_registration_number::text = pci.business_registration_number::text
        LEFT JOIN file fi
            ON fi.id::text = ANY(ARRAY(
                SELECT jsonb_array_elements_text(f.data::jsonb->'file_ids')
            ))
        WHERE f.id = :id
        AND (f.is_deleted IS NULL OR f.is_deleted = FALSE)           
        GROUP BY
            f.id, f.created_at, f.updated_at, f.company_id, f.user_id,
            -- JSON 필드는 TEXT로 캐스팅하여 GROUP BY에 사용
            f.data::text, f.access_control::text, f.folder_id,
            pci.smtp_id,
            pci.company_name,
            pci.representative,
            pci.postal_code,
            pci.address,
            pci.phone_number,
            pci.fax_number,
            pci.website,
            pci.email,
            pci.company_type,
            pci.establishment_date,
            pci.founding_date,
            pci.employee_count,
            pci.industry_code1,
            pci.industry_code2,
            pci.industry,
            pci.main_product,
            pci.main_bank,
            pci.main_branch,
            pci.group_name,
            pci.stock_code,
            pci.business_registration_number,
            pci.corporate_number,
            pci.english_name,
            pci.trade_name,
            pci.fiscal_month,
            pci.region1,
            pci.region2,
            pci.industry_major,
            pci.industry_middle,
            pci.industry_small,
            pci.latitude,
            pci.longitude
        ORDER BY f.updated_at DESC
        """
        
        stmt = text(bookmark_sql_query)
        params = {"id": id}
        
        with get_db() as db:
            if log.level <= logging.DEBUG:
                compiled_query = stmt.compile(dialect=db.bind.dialect, compile_kwargs={"literal_binds": True})
                log.debug(f"Private company query: {compiled_query} | Parameters: {params}")
            else:
                log.info(f"Executing private company query for id={id}")
            
            bookmark_result = db.execute(stmt, params)
            bookmark_data = [row._mapping for row in bookmark_result.fetchall()]
            
            if not bookmark_data:
                return {
                    "success": False,
                    "error": "북마크를 찾을 수 없음",
                    "message": f"Bookmark with id '{id}' 를 찾을 수 없습니다."
                }
            
            bookmark_user_id = bookmark_data[0].bookmark_user_id
            access_control = bookmark_data[0].access_control
            
            if user_id and user_id != bookmark_user_id:
                
                if access_control is None:
                    return {
                        "success": False,
                        "error": "권한 없음",
                        "message": f"Bookmark with id '{id}' 에 대한 접근 권한이 없습니다."
                    }
                
                user_groups = Groups.get_groups_by_member_id(user_id)
                user_group_ids = [group.id for group in user_groups]
                
                write_permission = access_control.get("write", {})
                permitted_group_ids = write_permission.get("group_ids", [])
                permitted_user_ids = write_permission.get("user_ids", [])
                
                if not (user_id in permitted_user_ids or any(
                    group_id in permitted_group_ids for group_id in user_group_ids
                )):
                    return {
                        "success": False,
                        "error": "권한 없음",
                        "message": f"Bookmark with id '{id}' 에 대한 접근 권한이 없습니다."
                    }
            
            # Chat List 조회
            conditions = []
            
            bookmark_owner_id = bookmark_data[0].bookmark_user_id            
            
            # 항상 북마크 소유자의 채팅을 가져옴
            conditions.append("user_id = " + format_parameter(bookmark_owner_id))
            conditions.append("c.business_registration_number = " + format_parameter(bookmark_data[0].business_registration_number))
            
            chat_query = "SELECT * FROM chat c WHERE " + " AND ".join(conditions)
            chat_query = get_executable_query(chat_query, [])
            
            if log.level <= logging.DEBUG:
                log.debug(f"Chat query: {chat_query}")
            else:
                log.info(f"Executing chat query for bookmark_id={id}")
                
            chat_result = db.execute(text(chat_query))
            chat_list = [row._mapping for row in chat_result.fetchall()]
        
        return {
            "success": True,
            "bookmark": bookmark_data,
            "bookmark_total": len(bookmark_data),
            "chatList": chat_list,
            "chat_total": len(chat_list)
        }
    except Exception as e:
        log.error(f"Get private company by ID error: {str(e)}")
        return {
            "success": False,
            "error": "Fetch failed",
            "message": str(e)
        }

@router.put("/company/update")
async def update_private_entity_info(request: Request):
    """
    기업 정보를 private_entity_info 테이블에서 업데이트합니다.
    """
    try:
        data = await request.json()
        company_data = data.get("company_data", {})
        business_registration_number = data.get("business_registration_number")
        
        # 사업자등록번호 필수 확인
        if not business_registration_number:
            return {
                "success": False,
                "error": "필수 정보 누락",
                "message": "사업자등록번호는 필수 입력 항목입니다."
            }
        
        # 업데이트할 필드 정리
        set_clauses = []
        params = {"business_registration_number": business_registration_number}
        
        for key, value in company_data.items():
            # 업데이트 가능한 필드 목록 (필요에 따라 조정)
            allowed_fields = [
                "company_name", "representative", "address", "phone_number", 
                "fax_number", "email", "website", "establishment_date", 
                "employee_count", "industry", "main_product"
            ]
            
            if key in allowed_fields:
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
        
        if not set_clauses:
            return {
                "success": False,
                "error": "업데이트 정보 누락",
                "message": "업데이트할 정보가 없습니다."
            }
        
        # 업데이트 쿼리 구성
        update_query = f"""
        UPDATE private_entity_info
        SET {", ".join(set_clauses)}
        WHERE business_registration_number = :business_registration_number
        RETURNING smtp_id, company_name
        """
        
        with get_db() as db:
            log.info(f"Executing query: {update_query} with params: {params}")
            result = db.execute(text(update_query), params)
            updated = result.fetchone()
            
            if not updated:
                return {
                    "success": False,
                    "error": "업데이트 실패",
                    "message": "해당 사업자등록번호를 가진 기업 정보를 찾을 수 없습니다."
                }
            
            db.commit()
            
            return {
                "success": True,
                "message": "기업 정보가 성공적으로 업데이트되었습니다.",
                "data": {
                    "smtp_id": updated[0],
                    "company_name": updated[1]
                }
            }
    except Exception as e:
        log.error("기업 정보 업데이트 오류: " + str(e))
        return {
            "success": False,
            "error": "업데이트 실패",
            "message": str(e)
        }

