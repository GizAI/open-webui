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

    excluded_industries = filters.get("excluded_industries", {}).get("value") if filters.get("excluded_industries") else None

    gender_raw = filters.get("gender", {}).get("value") if filters.get("gender") else None
    gender = "남" if gender_raw == "male" else ("여" if gender_raw == "female" else None)
    representative_age = filters.get("representative_age", {}).get("value") if filters.get("representative_age") else None

    def process_range_filter(data, multiplier=1_000_000):
        if not data:
            return None, None
        min_val = data.get("min")  
        max_val = data.get("max")

        min_val = None if min_val == '' else min_val
        max_val = None if max_val == '' else max_val

        return (float(min_val) * multiplier if min_val is not None else None,
                float(max_val) * multiplier if max_val is not None else None)

    net_profit_min, net_profit_max = process_range_filter(filters.get("net_profit"))
    profit_min, profit_max = process_range_filter(filters.get("profit"))
    sales_min, sales_max = process_range_filter(filters.get("sales"))
    unallocated_profit_min, unallocated_profit_max = process_range_filter(filters.get("unallocated_profit"))

    try:
        params = []
        param_count = 1

        sql_query = """
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
            sql_query += f" AND (mci.smtp_id = ${param_count} OR mci.business_registration_number = ${param_count})"
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
                    # latitude와 longitude가 제공되지 않은 경우 기존 코드대로 userLatitude, userLongitude와 필터의 distance를 사용
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
                    params.extend([user_latitude, user_longitude, distance])
                    param_count += 3
            else:
                if len(categories) > 0:
                    # 여러 토글 중 활성화된 것만 조건 생성
                    conditions = []
                    for cat in categories:
                        if cat == "company":
                            conditions.append(f"mci.company_name ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1
                        elif cat == "representative":
                            conditions.append(f"mci.representative ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1
                        elif cat == "bizNumber":
                            conditions.append(f"mci.business_registration_number ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1
                        elif cat == "location":
                            conditions.append(f"mci.address ILIKE ${param_count}")
                            params.append(f"%{query}%")
                            param_count += 1

                    if conditions:
                        joined_conditions = " OR ".join(conditions)
                        sql_query += f" AND ({joined_conditions}) "
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
                

        if not query:
            if sales_min not in [None, '']:
                sql_query += f" AND (mci.sales_amount)::numeric >= ${param_count}"
                params.append(sales_min)
                param_count += 1

            if sales_max not in [None, '']:
                sql_query += f" AND (mci.sales_amount)::numeric <= ${param_count}"
                params.append(sales_max)
                param_count += 1

            if profit_min not in [None, '']:
                sql_query += f" AND (mci.recent_profit)::numeric >= ${param_count}"
                params.append(profit_min)
                param_count += 1

            if profit_max not in [None, '']:
                sql_query += f" AND (mci.recent_profit)::numeric <= ${param_count}"
                params.append(profit_max)
                param_count += 1

            if employee_count_min not in [None, '']:
                sql_query += f" AND (mci.employee_count)::numeric >= ${param_count}"
                params.append(employee_count_min)
                param_count += 1

            if employee_count_max not in [None, '']:
                sql_query += f" AND (mci.employee_count)::numeric <= ${param_count}"
                params.append(employee_count_max)
                param_count += 1

            if net_profit_min not in [None, '']:
                sql_query += f" AND (mci.net_income)::numeric >= ${param_count}"
                params.append(net_profit_min)
                param_count += 1

            if net_profit_max not in [None, '']:
                sql_query += f" AND (mci.net_income)::numeric <= ${param_count}"
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

            if establishment_year not in [None, '']:
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

            if representative_age is not None:
                sql_query += f" AND (EXTRACT(YEAR FROM CURRENT_DATE) - mci.birth_year) >= ${param_count}"
                params.append(representative_age)
                param_count += 1

            # if loan is not None:
            #     sql_query += f" AND mci.loan = ${param_count}"
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
