from fastapi import APIRouter, Request, HTTPException
from typing import Optional

from open_webui.internal.db import get_db
from sqlalchemy import text

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

@router.get("/")
async def get_corpbookmarks():
    try:
        params = []
        param_count = 1

        sql_query = """
        WITH FinancialComparison AS (
            SELECT 
                mfd.financial_company_id,
                mfd.revenue,
                mfd.net_income,
                mfd.total_assets,
                mfd.total_liabilities,
                CASE
                    WHEN LAG(mfd.revenue) OVER (PARTITION BY mfd.financial_company_id ORDER BY mfd.year) IS NOT NULL
                    THEN (mfd.revenue - LAG(mfd.revenue) OVER (PARTITION BY mfd.financial_company_id ORDER BY mfd.year)) 
                        / NULLIF(LAG(mfd.revenue) OVER (PARTITION BY mfd.financial_company_id ORDER BY mfd.year), 0) * 100
                    ELSE 0
                END AS revenue_growth_rate
            FROM smtp_financial_data mfd
            WHERE mfd.year = '2023'
        )
        SELECT DISTINCT
            f.id,
            f.created_at,
            f.updated_at,
            f.company_id,
            f.memo,
            ci.company_name,
            ci.id AS company_id,
            ci.business_registration_number,
            ci.representative,
            ci.postal_code,
            ci.address,
            ci.representative,
            ci.phone_number,
            ci.fax_number,
            ci.website,
            ci.email,
            ci.company_type,
            ci.establishment_date,
            ci.employee_count,
            ci.latitude,
            ci.longitude,
            ci.industry,
            ci.recent_sales,
            ci.recent_profit,
            me.executive_name,
            me.birth_date,
            fc.industry,
            FinancialComparison.revenue AS recent_revenue,
            FinancialComparison.net_income AS recent_net_income,
            FinancialComparison.total_assets AS recent_total_assets,
            FinancialComparison.total_liabilities AS recent_total_liabilities,
            FinancialComparison.revenue_growth_rate
        FROM corp_bookmark f
        INNER JOIN smtp_company_info ci ON f.company_id = ci.id
        LEFT JOIN smtp_financial_company fc 
            ON ci.company_name = fc.company_name
        LEFT JOIN smtp_executives me
            ON ci.business_registration_number = me.business_registration_number
            AND me.position = '대표이사'    
        LEFT JOIN FinancialComparison 
            ON fc.id = FinancialComparison.financial_company_id   
        WHERE f.user_id = '87cb7169-8c44-4e04-9944-76d6deb389c6'    
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
    
@router.get("/{id}")
async def get_corpbookmark_by_id(id: str):
    """
    특정 북마크(ID)를 조회하는 API
    """
    try:
        # 동일한 쿼리이지만 WHERE 조건에 f.id = :id 부분만 추가
        sql_query = """
        WITH FinancialComparison AS (
            SELECT 
                mfd.financial_company_id,
                mfd.revenue,
                mfd.net_income,
                mfd.total_assets,
                mfd.total_liabilities,
                CASE
                    WHEN LAG(mfd.revenue) OVER (PARTITION BY mfd.financial_company_id ORDER BY mfd.year) IS NOT NULL
                    THEN (mfd.revenue - LAG(mfd.revenue) OVER (PARTITION BY mfd.financial_company_id ORDER BY mfd.year)) 
                         / NULLIF(LAG(mfd.revenue) OVER (PARTITION BY mfd.financial_company_id ORDER BY mfd.year), 0) * 100
                    ELSE 0
                END AS revenue_growth_rate
            FROM smtp_financial_data mfd
            WHERE mfd.year = '2023'
        )
        SELECT DISTINCT
            f.id,
            f.created_at,
            f.updated_at,
            f.company_id,
            f.memo,
            ci.company_name,
            ci.id AS company_id,
            ci.business_registration_number,
            ci.representative,
            ci.postal_code,
            ci.address,
            ci.representative,
            ci.phone_number,
            ci.fax_number,
            ci.website,
            ci.email,
            ci.company_type,
            ci.establishment_date,
            ci.employee_count,
            ci.latitude,
            ci.longitude,
            ci.industry,
            ci.recent_sales,
            ci.recent_profit,
            me.executive_name,
            me.birth_date,
            fc.industry,
            FinancialComparison.revenue AS recent_revenue,
            FinancialComparison.net_income AS recent_net_income,
            FinancialComparison.total_assets AS recent_total_assets,
            FinancialComparison.total_liabilities AS recent_total_liabilities,
            FinancialComparison.revenue_growth_rate
        FROM corp_bookmark f
        INNER JOIN smtp_company_info ci ON f.company_id = ci.id
        LEFT JOIN smtp_financial_company fc 
            ON ci.company_name = fc.company_name
        LEFT JOIN smtp_executives me
            ON ci.business_registration_number = me.business_registration_number
            AND me.position = '대표이사'
        LEFT JOIN FinancialComparison 
            ON fc.id = FinancialComparison.financial_company_id
        WHERE f.user_id = '87cb7169-8c44-4e04-9944-76d6deb389c6'
          AND f.id = :id
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
            result = db.execute(text(sql_query), {"id": id})
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


