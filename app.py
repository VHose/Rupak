# app.py
import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations
from algoritma import CourierRouteSimulator

# 1. Page Configuration
st.set_page_config(
    page_title="Simulasi Rute Kurir Paket Optimal",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Premium Theme Styles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Custom button style */
.stButton>button {
    background: linear-gradient(135deg, #00C853 0%, #00E676 100%);
    color: white;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    padding: 10px 24px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 230, 118, 0.2);
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 230, 118, 0.4);
    background: linear-gradient(135deg, #00E676 0%, #00C853 100%);
}

.demo-btn>button {
    background: linear-gradient(135deg, #374151 0%, #111827 100%) !important;
    border: 1px solid #4B5563 !important;
    color: #F3F4F6 !important;
    box-shadow: none !important;
}

.demo-btn>button:hover {
    background: linear-gradient(135deg, #4B5563 0%, #1F2937 100%) !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
}

/* Metric Cards */
.metric-container {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    margin-bottom: 25px;
    width: 100%;
}

.metric-card {
    flex: 1;
    background: rgba(128, 128, 128, 0.08);
    border: 1px solid rgba(128, 128, 128, 0.15);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
    backdrop-filter: blur(8px);
}

.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #00E676;
    margin-bottom: 5px;
}

.metric-value-accent {
    color: #3B82F6;
}

.metric-value-warn {
    color: #EF4444;
}

.metric-label {
    font-size: 0.95rem;
    color: #8892B0;
    font-weight: 500;
}

/* Timeline Styles */
.timeline {
    position: relative;
    padding: 20px 0;
    margin: 20px 0;
}
.timeline::before {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #3B82F6 0%, #10B981 100%);
    left: 20px;
    border-radius: 2px;
}
.timeline-item {
    position: relative;
    padding-left: 55px;
    margin-bottom: 30px;
}
.timeline-item:last-child {
    margin-bottom: 0;
}
.timeline-badge {
    position: absolute;
    left: 6px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #0F172A;
    border: 4px solid #10B981;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 0.8rem;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}
.timeline-badge.start {
    border-color: #3B82F6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
}
.timeline-card {
    background: rgba(128, 128, 128, 0.05);
    border: 1px solid rgba(128, 128, 128, 0.12);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
}
.timeline-title {
    font-weight: 600;
    font-size: 1.15rem;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.timeline-meta {
    font-size: 0.88rem;
    color: #64748B;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-top: 8px;
}
.timeline-meta span {
    background: rgba(128, 128, 128, 0.1);
    padding: 3px 10px;
    border-radius: 20px;
}
.tag-priority {
    font-weight: 600;
    color: #F59E0B;
}
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if 'nodes' not in st.session_state:
    st.session_state.nodes = ['Depot', 'Jakarta', 'Bandung', 'Bekasi', 'Bogor']
if 'kecepatan' not in st.session_state:
    st.session_state.kecepatan = 60
if 'kapasitas' not in st.session_state:
    st.session_state.kapasitas = 80
if 'paket_data' not in st.session_state:
    st.session_state.paket_data = {
        'volume': {'Depot': 0, 'Jakarta': 30, 'Bandung': 25, 'Bekasi': 20, 'Bogor': 15},
        'prioritas': {'Depot': 0, 'Jakarta': 3, 'Bandung': 2, 'Bekasi': 1, 'Bogor': 3},
        'deadline': {'Depot': 0.0, 'Jakarta': 2.5, 'Bandung': 4.0, 'Bekasi': 1.5, 'Bogor': 3.0}
    }
if 'jarak_matrix' not in st.session_state:
    st.session_state.jarak_matrix = [
        [0, 40, 150, 20, 60],
        [40, 0, 130, 30, 50],
        [150, 130, 0, 120, 100],
        [20, 30, 120, 0, 80],
        [60, 50, 100, 80, 0]
    ]
if 'start_node' not in st.session_state:
    st.session_state.start_node = 'Depot'
if 'results' not in st.session_state:
    st.session_state.results = None

# Helper to sync nodes additions/deletions
def update_nodes(new_nodes):
    old_nodes = st.session_state.nodes
    if old_nodes == new_nodes:
        return
    
    # Update package info maps
    for node in new_nodes:
        if node not in old_nodes:
            st.session_state.paket_data['volume'][node] = 0
            st.session_state.paket_data['prioritas'][node] = 1
            st.session_state.paket_data['deadline'][node] = 1.0
            
    for node in list(st.session_state.paket_data['volume'].keys()):
        if node not in new_nodes:
            st.session_state.paket_data['volume'].pop(node, None)
            st.session_state.paket_data['prioritas'].pop(node, None)
            st.session_state.paket_data['deadline'].pop(node, None)
            
    # Update distance matrix dimensions
    n = len(new_nodes)
    new_matrix = [[0] * n for _ in range(n)]
    for i, u in enumerate(new_nodes):
        for j, v in enumerate(new_nodes):
            if u in old_nodes and v in old_nodes:
                old_i = old_nodes.index(u)
                old_j = old_nodes.index(v)
                new_matrix[i][j] = st.session_state.jarak_matrix[old_i][old_j]
            else:
                new_matrix[i][j] = 0 if u == v else -1
                
    st.session_state.nodes = new_nodes
    st.session_state.jarak_matrix = new_matrix
    if st.session_state.start_node not in new_nodes:
        st.session_state.start_node = new_nodes[0] if new_nodes else None

# Helper to load demo data
def muat_demo():
    st.session_state.nodes = ['Depot', 'Jakarta', 'Bandung', 'Bekasi', 'Bogor']
    st.session_state.kecepatan = 60
    st.session_state.kapasitas = 80
    st.session_state.paket_data = {
        'volume': {'Depot': 0, 'Jakarta': 30, 'Bandung': 25, 'Bekasi': 20, 'Bogor': 15},
        'prioritas': {'Depot': 0, 'Jakarta': 3, 'Bandung': 2, 'Bekasi': 1, 'Bogor': 3},
        'deadline': {'Depot': 0.0, 'Jakarta': 2.5, 'Bandung': 4.0, 'Bekasi': 1.5, 'Bogor': 3.0}
    }
    st.session_state.jarak_matrix = [
        [0, 40, 150, 20, 60],
        [40, 0, 130, 30, 50],
        [150, 130, 0, 120, 100],
        [20, 30, 120, 0, 80],
        [60, 50, 100, 80, 0]
    ]
    st.session_state.start_node = 'Depot'
    st.session_state.results = None

# Helper to generate Graphviz code
def generate_graphviz(nodes, jarak, route=None):
    dot = "digraph G {\n"
    dot += '  graph [bgcolor="transparent", pad="0.3", nodesep="0.4", ranksep="0.4"];\n'
    dot += '  node [fontname="Outfit", shape=circle, style="filled", fillcolor="#1E293B", color="#334155", fontcolor="#F8FAFC", width=0.8, fixedsize=true, fontsize=10];\n'
    dot += '  edge [fontname="Outfit", fontsize=9, color="#475569", fontcolor="#94A3B8"];\n'
    
    path_edges = set()
    if route:
        for idx in range(len(route) - 1):
            u, v = route[idx], route[idx+1]
            path_edges.add((u, v))
            path_edges.add((v, u))
            
    # Nodes styling
    for n in nodes:
        if route and n == route[0]:
            dot += f'  "{n}" [fillcolor="#1E3A8A", color="#3B82F6", fontcolor="#FFFFFF", penwidth=2, label="{n}\\n(Asal)"];\n'
        elif route and n in route:
            dot += f'  "{n}" [fillcolor="#064E3B", color="#059669", fontcolor="#FFFFFF", penwidth=1.5];\n'
        else:
            dot += f'  "{n}";\n'
            
    # Draw connections
    n_nodes = len(nodes)
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            dist = jarak[i][j]
            if dist > 0:
                u, v = nodes[i], nodes[j]
                if (u, v) in path_edges or (v, u) in path_edges:
                    # Highlight edges in calculated route
                    dot += f'  "{u}" -> "{v}" [dir=none, label="{dist} km", color="#10B981", penwidth=3.5, fontcolor="#10B981"];\n'
                else:
                    dot += f'  "{u}" -> "{v}" [dir=none, label="{dist} km", style="dashed"];\n'
                    
    dot += "}"
    return dot

# 4. App Header
st.title("Simulasi Rute Kurir Paket Optimal 🚚")
st.markdown("Optimalkan urutan pengiriman paket berdasarkan **Algoritma Dijkstra** & **Greedy Heuristics** (Kapasitas, Batas Waktu, dan Prioritas).")

# 5. Sidebar - Parameters Configuration
st.sidebar.header("🛠️ Pengaturan Utama")

# Manage Nodes list
nodes_input_str = st.sidebar.text_area(
    "Daftar Node (pisahkan dengan koma)",
    value=", ".join(st.session_state.nodes),
    help="Ubah nama node atau tambahkan node baru secara langsung di sini."
)
parsed_nodes = [n.strip() for n in nodes_input_str.split(",") if n.strip()]
if parsed_nodes != st.session_state.nodes:
    update_nodes(parsed_nodes)

# Vehicle Settings
st.sidebar.subheader("🚚 Pengaturan Truk")
st.session_state.kapasitas = st.sidebar.number_input(
    "Kapasitas Maksimal (kg)",
    min_value=10,
    max_value=500,
    value=st.session_state.kapasitas,
    step=10
)
st.session_state.kecepatan = st.sidebar.number_input(
    "Kecepatan Rata-rata (km/jam)",
    min_value=10,
    max_value=150,
    value=st.session_state.kecepatan,
    step=5
)

# Start Node Selector
if st.session_state.nodes:
    current_start_idx = 0
    if st.session_state.start_node in st.session_state.nodes:
        current_start_idx = st.session_state.nodes.index(st.session_state.start_node)
        
    st.session_state.start_node = st.sidebar.selectbox(
        "Posisi Awal Kurir (Depot/Asal)",
        options=st.session_state.nodes,
        index=current_start_idx
    )

st.sidebar.markdown("---")

# Demo Button
col_demo = st.sidebar.container()
with col_demo:
    st.markdown('<div class="demo-btn">', unsafe_allow_html=True)
    if st.button("Muat Data Demo 📦", use_container_width=True):
        muat_demo()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Run Simulation Button
if st.sidebar.button("🚀 Mulai Pengiriman", use_container_width=True):
    # Verify nodes
    if len(st.session_state.nodes) < 2:
        st.sidebar.error("Masukkan minimal 2 node untuk memulai simulasi.")
    else:
        # Prepare inputs
        prioritas_list = [st.session_state.paket_data['prioritas'].get(node, 1) for node in st.session_state.nodes]
        deadline_list = [st.session_state.paket_data['deadline'].get(node, 1.0) for node in st.session_state.nodes]
        volume_list = [st.session_state.paket_data['volume'].get(node, 0) for node in st.session_state.nodes]
        
        # Instantiate simulator
        simulator = CourierRouteSimulator(
            node=st.session_state.nodes,
            jarak=st.session_state.jarak_matrix,
            kecepatan=st.session_state.kecepatan,
            kapasitas=st.session_state.kapasitas,
            prioritas=prioritas_list,
            deadline=deadline_list,
            volume=volume_list
        )
        
        try:
            st.session_state.results = simulator.jalankan_simulasi(st.session_state.start_node)
            st.toast("Simulasi berhasil dijalankan!", icon="🎉")
        except Exception as e:
            st.sidebar.error(f"Error dalam simulasi: {e}")

# 6. Main Panel Layout
tab1, tab2 = st.tabs(["⚙️ Pengaturan Data & Jaringan", "📊 Hasil Simulasi & Analisis"])

# --- TAB 1: Inputs and Connections ---
with tab1:
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Package Information
        st.subheader("📦 Informasi Paket pada Setiap Node")
        st.markdown("Isikan spesifikasi paket yang akan dituju untuk setiap node. Volume paket *Start Node* secara otomatis bernilai 0.")
        
        # Build DataFrame
        package_rows = []
        for n in st.session_state.nodes:
            is_start = (n == st.session_state.start_node)
            package_rows.append({
                "Node": n,
                "Tipe": "🚩 Start Node (Asal)" if is_start else "📦 Penerima Paket",
                "Berat Paket (kg)": 0 if is_start else st.session_state.paket_data['volume'].get(n, 10),
                "Prioritas (1-3)": 0 if is_start else st.session_state.paket_data['prioritas'].get(n, 1),
                "Deadline Paket (Jam)": 0.0 if is_start else st.session_state.paket_data['deadline'].get(n, 1.0)
            })
            
        df_packages = pd.DataFrame(package_rows)
        
        # Display data editor
        edited_df = st.data_editor(
            df_packages,
            disabled=["Node", "Tipe"],
            column_config={
                "Berat Paket (kg)": st.column_config.NumberColumn(min_value=0, max_value=st.session_state.kapasitas, step=1),
                "Prioritas (1-3)": st.column_config.NumberColumn(min_value=1, max_value=3, step=1, help="1: Rendah, 2: Sedang, 3: Tinggi"),
                "Deadline Paket (Jam)": st.column_config.NumberColumn(min_value=0.1, max_value=48.0, step=0.5, format="%.1f jam")
            },
            use_container_width=True,
            key="package_editor"
        )
        
        # Save edits back to session state
        for _, row in edited_df.iterrows():
            node = row["Node"]
            if node == st.session_state.start_node:
                st.session_state.paket_data['volume'][node] = 0
                st.session_state.paket_data['prioritas'][node] = 0
                st.session_state.paket_data['deadline'][node] = 0.0
            else:
                st.session_state.paket_data['volume'][node] = int(row["Volume Paket (m³)"])
                st.session_state.paket_data['prioritas'][node] = int(row["Prioritas (1-3)"])
                st.session_state.paket_data['deadline'][node] = float(row["Deadline Paket (Jam)"])
                
    with col_right:
        # Distance Grid
        st.subheader("🛣️ Jarak Hubungan Node (km)")
        st.markdown("Tentukan jarak antar node. Nilai `-1` menandakan node **tidak terhubung langsung**.")
        
        nodes = st.session_state.nodes
        n_nodes = len(nodes)
        
        if n_nodes < 2:
            st.warning("Masukkan minimal 2 node untuk mengatur konektivitas.")
        else:
            with st.expander("Klik untuk Mengedit Jarak Hubungan", expanded=True):
                grid_cols = st.columns(2)
                idx_grid = 0
                for i in range(n_nodes):
                    for j in range(i+1, n_nodes):
                        col = grid_cols[idx_grid % 2]
                        u, v = nodes[i], nodes[j]
                        current_val = st.session_state.jarak_matrix[i][j]
                        
                        dist_val = col.number_input(
                            f"Jarak {u} ↔️ {v}",
                            min_value=-1,
                            value=int(current_val),
                            step=1,
                            key=f"grid_dist_{u}_{v}"
                        )
                        st.session_state.jarak_matrix[i][j] = dist_val
                        st.session_state.jarak_matrix[j][i] = dist_val
                        idx_grid += 1

    # Network Visualization
    st.subheader("🕸️ Struktur Jaringan Logistik")
    st.caption("Graf di bawah ini menggambarkan koneksi node saat ini. Garis putus-putus menunjukkan hubungan rute tidak langsung.")
    current_dot = generate_graphviz(st.session_state.nodes, st.session_state.jarak_matrix)
    st.graphviz_chart(current_dot, use_container_width=True)

# --- TAB 2: Results Analysis ---
with tab2:
    if st.session_state.results is None:
        st.info("⚠️ Silakan tekan tombol **🚀 Mulai Pengiriman** di sidebar sebelah kiri untuk melihat hasil analisis optimal rute kurir.")
    else:
        res = st.session_state.results
        rute = res["rute_pengantaran"]
        langkah = res["langkah_langkah"]
        total_vol_sent = res["total_volume_dikirim"]
        sisa_kap = res["sisa_kapasitas"]
        terkirim = res["paket_terkirim"]
        tidak_terkirim = res["paket_tidak_terkirim"]
        
        total_jarak = sum(step["jarak"] for step in langkah)
        
        # Render Metric Cards in HTML for Premium Styling
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-value">{total_jarak} km</div>
                <div class="metric-label">🛣️ Total Jarak Rute</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-value-accent">{len(terkirim)} / {len(st.session_state.nodes) - 1}</div>
                <div class="metric-label">📦 Paket Terkirim</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-value-accent">{total_vol_sent} m³</div>
                <div class="metric-label">🚚 Volume Terisi (Sisa: {sisa_kap} m³)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value metric-value-warn">{len(tidak_terkirim)}</div>
                <div class="metric-label">⚠️ Paket Tertunda</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Highlight unresolved deliveries
        if tidak_terkirim:
            st.warning(f"⚠️ **Informasi Pengantaran:** Paket untuk node **{', '.join(tidak_terkirim)}** tidak dapat diantarkan karena batasan volume kendaraan atau batasan waktu pengantaran (deadline).")
        else:
            st.success("🎉 **Luar Biasa!** Semua paket berhasil dikirimkan ke seluruh node tujuan dengan optimal.")
            
        # Left and Right layout for timeline & Graphviz
        col_res_left, col_res_right = st.columns([3, 2])
        
        with col_res_left:
            st.subheader("📋 Kronologi Perjalanan Kurir")
            
            # Construct Custom HTML Timeline
            timeline_html = '<div class="timeline">'
            timeline_html += f"""
            <div class="timeline-item">
                <div class="timeline-badge start">🚩</div>
                <div class="timeline-card">
                    <div class="timeline-title" style="color: #3B82F6;">Kurir Berangkat</div>
                    <p style="margin: 0; font-size: 0.95rem;">Kurir memulai perjalanan dari titik asal <strong>{st.session_state.start_node}</strong>.</p>
                    <div class="timeline-meta">
                        <span>Kapasitas Truk: <strong>{st.session_state.kapasitas} kg</strong></span>
                        <span>Kecepatan Truk: <strong>{st.session_state.kecepatan} km/jam</strong></span>
                    </div>
                </div>
            </div>
            """
            
            for idx, step in enumerate(langkah):
                prio_val = st.session_state.paket_data['prioritas'].get(step['ke'], 1)
                prio_map = {0: "Depot", 1: "Rendah", 2: "Sedang", 3: "Tinggi"}
                prio_str = prio_map.get(prio_val, "Rendah")
                
                deadline_val = st.session_state.paket_data['deadline'].get(step['ke'], 0.0)
                waktu_menit = (step['jarak'] / st.session_state.kecepatan) * 60
                rute_detail = " ➔ ".join(step['rute_dilewati'])
                
                timeline_html += f"""
                <div class="timeline-item">
                    <div class="timeline-badge">📦</div>
                    <div class="timeline-card">
                        <div class="timeline-title" style="color: #10B981;">Langkah {idx+1}: Kirim ke {step['ke']}</div>
                        <p style="margin: 0; font-size: 0.95rem;">
                            Kurir bergerak ke node <strong>{step['ke']}</strong> melalui jalur optimal Dijkstra: <code>{rute_detail}</code>.
                        </p>
                        <div class="timeline-meta">
                            <span>Jarak: <strong>{step['jarak']} km</strong></span>
                            <span>Waktu Tempuh: <strong>{waktu_menit:.1f} menit</strong></span>
                            <span>Berat Paket: <strong>{step['volume_paket']} kg</strong></span>
                            <span>Sisa Kapasitas: <strong>{step['sisa_kapasitas_sesudah']} kg</strong></span>
                            <span>Prioritas: <strong class="tag-priority">{prio_str}</strong></span>
                            <span>Deadline: <strong>{deadline_val} jam</strong></span>
                            <span>Skor Kelayakan: <strong>{step['skor']:.2f}</strong></span>
                        </div>
                    </div>
                </div>
                """
            timeline_html += '</div>'
            st.markdown(timeline_html, unsafe_allow_html=True)
            
        with col_res_right:
            st.subheader("🕸️ Visualisasi Rute Pengantaran Optimal")
            st.caption("Hubungan garis hijau solid tebal menunjukkan urutan rute perjalanan kurir sesungguhnya.")
            res_dot = generate_graphviz(st.session_state.nodes, st.session_state.jarak_matrix, rute)
            st.graphviz_chart(res_dot, use_container_width=True)
            
        # Detailed table breakdown
        st.markdown("---")
        st.subheader("📊 Tabel Rincian Perjalanan Kurir")
        
        df_breakdown = pd.DataFrame([
            {
                "No. Langkah": idx + 1,
                "Dari": step["dari"],
                "Ke": step["ke"],
                "Rute Rincian (Dijkstra)": " ➔ ".join(step["rute_dilewati"]),
                "Jarak Tempuh (km)": step["jarak"],
                "Waktu Tempuh (Menit)": round((step["jarak"] / st.session_state.kecepatan) * 60, 1),
                "Berat Diantar (kg)": step["volume_paket"],
                "Sisa Kapasitas Truk (kg)": step["sisa_kapasitas_sesudah"],
                "Skor Seleksi Greedy": round(step["skor"], 2)
            }
            for idx, step in enumerate(langkah)
        ])
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)