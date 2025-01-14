from fastapi import APIRouter, Request, HTTPException
from typing import Optional
import json

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
async def search(request: Request):
    print("====================================================")
    search_params = request.query_params
    id = search_params.get("id")
    query = search_params.get("query", "").strip()
    latitude = search_params.get("latitude")
    longitude = search_params.get("longitude")
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
    gender_age = filters.get("gender_age", {}).get("age")

    loan = filters.get("loan")

    print("====================================================")

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
            ci.company_name,
            ci.id,
            ci.business_registration_number,
            ci.representative,
            ci.postal_code,
            ci.address,
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
            FinancialComparison.revenue AS recent_revenue,
            FinancialComparison.net_income AS recent_net_income,
            FinancialComparison.total_assets AS recent_total_assets,
            FinancialComparison.total_liabilities AS recent_total_liabilities,
            FinancialComparison.revenue_growth_rate
        """
        if not id:
            if latitude and longitude:
                sql_query += f"""
                    , ROUND(
                        (
                            6371 * acos(
                                cos(radians(${param_count})) *
                                cos(radians(ci.latitude)) *
                                cos(radians(ci.longitude) - radians(${param_count + 1})) +
                                sin(radians(${param_count})) *
                                sin(radians(ci.latitude))
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
                            cos(radians(ci.latitude)) *
                            cos(radians(ci.longitude) - radians(${param_count + 1})) +
                            sin(radians(${param_count})) *
                            sin(radians(ci.latitude))
                        )
                    ) * 1000
                ) AS distance_from_user
            """
            params.extend([user_latitude, user_longitude])
            param_count += 2

        sql_query += """
        FROM smtp_company_info ci
        LEFT JOIN smtp_financial_company fc 
            ON ci.company_name = fc.company_name
        LEFT JOIN smtp_executives me
            ON ci.business_registration_number = me.business_registration_number
            AND me.position = '대표이사'
        LEFT JOIN FinancialComparison 
            ON fc.id = FinancialComparison.financial_company_id
        WHERE ci.latitude IS NOT NULL
        """
        if id:
            sql_query += f" AND ci.id = ${param_count}"
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
                                    cos(radians(ci.latitude)) *
                                    cos(radians(ci.longitude) - radians(${param_count + 1})) +
                                    sin(radians(${param_count})) *
                                    sin(radians(ci.latitude))
                                )
                            ) * 1000
                        ) <= ${param_count + 2}
                    """
                    params.extend([float(latitude), float(longitude), distance])
                    param_count += 3
                else:
                    if distance:
                        sql_query += f"""
                            AND ROUND(
                                (
                                    6371 * acos(
                                        cos(radians(${param_count})) *
                                        cos(radians(ci.latitude)) *
                                        cos(radians(ci.longitude) - radians(${param_count + 1})) +
                                        sin(radians(${param_count})) *
                                        sin(radians(ci.latitude))
                                    )
                                ) * 1000
                            ) <= ${param_count + 2}
                        """
                        params.extend([user_latitude, user_longitude, distance])
                        param_count += 3

            if query:
                sql_query += f"""
                    AND (
                        ci.company_name ILIKE ${param_count}
                        OR ci.representative ILIKE ${param_count}
                        OR ci.address ILIKE ${param_count}
                    )
                """
                params.append(f"%{query}%")
                param_count += 1

        # 기존 필터 조건들
        if sales_min is not None:
            sql_query += f" AND (FinancialComparison.revenue)::numeric >= ${param_count}"
            params.append(sales_min)
            param_count += 1

        if sales_max is not None:
            sql_query += f" AND (FinancialComparison.revenue)::numeric <= ${param_count}"
            params.append(sales_max)
            param_count += 1

        if profit_min is not None:
            sql_query += f" AND (ci.recent_profit)::numeric >= ${param_count}"
            params.append(profit_min)
            param_count += 1

        if profit_max is not None:
            sql_query += f" AND (ci.recent_profit)::numeric <= ${param_count}"
            params.append(profit_max)
            param_count += 1

        if employee_count_min is not None:
            sql_query += f" AND ci.employee_count >= ${param_count}"
            params.append(employee_count_min)
            param_count += 1

        if employee_count_max is not None:
            sql_query += f" AND ci.employee_count <= ${param_count}"
            params.append(employee_count_max)
            param_count += 1

        if net_profit_min is not None:
            sql_query += f" AND (FinancialComparison.net_income)::numeric >= ${param_count}"
            params.append(net_profit_min)
            param_count += 1

        if net_profit_max is not None:
            sql_query += f" AND (FinancialComparison.net_income)::numeric <= ${param_count}"
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
            sql_query += f" AND EXTRACT(YEAR FROM ci.establishment_date) = ${param_count}"
            params.append(establishment_year)
            param_count += 1

        if certification:
            sql_query += f" AND ci.certifications @> ${param_count}::jsonb"
            params.append(json.dumps(certification))
            param_count += 1

        if excluded_industries:
            sql_query += f" AND ci.industry != ALL(${param_count}::text[])"
            array_value = "{" + ",".join(excluded_industries) + "}"
            params.append(array_value)
            param_count += 1

        if gender:
            sql_query += f" AND me.gender = ${param_count}"
            params.append(gender)
            param_count += 1

        if gender_age is not None:
            sql_query += f" AND EXTRACT(YEAR FROM AGE(to_date(me.birth_date, 'YYYY-MM-DD'))) >= ${param_count}"
            params.append(gender_age)
            param_count += 1

        if loan is not None:
            sql_query += f" AND ci.loan = ${param_count}"
            params.append(loan)
            param_count += 1

        if not id:
            if latitude and longitude:
                sql_query += " ORDER BY distance_from_location ASC"
            else:
                sql_query += " ORDER BY distance_from_user ASC"

        sql_query += " LIMIT 100"

        executable_query = get_executable_query(sql_query, params)

        with get_db() as db:
            result = db.execute(text(executable_query))
            companies = [row._mapping for row in result.fetchall()]

        print(companies)
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
