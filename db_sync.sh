#!/bin/bash

# 원본 DB 정보
SRC_HOST="45.132.75.98"
SRC_PORT="15432"
SRC_DB="openwebui"
SRC_USER="jytdev"

# 대상 DB 정보 (로컬)
DEST_HOST="localhost"
DEST_PORT="5432"
DEST_DB="openwebui"
DEST_USER="jytdev"

# 임시 덤프 파일 경로
DUMP_FILE="/tmp/openwebui_dump.dump"

# 제외할 테이블 목록
EXCLUDE_TABLES=(
  "city_company_info"
  "city_company_info_20250204"
  "master_company_info"
  "master_company_info_20250205"
  "rb_company_ext"
  "rb_master_company"
)

# 사용자에게 테이블 제외 여부 확인
echo "🚩 제외 가능한 테이블 목록:"
for table in "${EXCLUDE_TABLES[@]}"; do
  echo "  - $table"
done

read -p "위 테이블을 모두 제외하시겠습니까? (Y/n): " exclude_all
if [[ "$exclude_all" == "n" || "$exclude_all" == "N" ]]; then
  EXCLUDE_PARAMS=""
  for table in "${EXCLUDE_TABLES[@]}"; do
    read -p "$table 테이블을 제외하시겠습니까? (Y/n): " exclude_choice
    if [[ "$exclude_choice" != "n" && "$exclude_choice" != "N" ]]; then
      EXCLUDE_PARAMS+=" --exclude-table=${table}"
    fi
  done
else
  EXCLUDE_PARAMS=""
  for table in "${EXCLUDE_TABLES[@]}"; do
    EXCLUDE_PARAMS+=" --exclude-table=${table}"
  done
fi

# 비밀번호 입력 및 검증 함수
check_db_connection() {
  local HOST=$1
  local PORT=$2
  local USER=$3
  local PASSWORD=$4
  local DB=$5

  PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DB -c '\q' &>/dev/null
  return $?
}

while true; do
  read -sp "🔑 원격지 DB 비밀번호 입력: " SRC_PASSWORD
  echo ""
  check_db_connection $SRC_HOST $SRC_PORT $SRC_USER $SRC_PASSWORD $SRC_DB
  if [ $? -eq 0 ]; then
    echo "✅ 원격지 DB 비밀번호가 확인되었습니다."
    break
  else
    echo "❌ 원격지 DB 비밀번호가 잘못되었습니다. 다시 입력해주세요."
  fi
done

while true; do
  read -sp "🔑 대상지 DB 비밀번호 입력: " DEST_PASSWORD
  echo ""
  check_db_connection $DEST_HOST $DEST_PORT $DEST_USER $DEST_PASSWORD "postgres"
  if [ $? -eq 0 ]; then
    echo "✅ 대상지 DB 비밀번호가 확인되었습니다."
    break
  else
    echo "❌ 대상지 DB 비밀번호가 잘못되었습니다. 다시 입력해주세요."
  fi
done

# 기존 덤프 파일 존재 여부 확인
if [ -f "$DUMP_FILE" ]; then
  read -p "⚠️ 기존 덤프 파일이 존재합니다. 새로 생성하시겠습니까? (y/N): " choice
  if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    CREATE_DUMP=true
  else
    CREATE_DUMP=false
  fi
else
  CREATE_DUMP=true
fi

if [ "$CREATE_DUMP" = true ]; then
  echo "🔹 원본 DB에서 덤프 생성 중..."
  PGPASSWORD=$SRC_PASSWORD pg_dump -Fc -h $SRC_HOST -p $SRC_PORT -U $SRC_USER $EXCLUDE_PARAMS $SRC_DB > $DUMP_FILE

  if [ $? -ne 0 ]; then
    echo "❌ 원본 DB에서 덤프 생성 중 오류 발생!"
    exit 1
  fi

  echo "✅ 덤프 생성 완료"
else
  echo "🔄 기존 덤프 파일을 사용합니다."
fi

# 대상 DB 삭제 및 재생성 (존재하지 않을 때 에러 무시)
echo "🔹 기존 대상 DB 확인 중..."

# 대상 DB가 존재하는지 확인
PGPASSWORD=$DEST_PASSWORD psql -h $DEST_HOST -p $DEST_PORT -U $DEST_USER -d postgres -c "SELECT 1 FROM pg_database WHERE datname='$DEST_DB'" | grep -q 1
DB_EXISTS=$?

if [ $DB_EXISTS -eq 0 ]; then
  read -p "⚠️ 데이터베이스 '$DEST_DB'가 이미 존재합니다. 삭제하고 새로 생성하시겠습니까? (Y/n): " drop_choice
  if [[ "$drop_choice" != "n" && "$drop_choice" != "N" ]]; then
    echo "🔹 기존 대상 DB 삭제 중..."
    PGPASSWORD=$DEST_PASSWORD dropdb -h $DEST_HOST -p $DEST_PORT -U $DEST_USER $DEST_DB
    if [ $? -ne 0 ]; then
      echo "❌ 대상 DB 삭제 중 오류 발생!"
      exit 1
    fi
    
    echo "🔹 대상 DB 생성 중..."
    PGPASSWORD=$DEST_PASSWORD createdb -h $DEST_HOST -p $DEST_PORT -U $DEST_USER $DEST_DB
    if [ $? -ne 0 ]; then
      echo "❌ 대상 DB 생성 중 오류 발생!"
      exit 1
    fi
  else
    echo "🔹 기존 대상 DB를 사용합니다."
  fi
else
  echo "🔹 대상 DB 생성 중..."
  PGPASSWORD=$DEST_PASSWORD createdb -h $DEST_HOST -p $DEST_PORT -U $DEST_USER $DEST_DB
  if [ $? -ne 0 ]; then
    echo "❌ 대상 DB 생성 중 오류 발생!"
    exit 1
  fi
fi

# 대상 DB 복원
echo "🔹 대상 DB에 복원 중..."
PGPASSWORD=$DEST_PASSWORD pg_restore -h $DEST_HOST -p $DEST_PORT -U $DEST_USER -d $DEST_DB -v $DUMP_FILE

if [ $? -ne 0 ]; then
  echo "❌ DB 복원 중 오류 발생!"
  exit 1
fi

# 임시 덤프파일 삭제
rm -f $DUMP_FILE

# 완료 메시지
echo "🎉 동기화 작업 완료!"

