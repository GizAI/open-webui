from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS

import json
import logging
import requests

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

import requests

def get_coordinates(query: str):
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": "t80s8o2xsl",
        "X-NCP-APIGW-API-KEY": "a9l3a5gkSDaxXryTsSVmMezstBHzfZPX8aC1s65b",
    }
    params = {"query": query}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("addresses"):
        address = data["addresses"][0]
        return {"latitude": address["y"], "longitude": address["x"], "address": address["roadAddress"]}
    else:
        return {"error": "주소로 검색된 결과가 없습니다."}

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

@router.get("/test")
async def test(request: Request):
    return {"message": "Hello, World!"}

@router.get("/")
async def search(request: Request):
    search_params = request.query_params
    id = search_params.get("id")    
    query = search_params.get("query", "").strip()
    user_id = search_params.get("user_id")
    latitude = search_params.get("latitude")
    longitude = search_params.get("longitude")

    if query:
        result = get_coordinates(query)
        if result:
            latitude = result['latitude']
            longitude = result['longitude']

    user_latitude = float(search_params.get("userLatitude", 0))
    user_longitude = float(search_params.get("userLongitude", 0))
    
    filters_param = search_params.get("filters")
    filters = json.loads(filters_param) if filters_param else {}

    distance = float(filters.get("radius", 200))

    employee_count_data = filters.get("employee_count", {})
    employee_count_min = employee_count_data.get("min")
    employee_count_max = employee_count_data.get("max")
    
    certification = filters.get("certification", [])

    establishment_year = filters.get("establishment_year", {}).get("year")

    excluded_industries = filters.get("excluded_industries", [])

    gender_raw = filters.get("gender")
    gender = "남" if gender_raw == "male" else ("여" if gender_raw == "female" else None)
    gender_age = filters.get("gender_age")

    loan = filters.get("loan")    

    net_profit_data = filters.get("net_profit", {})
    net_profit_min = net_profit_data.get("min")
    net_profit_max = net_profit_data.get("max")
    if net_profit_min is not None:
        net_profit_min = float(net_profit_min) * 1_000_000
    if net_profit_max is not None:
        net_profit_max = float(net_profit_max) * 1_000_000

    profit_data = filters.get("profit", {})
    profit_min = profit_data.get("min")
    profit_max = profit_data.get("max")
    if profit_min is not None:
        profit_min = float(profit_min) * 1_000_000
    if profit_max is not None:
        profit_max = float(profit_max) * 1_000_000

    sales_data = filters.get("sales", {})
    sales_min = sales_data.get("min")
    sales_max = sales_data.get("max")
    if sales_min is not None:
        sales_min = float(sales_min) * 1_000_000
    if sales_max is not None:
        sales_max = float(sales_max) * 1_000_000

    unallocated_data = filters.get("unallocated_profit", {})
    unallocated_profit_min = unallocated_data.get("min")
    unallocated_profit_max = unallocated_data.get("max")
    if unallocated_profit_min is not None:
        unallocated_profit_min = float(unallocated_profit_min) * 1_000_000
    if unallocated_profit_max is not None:
        unallocated_profit_max = float(unallocated_profit_max) * 1_000_000

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
                    mfd.retained_earnings,
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
                mci.smtp_id,
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
                mci.certificate_expiry_date,
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
                cb.id as bookmark_id
        """        

        if not id:
            if latitude and longitude:
                sql_query += f"""
                    , ROUND(
                        (
                            6371 * acos(
                                cos(radians(${param_count})) *
                                cos(radians(mci.latitude)) *
                                cos(radians(mci.longitude) - radians(${param_count + 1})) +
                                sin(radians(${param_count})) *
                                sin(radians(mci.latitude))
                            )
                        ) * 1000
                    ) AS distance_from_location
                """
                params.extend([float(latitude), float(longitude)])
                param_count += 2

            sql_query += f"""
                , ROUND(
                    (
                        6371 * acos(
                            cos(radians(${param_count})) *
                            cos(radians(mci.latitude)) *
                            cos(radians(mci.longitude) - radians(${param_count + 1})) +
                            sin(radians(${param_count})) *
                            sin(radians(mci.latitude))
                        )
                    ) * 1000
                ) AS distance_from_user
            """
            params.extend([user_latitude, user_longitude])
            param_count += 2

        params.append(user_id)
        user_id_param = param_count
        param_count += 1

        sql_query += f"""
        FROM master_company_info mci
        LEFT JOIN corp_bookmark cb ON cb.company_id = mci.smtp_id AND cb.user_id = ${user_id_param}
        LEFT JOIN smtp_executives me
            ON mci.business_registration_number = me.business_registration_number
            AND me.position = '대표이사'
        WHERE mci.latitude IS NOT NULL
        """

        if id:
            sql_query += f" AND mci.smtp_id = ${param_count}"
            params.append(float(id))
            param_count += 1
        else:
            if latitude and longitude:
                sql_query += f"""
                AND ROUND(
                    (
                        6371 * acos(
                            cos(radians(${param_count})) *
                            cos(radians(mci.latitude)) *
                            cos(radians(mci.longitude) - radians(${param_count + 1})) +
                            sin(radians(${param_count})) *
                            sin(radians(mci.latitude))
                        )
                    ) * 1000
                ) <= ${param_count + 2}
                """
                params.extend([float(latitude), float(longitude), distance])
                param_count += 3

            else:
                sql_query += f"""
                    AND (
                        mci.company_name ILIKE ${param_count}
                        OR mci.representative ILIKE ${param_count}
                        OR mci.address ILIKE ${param_count}
                    )
                """
                params.append(f"%{query}%")
                param_count += 1

        # 기존 필터 조건들
        if sales_min is not None:
            sql_query += f" AND (mci.sales_amount)::numeric >= ${param_count}"
            params.append(sales_min)
            param_count += 1

        if sales_max is not None:
            sql_query += f" AND (mci.sales_amount)::numeric <= ${param_count}"
            params.append(sales_max)
            param_count += 1

        if profit_min is not None:
            sql_query += f" AND (mci.recent_profit)::numeric >= ${param_count}"
            params.append(profit_min)
            param_count += 1

        if profit_max is not None:
            sql_query += f" AND (mci.recent_profit)::numeric <= ${param_count}"
            params.append(profit_max)
            param_count += 1

        if employee_count_min is not None:
            sql_query += f" AND mci.employee_count >= ${param_count}"
            params.append(employee_count_min)
            param_count += 1

        if employee_count_max is not None:
            sql_query += f" AND mci.employee_count <= ${param_count}"
            params.append(employee_count_max)
            param_count += 1

        if net_profit_min is not None:
            sql_query += f" AND (mci.net_income)::numeric >= ${param_count}"
            params.append(net_profit_min)
            param_count += 1

        if net_profit_max is not None:
            sql_query += f" AND (mci.net_income)::numeric <= ${param_count}"
            params.append(net_profit_max)
            param_count += 1

        if unallocated_profit_min is not None:
            sql_query += f" AND (FinancialComparison.retained_earnings)::numeric >= ${param_count}"
            params.append(unallocated_profit_min)
            param_count += 1

        if unallocated_profit_max is not None:
            sql_query += f" AND (FinancialComparison.retained_earnings)::numeric <= ${param_count}"
            params.append(unallocated_profit_max)
            param_count += 1

        if establishment_year is not None:
            sql_query += f" AND SUBSTRING(mci.establishment_date, 1, 4)::INTEGER >= ${param_count}"
            params.append(establishment_year)
            param_count += 1

        if certification:
            conditions = []
            if 'innobiz' in certification:
                conditions.append(f"mci.sme_type = '기술혁신'")
            if 'mainbiz' in certification:
                conditions.append(f"mci.sme_type = '경영혁신'")
            if 'research_institute' in certification:
                conditions.append(f"mci.division = '연구소'")
            if 'venture' in certification:
                conditions.append(f"mci.confirming_authority = '벤처기업확인기관'")
            
            if conditions:
                sql_query += " AND (" + " AND ".join(conditions) + ")"             

        if excluded_industries:
            sql_query += f" AND mci.industry_code1 != ALL(${param_count}::text[])"
            array_value = "{" + ",".join(excluded_industries) + "}"
            params.append(array_value)
            param_count += 1

        if gender:
            sql_query += f" AND me.gender = ${param_count}"
            params.append(gender)
            param_count += 1

        if gender_age is not None:
            sql_query += f" AND (EXTRACT(YEAR FROM CURRENT_DATE) - mci.birth_year) >= ${param_count}"
            params.append(gender_age)
            param_count += 1

        if loan is not None:
            sql_query += f" AND mci.loan = ${param_count}"
            params.append(loan)
            param_count += 1

        if not id:
            if latitude and longitude:
                sql_query += " ORDER BY distance_from_location ASC"
            else:
                sql_query += " ORDER BY distance_from_user ASC"

        sql_query += " LIMIT 1000"

        executable_query = get_executable_query(sql_query, params)

        executable_query = '\n'.join(line for line in executable_query.splitlines() if line.strip())
        log.info("Executing SQL Query:")
        log.info(executable_query)

        with get_db() as db:
            result = db.execute(text(executable_query))
            companies = [row._mapping for row in result.fetchall()]
        
        return {
            "success": True,
            "data": companies,
            "total": len(companies),
            "query": id or {
                "search": query,
                "filters": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "userLatitude": user_latitude,
                    "userLongitude": user_longitude,
                    "distance": distance,
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Search failed",
                "message": str(e)
            }
        )
