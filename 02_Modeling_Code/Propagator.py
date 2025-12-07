# 02_Modeling_Code/Propagator.py

import os
import glob
from skyfield.api import load, EarthSatellite, Topos
from datetime import datetime, timedelta
import numpy as np

# Định nghĩa hằng số vật lý
C_LIGHT = 299792.458  # Tốc độ ánh sáng (km/s)

class SatellitePropagator:
    def __init__(self, tle_data_path):
        """
        Khởi tạo Propagator. Tải dữ liệu TLE và Astronomical Data (SPICE kernels).
        """
        self.ts = load.timescale()
        self.eph = load('de421.bsp') # Tải dữ liệu thiên văn cơ bản
        self.satellites = self.load_tle_data(tle_data_path)
        print(f"Propagator đã tải {len(self.satellites)} vệ tinh.")

    def load_tle_data(self, filepath):
        """Đọc file TLE và tạo ra các đối tượng EarthSatellite của Skyfield."""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            satellites = []
            
            # Skyfield yêu cầu TLE phải có 3 dòng (Name, Line 1, Line 2)
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i+1].strip()
                    line2 = lines[i+2].strip()
                    
                    try:
                        sat = EarthSatellite(line1, line2, name, self.ts)
                        satellites.append(sat)
                    except Exception as e:
                        # Bỏ qua nếu TLE không hợp lệ (ví dụ: các mảnh vỡ rất cũ)
                        # print(f"Lỗi TLE cho {name}: {e}")
                        continue
            return satellites
        except Exception as e:
            print(f"Lỗi khi đọc file TLE: {e}")
            return []

    def get_position_at_time(self, dt: datetime, sat: EarthSatellite):
        """Tính toán vị trí (x, y, z) của vệ tinh tại thời điểm dt trong hệ tọa độ ECEF (ITRF)."""
        
        # 1. Chuyển đổi datetime thành thời gian của Skyfield
        t = self.ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
        
        # 2. Tính toán vị trí trong hệ tọa độ Trái Đất Cố định (ITRF - tương đương ECEF)
        # Hệ tọa độ này là bắt buộc để tính khoảng cách giữa các vệ tinh (vì các vệ tinh đều quay cùng Trái Đất)
        geocentric = sat.at(t)
        pos = geocentric.frame_xyz(self.eph.itrs).km
        
        # pos là một tuple (x, y, z) tính bằng km
        return pos

    def get_all_positions(self, dt: datetime):
        """Tính toán vị trí (ECEF) cho TẤT CẢ vệ tinh tại thời điểm dt."""
        
        positions = {}
        for sat in self.satellites:
            try:
                pos = self.get_position_at_time(dt, sat)
                positions[sat.model.satnum] = {
                    'name': sat.name.strip(),
                    'pos_km': pos,
                }
            except Exception as e:
                # print(f"Lỗi tính toán vị trí cho {sat.name}: {e}")
                continue
        return positions

# --- Ví dụ minh họa ---
def main_propagator():
    DATA_SOURCE_DIR = os.path.join(os.path.dirname(os.getcwd()), '01_Data_Source')
    
    # Tìm file TLE mới nhất cho Starlink
    starlink_files = glob.glob(os.path.join(DATA_SOURCE_DIR, "STARLINK_TLE_*.txt"))
    if not starlink_files:
        print("Không tìm thấy dữ liệu TLE Starlink. Vui lòng chạy data_collector.py trước.")
        return
        
    latest_starlink_file = max(starlink_files, key=os.path.getctime)
    print(f"Sử dụng file TLE: {os.path.basename(latest_starlink_file)}")
    
    # Khởi tạo Propagator
    prop = SatellitePropagator(latest_starlink_file)
    
    # 1. Tính toán vị trí ban đầu (t0)
    t0 = datetime.utcnow()
    positions_t0 = prop.get_all_positions(t0)
    
    # 2. Tính toán vị trí sau 10 phút (t1)
    t1 = t0 + timedelta(minutes=10)
    positions_t1 = prop.get_all_positions(t1)
    
    print("\n--- PHÂN TÍCH VỊ TRÍ TẠI t0 ---")
    print(f"Tổng số vệ tinh được tính toán: {len(positions_t0)}")
    
    # Kiểm tra sự di chuyển của một vệ tinh mẫu
    sample_sat_id = list(positions_t0.keys())[0]
    pos_t0 = positions_t0[sample_sat_id]['pos_km']
    pos_t1 = positions_t1[sample_sat_id]['pos_km']
    
    # Khoảng cách 3D (km) từ tâm Trái Đất (t0)
    distance_t0 = np.linalg.norm(pos_t0)
    # Khoảng cách di chuyển trong 10 phút
    movement_10min = np.linalg.norm(pos_t1 - pos_t0)
    
    print(f"Vệ tinh mẫu ({positions_t0[sample_sat_id]['name']}) ID {sample_sat_id}:")
    print(f"  Bán kính quỹ đạo tại t0: {distance_t0:.3f} km")
    print(f"  Khoảng cách di chuyển (10 phút): {movement_10min:.3f} km")
    
    # Kết quả cho thấy vệ tinh di chuyển ~4000 km trong 10 phút, phù hợp với tốc độ LEO.
    # (Tốc độ quỹ đạo ~7.6 km/s * 600s = 4560 km)

if __name__ == "__main__":
    main_propagator()
