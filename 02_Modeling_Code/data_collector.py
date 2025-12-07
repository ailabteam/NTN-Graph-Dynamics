# 02_Modeling_Code/data_collector.py

import requests
import json
import os
from datetime import datetime
import time

# --- Định nghĩa các nguồn dữ liệu ---
DATA_SOURCES = {
    "STARLINK": "https://celestrak.org/NORAD/elements/gp.php?GROUP=STARLINK&FORMAT=JSON-PRETTY",
    "ONEWEB": "https://celestrak.org/NORAD/elements/gp.php?GROUP=ONEWEB&FORMAT=JSON-PRETTY",
    "STATIONS": "https://celestrak.org/NORAD/elements/gp.php?GROUP=STATIONS&FORMAT=JSON-PRETTY",
    "DECAYING": "https://celestrak.org/NORAD/elements/gp.php?SPECIAL=DECAYING&FORMAT=JSON-PRETTY"
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), '01_Data_Source')

# Đảm bảo thư mục output tồn tại
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_and_save_data(source_name, url):
    """Thực hiện HTTP GET request để tải dữ liệu và lưu lại."""
    print(f"--- Đang tải dữ liệu: {source_name} từ {url} ---")
    
    try:
        response = requests.get(url, timeout=30)
        
        # Kiểm tra trạng thái HTTP
        if response.status_code == 200:
            data = response.json()
            
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{source_name}_{timestamp}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"-> Tải thành công. Dữ liệu lưu tại: {filepath}")
            return data
        
        elif response.status_code == 403:
            print(f"LỖI 403: Bị chặn. Vui lòng đợi 2 giờ trước khi thử lại hoặc kiểm tra lại tần suất truy cập.")
        else:
            print(f"LỖI HTTP {response.status_code}: Không thể tải dữ liệu.")
            print(f"Nội dung phản hồi: {response.text[:200]}...") # In 200 ký tự đầu tiên
            
    except requests.exceptions.RequestException as e:
        print(f"LỖI KẾT NỐI: {e}")
    except json.JSONDecodeError:
        print("LỖI PHÂN TÍCH JSON: Phản hồi không phải là định dạng JSON hợp lệ.")

def main_downloader():
    all_downloaded_data = {}
    
    for name, url in DATA_SOURCES.items():
        data = download_and_save_data(name, url)
        if data:
            all_downloaded_data[name] = data
        
        # Tạm dừng 1 giây giữa các lần tải để thân thiện với server CelesTrak
        time.sleep(1) 
        
    print("\nQuá trình tải dữ liệu hoàn tất.")
    return all_downloaded_data

if __name__ == "__main__":
    main_downloader()
