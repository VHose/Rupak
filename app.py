# app.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import time
import math
import csv
import streamlit.components.v1 as components
import algoritma

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Simulasi Distribusi Paket",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk menyembunyikan sidebar dan memberikan styling bersih (clean design)
st.markdown("""
<style>
    /* Sembunyikan Sidebar */
    [data-testid="sidebar"] {
        display: none;
    }
    
    /* Layout Utama */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Card Panel */
    .dashboard-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Heading Section */
    .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        margin-top: 0px;
        margin-bottom: 18px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Metric Cards */
    .metric-item {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .metric-lbl {
        font-size: 11px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
    }
    
    /* Alert Status Panels */
    .status-panel-success {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        padding: 14px 18px;
        border-radius: 6px;
        font-size: 14px;
        margin-bottom: 18px;
    }
    .status-panel-error {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 14px 18px;
        border-radius: 6px;
        font-size: 14px;
        margin-bottom: 18px;
    }
    .status-panel-info {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #075985;
        padding: 14px 18px;
        border-radius: 6px;
        font-size: 14px;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Sesi State Multi-Step
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "data_valid" not in st.session_state:
    st.session_state.data_valid = False
if "validation_message" not in st.session_state:
    st.session_state.validation_message = "Data belum dimasukkan."
if "validation_type" not in st.session_state:
    st.session_state.validation_type = "info"

# State data utama
if "node" not in st.session_state:
    st.session_state.node = []
if "volume" not in st.session_state:
    st.session_state.volume = []
if "prioritas" not in st.session_state:
    st.session_state.prioritas = []
if "deadline" not in st.session_state:
    st.session_state.deadline = []
if "jarak" not in st.session_state:
    st.session_state.jarak = []
if "asal" not in st.session_state:
    st.session_state.asal = ""
if "kecepatan" not in st.session_state:
    st.session_state.kecepatan = 0.0
if "kapasitas" not in st.session_state:
    st.session_state.kapasitas = 0

# State hasil simulasi
if "riwayat_langkah" not in st.session_state:
    st.session_state.riwayat_langkah = None
if "table_page" not in st.session_state:
    st.session_state.table_page = 1

# Fungsi sinkronisasi matriks jarak manual
def sync_matrix(old_df, new_nodes):
    n = len(new_nodes)
    new_matrix = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(new_matrix, 0)
    
    new_df = pd.DataFrame(new_matrix, index=new_nodes, columns=new_nodes)
    
    for u in old_df.index:
        for v in old_df.columns:
            if u in new_nodes and v in new_nodes:
                new_df.loc[u, v] = old_df.loc[u, v]
    return new_df

# Fungsi validasi state data
def validate_data_state():
    try:
        node_list = st.session_state.node
        if not node_list:
            return "Daftar node kosong.", "error"
        
        if len(node_list) != len(set(node_list)):
            return "Nama node tidak boleh ada yang duplikat.", "error"
            
        for i, n in enumerate(node_list):
            if not str(n).strip():
                return f"Nama node pada indeks {i+1} tidak boleh kosong.", "error"
            if st.session_state.volume[i] < 0:
                return f"Volume paket untuk node '{n}' tidak boleh negatif.", "error"
            if st.session_state.prioritas[i] < 0:
                return f"Prioritas paket untuk node '{n}' tidak boleh negatif.", "error"
            if st.session_state.deadline[i] < 0:
                return f"Deadline paket untuk node '{n}' tidak boleh negatif.", "error"
                
        jarak_matrix = st.session_state.jarak
        n_size = len(node_list)
        if len(jarak_matrix) != n_size or any(len(row) != n_size for row in jarak_matrix):
            return f"Jumlah node pada matriks tidak sesuai dengan data paket.", "error"
            
        for i in range(n_size):
            for j in range(n_size):
                val = jarak_matrix[i][j]
                if i == j and val != 0:
                    return f"Jarak dari node ke dirinya sendiri (diagonal '{node_list[i]}' -> '{node_list[j]}') harus bernilai 0.", "error"
                if val < -1:
                    return f"Jarak antara '{node_list[i]}' dan '{node_list[j]}' tidak boleh negatif selain -1 (ditemukan: {val}).", "error"
                if jarak_matrix[i][j] != jarak_matrix[j][i]:
                    return f"Matriks jarak tidak simetris pada hubungan antara '{node_list[i]}' dan '{node_list[j]}'.", "error"
                    
        asal_node = st.session_state.asal
        if asal_node not in node_list:
            return f"Node asal '{asal_node}' tidak ditemukan dalam daftar node paket.", "error"
        if st.session_state.kecepatan <= 0:
            return "Kecepatan kendaraan harus lebih besar dari 0.", "error"
        if st.session_state.kapasitas <= 0:
            return "Kapasitas kendaraan harus lebih besar dari 0.", "error"
            
        return "File berhasil dimuat. Format data valid.", "success"
    except Exception as e:
        return f"Terjadi kesalahan validasi: {e}", "error"

# Fungsi sinkronisasi data state ke variabel global algoritma.py
def load_state_to_globals():
    algoritma.node = list(st.session_state.node)
    algoritma.n = len(st.session_state.node)
    algoritma.volume = list(st.session_state.volume)
    algoritma.prioritas = list(st.session_state.prioritas)
    algoritma.deadline = list(st.session_state.deadline)
    algoritma.jarak = np.array(st.session_state.jarak)
    algoritma.asal = st.session_state.asal
    algoritma.kecepatan = st.session_state.kecepatan
    algoritma.kapasitas = st.session_state.kapasitas
    algoritma.sisa_kapasitas = st.session_state.kapasitas
    algoritma.hasil_pengiriman = [st.session_state.asal]
    algoritma.rute = []
    algoritma.idx_paket_tersedia = []
    algoritma.waktu_tempuh = []

def get_node_name(i):
    if i < 26:
        return chr(65 + i)
    else:
        div = i // 26
        rem = i % 26
        return chr(65 + div - 1) + chr(65 + rem)

# Fungsi pembuat template CSV tunggal secara dinamis
def generate_template_csv(num_nodes=5):
    nodes = [get_node_name(i) for i in range(num_nodes)]
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    header = ['tipe', 'node', 'volume', 'prioritas', 'deadline', 'kecepatan', 'kapasitas'] + nodes
    writer.writerow(header)
    
    # 1. Row Konfigurasi
    config_row = ['konfigurasi', nodes[0], '', '', '', '60', '100'] + [''] * num_nodes
    writer.writerow(config_row)
    
    # 2. Rows Paket
    origin_row = ['paket', nodes[0], '0', '0', '0.0'] + [''] * (num_nodes + 2)
    writer.writerow(origin_row)
    
    for i in range(1, num_nodes):
        vol = 10 + (i * 5) % 30
        prio = 1 + (i % 3)
        dline = round(1.0 + (i * 0.5) % 4.0, 1)
        paket_row = ['paket', nodes[i], str(vol), str(prio), str(dline)] + [''] * (num_nodes + 2)
        writer.writerow(paket_row)
        
    # 3. Rows Jarak (Adjacency Matrix)
    for i in range(num_nodes):
        row_node = nodes[i]
        distances = []
        for j in range(num_nodes):
            if i == j:
                distances.append('0')
            elif abs(i - j) == 1:
                u = min(i, j)
                dist = 10 + (u * 5) % 25
                distances.append(str(dist))
            elif abs(i - j) == 2:
                u = min(i, j)
                dist = 15 + (u * 10) % 40
                distances.append(str(dist))
            else:
                distances.append('-1')
        jarak_row = ['jarak', row_node, '', '', '', '', ''] + distances
        writer.writerow(jarak_row)
        
    return output.getvalue()


# Fungsi visualisasi graf interaktif
def render_interactive_graph(nodes, jarak_matrix, asal_node):
    js_nodes = []
    for n in nodes:
        color = "#eff6ff" if n == asal_node else "#f8fafc"
        border_color = "#1e40af" if n == asal_node else "#475569"
        border_width = 3 if n == asal_node else 1.5
        font_color = "#1e40af" if n == asal_node else "#0f172a"
        js_nodes.append(f"{{id: '{n}', label: '{n}', color: {{background: '{color}', border: '{border_color}'}}, borderWidth: {border_width}, font: {{color: '{font_color}'}}}}")
        
    js_edges = []
    n_size = len(nodes)
    added_edges = set()
    for i in range(n_size):
        for j in range(n_size):
            dist = jarak_matrix[i][j]
            if dist > 0:
                edge_key = tuple(sorted([nodes[i], nodes[j]]))
                if edge_key not in added_edges:
                    js_edges.append(f"{{from: '{nodes[i]}', to: '{nodes[j]}', label: '{dist} km', color: '#cbd5e1', font: {{align: 'horizontal'}}}}")
                    added_edges.add(edge_key)
                    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {{
                width: 100%;
                height: 480px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #ffffff;
            }}
            .btn-container {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
            }}
            .btn {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                padding: 6px 12px;
                font-size: 13px;
                font-family: sans-serif;
                border-radius: 4px;
                cursor: pointer;
            }}
            .btn:hover {{
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <div class="btn-container">
            <button class="btn" onclick="network.fit()">Reset View</button>
            <button class="btn" onclick="zoomIn()">Zoom In</button>
            <button class="btn" onclick="zoomOut()">Zoom Out</button>
        </div>
        <script type="text/javascript">
            var nodes = new vis.DataSet([
                {", ".join(js_nodes)}
            ]);
            var edges = new vis.DataSet([
                {", ".join(js_edges)}
            ]);
            var container = document.getElementById('mynetwork');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            var options = {{
                nodes: {{
                    shape: 'circle',
                    font: {{
                        size: 14,
                        face: 'sans-serif'
                    }},
                    shadow: false
                }},
                edges: {{
                    shadow: false,
                    smooth: false
                }},
                interaction: {{
                    dragNodes: true,
                    dragView: true,
                    zoomView: true
                }},
                physics: {{
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {{
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 100,
                        springConstant: 0.08
                    }}
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            function zoomIn() {{
                network.moveTo({{
                    scale: network.getScale() * 1.2
                }});
            }}
            function zoomOut() {{
                network.moveTo({{
                    scale: network.getScale() / 1.2
                }});
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=530)


# Fungsi visualisasi graf animasi bertahap (player controls)
def render_animated_graph(nodes, jarak_matrix, asal_node, riwayat_langkah):
    if not riwayat_langkah:
        render_interactive_graph(nodes, jarak_matrix, asal_node)
        return

    import json
    
    js_nodes = [str(n) for n in nodes]
    
    js_edges = []
    n_size = len(nodes)
    added_edges = set()
    for i in range(n_size):
        for j in range(n_size):
            dist = jarak_matrix[i][j]
            if dist > 0:
                edge_key = tuple(sorted([nodes[i], nodes[j]]))
                if edge_key not in added_edges:
                    js_edges.append({
                        "id": f"{nodes[i]}_{nodes[j]}",
                        "from": nodes[i],
                        "to": nodes[j],
                        "label": f"{dist} km"
                    })
                    added_edges.add(edge_key)
                    
    frames = []
    
    # Frame 0: Start at Origin
    frames.append({
        "stepIndex": -1,
        "edgeStart": None,
        "edgeEnd": None,
        "deliveredBefore": [],
        "activeTarget": None,
        "activeRoute": [],
        "description": f"<b>Persiapan:</b> Kendaraan berada di titik asal <b>{asal_node}</b>. Siap memulai pengiriman paket."
    })
    
    delivered_list = []
    for step_idx, step in enumerate(riwayat_langkah):
        r = step["rute"]
        target = step["tujuan"]
        
        if len(r) > 1:
            for i in range(len(r) - 1):
                u = r[i]
                v = r[i+1]
                frames.append({
                    "stepIndex": step_idx,
                    "edgeStart": u,
                    "edgeEnd": v,
                    "deliveredBefore": list(delivered_list),
                    "activeTarget": target,
                    "activeRoute": list(r),
                    "description": f"<b>Langkah {step_idx + 1}:</b> Kendaraan bergerak dari <b>{u}</b> ke <b>{v}</b> menuju tujuan <b>{target}</b>."
                })
        
        delivered_list.append(target)
        frames.append({
            "stepIndex": step_idx,
            "edgeStart": None,
            "edgeEnd": None,
            "deliveredBefore": list(delivered_list),
            "activeTarget": target,
            "activeRoute": [],
            "description": f"<b>Pengiriman Sukses:</b> Paket dikirim ke <b>{target}</b> (Volume: {step['volume_paket']} m³). Sisa kapasitas kendaraan: {step['sisa_kapasitas']} m³."
        })
        
    frames.append({
        "stepIndex": len(riwayat_langkah),
        "edgeStart": None,
        "edgeEnd": None,
        "deliveredBefore": list(delivered_list),
        "activeTarget": None,
        "activeRoute": [],
        "description": "<b>Selesai:</b> Proses distribusi paket telah selesai dilaksanakan secara penuh."
    })
    
    frames_json = json.dumps(frames)
    js_nodes_json = json.dumps(js_nodes)
    edges_json = json.dumps(js_edges)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {{
                width: 100%;
                height: 400px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #ffffff;
            }}
            .player-container {{
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            .control-bar {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: 15px;
                padding: 8px 12px;
                background-color: #f8fafc;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
            }}
            .btn {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                padding: 6px 14px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                min-width: 44px;
                height: 34px;
                user-select: none;
            }}
            .btn:hover {{
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }}
            .btn:active {{
                background-color: #e2e8f0;
            }}
            .btn-primary {{
                background-color: #2563eb;
                color: #ffffff;
                border-color: #1d4ed8;
            }}
            .btn-primary:hover {{
                background-color: #1d4ed8;
            }}
            .slider {{
                flex-grow: 1;
                height: 6px;
                background: #cbd5e1;
                outline: none;
                border-radius: 3px;
                cursor: pointer;
            }}
            .status-box {{
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                color: #1e3a8a;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
                margin-top: 15px;
                line-height: 1.5;
                min-height: 48px;
            }}
            .speed-select {{
                padding: 6px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: #ffffff;
                color: #334155;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="player-container">
            <div id="mynetwork"></div>
            
            <div class="status-box" id="statusText">
                Inisialisasi simulasi...
            </div>
            
            <div class="control-bar">
                <button class="btn" id="btnPrev" onclick="stepPrev()">⏮</button>
                <button class="btn btn-primary" id="btnPlay" onclick="togglePlay()">▶ Play</button>
                <button class="btn" id="btnNext" onclick="stepNext()">⏭</button>
                <button class="btn" id="btnReset" onclick="resetAnimation()">↺ Reset</button>
                
                <input type="range" min="0" max="{len(frames) - 1}" value="0" class="slider" id="progressSlider" oninput="onSliderInput(this.value)">
                
                <span id="stepCounter" style="font-size: 13px; font-weight: 600; color: #475569; min-width: 60px; text-align: center;">0 / 0</span>
                
                <select class="speed-select" id="speedSelect" onchange="changeSpeed(this.value)">
                    <option value="2000">Lambat (2s)</option>
                    <option value="1000" selected>Normal (1s)</option>
                    <option value="500">Cepat (0.5s)</option>
                </select>
            </div>
        </div>
        
        <script type="text/javascript">
            var originalOrigin = '{asal_node}';
            var nodesList = {js_nodes_json};
            var edgesList = {edges_json};
            var frames = {frames_json};
            
            var currentFrameIndex = 0;
            var isPlaying = false;
            var timer = null;
            var intervalMs = 1000;
            
            var nodes = new vis.DataSet([]);
            var edges = new vis.DataSet([]);
            
            nodesList.forEach(function(nodeId) {{
                nodes.add({{
                    id: nodeId,
                    label: nodeId,
                    shape: 'circle',
                    font: {{ size: 14, face: 'sans-serif' }},
                    color: {{ background: '#f1f5f9', border: '#cbd5e1' }}
                }});
            }});
            
            edgesList.forEach(function(edge) {{
                edges.add({{
                    id: edge.id,
                    from: edge.from,
                    to: edge.to,
                    label: edge.label,
                    color: {{ color: '#e2e8f0' }},
                    width: 1.5,
                    font: {{ align: 'horizontal', size: 11 }}
                }});
            }});
            
            var container = document.getElementById('mynetwork');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                nodes: {{
                    shape: 'circle',
                    shadow: false
                }},
                edges: {{
                    shadow: false,
                    smooth: false
                }},
                physics: {{
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {{
                        gravitationalConstant: -40,
                        centralGravity: 0.015,
                        springLength: 90,
                        springConstant: 0.08
                    }}
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            updateFrame(0);
            
            function updateFrame(idx) {{
                currentFrameIndex = idx;
                var frame = frames[idx];
                var delivered = frame.deliveredBefore;
                var activeTarget = frame.activeTarget;
                var edgeStart = frame.edgeStart;
                var edgeEnd = frame.edgeEnd;
                var activeRoute = frame.activeRoute || [];
                
                var updatedNodes = [];
                nodesList.forEach(function(nodeId) {{
                    var bgColor = "#f1f5f9";
                    var borderColor = "#cbd5e1";
                    var borderWidth = 1.5;
                    var size = 15;
                    var label = nodeId;
                    
                    if (nodeId === originalOrigin) {{
                        bgColor = "#eff6ff";
                        borderColor = "#1e40af";
                        borderWidth = 3;
                        size = 18;
                    }}
                    
                    if (delivered.indexOf(nodeId) !== -1) {{
                        bgColor = "#dcfce7";
                        borderColor = "#166534";
                        borderWidth = 2;
                        label = "✓ " + nodeId;
                    }} else if (nodeId === activeTarget) {{
                        bgColor = "#ffedd5";
                        borderColor = "#ea580c";
                        borderWidth = 3;
                        size = 20;
                    }} else if (activeRoute.indexOf(nodeId) !== -1) {{
                        bgColor = "#fef3c7";
                        borderColor = "#d97706";
                        borderWidth = 2;
                    }}
                    
                    updatedNodes.push({{
                        id: nodeId,
                        label: label,
                        color: {{
                            background: bgColor,
                            border: borderColor,
                            highlight: {{ background: bgColor, border: borderColor }}
                        }},
                        borderWidth: borderWidth,
                        size: size
                    }});
                }});
                nodes.update(updatedNodes);
                
                var updatedEdges = [];
                edgesList.forEach(function(edge) {{
                    var color = "#e2e8f0";
                    var width = 1.5;
                    var dashes = false;
                    
                    var is_active = (edge.from === edgeStart && edge.to === edgeEnd) || (edge.from === edgeEnd && edge.to === edgeStart);
                    
                    var is_route = false;
                    if (activeRoute.length > 1) {{
                        for (var r_idx = 0; r_idx < activeRoute.length - 1; r_idx++) {{
                            var u = activeRoute[r_idx];
                            var v = activeRoute[r_idx+1];
                            if ((edge.from === u && edge.to === v) || (edge.from === v && edge.to === u)) {{
                                if (!is_active) {{
                                    is_route = true;
                                }}
                            }}
                        }}
                    }}
                    
                    if (is_active) {{
                        color = "#ef4444";
                        width = 4.5;
                        dashes = true;
                    }} else if (is_route) {{
                        color = "#f59e0b";
                        width = 3.0;
                    }}
                    
                    updatedEdges.push({{
                        id: edge.id,
                        color: {{ color: color, highlight: color }},
                        width: width,
                        dashes: dashes
                    }});
                }});
                edges.update(updatedEdges);
                
                document.getElementById("statusText").innerHTML = frame.description;
                document.getElementById("progressSlider").value = idx;
                document.getElementById("stepCounter").innerText = (idx + 1) + " / " + frames.length;
                
                if (idx === frames.length - 1 && isPlaying) {{
                    togglePlay();
                }}
            }}
            
            function togglePlay() {{
                isPlaying = !isPlaying;
                var btn = document.getElementById("btnPlay");
                if (isPlaying) {{
                    btn.innerHTML = "⏸ Pause";
                    btn.className = "btn";
                    
                    if (currentFrameIndex >= frames.length - 1) {{
                        currentFrameIndex = 0;
                        updateFrame(0);
                    }}
                    
                    timer = setInterval(function() {{
                        if (currentFrameIndex < frames.length - 1) {{
                            updateFrame(currentFrameIndex + 1);
                        }} else {{
                            togglePlay();
                        }}
                    }}, intervalMs);
                }} else {{
                    btn.innerHTML = "▶ Play";
                    btn.className = "btn btn-primary";
                    clearInterval(timer);
                }}
            }}
            
            function resetAnimation() {{
                if (isPlaying) {{
                    togglePlay();
                }}
                updateFrame(0);
            }}
            
            function stepNext() {{
                if (isPlaying) {{
                    togglePlay();
                }}
                if (currentFrameIndex < frames.length - 1) {{
                    updateFrame(currentFrameIndex + 1);
                }}
            }}
            
            function stepPrev() {{
                if (isPlaying) {{
                    togglePlay();
                }}
                if (currentFrameIndex > 0) {{
                    updateFrame(currentFrameIndex - 1);
                }}
            }}
            
            function onSliderInput(val) {{
                if (isPlaying) {{
                    togglePlay();
                }}
                updateFrame(parseInt(val));
            }}
            
            function changeSpeed(ms) {{
                intervalMs = parseInt(ms);
                if (isPlaying) {{
                    clearInterval(timer);
                    timer = setInterval(function() {{
                        if (currentFrameIndex < frames.length - 1) {{
                            updateFrame(currentFrameIndex + 1);
                        }} else {{
                            togglePlay();
                        }}
                    }}, intervalMs);
                }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=530)


# Fungsi untuk merender linimasa perjalanan vertikal kurir
def render_timeline(riwayat_langkah, asal_awal):
    timeline_items = []
    
    # Titik Mulai
    timeline_items.append(f"""
    <div class="timeline-item">
        <div class="timeline-marker origin"></div>
        <div class="timeline-content">
            <div class="timeline-title">📍 Titik Keberangkatan: {asal_awal}</div>
            <div class="timeline-time">Waktu: 0.0 menit | Akumulasi Jarak: 0.0 km</div>
            <div class="timeline-details">Kendaraan siap berangkat dari titik asal dengan kapasitas penuh.</div>
        </div>
    </div>
    """)
    
    accum_distance = 0.0
    accum_time = 0.0
    
    for idx, step in enumerate(riwayat_langkah, start=1):
        target = step["tujuan"]
        rute_path = " -> ".join(step["rute"])
        vol = step["volume_paket"]
        sisa = step["sisa_kapasitas"]
        jarak_step = step["jarak"]
        waktu_step = step["waktu_tempuh"]
        skor = step["skor"]
        
        accum_distance += jarak_step
        accum_time += waktu_step
        
        timeline_items.append(f"""
    <div class="timeline-item delivered">
        <div class="timeline-marker delivery"></div>
        <div class="timeline-content">
            <div class="timeline-title">🚚 Pengiriman {idx}: Node {target}</div>
            <div class="timeline-time">Jarak Tempuh: {round(jarak_step, 2)} km (Waktu: {round(waktu_step, 1)} menit)</div>
            <div class="timeline-details">
                <b>Rute:</b> {rute_path}<br>
                <b>Paket Terkirim:</b> {vol} m³ (Skor: {round(skor, 2)})<br>
                <b>Sisa Kapasitas Kendaraan:</b> {sisa} m³<br>
                <span style="color:#64748b; font-size:12px;">Akumulasi: {round(accum_distance, 2)} km | {round(accum_time, 1)} menit</span>
            </div>
        </div>
    </div>
        """)
        
    timeline_html = f"""
    <style>
        .timeline {{
            border-left: 2px solid #e2e8f0;
            padding-left: 24px;
            margin-left: 12px;
            position: relative;
        }}
        .timeline-item {{
            margin-bottom: 24px;
            position: relative;
        }}
        .timeline-marker {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            position: absolute;
            left: -32px;
            top: 4px;
            border: 2px solid #ffffff;
            box-shadow: 0 0 0 2px #cbd5e1;
        }}
        .timeline-marker.origin {{
            background-color: #3b82f6;
            box-shadow: 0 0 0 2px #3b82f6;
        }}
        .timeline-marker.delivery {{
            background-color: #22c55e;
            box-shadow: 0 0 0 2px #22c55e;
        }}
        .timeline-content {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 14px 18px;
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .timeline-title {{
            font-weight: 700;
            font-size: 15px;
            color: #0f172a;
        }}
        .timeline-time {{
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
            font-weight: 500;
        }}
        .timeline-details {{
            font-size: 13px;
            color: #334155;
            margin-top: 8px;
            line-height: 1.5;
        }}
    </style>
    <div class="timeline">
        {"".join(timeline_items)}
    </div>
    """
    return timeline_html


# Fungsi untuk memvisualisasikan rute akhir graf statis
def render_final_graph(nodes, jarak_matrix, asal_node, riwayat_langkah):
    if not riwayat_langkah:
        return
        
    import json
    
    # Ekstrak node yang dikunjungi
    visited_nodes = [asal_node]
    traversed_edges = set()
    
    for step in riwayat_langkah:
        visited_nodes.append(step["tujuan"])
        r = step["rute"]
        if len(r) > 1:
            for i in range(len(r) - 1):
                u = r[i]
                v = r[i+1]
                traversed_edges.add(tuple(sorted([u, v])))
                
    js_nodes = [str(n) for n in nodes]
    
    js_edges = []
    n_size = len(nodes)
    added_edges = set()
    for i in range(n_size):
        for j in range(n_size):
            dist = jarak_matrix[i][j]
            if dist > 0:
                u = nodes[i]
                v = nodes[j]
                edge_key = tuple(sorted([u, v]))
                if edge_key not in added_edges:
                    is_traversed = edge_key in traversed_edges
                    js_edges.append({
                        "id": f"{u}_{v}",
                        "from": u,
                        "to": v,
                        "label": f"{dist} km",
                        "isTraversed": is_traversed
                    })
                    added_edges.add(edge_key)
                    
    visited_nodes_json = json.dumps(visited_nodes)
    js_nodes_json = json.dumps(js_nodes)
    edges_json = json.dumps(js_edges)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {{
                width: 100%;
                height: 420px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #ffffff;
            }}
            .btn-container {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
            }}
            .btn {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                padding: 6px 12px;
                font-size: 13px;
                font-family: sans-serif;
                border-radius: 4px;
                cursor: pointer;
            }}
            .btn:hover {{
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <div class="btn-container">
            <button class="btn" onclick="network.fit()">Reset View</button>
            <button class="btn" onclick="zoomIn()">Zoom In</button>
            <button class="btn" onclick="zoomOut()">Zoom Out</button>
        </div>
        <script type="text/javascript">
            var originalOrigin = '{asal_node}';
            var nodesList = {js_nodes_json};
            var visitedNodes = {visited_nodes_json};
            var edgesList = {edges_json};
            
            var nodes = new vis.DataSet([]);
            var edges = new vis.DataSet([]);
            
            nodesList.forEach(function(nodeId) {{
                var bgColor = "#f1f5f9";
                var borderColor = "#cbd5e1";
                var borderWidth = 1.5;
                var size = 15;
                var label = nodeId;
                var fontColor = "#0f172a";
                
                if (nodeId === originalOrigin) {{
                    bgColor = "#eff6ff";
                    borderColor = "#1e40af";
                    borderWidth = 3;
                    size = 18;
                    label = nodeId;
                }} else if (visitedNodes.indexOf(nodeId) !== -1) {{
                    bgColor = "#dcfce7";
                    borderColor = "#166534";
                    borderWidth = 2.5;
                    size = 18;
                    label = "✓ " + nodeId;
                }} else {{
                    bgColor = "#e2e8f0";
                    borderColor = "#94a3b8";
                    borderWidth = 1;
                    fontColor = "#64748b";
                }}
                
                nodes.add({{
                    id: nodeId,
                    label: label,
                    shape: 'circle',
                    font: {{ size: 13, face: 'sans-serif', color: fontColor }},
                    color: {{
                        background: bgColor,
                        border: borderColor,
                        highlight: {{ background: bgColor, border: borderColor }}
                    }},
                    borderWidth: borderWidth,
                    size: size
                }});
            }});
            
            edgesList.forEach(function(edge) {{
                var color = "#e2e8f0";
                var width = 1.0;
                var fontColor = "#94a3b8";
                
                if (edge.isTraversed) {{
                    color = "#22c55e";
                    width = 3.5;
                    fontColor = "#15803d";
                }}
                
                edges.add({{
                    id: edge.id,
                    from: edge.from,
                    to: edge.to,
                    label: edge.label,
                    color: {{ color: color, highlight: color }},
                    width: width,
                    font: {{ align: 'horizontal', size: 10, color: fontColor }}
                }});
            }});
            
            var container = document.getElementById('mynetwork');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                nodes: {{
                    shape: 'circle',
                    shadow: false
                }},
                edges: {{
                    shadow: false,
                    smooth: false
                }},
                physics: {{
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {{
                        gravitationalConstant: -40,
                        centralGravity: 0.015,
                        springLength: 90,
                        springConstant: 0.08
                    }}
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            function zoomIn() {{
                network.moveTo({{
                    scale: network.getScale() * 1.2
                }});
            }}
            function zoomOut() {{
                network.moveTo({{
                    scale: network.getScale() / 1.2
                }});
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=480)


# Main Title & Subtitle
st.write("")
st.write("")
st.markdown("<div style='font-size: 26px; font-weight: 700; color: #0f172a; margin-bottom: 8px;'>Sistem Simulasi Distribusi Logistik</div>", unsafe_allow_html=True)
st.markdown("<div style='font-size: 14px; color: #64748b; margin-bottom: 30px;'>Optimasi operasional kurir paket menggunakan integrasi algoritma Dijkstra dan pembobotan multi-kriteria.</div>", unsafe_allow_html=True)

# Wizard / Stepper Progress Flow (5 Langkah)
steps = [
    "1. Input Data",
    "2. Validasi Data",
    "3. Visualisasi Graf",
    "4. Hasil",
    "5. Ringkasan"
]
current_step = st.session_state.current_step

stepper_html = "<div style='display: flex; justify-content: space-between; margin-bottom: 30px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px;'>"
for i, s in enumerate(steps, start=1):
    if current_step == i:
        active_style = "color: #1e40af; font-weight: 700; border-bottom: 3px solid #1e40af; padding-bottom: 10px;"
    else:
        active_style = "color: #64748b; padding-bottom: 10px;"
    stepper_html += f"<div style='flex: 1; text-align: center; {active_style}'>{s}</div>"
stepper_html += "</div>"
st.markdown(stepper_html, unsafe_allow_html=True)

# -----------------
# LANGKAH 1 - INPUT DATA
# -----------------
if current_step == 1:
    # Header Input Data ditampilkan sebagai teks judul biasa, bukan di dalam card/box
    st.markdown("### Input Data")
    
    metode_input = st.radio(
        "Metode Input Data:",
        ("Upload CSV", "Input Manual"),
        horizontal=True
    )
    
    if metode_input == "Upload CSV":
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 15px; margin-bottom: 10px;'>Upload Data Distribusi</div>", unsafe_allow_html=True)
        
        # Area upload file CSV tunggal
        uploaded_file = st.file_uploader("Upload Data Distribusi", type=['csv'], label_visibility="collapsed", key="csv_file_uploader")
        st.markdown("<div style='font-size:12px; color:#64748b; margin-top:-10px; margin-bottom:15px;'>Unggah berkas CSV distribusi tunggal Anda. Sistem secara otomatis membaca jumlah node langsung dari berkas yang diunggah.</div>", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Muat Data dari CSV", use_container_width=True):
                if uploaded_file:
                    try:
                        list_node, list_volume, list_prioritas, list_deadline, matriks_jarak, asal_node, kec, kap = algoritma.baca_data_distribusi_tunggal(uploaded_file)
                        
                        st.session_state.node = list_node
                        st.session_state.volume = list_volume
                        st.session_state.prioritas = list_prioritas
                        st.session_state.deadline = list_deadline
                        st.session_state.jarak = matriks_jarak.tolist()
                        st.session_state.asal = asal_node
                        st.session_state.kecepatan = kec
                        st.session_state.kapasitas = kap
                        st.session_state.data_loaded = True
                        st.session_state.riwayat_langkah = None
                        
                        msg, val_type = validate_data_state()
                        st.session_state.validation_message = msg
                        st.session_state.validation_type = val_type
                        
                        if val_type == "success":
                            st.session_state.data_valid = True
                            st.success("File berhasil dimuat. Format data valid. Silakan klik tombol 'Selanjutnya >' di bawah untuk melakukan validasi.")
                        else:
                            st.session_state.data_valid = False
                            st.error(f"Gagal memvalidasi data: {msg}")
                    except Exception as e:
                        st.session_state.data_loaded = False
                        st.session_state.validation_message = f"Gagal memproses file CSV: {e}"
                        st.session_state.validation_type = "error"
                        st.error(st.session_state.validation_message)
                else:
                    st.warning("Mohon unggah file CSV terlebih dahulu.")
                    
        with col_c2:
            if st.button("Gunakan Data Contoh Workspace", use_container_width=True):
                try:
                    list_node, list_volume, list_prioritas, list_deadline, matriks_jarak, asal_node, kec, kap = algoritma.baca_data_distribusi_tunggal("distribusi.csv")
                    
                    st.session_state.node = list_node
                    st.session_state.volume = list_volume
                    st.session_state.prioritas = list_prioritas
                    st.session_state.deadline = list_deadline
                    st.session_state.jarak = matriks_jarak.tolist()
                    st.session_state.asal = asal_node
                    st.session_state.kecepatan = kec
                    st.session_state.kapasitas = kap
                    st.session_state.data_loaded = True
                    st.session_state.riwayat_langkah = None
                    
                    msg, val_type = validate_data_state()
                    st.session_state.validation_message = msg
                    st.session_state.validation_type = val_type
                    
                    if val_type == "success":
                        st.session_state.data_valid = True
                        st.success("File contoh berhasil dimuat. Format data valid. Silakan klik tombol 'Selanjutnya >' di bawah untuk melakukan validasi.")
                    else:
                        st.session_state.data_valid = False
                        st.error(f"Gagal memvalidasi data contoh: {msg}")
                except Exception as e:
                    st.session_state.data_loaded = False
                    st.session_state.validation_message = f"Gagal memproses data contoh: {e}"
                    st.session_state.validation_type = "error"
                    st.error(st.session_state.validation_message)
                    
        st.write("---")
        
        # Area opsional pengunduhan template
        with st.expander("Butuh Berkas Template CSV?"):
            st.write("Tentukan jumlah node yang diinginkan lalu unduh berkas template untuk mempermudah pengisian data:")
            num_nodes_template = st.number_input(
                "Jumlah Node untuk Template CSV:",
                min_value=2,
                max_value=30,
                value=5,
                step=1,
                key="template_node_count_selector",
                help="Pilih jumlah node (2-30) untuk file template CSV yang akan diunduh."
            )
            st.download_button(
                label="Download Template CSV",
                data=generate_template_csv(num_nodes_template),
                file_name="template_distribusi.csv",
                mime="text/csv",
                use_container_width=True,
                key="template_download_btn"
            )
                    
    else:
        # Input Manual menggunakan Data Editor
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 15px; margin-bottom: 10px;'>Data Paket</div>", unsafe_allow_html=True)
        st.write("Isi data paket untuk masing-masing tujuan. Kolom No merupakan nomor urut otomatis yang tidak dapat diedit.")
        
        if "manual_df_paket" not in st.session_state:
            st.session_state.manual_df_paket = pd.DataFrame([
                {"No": 1, "Node": "A", "Volume": 0, "Prioritas": 0, "Deadline": 0.0},
                {"No": 2, "Node": "B", "Volume": 15, "Prioritas": 2, "Deadline": 1.5},
                {"No": 3, "Node": "C", "Volume": 20, "Prioritas": 3, "Deadline": 2.0},
                {"No": 4, "Node": "D", "Volume": 10, "Prioritas": 1, "Deadline": 1.0}
            ])
            
        # Re-index 'No' secara otomatis agar selalu urut 1, 2, 3...
        st.session_state.manual_df_paket["No"] = range(1, len(st.session_state.manual_df_paket) + 1)
        
        edited_df_paket = st.data_editor(
            st.session_state.manual_df_paket,
            column_config={
                "No": st.column_config.NumberColumn(
                    label="No",
                    disabled=True,
                    width="small",
                    alignment="center"
                ),
                "Node": st.column_config.TextColumn(label="Node", width="medium"),
                "Volume": st.column_config.NumberColumn(label="Volume (m³)", min_value=0, width="small"),
                "Prioritas": st.column_config.NumberColumn(label="Prioritas", min_value=0, max_value=3, width="small"),
                "Deadline": st.column_config.NumberColumn(label="Deadline (Jam)", min_value=0.0, width="small")
            },
            num_rows="dynamic",
            key="manual_paket_editor",
            use_container_width=True
        )
        st.session_state.manual_df_paket = edited_df_paket
        
        # Tombol Tambah Baris dan Hapus Baris
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Tambah Baris", use_container_width=True):
                new_no = len(st.session_state.manual_df_paket) + 1
                new_row = pd.DataFrame([{"No": new_no, "Node": f"Node_{new_no}", "Volume": 10, "Prioritas": 1, "Deadline": 1.0}])
                st.session_state.manual_df_paket = pd.concat([st.session_state.manual_df_paket, new_row], ignore_index=True)
                st.rerun()
        with col_btn2:
            if st.button("Hapus Baris", use_container_width=True):
                if len(st.session_state.manual_df_paket) > 0:
                    st.session_state.manual_df_paket = st.session_state.manual_df_paket.iloc[:-1]
                    st.rerun()
        
        # Ekstrak node list aktif untuk sinkronisasi
        nodes = [str(n).strip() for n in edited_df_paket["Node"] if str(n).strip()]
        
        # Sinkronisasi Matriks Jarak
        if "manual_df_jarak" not in st.session_state:
            initial_nodes = ["A", "B", "C", "D"]
            matrix_data = [
                [0, 10, 20, -1],
                [10, 0, 15, 30],
                [20, 15, 0, 25],
                [-1, 30, 25, 0]
            ]
            st.session_state.manual_df_jarak = pd.DataFrame(matrix_data, index=initial_nodes, columns=initial_nodes)
            
        current_matrix_nodes = list(st.session_state.manual_df_jarak.index)
        if current_matrix_nodes != nodes:
            st.session_state.manual_df_jarak = sync_matrix(st.session_state.manual_df_jarak, nodes)
            st.rerun()
            
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 20px; margin-bottom: 5px;'>Matriks Jarak Antar Node</div>", unsafe_allow_html=True)
        st.write("Masukkan jarak langsung antar node. Nilai **-1** berarti tidak ada jalan/koneksi langsung. Jarak bolak-balik otomatis disinkronkan secara simetris.")
        
        # Pastikan diagonal utama selalu 0
        for node_name in st.session_state.manual_df_jarak.index:
            if node_name in st.session_state.manual_df_jarak.columns:
                st.session_state.manual_df_jarak.loc[node_name, node_name] = 0
                
        n_nodes = len(nodes)
        route_pairs = []
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                route_pairs.append((nodes[i], nodes[j]))
                
        if route_pairs:
            cols_per_row = 3
            for chunk_idx in range(0, len(route_pairs), cols_per_row):
                chunk = route_pairs[chunk_idx:chunk_idx + cols_per_row]
                cols = st.columns(cols_per_row)
                for col, (u, v) in zip(cols, chunk):
                    if u in st.session_state.manual_df_jarak.index and v in st.session_state.manual_df_jarak.columns:
                        current_val = int(st.session_state.manual_df_jarak.loc[u, v])
                    else:
                        current_val = 10
                        
                    new_val = col.number_input(
                        f"Jarak {u} ➔ {v} (km):",
                        min_value=-1,
                        value=current_val,
                        step=1,
                        key=f"dist_{u}_{v}"
                    )
                    st.session_state.manual_df_jarak.loc[u, v] = new_val
                    st.session_state.manual_df_jarak.loc[v, u] = new_val
        else:
            st.info("Tambahkan minimal 2 node paket pada tabel di atas untuk mengonfigurasi jarak.")
            
        # Form Konfigurasi Kendaraan
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 20px; margin-bottom: 10px;'>Konfigurasi Distribusi</div>", unsafe_allow_html=True)
        
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            manual_asal = st.selectbox(
                "Node Asal:",
                options=nodes,
                index=0 if (nodes and st.session_state.asal in nodes) else 0 if nodes else None
            )
        with f_col2:
            manual_kecepatan = st.number_input(
                "Kecepatan Kendaraan (km/jam):",
                min_value=1.0,
                value=float(st.session_state.kecepatan) if st.session_state.kecepatan > 0 else 60.0,
                step=5.0
            )
        with f_col3:
            manual_kapasitas = st.number_input(
                "Kapasitas Kendaraan (m³):",
                min_value=1,
                value=int(st.session_state.kapasitas) if st.session_state.kapasitas > 0 else 100,
                step=10
            )
            
        if st.button("Simpan Data Manual", use_container_width=True):
            try:
                # Validasi jumlah
                if len(edited_df_paket) != len(nodes):
                    raise ValueError("Nama node tidak boleh kosong pada baris manapun.")
                
                vol_list = [int(v) for v in edited_df_paket["Volume"]]
                prio_list = [int(p) for p in edited_df_paket["Prioritas"]]
                dline_list = [float(d) for d in edited_df_paket["Deadline"]]
                jarak_matrix = st.session_state.manual_df_jarak.values.tolist()
                
                # Masukkan ke state
                st.session_state.node = nodes
                st.session_state.volume = vol_list
                st.session_state.prioritas = prio_list
                st.session_state.deadline = dline_list
                st.session_state.jarak = jarak_matrix
                st.session_state.asal = manual_asal
                st.session_state.kecepatan = manual_kecepatan
                st.session_state.kapasitas = manual_kapasitas
                st.session_state.data_loaded = True
                st.session_state.riwayat_langkah = None
                
                # Validasi
                msg, val_type = validate_data_state()
                st.session_state.validation_message = msg
                st.session_state.validation_type = val_type
                
                if val_type == "success":
                    st.session_state.data_valid = True
                    st.success("Data manual berhasil disimpan. Format data valid. Silakan klik tombol 'Selanjutnya >' di bawah untuk melakukan validasi.")
                else:
                    st.session_state.data_valid = False
                    st.error(f"Gagal memvalidasi data: {msg}")
            except Exception as e:
                st.error(f"Gagal memproses data manual: {e}")

# -----------------
# LANGKAH 2 - VALIDASI DATA
# -----------------
elif current_step == 2:
    st.markdown("<div class='dashboard-card'><div class='card-title'>Validasi & Penyesuaian Data</div>", unsafe_allow_html=True)
    st.write("Anda dapat menyesuaikan konfigurasi distribusi dan data paket di bawah ini sebelum melanjutkan ke simulasi.")
    
    # 1. Konfigurasi Distribusi
    st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 10px; margin-bottom: 10px;'>Konfigurasi Distribusi</div>", unsafe_allow_html=True)
    
    col_adj1, col_adj2, col_adj3 = st.columns(3)
    with col_adj1:
        node_options = list(st.session_state.node)
        try:
            default_asal_idx = node_options.index(st.session_state.asal)
        except ValueError:
            default_asal_idx = 0
            
        new_asal = st.selectbox(
            "Node Asal (Titik Mulai):",
            options=node_options,
            index=default_asal_idx if node_options else None,
            key="step2_asal_select"
        )
    with col_adj2:
        new_kecepatan = st.number_input(
            "Kecepatan Kendaraan (km/jam):",
            min_value=1.0,
            value=float(st.session_state.kecepatan) if st.session_state.kecepatan > 0 else 60.0,
            step=5.0,
            key="step2_kecepatan_input"
        )
    with col_adj3:
        new_kapasitas = st.number_input(
            "Kapasitas Kendaraan (m³):",
            min_value=1,
            value=int(st.session_state.kapasitas) if st.session_state.kapasitas > 0 else 100,
            step=10,
            key="step2_kapasitas_input"
        )
        
    # 2. Data Editor untuk Paket
    st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 15px; margin-bottom: 10px;'>Data Paket (Volume, Prioritas, & Deadline)</div>", unsafe_allow_html=True)
    st.write("Silakan klik sel pada tabel untuk mengedit data paket secara langsung:")
    
    df_edit = pd.DataFrame({
        "Node": st.session_state.node,
        "Volume (m³)": st.session_state.volume,
        "Prioritas": st.session_state.prioritas,
        "Deadline (Jam)": st.session_state.deadline
    })
    
    edited_df = st.data_editor(
        df_edit,
        column_config={
            "Node": st.column_config.TextColumn("Node", disabled=True),
            "Volume (m³)": st.column_config.NumberColumn("Volume (m³)", min_value=0),
            "Prioritas": st.column_config.NumberColumn("Prioritas", min_value=0, max_value=3),
            "Deadline (Jam)": st.column_config.NumberColumn("Deadline (Jam)", min_value=0.0)
        },
        use_container_width=True,
        key="step2_data_editor_widget"
    )
    
    # Simpan perubahan kembali ke session state secara dinamis
    st.session_state.asal = new_asal
    st.session_state.kecepatan = new_kecepatan
    st.session_state.kapasitas = new_kapasitas
    st.session_state.volume = [int(v) for v in edited_df["Volume (m³)"]]
    st.session_state.prioritas = [int(p) for p in edited_df["Prioritas"]]
    st.session_state.deadline = [float(d) for d in edited_df["Deadline (Jam)"]]
    
    # Jalankan validasi setelah penyesuaian state
    msg, val_type = validate_data_state()
    st.session_state.validation_message = msg
    st.session_state.validation_type = val_type
    
    st.write("")
    
    if val_type == "success":
        st.session_state.data_valid = True
        st.markdown(f"<div class='status-panel-success'>{msg}</div>", unsafe_allow_html=True)
        
        # Rincian Ringkasan parameter graf (read-only)
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 15px; margin-bottom: 10px;'>Ringkasan Parameter Data</div>", unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Node Asal", st.session_state.asal)
            st.metric("Jumlah Node", len(st.session_state.node))
        with m_col2:
            st.metric("Kecepatan Kendaraan", f"{st.session_state.kecepatan} km/jam")
            st.metric("Jumlah Paket", len([v for i, v in enumerate(st.session_state.volume) if v > 0 and st.session_state.node[i] != st.session_state.asal]))
        with m_col3:
            st.metric("Kapasitas Kendaraan", f"{st.session_state.kapasitas} m³")
            # Hitung jumlah koneksi unik (i < j dan jarak > 0)
            jarak_matrix = np.array(st.session_state.jarak)
            num_edges = 0
            if jarak_matrix.ndim == 2:
                n_size = len(st.session_state.node)
                for i in range(n_size):
                    for j in range(i + 1, n_size):
                        if jarak_matrix[i][j] > 0:
                            num_edges += 1
            st.metric("Jumlah Koneksi Graf", f"{num_edges} Rute")
            
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 20px; margin-bottom: 10px;'>Matriks Jarak Antar Node (Graf)</div>", unsafe_allow_html=True)
        df_jarak = pd.DataFrame(st.session_state.jarak, index=st.session_state.node, columns=st.session_state.node)
        st.dataframe(df_jarak, use_container_width=True)
    else:
        st.session_state.data_valid = False
        st.markdown(f"<div class='status-panel-error'>Kesalahan Validasi Data:<br><b>{msg}</b></div>", unsafe_allow_html=True)
        st.info("Harap perbaiki data di atas agar sistem menjadi valid dan tombol 'Selanjutnya >' aktif.")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------
# LANGKAH 3 - VISUALISASI GRAF
# -----------------
elif current_step == 3:
    st.markdown("<div class='dashboard-card'><div class='card-title'>Visualisasi Graf</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 13px; color: #64748b; margin-bottom: 15px;'>Gunakan scroll mouse untuk memperbesar/memperkecil visualisasi graf (zoom). Klik dan seret (drag) node untuk mengubah posisinya, atau seret latar belakang untuk menggeser sudut pandang (pan).</div>", unsafe_allow_html=True)
    
    render_interactive_graph(st.session_state.node, st.session_state.jarak, st.session_state.asal)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------
# LANGKAH 4 - HASIL
# -----------------
elif current_step == 4:
    st.markdown("<div class='dashboard-card'><div class='card-title'>Proses Distribusi</div>", unsafe_allow_html=True)
    
    asal_awal = st.session_state.asal
    
    if st.session_state.riwayat_langkah is None:
        if st.button("Jalankan Simulasi", type="primary", use_container_width=True):
            load_state_to_globals()
            
            # Animasi Progress Bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            for percent in range(1, 101):
                time.sleep(0.01)
                progress_bar.progress(percent)
                status_text.text(f"Memproses optimasi rute... {percent}%")
                
            # Jalankan simulasi riil
            riwayat = algoritma.proses_pengiriman()
            st.session_state.riwayat_langkah = riwayat
            status_text.text("Simulasi selesai.")
            st.rerun()
    else:
        st.success("Simulasi selesai dijalankan.")
        
        # Tampilkan Visualisasi Graf Animasi dengan Player Controls
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 15px; margin-bottom: 10px;'>Visualisasi Pergerakan Distribusi</div>", unsafe_allow_html=True)
        render_animated_graph(st.session_state.node, st.session_state.jarak, st.session_state.asal, st.session_state.riwayat_langkah)
        
        # Ambil riwayat hasil
        riwayat_langkah = st.session_state.riwayat_langkah
        
        delivered_map = {}
        for idx, step in enumerate(riwayat_langkah, start=1):
            delivered_map[step["tujuan"]] = {
                "langkah": idx,
                "jarak": step["jarak"],
                "waktu_tempuh": step["waktu_tempuh"],
                "skor": step["skor"],
                "rute": " -> ".join(step["rute"])
            }
            
        rows_hasil = []
        for i in range(len(st.session_state.node)):
            node_name = st.session_state.node[i]
            vol = st.session_state.volume[i]
            prio = st.session_state.prioritas[i]
            dline = st.session_state.deadline[i]
            
            if node_name == asal_awal:
                rows_hasil.append({
                    "Tujuan": node_name,
                    "Volume": vol,
                    "Prioritas": prio,
                    "Deadline": dline,
                    "Jarak": 0.0,
                    "Waktu Tempuh": 0.0,
                    "Skor": 0.0,
                    "Status Pengiriman": "Asal",
                    "Rute": "Titik Awal"
                })
            elif node_name in delivered_map:
                info = delivered_map[node_name]
                rows_hasil.append({
                    "Tujuan": node_name,
                    "Volume": vol,
                    "Prioritas": prio,
                    "Deadline": dline,
                    "Jarak": float(round(info["jarak"], 2)),
                    "Waktu Tempuh": float(round(info["waktu_tempuh"], 2)),
                    "Skor": float(round(info["skor"], 2)),
                    "Status Pengiriman": "Terkirim",
                    "Rute": info["rute"]
                })
            else:
                rows_hasil.append({
                    "Tujuan": node_name,
                    "Volume": vol,
                    "Prioritas": prio,
                    "Deadline": dline,
                    "Jarak": 0.0,
                    "Waktu Tempuh": 0.0,
                    "Skor": 0.0,
                    "Status Pengiriman": "Belum Terkirim",
                    "Rute": "-"
                })
                
        df_tabel_hasil = pd.DataFrame(rows_hasil)
        
        # Hasil Distribusi dengan Sort, Filter, Pagination, Export
        st.markdown("<div class='card-title' style='margin-top:20px;'>Hasil Distribusi</div>", unsafe_allow_html=True)
        
        # Filters UI
        st.markdown("<div style='font-size: 13px; font-weight: 600; color: #475569;'>Filter Data</div>", unsafe_allow_html=True)
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            cari_node = st.text_input("Cari Nama Node Tujuan:", value="", placeholder="Ketik nama node...")
        with f_col2:
            status_pilih = st.selectbox("Status Pengiriman:", ["Semua", "Terkirim", "Belum Terkirim", "Asal"])
            
        # Terapkan Filter
        df_filtered = df_tabel_hasil.copy()
        if cari_node.strip():
            df_filtered = df_filtered[df_filtered["Tujuan"].str.contains(cari_node.strip(), case=False)]
        if status_pilih != "Semua":
            df_filtered = df_filtered[df_filtered["Status Pengiriman"] == status_pilih]
            
        # Pagination UI
        st.markdown("<div style='font-size: 13px; font-weight: 600; color: #475569; margin-top: 15px;'>Pagination</div>", unsafe_allow_html=True)
        
        page_size = 5
        total_rows = len(df_filtered)
        if total_rows > 0:
            total_pages = math.ceil(total_rows / page_size)
            
            if st.session_state.table_page > total_pages:
                st.session_state.table_page = total_pages
            if st.session_state.table_page < 1:
                st.session_state.table_page = 1
                
            start_row = (st.session_state.table_page - 1) * page_size
            end_row = st.session_state.table_page * page_size
            df_page = df_filtered.iloc[start_row:end_row].copy()
            
            # Sisipkan kolom No index sebagai nomor urut rata tengah
            df_page.insert(0, "No", range(start_row + 1, start_row + len(df_page) + 1))
            
            # Render Tabel dengan data alignment yang sesuai:
            # Index center, teks left, angka rata kanan.
            st.dataframe(
                df_page,
                column_config={
                    "No": st.column_config.NumberColumn(label="No", alignment="center"),
                    "Tujuan": st.column_config.TextColumn(label="Tujuan", alignment="left"),
                    "Volume": st.column_config.NumberColumn(label="Volume", alignment="right"),
                    "Prioritas": st.column_config.NumberColumn(label="Prioritas", alignment="right"),
                    "Deadline": st.column_config.NumberColumn(label="Deadline", alignment="right"),
                    "Jarak": st.column_config.NumberColumn(label="Jarak (km)", alignment="right"),
                    "Waktu Tempuh": st.column_config.NumberColumn(label="Waktu Tempuh (menit)", alignment="right"),
                    "Skor": st.column_config.NumberColumn(label="Skor", alignment="right"),
                    "Status Pengiriman": st.column_config.TextColumn(label="Status Pengiriman", alignment="left"),
                    "Rute": st.column_config.TextColumn(label="Rute", alignment="left")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Navigasi halaman berbentuk tombol < dan > di bagian bawah (bukan + dan -)
            pag_col1, pag_col2, pag_col3 = st.columns([1, 4, 1])
            with pag_col1:
                if st.button("<", key="btn_pag_prev", disabled=(st.session_state.table_page == 1), use_container_width=True):
                    st.session_state.table_page -= 1
                    st.rerun()
            with pag_col2:
                st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 14px; padding-top: 6px;'>Halaman {st.session_state.table_page} dari {total_pages}</div>", unsafe_allow_html=True)
            with pag_col3:
                if st.button(">", key="btn_pag_next", disabled=(st.session_state.table_page == total_pages), use_container_width=True):
                    st.session_state.table_page += 1
                    st.rerun()
        else:
            st.info("Tidak ada data yang cocok dengan kriteria pencarian/filter.")
            
        # Export CSV Button
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.write("")
        st.download_button(
            label="Ekspor CSV Hasil Perhitungan",
            data=csv_data,
            file_name="hasil_distribusi.csv",
            mime="text/csv"
        )
        
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------
# LANGKAH 5 - RINGKASAN
# -----------------
elif current_step == 5:
    st.markdown("<div class='dashboard-card'><div class='card-title'>Ringkasan</div>", unsafe_allow_html=True)
    
    asal_awal = st.session_state.asal
    riwayat_langkah = st.session_state.riwayat_langkah
    
    if riwayat_langkah is not None:
        total_terkirim_vol = st.session_state.kapasitas - algoritma.sisa_kapasitas
        paket_terkirim_list = algoritma.hasil_pengiriman[1:]
        paket_belum_terkirim_list = [
            n for n in st.session_state.node 
            if n not in algoritma.hasil_pengiriman and n != asal_awal
        ]
        total_jarak = sum(step["jarak"] for step in riwayat_langkah)
        total_waktu = sum(step["waktu_tempuh"] for step in riwayat_langkah)
        node_awal = st.session_state.asal
        node_akhir = riwayat_langkah[-1]["tujuan"] if riwayat_langkah else asal_awal
        
        # Tampilkan Rute Pengiriman
        rute_pengiriman_str = asal_awal
        for step in riwayat_langkah:
            rute_pengiriman_str += f" -> {step['tujuan']}"
            
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 15px; margin-bottom: 15px;'>Ringkasan Hasil Operasional</div>", unsafe_allow_html=True)
        
        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            st.markdown(f"""
            <div style='background-color:#ffffff; border:1px solid #e2e8f0; padding:16px; border-radius:6px; height: 100%; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);'>
                <div style='font-size:13px; font-weight:600; color:#475569; margin-bottom:12px; text-transform:uppercase; border-bottom:1px solid #f1f5f9; padding-bottom:6px;'>Parameter Rute</div>
                <table style='width:100%; font-size:14px; border-collapse:collapse;'>
                    <tr style='border-bottom:1px solid #f1f5f9;'><td style='padding:8px 0; color:#64748b;'>Node Awal</td><td style='padding:8px 0; text-align:right; font-weight:600;'>{node_awal}</td></tr>
                    <tr style='border-bottom:1px solid #f1f5f9;'><td style='padding:8px 0; color:#64748b;'>Node Akhir</td><td style='padding:8px 0; text-align:right; font-weight:600;'>{node_akhir}</td></tr>
                    <tr style='border-bottom:1px solid #f1f5f9;'><td style='padding:8px 0; color:#64748b;'>Total Jarak Tempuh</td><td style='padding:8px 0; text-align:right; font-weight:600;'>{round(total_jarak, 2)} km</td></tr>
                    <tr><td style='padding:8px 0; color:#64748b;'>Total Waktu Tempuh</td><td style='padding:8px 0; text-align:right; font-weight:600;'>{round(total_waktu, 1)} menit</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
        with col_sum2:
            total_paket_tujuan = len(st.session_state.node) - 1
            pct_paket = (len(paket_terkirim_list) / total_paket_tujuan * 100) if total_paket_tujuan > 0 else 0.0
            pct_kapasitas = (total_terkirim_vol / st.session_state.kapasitas * 100) if st.session_state.kapasitas > 0 else 0.0
            
            st.markdown(f"""
            <div style='background-color:#ffffff; border:1px solid #e2e8f0; padding:16px; border-radius:6px; height: 100%; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);'>
                <div style='font-size:13px; font-weight:600; color:#475569; margin-bottom:12px; text-transform:uppercase; border-bottom:1px solid #f1f5f9; padding-bottom:6px;'>Parameter Pengiriman</div>
                <table style='width:100%; font-size:14px; border-collapse:collapse;'>
                    <tr style='border-bottom:1px solid #f1f5f9;'><td style='padding:8px 0; color:#64748b;'>Total Paket Terkirim</td><td style='padding:8px 0; text-align:right; font-weight:600; color:#166534;'>{len(paket_terkirim_list)} Paket ({round(pct_paket, 1)}%)</td></tr>
                    <tr style='border-bottom:1px solid #f1f5f9;'><td style='padding:8px 0; color:#64748b;'>Total Paket Gagal</td><td style='padding:8px 0; text-align:right; font-weight:600; color:#991b1b;'>{len(paket_belum_terkirim_list)} Paket</td></tr>
                    <tr style='border-bottom:1px solid #f1f5f9;'><td style='padding:8px 0; color:#64748b;'>Kapasitas Terpakai</td><td style='padding:8px 0; text-align:right; font-weight:600;'>{total_terkirim_vol} m³ ({round(pct_kapasitas, 1)}%)</td></tr>
                    <tr><td style='padding:8px 0; color:#64748b;'>Kapasitas Tersisa</td><td style='padding:8px 0; text-align:right; font-weight:600;'>{st.session_state.kapasitas - total_terkirim_vol} m³</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 10px; margin-bottom: 10px;'>Rute Akhir Distribusi</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: 500; font-family: monospace;'>{rute_pengiriman_str}</div>", unsafe_allow_html=True)
        
        # Tampilkan visualisasi graf hasil akhir
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 25px; margin-bottom: 10px;'>Visualisasi Rute Akhir Graf</div>", unsafe_allow_html=True)
        
        # Penanda Urutan Perjalanan Rute di atas canvas
        rute_nodes = [asal_awal] + [step["tujuan"] for step in riwayat_langkah]
        rute_badges = []
        for idx, node_name in enumerate(rute_nodes):
            if idx == 0:
                rute_badges.append(f"<span style='background-color: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 13px;'>{node_name} (Asal)</span>")
            else:
                rute_badges.append(f"<span style='background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 13px;'>{node_name}</span>")
        
        rute_path_html = f"""
        <div style='display: flex; flex-wrap: wrap; align-items: center; gap: 8px; background-color: #ffffff; border: 1px solid #e2e8f0; padding: 12px 16px; border-radius: 6px; margin-bottom: 15px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
            <span style='color: #475569; font-weight: 600; font-size: 13px; margin-right: 4px; text-transform: uppercase; letter-spacing: 0.5px;'>Urutan Distribusi:</span>
            {" <span style='color: #94a3b8; font-weight: bold;'>➔</span> ".join(rute_badges)}
        </div>
        """
        st.markdown(rute_path_html, unsafe_allow_html=True)
        
        render_final_graph(st.session_state.node, st.session_state.jarak, st.session_state.asal, st.session_state.riwayat_langkah)
        
        # Progres bar visual
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 25px; margin-bottom: 10px;'>Visualisasi Progres Distribusi</div>", unsafe_allow_html=True)
        
        col_prog1, col_prog2 = st.columns(2)
        with col_prog1:
            st.write(f"**Progres Volume Kapasitas Terpakai:** {total_terkirim_vol} m³ / {st.session_state.kapasitas} m³ ({round(pct_kapasitas, 1)}%)")
            st.progress(total_terkirim_vol / st.session_state.kapasitas)
        with col_prog2:
            st.write(f"**Progres Paket Berhasil Terkirim:** {len(paket_terkirim_list)} / {total_paket_tujuan} Paket ({round(pct_paket, 1)}%)")
            st.progress(len(paket_terkirim_list) / total_paket_tujuan if total_paket_tujuan > 0 else 0.0)
            
        # Timeline Perjalanan
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1e293b; margin-top: 30px; margin-bottom: 15px;'>Timeline Perjalanan Kurir</div>", unsafe_allow_html=True)
        st.markdown(render_timeline(riwayat_langkah, asal_awal), unsafe_allow_html=True)
            
    else:
        st.warning("Data simulasi belum tersedia. Harap selesaikan proses di Langkah 4 terlebih dahulu.")
        
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------
# TOMBOL NAVIGASI ALUR WIZARD (DI BAGIAN BAWAH)
# -----------------
st.write("")
nav_col1, nav_col2 = st.columns(2)

# Gunakan pelabelan bersyarat sesuai dengan step
if current_step in [4, 5]:
    prev_label = "<"
    next_label = ">"
else:
    prev_label = "< Sebelumnya"
    next_label = "Selanjutnya >"

with nav_col1:
    is_prev_disabled = (current_step == 1)
    if st.button(prev_label, disabled=is_prev_disabled, use_container_width=True, key="btn_nav_prev"):
        st.session_state.current_step -= 1
        st.rerun()
        
with nav_col2:
    is_next_disabled = False
    if current_step == 1 and not st.session_state.data_loaded:
        is_next_disabled = True
    elif current_step == 2 and not st.session_state.data_valid:
        is_next_disabled = True
    elif current_step == 4 and st.session_state.riwayat_langkah is None:
        is_next_disabled = True
    elif current_step == 5:
        is_next_disabled = True
        
    # Tambahan tombol reset di langkah terakhir jika diinginkan untuk mempermudah alur simulasi baru
    if current_step == 5:
        if st.button("Ulangi Simulasi", type="primary", use_container_width=True, key="btn_nav_reset"):
            st.session_state.current_step = 1
            st.session_state.riwayat_langkah = None
            st.rerun()
    else:
        if st.button(next_label, disabled=is_next_disabled, use_container_width=True, key="btn_nav_next"):
            st.session_state.current_step += 1
            st.rerun()