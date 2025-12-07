# 02_Modeling_Code/Graph_Generator.py

import yaml
import os
import glob
from datetime import datetime, timedelta
import networkx as nx

# Import các module đã xây dựng
from Propagator import SatellitePropagator, R_EARTH
from Link_Model import LinkModel
from skyfield.api import Topos # Cần cho việc mô hình hóa trạm mặt đất

# --- THIẾT LẬP ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.getcwd())
DATA_SOURCE_DIR = os.path.join(BASE_DIR, '01_Data_Source')
SCENARIOS_DIR = os.path.join(BASE_DIR, '03_Scenarios')
OUTPUT_DATASET_DIR = os.path.join(BASE_DIR, '04_Output_Dataset')
os.makedirs(OUTPUT_DATASET_DIR, exist_ok=True)

class DynamicGraphGenerator:
    def __init__(self, config_path):
        """Khởi tạo Generator bằng file cấu hình kịch bản."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.scenario_name = self.config['SCENARIO_NAME']
        print(f"Khởi tạo Generator cho kịch bản: {self.scenario_name}")
        
        # 1. Tải dữ liệu TLE cho vệ tinh (Mạng lưới chính)
        tle_pattern = f"{self.config['CONSTELLATION']}_TLE_*.txt"
        latest_tle = self._find_latest_file(tle_pattern)
        self.sat_propagator = SatellitePropagator(latest_tle)
        
        # Lấy subset vệ tinh theo cấu hình
        self.satellites = self.sat_propagator.satellites[:self.config['SUBSET_SIZE']]
        
        # 2. Tải dữ liệu TLE cho Trạm Mặt đất (nếu cần)
        self.ground_stations = []
        if self.config['INCLUDE_GROUND_NODES']:
            gs_tle_pattern = f"{self.config['GS_LOCATION_FILE']}_*.txt"
            latest_gs_tle = self._find_latest_file(gs_tle_pattern)
            gs_prop = SatellitePropagator(latest_gs_tle)
            self.ground_stations = gs_prop.satellites
        
        # 3. Khởi tạo Link Model
        self.link_model = LinkModel(is_multi_objective=(self.config['OBJECTIVE'] == 'MULTI'))
        
        # 4. Thiết lập thời gian
        self.start_time = datetime.fromisoformat(self.config['START_TIME'].replace('Z', '+00:00'))
        self.duration = timedelta(minutes=self.config['DURATION_MINUTES'])
        self.time_step = timedelta(seconds=self.config['TIME_STEP_SECONDS'])
        
    def _find_latest_file(self, pattern):
        """Hàm helper tìm file mới nhất trong thư mục dữ liệu."""
        full_pattern = os.path.join(DATA_SOURCE_DIR, pattern)
        list_of_files = glob.glob(full_pattern)
        if not list_of_files:
             raise FileNotFoundError(f"Không tìm thấy file nào khớp với pattern: {pattern}")
        return max(list_of_files, key=os.path.getctime)

    def generate_graphs(self):
        """Chạy mô phỏng theo thời gian và tạo chuỗi đồ thị."""
        current_time = self.start_time
        end_time = self.start_time + self.duration
        step_count = 0
        
        graphs_sequence = []
        
        while current_time <= end_time:
            print(f"\n[{current_time.isoformat()}] Bắt đầu tính toán snapshot {step_count}...")
            
            # 1. Tính toán vị trí của tất cả node (Satellites + GS)
            
            # 1a. Vị trí Vệ tinh (sử dụng Propagator)
            sat_positions = {}
            for sat in self.satellites:
                try:
                    # Lấy vị trí ECEF (ITRF)
                    pos = self.sat_propagator.get_position_at_time(current_time, sat)
                    sat_positions[sat.model.satnum] = {
                        'name': sat.name.strip(),
                        'pos_km': pos
                    }
                except Exception:
                    continue
            
            # 1b. Thêm vị trí Trạm Mặt đất (GS) 
            # (Chúng ta sẽ đơn giản hóa bằng cách sử dụng các vệ tinh trong GS_LOCATION_FILE làm 'trạm mặt đất' 
            # để có tọa độ ban đầu. Trong thực tế, GS là cố định trên mặt đất.)
            
            # CHÚ Ý: ĐỂ ĐƠN GIẢN VÀ TEST LOGIC: Ta dùng các vệ tinh GS_LOCATION_FILE làm các node đặc biệt 
            # (ví dụ: các vệ tinh relay ở quỹ đạo cao hơn)
            # Nếu muốn mô phỏng GS thực, cần định nghĩa tọa độ Latitude/Longitude cố định.
            
            # Tạm thời: Ta chỉ tập trung vào ISL để kiểm tra ACO/Q-ACO trên mạng động lớn.
            
            # 2. Tạo Đồ thị G(t)
            G_t = self.link_model.create_dynamic_graph(sat_positions)
            G_t.graph['time_step'] = step_count
            G_t.graph['timestamp'] = current_time.isoformat()
            
            # 3. Lưu trữ Đồ thị (Sử dụng GEXF hoặc JSON/CSV để dễ dàng public)
            
            # Định dạng file GEXF là tốt cho các công cụ trực quan hóa
            # Định dạng file JSON là tốt cho việc đọc bằng code
            filename = f"{self.scenario_name}_T{step_count:03d}.gexf"
            filepath = os.path.join(OUTPUT_DATASET_DIR, filename)
            
            # networkx có thể export GEXF
            nx.write_gexf(G_t, filepath)
            
            graphs_sequence.append(G_t)
            
            # 4. Tăng thời gian
            current_time += self.time_step
            step_count += 1
            
        print(f"\n--- HOÀN TẤT TẠO DATASET ---")
        print(f"Đã tạo {step_count} snapshot đồ thị trong {self.config['DURATION_MINUTES']} phút.")
        return graphs_sequence

# --- Hàm chạy chính ---
def main_generator():
    # Đảm bảo file cấu hình tồn tại
    config_path = os.path.join(SCENARIOS_DIR, 'Starlink_V1_Normal.yaml')
    if not os.path.exists(config_path):
        print(f"Lỗi: File cấu hình không tồn tại tại {config_path}")
        return

    # Khởi chạy quá trình tạo Dataset
    generator = DynamicGraphGenerator(config_path)
    graphs = generator.generate_graphs()
    
    # Kiểm tra đồ thị mẫu đầu tiên
    if graphs:
        G0 = graphs[0]
        print(f"\nPhân tích đồ thị đầu tiên (T=0):")
        print(f"  Nodes: {G0.number_of_nodes()}, Edges: {G0.number_of_edges()}")

if __name__ == "__main__":
    main_generator()
