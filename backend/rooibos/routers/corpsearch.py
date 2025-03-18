from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS
from rooibos.config_extension import NAVER_MAP_CLIENT_ID, NAVER_MAP_CLIENT_SECRET, NAVER_ID, NAVER_CLIENT_SECRET

import json
import logging
import requests

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

import requests

import requests

import requests

import requests

def search_place(query: str):
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": str(NAVER_ID).strip(),
        "X-Naver-Client-Secret": str(NAVER_CLIENT_SECRET).strip(),
    }
    params = {"query": query}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return {"error": response.json()}

    data = response.json()

    if data.get("items"):
        for place in data["items"]:
            if "mapx" in place and "mapy" in place:
                try:
                    place["x"] = float(place["mapx"]) / 1e7
                    place["y"] = float(place["mapy"]) / 1e7
                except Exception:
                    place["x"] = None
                    place["y"] = None
        return data["items"]
    else:
        return {"error": "검색된 장소가 없습니다."}


def get_coordinates(query: str):
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": str(NAVER_MAP_CLIENT_ID).strip(),
        "X-NCP-APIGW-API-KEY": str(NAVER_MAP_CLIENT_SECRET).strip(),
    }
    params = {"query": query}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("addresses"):
        return data["addresses"]
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

@router.get("/")
async def search(request: Request):
    search_params = request.query_params
    id = search_params.get("id")    
    query = search_params.get("query", "").strip()
    user_id = search_params.get("user_id")
    latitude = search_params.get("latitude")
    longitude = search_params.get("longitude")

    categories_str = search_params.get("queryCategories", "")
    categories = [cat.strip() for cat in categories_str.split(",") if cat.strip()]


    if "location" in categories and query:
        if "역" in query:
            location_result = search_place(query)
        else:
            location_result = get_coordinates(query)
        if location_result:
            return {
                "success": True,
                "data": location_result,
                "total": 0,
                "query": {
                    "search": query,
                    "filters": {},
                },
            }
        else:
            # If no valid coordinates were found, return an error response.
            return {
                "success": False,
                "error": "No location found",
                "data": location_result,
                "total": 0,
                "query": {"search": query, "filters": {}},
            }     
    
    user_latitude = float(search_params.get("userLatitude", 0))
    user_longitude = float(search_params.get("userLongitude", 0))
    
    filters_param = search_params.get("filters")
    filters = json.loads(filters_param) if filters_param else {}

    distance = float(filters.get("radius", {}).get("value", "200")) if filters.get("radius") else "200"

    certification = filters.get("certification", {}).get("value") if filters.get("certification") else None

    employee_count_data = filters.get("employee_count", {})
    employee_count_min = employee_count_data.get("min") if filters.get("employee_count") else None
    employee_count_max = employee_count_data.get("max") if filters.get("employee_count") else None

    establishment_year = filters.get("establishment_year", {}).get("value") if filters.get("establishment_year") else None

    included_industries = filters.get("included_industries", {}).get("value") if filters.get("included_industries") else None
    excluded_industries = filters.get("excluded_industries", {}).get("value") if filters.get("excluded_industries") else None

    gender_raw = filters.get("gender", {}).get("value") if filters.get("gender") else None
    gender = "남" if gender_raw == "male" else ("여" if gender_raw == "female" else None)
    representative_age = filters.get("representative_age", {}).get("value") if filters.get("representative_age") else None

    def process_range_filter(data):
        if not data:
            return None, None
        min_val = data.get("min")  
        max_val = data.get("max")

        min_val = None if min_val == '' else min_val
        max_val = None if max_val == '' else max_val

        return (min_val, max_val)

    net_profit_min, net_profit_max = process_range_filter(filters.get("net_profit"))
    profit_min, profit_max = process_range_filter(filters.get("profit"))
    sales_min, sales_max = process_range_filter(filters.get("sales"))
    unallocated_profit_min, unallocated_profit_max = process_range_filter(filters.get("unallocated_profit"))
    total_equity_min, total_equity_max = process_range_filter(filters.get("total_equity"))
    try:
        params = []
        param_count = 1

        sql_query = """
            SELECT 
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
                rmc.representative_birth ,
                rmc.is_family_shareholder s_ha,
                rmc.is_non_family_shareholder ,
                rmc.financial_statement_year,
                rmc.total_assets,
                rmc.total_equity,
                rmc.net_income,
                rmc.venture_confirmation_type,
                rmc.venture_valid_from,
                rmc.venture_valid_until,
                rmc.confirming_authority,
                rmc.new_reconfirmation_code,
                sfd_latest.total_equity AS financial_total_equity,
                cb.id as bookmark_id,
                cb.user_id as bookmark_user_id,
                cb.data as files
        """        

        if not id:
            if latitude and longitude:
                sql_query += f"""
                    , ROUND(
                        (
                            6371 * acos(
                                cos(radians(${param_count})) *
                                cos(radians(rmc.latitude)) *
                                cos(radians(rmc.longitude) - radians(${param_count + 1})) +
                                sin(radians(${param_count})) *
                                sin(radians(rmc.latitude))
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
                            cos(radians(rmc.latitude)) *
                            cos(radians(rmc.longitude) - radians(${param_count + 1})) +
                            sin(radians(${param_count})) *
                            sin(radians(rmc.latitude))
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
            FROM rb_master_company rmc
            LEFT JOIN corp_bookmark cb ON cb.company_id::text = rmc.master_id::text AND cb.user_id = ${user_id_param}
            LEFT JOIN smtp_executives me
                ON rmc.business_registration_number = me.business_registration_number
                AND me.position = '대표이사' 
            LEFT JOIN smtp_financial_company sfc 
                ON sfc.company_name = rmc.company_name
            LEFT JOIN (
                SELECT *
                FROM (
                    SELECT 
                        sfd.*,
                        ROW_NUMBER() OVER (PARTITION BY sfd.financial_company_id ORDER BY sfd.year DESC) AS rn
                    FROM smtp_financial_data sfd
                ) sub
                WHERE rn = 1
            ) sfd_latest 
                ON sfd_latest.financial_company_id = sfc.id    
            WHERE rmc.company_type != '개인' and rmc.latitude IS NOT NULL
            """

        if id:
            sql_query += f" AND (rmc.master_id = ${param_count} OR rmc.business_registration_number = ${param_count})"
            params.append(float(id))
            param_count += 1
        else:
            if not query:
                if latitude and longitude:
                    sql_query += f"""
                        AND ROUND(
                            (
                                6371 * acos(
                                    cos(radians(${param_count})) *
                                    cos(radians(rmc.latitude)) *
                                    cos(radians(rmc.longitude) - radians(${param_count + 1})) +
                                    sin(radians(${param_count})) *
                                    sin(radians(rmc.latitude))
                                )
                            ) * 1000
                        ) <= ${param_count + 2}
                    """
                    params.extend([float(latitude), float(longitude), distance])
                    param_count += 3
                else:
                    # latitude와 longitude가 제공되지 않은 경우 기존 코드대로 userLatitude, userLongitude와 필터의 distance를 사용
                    sql_query += f"""
                        AND ROUND(
                            (
                                6371 * acos(
                                    cos(radians(${param_count})) *
                                    cos(radians(rmc.latitude)) *
                                    cos(radians(rmc.longitude) - radians(${param_count + 1})) +
                                    sin(radians(${param_count})) *
                                    sin(radians(rmc.latitude))
                                )
                            ) * 1000
                        ) <= ${param_count + 2}
                    """
                    params.extend([user_latitude, user_longitude, distance])
                    param_count += 3
            else:
                if len(categories) > 0:
                    # 여러 토글 중 활성화된 것만 조건 생성
                    conditions = []
                    for cat in categories:
                        if cat == "company":
                            conditions.append(f"rmc.company_name ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1
                        elif cat == "representative":
                            conditions.append(f"rmc.representative ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1
                        elif cat == "bizNumber":
                            conditions.append(f"rmc.business_registration_number ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1
                        elif cat == "location":
                            conditions.append(f"rmc.address ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1

                    if conditions:
                        joined_conditions = " OR ".join(conditions)
                        sql_query += f" AND ({joined_conditions}) "
                    else:
                        sql_query += f"""
                            AND (
                                rmc.company_name ILIKE ${param_count}
                                OR rmc.representative ILIKE ${param_count}
                                OR rmc.address ILIKE ${param_count}
                            )
                        """
                        params.append(f"%{query}%")
                        param_count += 1
                

        if not query:

            if employee_count_min not in [None, '']:
                sql_query += f" AND (rmc.employee_count)::numeric >= ${param_count}"
                params.append(employee_count_min)
                param_count += 1

            if employee_count_max not in [None, '']:
                sql_query += f" AND (rmc.employee_count)::numeric <= ${param_count}"
                params.append(employee_count_max)
                param_count += 1

            if sales_min not in [None, '']:
                sql_query += f" AND (rmc.recent_sales)::numeric >= ${param_count}"
                params.append(sales_min)
                param_count += 1

            if sales_max not in [None, '']:
                sql_query += f" AND (rmc.recent_sales)::numeric <= ${param_count}"
                params.append(sales_max)
                param_count += 1

            if profit_min not in [None, '']:
                sql_query += f" AND (rmc.recent_profit)::numeric >= ${param_count}"
                params.append(profit_min)
                param_count += 1

            if profit_max not in [None, '']:
                sql_query += f" AND (rmc.recent_profit)::numeric <= ${param_count}"
                params.append(profit_max)
                param_count += 1

            

            if net_profit_min not in [None, '']:
                sql_query += f" AND (rmc.net_income)::numeric >= ${param_count}"
                params.append(net_profit_min)
                param_count += 1

            if net_profit_max not in [None, '']:
                sql_query += f" AND (rmc.net_income)::numeric <= ${param_count}"
                params.append(net_profit_max)
                param_count += 1

            if unallocated_profit_min not in [None, '']:
                sql_query += f" AND (FinancialComparison.retained_earnings)::numeric >= ${param_count}"
                params.append(unallocated_profit_min)
                param_count += 1

            if unallocated_profit_max not in [None, '']:
                sql_query += f" AND (FinancialComparison.retained_earnings)::numeric <= ${param_count}"
                params.append(unallocated_profit_max)
                param_count += 1

            if total_equity_min not in [None, '']:
                sql_query += f" AND (sfd_latest.total_equity)::numeric >= ${param_count}"
                params.append(total_equity_min)
                param_count += 1

            if total_equity_max not in [None, '']:
                sql_query += f" AND (sfd_latest.total_equity)::numeric <= ${param_count}"
                params.append(total_equity_max)
                param_count += 1    

            if establishment_year not in [None, '']:
                sql_query += f" AND SUBSTRING(rmc.establishment_date, 1, 4)::INTEGER >= ${param_count}"
                params.append(establishment_year)
                param_count += 1


            if certification:
                conditions = []
                if 'innobiz' in certification:
                    conditions.append("rmc.sme_type @> '[{\"sme_type\": \"기술혁신\"}]'")
                if 'mainbiz' in certification:
                    conditions.append("rmc.sme_type @> '[{\"sme_type\": \"경영혁신\"}]'")
                if 'research_institute' in certification:
                    conditions.append("(rmc.research_info @> '[{\"division\": \"연구소\"}]' OR rmc.research_info @> '[{\"division\": \"전담부서\"}]')")
                if 'venture' in certification:
                    conditions.append(f"rmc.confirming_authority = '벤처기업확인기관'")
                
                if conditions:
                    sql_query += " AND (" + " AND ".join(conditions) + ")"             

            if included_industries:
                industry_list = included_industries.split(", ")
                placeholders = ", ".join([f"${param_count + i}" for i in range(len(industry_list))])
                sql_query += f" AND rmc.industry IN ({placeholders})"
                params.extend(industry_list)
                param_count += len(industry_list)

            if excluded_industries:
                excluded_list = excluded_industries.split(", ")
                placeholders = ", ".join([f"${param_count + i}" for i in range(len(excluded_list))])
                sql_query += f" AND rmc.industry NOT IN ({placeholders})"
                params.extend(excluded_list)
                param_count += len(excluded_list)
   


            if gender:
                sql_query += f" AND me.gender = ${param_count}"
                params.append(gender)
                param_count += 1

            if representative_age is not None:
                sql_query += f" AND (EXTRACT(YEAR FROM CURRENT_DATE) - rmc.representative_birth::int) >= ${param_count}"
                params.append(representative_age)
                param_count += 1

            # if loan is not None:
            #     sql_query += f" AND rmc.loan = ${param_count}"
            #     params.append(loan)
            #     param_count += 1

        if not id:
            if latitude and longitude:
                sql_query += " ORDER BY distance_from_location ASC"
            else:
                sql_query += " ORDER BY distance_from_user ASC"

        # sql_query += " LIMIT 1000"

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

@router.get("/industries")
async def get_industries(query: str = ""):
    """
    rb_master_company 테이블에서 중복되지 않는 industry 값을 오름차순으로 조회합니다.
    query 파라미터가 전달되면, 해당 문자열을 포함하는 업종만 필터링하여 반환합니다.
    각 항목은 { id: industry, industry: industry } 형태로 반환됩니다.
    """
    try:
        with get_db() as db:
            base_query = """
                SELECT DISTINCT industry 
                FROM rb_master_company 
                WHERE industry IS NOT NULL AND industry != ''
            """
            params = {}
            if query:
                base_query += " AND industry ILIKE :q"
                params["q"] = f"%{query}%"
            base_query += " ORDER BY industry ASC"

            result = db.execute(text(base_query), params)
            # 각 행의 첫번째 컬럼이 industry 값임
            industries = [row[0] for row in result.fetchall()]

        # 문자열 배열을 객체 배열로 변환
        industries_objs = [{"id": industry, "industry": industry} for industry in industries]

        return {
            "success": True,
            "industries": industries_objs,
            "total": len(industries_objs)
        }
    except Exception as e:
        log.error("Failed to fetch industries: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to fetch industries",
                "message": str(e)
            }
        )



    
@router.get("/{id}/financialData")
async def get_corp_financialData(id: str):
    try:
        params = [id]

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
                sfd.pre_tax_income,
                rmc.recent_total_assets,
                rmc.recent_total_equity
            FROM rb_master_company rmc
            JOIN smtp_financial_company sfc 
                ON rmc.company_name = sfc.company_name
            JOIN smtp_financial_data sfd 
                ON sfc.id = sfd.financial_company_id
            WHERE rmc.master_id = $1
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
                sfd.pre_tax_income,
                rmc.recent_total_assets,
                rmc.recent_total_equity
            ORDER BY sfd.year DESC
        """

        query = get_executable_query(sql_query, params)

        with get_db() as db:
            # 실제 실행되는 재무 데이터 쿼리 로깅
            log.info(f"Executing Financial Data Query: {query}")
            result = db.execute(text(query))
            financial_data = [row._mapping for row in result.fetchall()]        

        return {
            "success": True,
            "financial_data": financial_data,
            "total": len(financial_data),
        }
    except Exception as e:
        log.error("Financial Data API error: %s", e)
        return {
            "success": False,
            "error": "Failed to fetch financial data",
            "message": str(e)
        }

