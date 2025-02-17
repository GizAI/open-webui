# 기업DB 통합작업

## 1. 엑셀 파일 CSV 병합

```bash
python excel_merge.py
```

---

## 2. DB Import

- 통합 CSV 파일을 데이터베이스로 가져오기

---

## 3. DB 작업

### 3.1 중복 데이터 제거

```sql
DELETE FROM public.rb_company_ext a
USING public.rb_company_ext b
WHERE a.ctid > b.ctid  -- 더 늦게 삽입된(큰 ctid) 행을 삭제
AND a.company_name = b.company_name
AND a.representative = b.representative
AND a.representative_birth = b.representative_birth
AND a.establishment_date = b.establishment_date
AND a.is_family_shareholder = b.is_family_shareholder
AND a.is_non_family_shareholder = b.is_non_family_shareholder
AND a.industry = b.industry
AND a.financial_statement_year = b.financial_statement_year
AND a.employee_count = b.employee_count
AND a.total_assets = b.total_assets
AND a.total_equity = b.total_equity
AND a.revenue = b.revenue
AND a.net_income = b.net_income
AND a.address = b.address
AND a.business_registration_number = b.business_registration_number
AND a.phone_number = b.phone_number
AND a.fax_number = b.fax_number
AND a.company_type = b.company_type;
```

### 3.2 인덱스 생성

```sql
CREATE INDEX idx_rb_company_ext_biz_reg_num
ON public.rb_company_ext (business_registration_number);

CREATE INDEX idx_rb_company_ext_company_type
ON public.rb_company_ext (company_type);
```

---

## 4. 사업자 번호 중복 처리

### 4.1 중복 데이터 제외 컬럼 추가

```sql
ALTER TABLE public.smtp_company_info
  ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false;

ALTER TABLE public.rb_company_ext
  ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false;
```

### 4.2 중복 데이터 마킹 (Deduplication)

```sql
WITH combined AS (
  SELECT
    'rb_company_ext' AS source,
    ctid AS row_id,
    business_registration_number,
    CASE
      WHEN establishment_date = '20130229' THEN to_date('20130228', 'YYYYMMDD')
      WHEN establishment_date ~ '^\d{6}00$' THEN to_date(substring(establishment_date from 1 for 6) || '01', 'YYYYMMDD')
      WHEN establishment_date <> '' THEN to_date(establishment_date, 'YYYYMMDD')
      ELSE NULL
    END AS est_date,
    financial_statement_year,
    file_name
  FROM public.rb_company_ext
  WHERE business_registration_number IS NOT NULL
),
ranked AS (
  SELECT
    source,
    row_id,
    business_registration_number,
    ROW_NUMBER() OVER (
      PARTITION BY business_registration_number
      ORDER BY
        COALESCE(est_date, '1900-01-01'::date) DESC,
        COALESCE(financial_statement_year, 0) DESC,
        CASE WHEN file_name LIKE '%250106%' THEN 1 ELSE 0 END DESC,
        row_id ASC
    ) AS rn
  FROM combined
)
UPDATE public.rb_company_ext t
SET is_deleted = true
FROM ranked r
WHERE t.ctid = r.row_id
  AND r.source = 'rb_company_ext'
  AND r.rn > 1;
```

### 4.3 검증

```sql
SELECT
  business_registration_number,
  COUNT(*) AS total_rows,
  SUM(CASE WHEN is_deleted THEN 1 ELSE 0 END) AS deleted_count,
  COUNT(*) - SUM(CASE WHEN is_deleted THEN 1 ELSE 0 END) AS active_count
FROM public.rb_company_ext
GROUP BY business_registration_number
HAVING COUNT(*) > 1
ORDER BY business_registration_number;
```

---

## 5. 마스터 테이블 생성

### 5.1 테이블 생성

```sql
CREATE TABLE public.rb_master_company (
  master_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  business_registration_number text,
  company_name text,
  representative text,
  establishment_date text,
  postal_code text,
  address text,
  phone_number text,
  fax_number text,
  website text,
  email text,
  company_type text,
  founding_date text,
  employee_count text,
  industry_code1 text,
  industry_code2 text,
  industry text,
  main_product text,
  main_bank text,
  main_branch text,
  group_name text,
  stock_code text,
  corporate_number text,
  english_name text,
  trade_name text,
  fiscal_month text,
  sales_year text,
  recent_sales text,
  profit_year text,
  recent_profit text,
  operating_profit_year text,
  recent_operating_profit text,
  asset_year text,
  recent_total_assets text,
  debt_year text,
  recent_total_debt text,
  equity_year text,
  recent_total_equity text,
  capital_year text,
  recent_capital text,
  region1 text,
  region2 text,
  industry_major text,
  industry_middle text,
  industry_small text,
  latitude numeric(10, 8),
  longitude numeric(11, 8),
  representative_birth varchar(50),
  is_family_shareholder varchar(255),
  is_non_family_shareholder varchar(255),
  financial_statement_year int4,
  total_assets float4,
  total_equity float4,
  revenue float4,
  net_income float4,
  source_table text,
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now()
);
```

### 5.2 인덱스 생성

```sql
CREATE UNIQUE INDEX idx_unique_business_registration_number
ON public.rb_master_company(business_registration_number);
```

### 5.3 데이터 병합 Insert

```sql
WITH smtp AS (
  SELECT *
  FROM public.smtp_company_info
  WHERE is_deleted IS NOT TRUE
),
rb AS (
  SELECT *
  FROM public.rb_company_ext
  WHERE is_deleted IS NOT TRUE
)
INSERT INTO public.rb_master_company (
  business_registration_number, company_name, representative, establishment_date, postal_code, address, phone_number, fax_number,
  website, email, company_type, founding_date, employee_count, industry_code1, industry_code2, industry, main_product, main_bank,
  main_branch, group_name, stock_code, corporate_number, english_name, trade_name, fiscal_month, sales_year, recent_sales, profit_year,
  recent_profit, operating_profit_year, recent_operating_profit, asset_year, recent_total_assets, debt_year, recent_total_debt, equity_year,
  recent_total_equity, capital_year, recent_capital, region1, region2, industry_major, industry_middle, industry_small, latitude, longitude,
  representative_birth, is_family_shareholder, is_non_family_shareholder, financial_statement_year, total_assets, total_equity, revenue,
  net_income, source_table
)
SELECT
  COALESCE(smtp.business_registration_number, rb.business_registration_number) AS business_registration_number,
  COALESCE(smtp.company_name, rb.company_name) AS company_name,
  COALESCE(smtp.representative, rb.representative) AS representative,
  ... (이하 생략)
```

### 5.4 추가 작업

```sql
delete from rb_master_company where business_registration_number is null;
delete from rb_master_company where rb_master_company.company_name ='';
```
