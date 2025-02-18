from fastapi import APIRouter, Request, HTTPException
from typing import Optional

from open_webui.internal.db import get_db
from sqlalchemy import text

import json

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
        param_count = 1

        sql_query = """
            SELECT DISTINCT
                f.id,
                f.created_at,
                f.updated_at,
                f.company_id,
                mci.master_id,
                mci.company_name,
                mci.address
            FROM corp_bookmark f
            INNER JOIN master_company_info mci
                ON f.company_id = mci.master_id
            WHERE f.user_id = $1
            ORDER BY f.updated_at DESC
        """

        favorites = get_executable_query(sql_query, params)

        with get_db() as db:
            result = db.execute(text(favorites))
            bookmarks = [row._mapping for row in result.fetchall()]

        return {
            "success": True,
            "data": bookmarks,
            "total": len(bookmarks),
        }
    except Exception as e:
        print("Search API error:", e)
        return {
            "success": False,
            "error": "Search failed",
            "message": str(e)
        }

@router.get("/{id}/financialData")
async def get_corp_financialData(id: str):
    try:
        params = [id]
        param_count = 1

        sql_query = """
            SELECT 
                sfd.financial_company_id,
                sfd.year,
                sfd.revenue,
                sfd.net_income,
                sfd.operating_income,
                sfd.total_assets,
                sfd.total_liabilities,
                sfd.total_equity,
                sfd.capital_stock,
                sfd.corporate_tax,
                sfd.current_assets,
                sfd.quick_assets,
                sfd.inventory,
                sfd.non_current_assets,
                sfd.investment_assets,
                sfd.tangible_assets,
                sfd.intangible_assets,
                sfd.current_liabilities,
                sfd.non_current_liabilities,
                sfd.retained_earnings,
                sfd.profit,
                sfd.sales_cost,
                sfd.sales_profit,
                sfd.sga,
                sfd.other_income,
                sfd.other_expenses,
                sfd.pre_tax_income
            FROM master_company_info mci
            JOIN smtp_financial_company sfc 
                ON mci.company_name = sfc.company_name
            JOIN smtp_financial_data sfd 
                ON sfc.id = sfd.financial_company_id
            WHERE mci.master_id = $1
            GROUP BY 
                sfd.financial_company_id,
                sfd.year,
                sfd.revenue,
                sfd.net_income,
                sfd.operating_income,
                sfd.total_assets,
                sfd.total_liabilities,
                sfd.total_equity,
                sfd.capital_stock,
                sfd.corporate_tax,
                sfd.current_assets,
                sfd.quick_assets,
                sfd.inventory,
                sfd.non_current_assets,
                sfd.investment_assets,
                sfd.tangible_assets,
                sfd.intangible_assets,
                sfd.current_liabilities,
                sfd.non_current_liabilities,
                sfd.retained_earnings,
                sfd.profit,
                sfd.sales_cost,
                sfd.sales_profit,
                sfd.sga,
                sfd.other_income,
                sfd.other_expenses,
                sfd.pre_tax_income
            ORDER BY sfd.year DESC
        """

        query = get_executable_query(sql_query, params)

        with get_db() as db:
            result = db.execute(text(query))
            financial_data = [row._mapping for row in result.fetchall()]

        return {
            "success": True,
            "data": financial_data,
            "total": len(financial_data),
        }
    except Exception as e:
        print("Financial Data API error:", e)
        return {
            "success": False,
            "error": "Failed to fetch financial data",
            "message": str(e)
        }

    
@router.get("/{id}")
async def get_corpbookmark_by_id(id: str):    
    try:
        sql_query = """        
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
            mci.master_id,
            mci.company_name,
            mci.representative,
            mci.postal_code,
            mci.address,
            mci.phone_number,
            mci.fax_number,
            mci.website,
            mci.email,
            mci.company_type,
            mci.establishment_date,
            mci.founding_date,
            mci.employee_count,
            mci.industry_code1,
            mci.industry_code2,
            mci.industry,
            mci.main_product,
            mci.main_bank,
            mci.main_branch,
            mci.group_name,
            mci.stock_code,
            mci.business_registration_number,
            mci.corporate_number,
            mci.english_name,
            mci.trade_name,
            mci.fiscal_month,
            mci.sales_year,
            mci.recent_sales,
            mci.profit_year,
            mci.recent_profit,
            mci.operating_profit_year,
            mci.recent_operating_profit,
            mci.asset_year,
            mci.recent_total_assets,
            mci.debt_year,
            mci.recent_total_debt,
            mci.equity_year,
            mci.recent_total_equity,
            mci.capital_year,
            mci.recent_capital,
            mci.region1,
            mci.region2,
            mci.industry_major,
            mci.industry_middle,
            mci.industry_small,
            mci.latitude,
            mci.longitude,
            mci.sme_type,
            mci.cri_company_size,
            mci.lab_name,
            mci.first_approval_date,
            mci.lab_location,
            mci.research_field,
            mci.division,
            mci.birth_year,
            mci.foundation_year,
            mci.family_shareholder_yn,
            mci.external_shareholder_yn,
            mci.financial_statement_year,
            mci.employees,
            mci.total_assets,
            mci.total_equity,
            mci.sales_amount,
            mci.net_income,
            mci.venture_confirmation_type,
            mci.svcl_region,
            mci.venture_valid_from,
            mci.venture_valid_until,
            mci.confirming_authority,
            mci.new_reconfirmation_code,
            me.executive_name,
            me.birth_date,
            fc.industry
        FROM corp_bookmark f
        INNER JOIN master_company_info mci ON f.company_id = mci.master_id
        LEFT JOIN smtp_financial_company fc 
            ON mci.company_name = fc.company_name
        LEFT JOIN smtp_executives me
            ON mci.business_registration_number = me.business_registration_number
            AND me.position = '대표이사'
        LEFT JOIN file fi
            ON fi.id::text = ANY(ARRAY(
                SELECT jsonb_array_elements_text(f.data::jsonb->'file_ids')
            ))     
        WHERE f.id = :id
        GROUP BY 
            f.id, f.created_at, f.updated_at, f.company_id,
            mci.master_id, mci.company_name, mci.representative, mci.postal_code, mci.address,
            mci.phone_number, mci.fax_number, mci.website, mci.email, mci.company_type,
            mci.establishment_date, mci.founding_date, mci.employee_count, mci.industry_code1,
            mci.industry_code2, mci.industry, mci.main_product, mci.main_bank, mci.main_branch,
            mci.group_name, mci.stock_code, mci.business_registration_number, mci.corporate_number,
            mci.english_name, mci.trade_name, mci.fiscal_month, mci.sales_year, mci.recent_sales,
            mci.profit_year, mci.recent_profit, mci.operating_profit_year, mci.recent_operating_profit,
            mci.asset_year, mci.recent_total_assets, mci.debt_year, mci.recent_total_debt, mci.equity_year,
            mci.recent_total_equity, mci.capital_year, mci.recent_capital, mci.region1, mci.region2,
            mci.industry_major, mci.industry_middle, mci.industry_small, mci.latitude, mci.longitude,
            mci.sme_type, mci.cri_company_size, mci.lab_name, mci.first_approval_date,
            mci.lab_location, mci.research_field, mci.division, mci.birth_year, mci.foundation_year,
            mci.family_shareholder_yn, mci.external_shareholder_yn, mci.financial_statement_year, mci.employees,
            mci.total_assets, mci.total_equity, mci.sales_amount, mci.net_income, mci.venture_confirmation_type,
            mci.svcl_region, mci.venture_valid_from, mci.venture_valid_until, mci.confirming_authority, mci.new_reconfirmation_code, 
            me.executive_name, me.birth_date, fc.industry
        ORDER BY f.updated_at DESC
        """
        with get_db() as db:
            result = db.execute(text(sql_query), {"id": id})
            data = [row._mapping for row in result.fetchall()]
        
        if not data:
            return {
                "success": False,
                "error": "Not Found",
                "message": f"Bookmark with id '{id}' does not exist."
            }
        
        return {
            "success": True,
            "data": data,
            "total": len(data)
        }
    except Exception as e:
        print("Get CorpBookmark by ID error:", e)
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
        print(text(sql_query), {"id": id})
        with get_db() as db:
            db.execute(text(sql_query), {"id": id})
            db.commit() 

        return {
            "success": True,
            "message": f"Bookmark with company_id {id} has been successfully deleted."
        }

    except Exception as e:
        print("Delete API error:", e)
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
        print("Add Bookmark API error:", e)
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

            result = db.execute(
                text(update_query),
                {"id": id, "new_data": json.dumps(new_data)}
            )            
            db.commit()

            corp_bookmark_data = await get_corpbookmark_by_id(id)
                        
        return {
            "success": True,
            "data": corp_bookmark_data["data"],
            "message": "File successfully added to bookmark."
        }

    except Exception as e:
        print("Add File to Bookmark API error:", e)
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

                if file_ids:
                    new_data = {"file_ids": file_ids}
                else:
                    new_data = None
            else:
                raise HTTPException(status_code=404, detail="Bookmark not found.")

            result = db.execute(
                text(update_query),
                {"id": id, "new_data": json.dumps(new_data) if new_data else None}
            )
            updated_data = result.fetchone()[0]

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
        print("Remove File from Bookmark API error:", e)
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

        with get_db() as db:
            result = db.execute(text(check_query), {"id": id})
            current_row = result.fetchone()
            db.commit()

            if current_row and current_row[0]:
                current_data = current_row[0]
                file_ids = current_data.get("file_ids", [])

                for file_id in file_ids:
                    # 파일 삭제 쿼리 실행
                    db.execute(text(delete_file_query), {"file_id": file_id})

                # corp_bookmark의 data 컬럼을 None으로 업데이트
                db.execute(text(update_query), {"id": id})
                db.commit()
            else:
                raise HTTPException(status_code=404, detail="Bookmark not found.")

        return {
            "success": True,
            "message": f"All files reset and removed for bookmark {id}."
        }

    except Exception as e:
        print("File Reset API error:", e)
        return {
            "success": False,
            "error": "Reset failed",
            "message": str(e)
        }








    
