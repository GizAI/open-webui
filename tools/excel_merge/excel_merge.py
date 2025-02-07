import os
import pandas as pd

def merge_excel_files(output_file="merged.xlsx"):
    # 현재 폴더의 모든 엑셀 파일 목록 가져오기
    excel_files = [file for file in os.listdir() if file.endswith(".xlsx") or file.endswith(".xls")]
    
    if not excel_files:
        print("엑셀 파일이 없습니다.")
        return
    
    merged_data = []
    header = None
    total_rows = 0
    
    for file in excel_files:
        try:
            # 첫 번째 시트 읽기 (모든 값을 문자열로 변환)
            df = pd.read_excel(file, sheet_name=0, dtype=str)
            
            if header is None:
                header = df.iloc[0].tolist()  # 첫 번째 파일의 헤더 저장
            
            # 첫 번째 행(헤더) 제외하고 데이터 추가
            df = df.iloc[1:]
            merged_data.append(df)
            total_rows += len(df)
            print(f"{file} 파일 추가 완료 (행 개수: {len(df)})")
        except Exception as e:
            print(f"{file} 파일 처리 중 오류 발생: {e}")
    
    if merged_data:
        # 모든 데이터프레임 병합 (빈 데이터프레임 제외)
        merged_data = [df for df in merged_data if not df.empty]
        if merged_data:
            merged_df = pd.concat(merged_data, ignore_index=True)
            # 첫 번째 파일의 헤더 추가
            merged_df.columns = header
            # 병합된 데이터 저장
            merged_df.to_excel(output_file, index=False)
            print(f"모든 엑셀 파일이 {output_file} 파일로 병합되었습니다. (총 행 개수: {len(merged_df)})")
            # 데이터 검증
            if len(merged_df) == total_rows:
                print("모든 데이터가 정상적으로 병합되었습니다.")
            else:
                print(f"경고: 예상 행 개수({total_rows})와 실제 병합된 행 개수({len(merged_df)})가 일치하지 않습니다.")
        else:
            print("병합할 데이터가 없습니다.")
    else:
        print("병합할 데이터가 없습니다.")

if __name__ == "__main__":
    merge_excel_files()
