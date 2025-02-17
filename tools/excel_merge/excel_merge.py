import os
import pandas as pd
import csv

def merge_excel_to_csv(root_dir='.'):
    all_data = []            # 각 파일의 DataFrame을 저장할 리스트
    total_excel_rows = 0     # 모든 엑셀 파일의 데이터 행 수 누적
    file_count = 0           # 처리한 엑셀 파일 수

    # 현재 폴더 및 하위 폴더의 모든 파일 순회
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.xlsx', '.xls')):
                file_path = os.path.join(dirpath, filename)
                file_count += 1
                print(f"Processing file: {file_path}")
                
                try:
                    # 첫 번째 시트만 읽음 (첫 행은 header)
                    df = pd.read_excel(file_path, sheet_name=0, dtype=str)
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")
                    continue

                # 엑셀 데이터의 행 수 (header는 제외됨)
                num_rows = df.shape[0]
                total_excel_rows += num_rows

                # company_type 컬럼: 파일명에 "개인"이 있으면 "개인", 아니면 빈 문자열
                company_type = "개인" if "개인" in filename else ""
                df["company_type"] = company_type

                # file_name 컬럼: 해당 엑셀 파일의 전체 경로
                df["file_name"] = file_path

                all_data.append(df)

    if not all_data:
        print("No Excel files found.")
        return

    # 모든 데이터 병합
    merged_df = pd.concat(all_data, ignore_index=True)

    # 행 수 검증: 각 파일의 데이터 행 수 총합과 최종 병합 데이터 행 수 비교
    merged_rows = merged_df.shape[0]
    if merged_rows != total_excel_rows:
        print(f"Row count mismatch! Total Excel rows: {total_excel_rows}, Merged CSV rows: {merged_rows}")
    else:
        print(f"Row count validation passed: {merged_rows} rows merged from {file_count} Excel files.")

    # CSV 저장: 모든 필드를 더블 쿼테이션 처리 ("")
    output_csv = "merged_output.csv"
    merged_df.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8-sig')
    print(f"CSV file '{output_csv}' created successfully.")

if __name__ == "__main__":
    merge_excel_to_csv('.')
