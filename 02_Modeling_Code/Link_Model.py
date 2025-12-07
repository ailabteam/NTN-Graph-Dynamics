# 02_Modeling_Code/Link_Model.py

import numpy as np
import networkx as nx
from typing import Dict, Any, List, Tuple
from Propagator import C_LIGHT # Lấy hằng số tốc độ ánh sáng

# --- HẰNG SỐ MÔ HÌNH HÓA STARLINK V1.0 ---
# Tham khảo: Các nghiên cứu về kiến trúc Starlink V1.0 (Altitude ~550km)
MAX_ISL_DISTANCE_KM = 2700.0  # Khoảng cách tối đa cho một Inter-Satellite Link (km)
MAX_ISL_PER_SAT = 4           # Số lượng ISL tối đa cho mỗi vệ tinh (thường là 2 intra-plane, 2 inter-plane)

# --- TRỌNG SỐ CHO BÀI TOÁN TỐI ƯU (ACO/Q-ACO) ---
# Tối ưu hóa đơn mục tiêu (Delay)
# Có thể mở rộng sang Multi-Objective (Delay, Energy, etc.) sau.

class LinkModel:
    def __init__(self, is_multi_objective=False):
        """Khởi tạo mô hình liên kết."""
        self.is_multi_objective = is_multi_objective
    
    def calculate_distance(self, pos1: np.ndarray, pos2: np.ndarray) -> float:
        """Tính toán khoảng cách Euclidean (3D) giữa hai vệ tinh (km)."""
        return np.linalg.norm(pos1 - pos2)

    def calculate_delay(self, distance_km: float) -> float:
        """Tính toán độ trễ truyền dẫn (Propagation Delay) (giây)."""
        # Độ trễ = Khoảng cách / Tốc độ Ánh sáng
        return distance_km / C_LIGHT

    def create_dynamic_graph(self, positions: Dict[int, Dict[str, Any]]) -> nx.Graph:
        """
        Tạo đồ thị G(t) động từ dữ liệu vị trí vệ tinh (ECEF).
        Nodes: Vệ tinh (ID NORAD).
        Edges: ISL và Link Mặt đất (sẽ được thêm sau).
        Weights: Độ trễ (Propagation Delay).
        """
        G = nx.Graph()
        node_data = list(positions.items())
        
        # 1. Thêm các Node
        for sat_id, data in positions.items():
            # Thêm vị trí vào thuộc tính node để dễ dàng tham chiếu
            G.add_node(sat_id, name=data['name'], pos=data['pos_km'])
            
        # 2. Xây dựng các Cạnh (ISL)
        
        # Lặp qua tất cả các cặp vệ tinh (tính toán n*(n-1)/2)
        # Vì 9000 vệ tinh là quá lớn (40 triệu cặp), chúng ta phải dùng heuristic
        # để chỉ kiểm tra các cặp có khả năng gần nhau (dựa trên cấu trúc chòm sao).
        
        # Heuristic đơn giản ban đầu (kiểm tra tất cả): CHỈ ÁP DỤNG CHO SUBSET NHỎ
        # Đối với 9000 vệ tinh, việc lặp toàn bộ là không khả thi về mặt tính toán.
        # Ta cần một cơ chế phân vùng (k-d tree hoặc phân loại theo mặt phẳng/thứ tự).
        
        # --- CHIẾN LƯỢC MÔ HÌNH HÓA ISL HIỆU QUẢ CAO ---
        # Chúng ta giả định rằng dữ liệu TLE được sắp xếp theo mặt phẳng quỹ đạo.
        # Tuy nhiên, điều này không phải lúc nào cũng đúng. 
        # Cách hiệu quả nhất là mô phỏng 4 kết nối chính:
        
        # 2a. Kết nối cùng mặt phẳng (Intra-Plane ISL)
        # Nếu TLE được sắp xếp theo NORAD_CAT_ID (thường gần nhau trong cùng plane)
        
        # Để đảm bảo tính toán nhanh, chúng ta chỉ tập trung vào các kết nối 
        # đã được thiết lập theo cấu trúc chòm sao (nội bộ Starlink).
        
        # VÌ CHÚNG TA KHÔNG CÓ THÔNG TIN MẶT PHẲNG (PLANE ID) TỪ TLE THÔ:
        # Chúng ta phải sử dụng một heuristic đơn giản hơn: Tìm kiếm hàng xóm gần nhất (Nearest Neighbors)
        
        # CHÚ Ý: Vì số lượng vệ tinh là 9000, việc lặp toàn bộ node là quá tốn kém (O(N^2)).
        # Tạm thời, chúng ta sẽ chỉ lặp qua 100 vệ tinh đầu tiên để minh họa logic.
        
        # --- Thực hiện mô phỏng ISL trên một TẬP HỢP GIỚI HẠN (ví dụ: 500 vệ tinh đầu) ---
        nodes_to_process = node_data[:500] 
        
        for i in range(len(nodes_to_process)):
            sat_i_id, sat_i_data = nodes_to_process[i]
            pos_i = sat_i_data['pos_km']
            
            # Khởi tạo danh sách các kết nối tiềm năng cho vệ tinh i
            potential_links = []
            
            for j in range(i + 1, len(nodes_to_process)):
                sat_j_id, sat_j_data = nodes_to_process[j]
                pos_j = sat_j_data['pos_km']
                
                distance = self.calculate_distance(pos_i, pos_j)
                
                if distance <= MAX_ISL_DISTANCE_KM:
                    delay = self.calculate_delay(distance)
                    
                    # Lưu trữ link tiềm năng
                    potential_links.append({
                        'target_id': sat_j_id,
                        'distance': distance,
                        'delay': delay
                    })
            
            # Áp dụng quy tắc MAX_ISL_PER_SAT (Chọn 4 kết nối gần nhất)
            potential_links.sort(key=lambda x: x['distance'])
            
            # Thêm các cạnh (ISL)
            for link in potential_links[:MAX_ISL_PER_SAT]:
                G.add_edge(sat_i_id, link['target_id'], 
                           weight_delay=link['delay'],
                           distance_km=link['distance'],
                           type='ISL')
                           
        # Dọn dẹp: Xóa các node không có kết nối nào (nếu có, thường là các vệ tinh mới phóng)
        isolated_nodes = list(nx.isolates(G))
        G.remove_nodes_from(isolated_nodes)
        
        print(f"Đã tạo đồ thị với {G.number_of_nodes()} node và {G.number_of_edges()} cạnh.")
        return G

# --- Ví dụ minh họa và Tích hợp với Propagator ---

def main_link_model(propagator_script):
    from Propagator import SatellitePropagator # Import Propagator để sử dụng
    
    # Chuẩn bị Propagator (Tải TLE mới nhất)
    DATA_SOURCE_DIR = os.path.join(os.path.dirname(os.getcwd()), '01_Data_Source')
    starlink_files = glob.glob(os.path.join(DATA_SOURCE_DIR, "STARLINK_TLE_*.txt"))
    latest_starlink_file = max(starlink_files, key=os.path.getctime)

    prop = SatellitePropagator(latest_starlink_file)
    
    # Chọn thời điểm mô phỏng
    t_sim = datetime.utcnow()
    
    # 1. Tính toán Vị trí tại t_sim
    positions = prop.get_all_positions(t_sim)
    
    # 2. Khởi tạo và Tạo Đồ thị
    link_model = LinkModel()
    
    # Truyền TẬP HỢP VỊ TRÍ GIỚI HẠN (ví dụ: chỉ 500 vệ tinh đầu) để test
    positions_subset = dict(list(positions.items())[:500])
    
    G_t = link_model.create_dynamic_graph(positions_subset)
    
    # 3. Phân tích Đồ thị (Kiểm tra xem đồ thị có đủ mạnh không)
    print("\n--- PHÂN TÍCH ĐỒ THỊ MẪU ---")
    
    if G_t.number_of_nodes() > 0:
        avg_degree = sum(dict(G_t.degree()).values()) / G_t.number_of_nodes()
        print(f"Bậc (Degree) trung bình: {avg_degree:.2f}")
        
        # Giá trị trung bình của độ trễ
        delays = [G_t.edges[u, v]['weight_delay'] for u, v in G_t.edges]
        print(f"Độ trễ trung bình (Mean Delay): {np.mean(delays)*1000:.3f} ms")
        print(f"Độ trễ tối đa (Max Delay): {np.max(delays)*1000:.3f} ms")
        
        # Kiểm tra tính liên thông
        if nx.is_connected(G_t):
            print("Đồ thị (Subset) Đã liên thông.")
        else:
            print(f"Đồ thị (Subset) Bị phân mảnh thành {nx.number_connected_components(G_t)} thành phần.")
    else:
        print("Đồ thị rỗng. Không có kết nối nào được tạo.")
        
    return G_t

if __name__ == "__main__":
    # CHÚ Ý: Đảm bảo Propagator.py đã được chạy thử nghiệm và không có lỗi
    main_link_model(os.path.join(os.getcwd(), 'Propagator.py'))
