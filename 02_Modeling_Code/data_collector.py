# 02_Modeling_Code/data_collector.py

import requests
import json
import os
from datetime import datetime
import time

# --- Định nghĩa các nguồn dữ liệu và định dạng ---
# Lưu ý: Chúng ta tải cả hai định dạng: TLE (cho Propagator) và JSON (cho Analysis/OMM structure)
DATA_SOURCES = {
    "STARLINK_TLE": {
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=STARLINK&FORMAT=TLE",
        "format": "tle"
    },
    "STARLINK_JSON": {
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=STARLINK&FORMAT=JSON-PRETTY",
        "format": "json"
    },
    "ONEWEB_TLE": {
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=ONEWEB&FORMAT=TLE",
        "format": "tle"
    },
    "STATIONS_TLE": {
        "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=STATIONS&FORMAT=TLE",
        "format": "tle"
    },
    "DECAYING_TLE": {
        "url": "https://celestrak.org/NORAD/elements/gp.php?SPECIAL=DECAYING&FORMAT=TLE",
        "format": "tle"
    }
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), '01_Data_Source')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_and_save_data(source_name, url, file_format):
    """Thực hiện HTTP GET request, tải dữ liệu và lưu lại."""
    print(f"--- Đang tải dữ liệu: {source_name} ({file_format.upper()}) ---")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if file_format == "json":
                data = response.json()
                filename = f"{source_name}_{timestamp}.json"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                
            elif file_format == "tle":
                data = response.text
                filename = f"{source_name}_{timestamp}.txt"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'w') as f:
                    f.write(data)

            print(f"-> Tải thành công. Dữ liệu lưu tại: {filepath}")
            return True
        
        elif response.status_code == 403:
            print(f"LỖI 403: Bị chặn. Vui lòng đợi 2 giờ trước khi thử lại.")
        else:
            print(f"LỖI HTTP {response.status_code}: Không thể tải dữ liệu.")
            print(f"Nội dung phản hồi: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"LỖI KẾT NỐI: {e}")
    except json.JSONDecodeError:
        print("LỖI PHÂN TÍCH JSON: Phản hồi không phải là định dạng JSON hợp lệ.")
        
    return False

def main_downloader():
    print("BẮT ĐẦU TẢI DỮ LIỆU TỪ CELESTRAK...")
    
    for name, params in DATA_SOURCES.items():
        download_and_save_data(name, params['url'], params['format'])
        # Tạm dừng 2 giây giữa các lần tải để tuân thủ quy tắc sử dụng
        time.sleep(2) 
        
    print("\nQuá trình tải dữ liệu hoàn tất.")

if __name__ == "__main__":
    main_downloader()
