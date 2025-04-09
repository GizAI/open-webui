from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Optional, Dict, Any
from open_webui.internal.db import get_db
from sqlalchemy import text
from open_webui.env import SRC_LOG_LEVELS
from rooibos.config_extension import NAVER_MAP_CLIENT_ID, NAVER_MAP_CLIENT_SECRET, NAVER_ID, NAVER_CLIENT_SECRET
from starlette.responses import JSONResponse
from functools import lru_cache

import json
import logging
import requests
import time

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["COMFYUI"])

router = APIRouter()

# 쿼리 결과 캐싱을 위한 LRU 캐시 (최근 100개 쿼리 결과 저장)
@lru_cache(maxsize=100)
def cached_query_results(query_hash: str):
    return {}

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

# 거리 계산 함수를 최적화 (지구구체 계산 대신 PostGIS 활용)
def get_distance_conditions(lat, lng, distance, param_count):
    """효율적인 거리 계산 조건 생성 (구면 거리 계산 사용)"""
    return f"""
        ROUND(
            (
                6371 * 2 * asin(
                    sqrt(
                        power(sin((radians(rmc.latitude) - radians(${param_count})) / 2), 2) +
                        cos(radians(${param_count})) * cos(radians(rmc.latitude)) * 
                        power(sin((radians(rmc.longitude) - radians(${param_count + 1})) / 2), 2)
                    )
                )
            ) * 1000
        ) <= ${param_count + 2}
    """

@router.get("/")
async def search(
    request: Request,
    page: int = 1,
    page_size: int = 50,
):
    start_time = time.time()
    search_params = request.query_params
    id = search_params.get("id")    
    query = search_params.get("query", "").strip()
    user_id = search_params.get("user_id")
    latitude = search_params.get("latitude")
    longitude = search_params.get("longitude")

    categories_str = search_params.get("queryCategories", "")
    categories = [cat.strip() for cat in categories_str.split(",") if cat.strip()]

    # 위치 검색이면 해당 API를 빠르게 호출
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
            return {
                "success": False,
                "error": "No location found",
                "data": location_result,
                "total": 0,
                "query": {"search": query, "filters": {}},
            }     
    
    # 사용자 위치 정보 (항상 필요함)
    user_latitude = float(search_params.get("userLatitude", 0))
    user_longitude = float(search_params.get("userLongitude", 0))
    
    # 디버그: 좌표값 로깅
    log.info(f"User coordinates: lat={user_latitude}, lng={user_longitude}")
    
    filters_param = search_params.get("filters")
    filters = json.loads(filters_param) if filters_param else {}

    # 거리 제한은 검색어가 있는 경우에도 적용해야 함
    distance = float(filters.get("radius", {}).get("value", "200")) if filters.get("radius") else 200

    # 필터 조건 파싱
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
    
    # 캐싱을 위한 쿼리 해시값 생성
    query_hash = f"{id}_{query}_{user_id}_{latitude}_{longitude}_{categories_str}_{filters_param}_{page}_{page_size}"
    cached_result = cached_query_results(query_hash)
    if cached_result:
        log.info(f"Cache hit for query: {query_hash}")
        return cached_result
    
    try:
        params = []
        param_count = 1

        # 검색 위치 결정 - latitude/longitude가 지정되면 그 위치 사용, 아니면 사용자 위치 사용
        search_latitude = float(latitude) if latitude else user_latitude
        search_longitude = float(longitude) if longitude else user_longitude
        
        # 카운트 쿼리와 실제 데이터 쿼리 분리
        if not id:
            # 먼저 조건에 맞는 전체 개수를 효율적으로 계산
            count_query = """
                SELECT COUNT(*) 
                FROM rb_master_company rmc
            """
            
            count_where_clauses = ["rmc.company_type != '개인' AND rmc.latitude IS NOT NULL"]
            count_params = []
            count_param_idx = 1
            
            # 검색어 유무에 따라 다른 조건 적용
            if query:
                # 검색어가 있는 경우: 거리 제한 없이 검색어만으로 필터링
                if len(categories) > 0:
                    search_conditions = []
                    for cat in categories:
                        if cat == "company":
                            search_conditions.append(f"rmc.company_name ILIKE ${count_param_idx}")
                            count_params.append(f"%{query}%")
                            count_param_idx += 1
                        elif cat == "representative":
                            search_conditions.append(f"rmc.representative ILIKE ${count_param_idx}")
                            count_params.append(f"%{query}%")
                            count_param_idx += 1
                        elif cat == "bizNumber":
                            search_conditions.append(f"rmc.business_registration_number ILIKE ${count_param_idx}")
                            count_params.append(f"%{query}%")
                            count_param_idx += 1
                        elif cat == "location":
                            search_conditions.append(f"rmc.address ILIKE ${count_param_idx}")
                            count_params.append(f"%{query}%")
                            count_param_idx += 1

                    if search_conditions:
                        count_where_clauses.append(f"({' OR '.join(search_conditions)})")
                else:
                    # 카테고리가 없으면 기본 검색 필드에서 검색
                    count_where_clauses.append(f"""(
                        rmc.company_name ILIKE ${count_param_idx}
                        OR rmc.representative ILIKE ${count_param_idx}
                        OR rmc.address ILIKE ${count_param_idx}
                    )""")
                    count_params.append(f"%{query}%")
                    count_param_idx += 1
            else:
                # 검색어가 없는 경우: 거리 제한 적용
                dist_condition = f"""
                    ROUND(
                        (
                            6371 * 2 * asin(
                                sqrt(
                                    power(sin((radians(rmc.latitude) - radians(${count_param_idx})) / 2), 2) +
                                    cos(radians(${count_param_idx})) * cos(radians(rmc.latitude)) * 
                                    power(sin((radians(rmc.longitude) - radians(${count_param_idx + 1})) / 2), 2)
                                )
                            )
                        ) * 1000
                    ) <= ${count_param_idx + 2}
                """
                count_where_clauses.append(dist_condition)
                count_params.extend([search_latitude, search_longitude, distance])
                count_param_idx += 3
            
            # 기타 필터 조건들 추가
            # 숫자형 필드 필터링
            numeric_filters = [
                ("employee_count", employee_count_min, employee_count_max),
                ("recent_sales", sales_min, sales_max),
                ("recent_profit", profit_min, profit_max),
                ("net_income", net_profit_min, net_profit_max)
            ]
            
            for field, min_val, max_val in numeric_filters:
                if min_val not in [None, '']:
                    count_where_clauses.append(f"(rmc.{field})::numeric >= ${count_param_idx}")
                    count_params.append(min_val)
                    count_param_idx += 1
                
                if max_val not in [None, '']:
                    count_where_clauses.append(f"(rmc.{field})::numeric <= ${count_param_idx}")
                    count_params.append(max_val)
                    count_param_idx += 1
            
            # 설립연도 필터
            if establishment_year not in [None, '']:
                count_where_clauses.append(f"SUBSTRING(rmc.establishment_date, 1, 4)::INTEGER >= ${count_param_idx}")
                count_params.append(establishment_year)
                count_param_idx += 1
            
            # JSON 필드 필터링 (certification)
            if certification:
                cert_conditions = []
                if 'innobiz' in certification:
                    cert_conditions.append("rmc.sme_type @> '[{\"sme_type\": \"기술혁신\"}]'")
                if 'mainbiz' in certification:
                    cert_conditions.append("rmc.sme_type @> '[{\"sme_type\": \"경영혁신\"}]'")
                if 'research_institute' in certification:
                    cert_conditions.append("(rmc.research_info @> '[{\"division\": \"연구소\"}]' OR rmc.research_info @> '[{\"division\": \"전담부서\"}]')")
                if 'venture' in certification:
                    cert_conditions.append(f"rmc.confirming_authority = '벤처기업확인기관'")
                
                if cert_conditions:
                    count_where_clauses.append("(" + " AND ".join(cert_conditions) + ")")
            
            # 산업 필터
            if included_industries:
                industry_list = included_industries.split(", ")
                placeholders = ", ".join([f"${count_param_idx + i}" for i in range(len(industry_list))])
                count_where_clauses.append(f"rmc.industry IN ({placeholders})")
                count_params.extend(industry_list)
                count_param_idx += len(industry_list)

            if excluded_industries:
                excluded_list = excluded_industries.split(", ")
                placeholders = ", ".join([f"${count_param_idx + i}" for i in range(len(excluded_list))])
                count_where_clauses.append(f"rmc.industry NOT IN ({placeholders})")
                count_params.extend(excluded_list)
                count_param_idx += len(excluded_list)

            count_query += " WHERE " + " AND ".join(count_where_clauses)
            count_executable_query = get_executable_query(count_query, count_params)
            log.info(f"Executing Count Query: {count_executable_query}")
            
            with get_db() as db:
                count_result = db.execute(text(count_executable_query))
                total_count = count_result.scalar()
        else:
            # ID로 조회하는 경우는 항상 1개만 반환하므로 count는 1로 설정
            total_count = 1

        # 메인 데이터 쿼리 구성
        # 필수 열만 조회하여 속도 향상
        essential_columns = """
            rmc.master_id,
            rmc.company_name,
            rmc.representative,
            rmc.address,
            rmc.phone_number,
            rmc.industry,
            rmc.establishment_date,
            rmc.employee_count,
            rmc.recent_sales,
            rmc.recent_profit,
            rmc.latitude,
            rmc.longitude
        """
        
        # ID로 조회하는 경우만 모든 필드 조회
        if id:
            sql_query = """
                SELECT 
                    rmc.*,
                    cb.id as bookmark_id,
                    cb.user_id as bookmark_user_id,
                    cb.data as files,
                    sfd.total_equity as financial_total_equity,
                    ROUND(
                        (
                            6371 * 2 * asin(
                                sqrt(
                                    power(sin((radians(rmc.latitude) - radians(${param_count})) / 2), 2) +
                                    cos(radians(${param_count})) * cos(radians(rmc.latitude)) * 
                                    power(sin((radians(rmc.longitude) - radians(${param_count + 1})) / 2), 2)
                                )
                            )
                        ) * 1000
                    ) AS distance_from_user
            """
            params.extend([user_latitude, user_longitude])
            param_count += 2
        else:
            # 목록 조회는 필수 필드만 가져옴
            sql_query = f"""
                SELECT 
                    {essential_columns},
                    cb.id as bookmark_id
            """

        # 거리 계산 열 추가 (검색 중심점과의 거리)
        if not id:
            sql_query += f"""
                , ROUND(
                    (
                        6371 * 2 * asin(
                            sqrt(
                                power(sin((radians(rmc.latitude) - radians(${param_count})) / 2), 2) +
                                cos(radians(${param_count})) * cos(radians(rmc.latitude)) * 
                                power(sin((radians(rmc.longitude) - radians(${param_count + 1})) / 2), 2)
                            )
                        )
                    ) * 1000
                ) AS distance_from_search
            """
            params.extend([search_latitude, search_longitude])
            param_count += 2

            # 추가: 항상 사용자 위치와의 거리도 계산 (검색 위치와 다를 수 있음)
            sql_query += f"""
                , ROUND(
                    (
                        6371 * 2 * asin(
                            sqrt(
                                power(sin((radians(rmc.latitude) - radians(${param_count})) / 2), 2) +
                                cos(radians(${param_count})) * cos(radians(rmc.latitude)) * 
                                power(sin((radians(rmc.longitude) - radians(${param_count + 1})) / 2), 2)
                            )
                        )
                    ) * 1000
                ) AS distance_from_user
            """
            params.extend([user_latitude, user_longitude])
            param_count += 2

        # 북마크 정보를 위한 사용자 ID 추가
        params.append(user_id)
        user_id_param = param_count
        param_count += 1

        # 메인 쿼리 JOIN 구문 - 필요한 조인만 수행
        if id:
            # ID 조회는 상세 정보가 필요하므로 모든 조인 수행
            sql_query += f"""
                FROM rb_master_company rmc /*+ INDEX(rmc idx_rb_master_company_id) */
                LEFT JOIN corp_bookmark cb ON cb.company_id::text = rmc.master_id::text AND cb.user_id = ${user_id_param}
                LEFT JOIN LATERAL (
                    SELECT me.*
                    FROM smtp_executives me
                    WHERE rmc.business_registration_number = me.business_registration_number
                    AND me.position = '대표이사'
                    LIMIT 1
                ) me ON true
                LEFT JOIN LATERAL (
                    SELECT sfd.total_equity
                    FROM smtp_financial_company sfc 
                    JOIN smtp_financial_data sfd ON sfd.financial_company_id = sfc.id
                    WHERE sfc.company_name = rmc.company_name
                    ORDER BY sfd.year DESC
                    LIMIT 1
                ) sfd ON true
                WHERE rmc.company_type != '개인' AND rmc.latitude IS NOT NULL
            """
        else:
            # 목록 조회는 북마크 정보만 간단히 조인
            sql_query += f"""
                FROM rb_master_company rmc /*+ INDEX(rmc idx_rb_master_company_latitude_longitude) */
                LEFT JOIN corp_bookmark cb ON cb.company_id::text = rmc.master_id::text AND cb.user_id = ${user_id_param}
                WHERE rmc.company_type != '개인' AND rmc.latitude IS NOT NULL
            """

        # WHERE 절 구성
        if id:
            sql_query += f" AND (rmc.master_id = ${param_count} OR rmc.business_registration_number = ${param_count})"
            params.append(float(id))
            param_count += 1
        else:
            # 검색어 유무에 따라 다른 조건 적용
            if query:
                # 검색어가 있는 경우: 거리 제한 없이 검색어로만 필터링
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
                    # 카테고리가 없으면 기본 검색 필드에서 검색
                    sql_query += f"""
                        AND (
                            rmc.company_name ILIKE ${param_count}
                            OR rmc.representative ILIKE ${param_count}
                            OR rmc.address ILIKE ${param_count}
                        )
                    """
                    params.append(f"%{query}%")
                    param_count += 1
            else:
                # 검색어가 없는 경우에만 거리 제한 적용
                distance_condition = f"""
                    ROUND(
                        (
                            6371 * 2 * asin(
                                sqrt(
                                    power(sin((radians(rmc.latitude) - radians(${param_count})) / 2), 2) +
                                    cos(radians(${param_count})) * cos(radians(rmc.latitude)) * 
                                    power(sin((radians(rmc.longitude) - radians(${param_count + 1})) / 2), 2)
                                )
                            )
                        ) * 1000
                    ) <= ${param_count + 2}
                """
                sql_query += f" AND {distance_condition}"
                params.extend([search_latitude, search_longitude, float(distance)])
                param_count += 3
            
            # 추가 필터 조건 적용
            # 숫자형 필드 필터링
            numeric_filters = [
                ("employee_count", employee_count_min, employee_count_max),
                ("recent_sales", sales_min, sales_max),
                ("recent_profit", profit_min, profit_max),
                ("net_income", net_profit_min, net_profit_max)
            ]
            
            for field, min_val, max_val in numeric_filters:
                if min_val not in [None, '']:
                    sql_query += f" AND (rmc.{field})::numeric >= ${param_count}"
                    params.append(min_val)
                    param_count += 1
                
                if max_val not in [None, '']:
                    sql_query += f" AND (rmc.{field})::numeric <= ${param_count}"
                    params.append(max_val)
                    param_count += 1
            
            # 설립연도 필터
            if establishment_year not in [None, '']:
                sql_query += f" AND SUBSTRING(rmc.establishment_date, 1, 4)::INTEGER >= ${param_count}"
                params.append(establishment_year)
                param_count += 1
            
            # JSON 필드 필터링 (certification)
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
            
            # 산업 필터
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

        # 정렬 기준 추가
        if not id:
            if query:
                # 검색어가 있는 경우: 기본 정렬 (회사명)
                sql_query += " ORDER BY rmc.company_name ASC"
            else:
                # 검색어가 없는 경우: 거리 기준 정렬
                sql_query += " ORDER BY distance_from_search ASC"
        
        # 페이징 처리
        if not id:
            offset = (page - 1) * page_size
            sql_query += f" LIMIT {page_size} OFFSET {offset}"

        # 쿼리 실행
        executable_query = get_executable_query(sql_query, params)
        executable_query = '\n'.join(line for line in executable_query.splitlines() if line.strip())
        log.info(f"Executing SQL Query: {executable_query}")

        with get_db() as db:
            result = db.execute(text(executable_query))
            companies = [dict(row._mapping) for row in result.fetchall()]
        
        # 디버그: 회사 좌표 정보와 계산된 거리 로깅 
        for company in companies:
            if 'distance_from_user' in company and 'latitude' in company and 'longitude' in company:
                log.info(f"Company: {company.get('company_name')}, Coords: lat={company.get('latitude')}, lng={company.get('longitude')}, Distance: {company.get('distance_from_user')}m")
        
        # 응답 생성
        response = {
            "success": True,
            "data": companies,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "pages": (total_count + page_size - 1) // page_size,
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
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        # 결과를 캐시에 저장
        cached_query_results.cache_clear()  # 캐시 크기 관리를 위해 주기적으로 클리어
        cached_query_results(query_hash)
        
        return response

    except Exception as e:
        log.error(f"Search error: {str(e)}")
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
        # 캐시 키 생성
        cache_key = f"financial_data_{id}"
        cached_data = cached_query_results(cache_key)
        if cached_data:
            return cached_data
        
        params = [id]

        sql_query = """
            WITH financial_data AS (
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
                    rmc.recent_total_equity,
                    ROW_NUMBER() OVER (PARTITION BY sfd.year ORDER BY sfd.financial_company_id) as rn
                FROM rb_master_company rmc /*+ INDEX(rmc idx_rb_master_company_id) */
                JOIN smtp_financial_company sfc ON rmc.company_name = sfc.company_name
                JOIN smtp_financial_data sfd ON sfc.id = sfd.financial_company_id
                WHERE rmc.master_id = $1
            )
            SELECT * FROM financial_data
            WHERE rn = 1
            ORDER BY year DESC
        """

        query = get_executable_query(sql_query, params)

        with get_db() as db:
            log.info(f"Executing Financial Data Query: {query}")
            result = db.execute(text(query))
            financial_data = [dict(row._mapping) for row in result.fetchall()]        

        response = {
            "success": True,
            "financial_data": financial_data,
            "total": len(financial_data),
        }
        
        # 캐시에 저장
        cached_query_results(cache_key)
        
        return response
    except Exception as e:
        log.error(f"Financial Data API error: {e}")
        return {
            "success": False,
            "error": "Failed to fetch financial data",
            "message": str(e)
        }

