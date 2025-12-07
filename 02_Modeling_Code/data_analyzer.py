# 02_Modeling_Code/data_analyzer.py

import json
import os
import glob
import pandas as pd

# Đường dẫn tới thư mục dữ liệu nguồn
DATA_SOURCE_DIR = os.path.join(os.path.dirname(os.getcwd()), '01_Data_Source')

def find_latest_file(group_name):
    """Tìm file JSON mới nhất cho một nhóm cụ thể."""
    pattern = os.path.join(DATA_SOURCE_DIR, f"{group_name}_*.json")
    list_of_files = glob.glob(pattern)
    if not list_of_files:
        print(f"Không tìm thấy file nào cho nhóm: {group_name}")
        return None
    # Sắp xếp theo tên (timestamp) và lấy file mới nhất
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def analyze_omm_structure(filepath):
    """Đọc và phân tích cấu trúc của file OMM JSON."""
    if not filepath:
        return
        
    print(f"\n=======================================================")
    print(f"ĐANG PHÂN TÍCH CẤU TRÚC: {os.path.basename(filepath)}")
    print(f"=======================================================")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    if not data:
        print("File JSON rỗng hoặc không hợp lệ.")
        return

    # Lấy mẫu một vệ tinh (element)
    sample_element = data[0]
    
    print(f"Tổng số phần tử (vệ tinh): {len(data)}")
    print("\n--- CÁC TRƯỜNG DỮ LIỆU CHÍNH (KEY) TRONG OMM ---")
    
    # Hiển thị các key của phần tử mẫu
    for key in sample_element.keys():
        print(f"  - {key}")

    print("\n--- PHÂN TÍCH CÁC TRƯỜNG DỮ LIỆU QUỸ ĐẠO (SGP4 INPUTS) ---")
    
    # Các trường quan trọng cho SGP4 (dùng để tính toán vị trí 3D):
    omm_keys_for_sgp4 = [
        "OBJECT_NAME", "OBJECT_ID", "EPOCH", "MEAN_MOTION", 
        "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE", 
        "ARG_OF_PERICENTER", "MEAN_ANOMALY", "BSTAR", 
        "CATALOG_NUMBER"
    ]
    
    for key in omm_keys_for_sgp4:
        if key in sample_element:
            print(f"  {key:<20}: {sample_element[key]}")
        else:
            print(f"  {key:<20}: [KHÔNG TÌM THẤY]")

    # Chuyển sang DataFrame để phân tích thống kê cơ bản
    df = pd.DataFrame(data)
    
    if "MEAN_MOTION" in df.columns:
        print("\n--- THỐNG KÊ CƠ BẢN (MEAN_MOTION - Tốc độ) ---")
        print(df['MEAN_MOTION'].describe())

    if "INCLINATION" in df.columns:
        print("\n--- THỐNG KÊ CƠ BẢN (INCLINATION - Góc nghiêng) ---")
        print(df['INCLINATION'].describe())

if __name__ == "__main__":
    # Phân tích Starlink (chòm sao cốt lõi)
    starlink_file = find_latest_file("STARLINK")
    analyze_omm_structure(starlink_file)
    
    # Phân tích các node đặc biệt (trạm)
    stations_file = find_latest_file("STATIONS")
    analyze_omm_structure(stations_file)
