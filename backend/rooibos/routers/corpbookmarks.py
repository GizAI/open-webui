from fastapi import APIRouter, Request, HTTPException

from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.users import UserModel, Users

import json
import logging

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
async def get_corpbookmarks(user_id: str):
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
async def get_corpbookmark_by_id(id: str, request: Request):
    search_params = request.query_params
    user_id = search_params.get("user_id")
    
    try:
        bookmark_sql_query = """
        SELECT DISTINCT
            f.id as bookmark_id,
            f.created_at,
            f.updated_at,
            f.company_id,
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
            rmc.master_id,
            rmc.company_name,
            rmc.representative,
            rmc.postal_code,
            rmc.address,
            rmc.phone_number,
            rmc.fax_number,
            rmc.website,
            rmc.email,
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
            rmc.business_registration_number,
            rmc.corporate_number,
            rmc.english_name,
            rmc.trade_name,
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
            rmc.region1,
            rmc.region2,
            rmc.industry_major,
            rmc.industry_middle,
            rmc.industry_small,
            rmc.latitude,
            rmc.longitude,
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
        INNER JOIN rb_master_company rmc ON f.company_id::text = rmc.master_id::text
        LEFT JOIN smtp_financial_company fc
            ON rmc.company_name = fc.company_name
        LEFT JOIN smtp_executives me
            ON rmc.business_registration_number = me.business_registration_number
            AND me.position = '대표이사'
        LEFT JOIN file fi
            ON fi.id::text = ANY(ARRAY(
                SELECT jsonb_array_elements_text(f.data::jsonb->'file_ids')
            ))
        WHERE f.id = :id 
          AND (
            f.user_id = :userId
            OR (f.access_control::jsonb->'user_ids') ? :userId
          )
        GROUP BY
            f.id, f.created_at, f.updated_at, f.company_id,
            rmc.master_id,
            rmc.company_name,
            rmc.representative,
            rmc.postal_code,
            rmc.address,
            rmc.phone_number,
            rmc.fax_number,
            rmc.website,
            rmc.email,
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
            rmc.business_registration_number,
            rmc.corporate_number,
            rmc.english_name,
            rmc.trade_name,
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
            rmc.region1,
            rmc.region2,
            rmc.industry_major,
            rmc.industry_middle,
            rmc.industry_small,
            rmc.latitude,
            rmc.longitude,
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
        ORDER BY f.updated_at DESC
        """
        
        stmt = text(bookmark_sql_query)
        params = {"id": id, "userId": user_id}
        
        with get_db() as db:
            compiled_query = stmt.compile(dialect=db.bind.dialect, compile_kwargs={"literal_binds": True})
            log.info(f"Final executed bookmark query: {compiled_query} | Parameters: {params}")
            
            bookmark_result = db.execute(stmt, params)
            bookmark_data = [row._mapping for row in bookmark_result.fetchall()]
            
            if not bookmark_data:
                return {
                    "success": False,
                    "error": "권한 없음",
                    "message": f"Bookmark with id '{id}' 에 대한 접근 권한이 없습니다."
                }
            
            # Chat List 조회
            business_reg_json = json.dumps({
                "selectedCompany": {
                    "business_registration_number": bookmark_data[0].business_registration_number
                }
            })
            
            conditions = []
            conditions.append("user_id = " + format_parameter(user_id))
            conditions.append("c.chat::jsonb @> " + format_parameter(business_reg_json) + "::jsonb")
            chat_query = "SELECT * FROM chat c WHERE " + " AND ".join(conditions)
            chat_query = get_executable_query(chat_query, [])
            
            log.info(f"Final executed chat query: {chat_query}")
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
        log.error("Get CorpBookmark by ID error: " + str(e))
        return {
            "success": False,
            "error": "Fetch failed",
            "message": str(e)
        }



@router.delete("/{id}/delete")
async def delete_corpbookmark(id: str):
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
    
@router.post("/add")
async def add_corpbookmark(request: Request):
    try:
        body = await request.json()
        user_id = body.get("userId")
        company_id = body.get("companyId")
        business_registration_number = body.get("business_registration_number")

        if not user_id or not company_id:
            raise HTTPException(status_code=400, detail="Invalid input. 'userId' and 'companyId' are required.")

        sql_query = """
        INSERT INTO corp_bookmark (user_id, company_id, business_registration_number, created_at, updated_at)
        VALUES (:user_id, :company_id, :business_registration_number, now(), now())
        RETURNING id
        """
        log.info(f"Executing query: {sql_query} with parameters: user_id={user_id}, company_id={company_id}, business_registration_number={business_registration_number}")
        with get_db() as db:
            result = db.execute(text(sql_query), {"user_id": user_id, "company_id": company_id, "business_registration_number": business_registration_number})
            bookmark_id = result.fetchone()[0]
            db.commit()

        return {
            "success": True,
            "data": {"id": bookmark_id},
            "message": "Bookmark successfully added."
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

            # get_corpbookmark_by_id는 내부에서 쿼리 로그를 남기므로 그대로 호출
            corp_bookmark_data = await get_corpbookmark_by_id(id)
                        
        return {
            "success": True,
            "data": corp_bookmark_data["data"],
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
async def file_reset_corpbookmark_by_id(id: str):
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
