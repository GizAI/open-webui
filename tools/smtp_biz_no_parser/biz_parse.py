import csv
import requests
import urllib.parse
import pandas as pd
import os

def read_csv(file_path):
    """CSV 파일을 읽고 데이터를 반환"""
    try:
        df = pd.read_csv(file_path)
        print(f"✅ CSV 파일 '{file_path}' 읽기 성공. {len(df)}개의 행을 처리합니다.")
        return df
    except Exception as e:
        print(f"❌ CSV 파일 읽기 오류: {e}")
        return None

def fetch_biz_no(company_name, representative):
    """API 요청을 보내고 bizNo 값을 가져옴"""
    encoded_name = urllib.parse.quote_plus(company_name)
    encoded_rep = urllib.parse.quote_plus(representative)
    url = f"https://moneypin.biz/_next/data/imM_mxtlXIpyPTEtKhxCX/ko/bizno.json?name={encoded_name}+{encoded_rep}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ 요청 실패: HTTP {response.status_code}. 실행을 중지합니다.")
            exit(1)
        
        response.raise_for_status()  # HTTP 오류가 있으면 예외 발생
        data = response.json()
        
        if "pageProps" in data:
            if "status" in data["pageProps"] and data["pageProps"]["status"] != 200:
                print(f"❌ 요청 실패: API 응답 상태 코드 {data['pageProps']['status']}. 실행을 중지합니다.")
                exit(1)
        
        if "defaultData" in data["pageProps"] and data["pageProps"]["defaultData"]:
            biz_no = data["pageProps"]["defaultData"][0]["bizNo"]
            print(f"🔹 {company_name} ({representative}) -> 사업자번호: {biz_no}")
            return biz_no
        else:
            print(f"⚠️ {company_name} ({representative})의 사업자번호를 찾을 수 없음.")
            return ""  # 사업자 번호가 없을 경우 빈 문자열 반환
    except requests.RequestException as e:
        print(f"❌ 요청 실패 ({company_name}, {representative}): {e}")
        exit(1)

def process_csv(input_file, output_file, limit=10):
    """CSV를 처리하여 새로운 CSV 파일로 저장, 중단 시 마지막 기록된 행 이후부터 이어서 실행"""
    df = read_csv(input_file)
    if df is None:
        return
    
    if "company_name" not in df.columns or "representative" not in df.columns:
        print("❌ CSV 파일에 'company_name' 또는 'representative' 컬럼이 없습니다.")
        return
    
    # 기존 처리된 데이터 확인
    if os.path.exists(output_file):
        processed_df = pd.read_csv(output_file)
        processed_entries = set(zip(processed_df["company_name"].astype(str), processed_df["representative"].astype(str)))
    else:
        processed_entries = set()
    
    # 아직 처리되지 않은 데이터 필터링
    df = df[~df.apply(lambda row: (str(row["company_name"]), str(row["representative"])) in processed_entries, axis=1)].head(limit)
    
    if df.empty:
        print("✅ 모든 데이터가 처리되었습니다.")
        return
    
    df["biz_no"] = df.apply(lambda row: fetch_biz_no(str(row["company_name"]), str(row["representative"])), axis=1)
    
    # 기존 파일이 있으면 이어서 저장, 없으면 새로 생성
    df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)
    print(f"✅ 새로운 CSV 파일이 저장되었습니다: {output_file}")

# 실행
if __name__ == "__main__":
    input_csv = "smtp_update_20250207.csv"  # CSV 파일 경로 onedrive 에 업로드 되어 있음
    output_csv = "smtp_update_with_bizno.csv"  # 새로운 CSV 파일 경로
    process_csv(input_csv, output_csv, limit=10)
