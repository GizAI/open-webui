-- 성능 최적화를 위한 인덱스 생성 스크립트
-- 작성일: 2025-04-09
-- 작성자: SQL 튜닝 전문가
-- 목적: 나의 고객 폴더 조회 시 성능 개선

-- corp_bookmark 테이블 인덱스 생성
-- 1. 폴더 ID로 조회 최적화 (기본 조회 조건)
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_folder_id ON corp_bookmark(folder_id);

-- 2. 사용자 ID로 조회 최적화 (모든 쿼리에서 공통으로 사용)
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_user_id ON corp_bookmark(user_id);

-- 3. 삭제 상태로 조회 최적화 (휴지통 기능)
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_is_deleted ON corp_bookmark(is_deleted);

-- 4. 사업자등록번호로 조회 최적화 (기업 정보 조인 시 사용)
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_brn ON corp_bookmark(business_registration_number);

-- 5. 복합 인덱스: 사용자 ID + 폴더 ID (가장 많이 사용되는 조건)
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_user_folder ON corp_bookmark(user_id, folder_id);

-- 6. 복합 인덱스: 사용자 ID + 삭제 상태 (휴지통 조회)
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_user_deleted ON corp_bookmark(user_id, is_deleted);

-- 7. 정렬 성능 개선을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_updated_at ON corp_bookmark(updated_at DESC);

-- 8. 공유 기능을 위한 인덱스 
-- JSON 타입에 적합한 방식으로 수정
-- 가장 좋은 방법은 JSON을 JSONB로 타입 변환하여 인덱싱하는 것입니다
-- 그러나 타입 변경 없이 access_control이 비어있지 않은 데이터에 대한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_corp_bookmark_has_access_control ON corp_bookmark((access_control::text <> '{}'));

-- rb_master_company 테이블 인덱스 생성
-- 9. 사업자등록번호로 조회 최적화 (기업 정보 조인 시 사용)
CREATE INDEX IF NOT EXISTS idx_master_company_brn ON rb_master_company(business_registration_number);

-- 10. master_id로 조회 최적화
CREATE INDEX IF NOT EXISTS idx_master_company_id ON rb_master_company(master_id);

-- private_entity_info 테이블 인덱스 생성
-- 11. 사업자등록번호로 조회 최적화 (기업 정보 조인 시 사용)
CREATE INDEX IF NOT EXISTS idx_private_entity_brn ON private_entity_info(business_registration_number);

-- 12. smtp_id로 조회 최적화
CREATE INDEX IF NOT EXISTS idx_private_entity_id ON private_entity_info(smtp_id);

-- rb_folder 테이블 인덱스 생성
-- 13. 사용자 ID로 폴더 조회 최적화
CREATE INDEX IF NOT EXISTS idx_rb_folder_user_id ON rb_folder(user_id);

-- 14. 폴더 타입으로 조회 최적화
CREATE INDEX IF NOT EXISTS idx_rb_folder_type ON rb_folder(type);

-- 통계 갱신 명령
-- 이 명령은 인덱스 생성 후 통계 정보를 갱신하여 쿼리 계획이 최적화되도록 함
ANALYZE corp_bookmark;
ANALYZE rb_master_company;
ANALYZE private_entity_info;
ANALYZE rb_folder; 