-- mycompanies.py에서 사용하는 쿼리 최적화를 위한 인덱스 생성
-- 작성일: 2025-04-09
-- 작성자: SQL 튜닝 전문가
-- 목적: 기업 정보 조회 성능 개선

-- 1. private_entity_info 테이블 인덱스
-- 사업자등록번호는 join 조건으로 자주 사용되므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_private_entity_brn ON private_entity_info(business_registration_number);
-- smtp_id는 기업 식별자로 자주 사용되므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_private_entity_smtp_id ON private_entity_info(smtp_id);
-- 회사명으로 검색하는 경우가 많으므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_private_entity_company_name ON private_entity_info(company_name);
-- 사용자 ID로 필터링하는 경우가 많으므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_private_entity_user_id ON private_entity_info(user_id);
-- entity_type으로 구분하는 경우가 많으므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_private_entity_type ON private_entity_info(entity_type);


-- 5. rb_master_company 테이블 추가 인덱스
-- 회사명으로 검색하는 경우가 많으므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_master_company_name ON rb_master_company(company_name);
-- 내부 모델에서 master_id로 조회하는 경우가 많음
CREATE INDEX IF NOT EXISTS idx_master_company_id ON rb_master_company(master_id);

-- 6. corp_bookmark 테이블 추가 인덱스
-- company_id로 조회하는 경우가 많으므로 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_company_id ON corp_bookmark(company_id);
-- data JSONB 필드에서 파일 ID 조회를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_data ON corp_bookmark((data->>'file_ids')) WHERE data IS NOT NULL;

-- 통계 갱신 명령
-- 통계 정보를 갱신하여 쿼리 최적화기가 더 나은 실행 계획을 선택하도록 함
ANALYZE private_entity_info;
ANALYZE rb_master_company;
ANALYZE corp_bookmark; 