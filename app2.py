# app.py
import io
from pathlib import Path

import algorithma as alg
import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

TEMPLATE_PATH = Path(__file__).parent / "template_adjacency_20node.xlsx"

WARNA_DEPOT = "#4a7bb7"
WARNA_TERTERIMA = "#51cf66"
WARNA_GAGAL = "#868e96"
WARNA_NORMAL = "#8b9cb3"
WARNA_EDGE = "#5c6670"
WARNA_EDGE_DEPOT = "#4a7bb7"
WARNA_RUTE = "#ffa94d"
BG_GRAF = "#2b2d31"


def nama_node_huruf(index: int) -> str:
    """Konversi indeks ke huruf: 0=A, 1=B, ..., 25=Z, 26=AA, ..."""
    nama = ""
    i = index
    while True:
        nama = chr(ord("A") + i % 26) + nama
        i = i // 26 - 1
        if i < 0:
            break
    return nama


def buat_daftar_nama(jumlah: int) -> list[str]:
    return [nama_node_huruf(i) for i in range(jumlah)]


def nama_node_baru(nodes: list[str]) -> str:
    for i in range(702):
        nama = nama_node_huruf(i)
        if nama not in nodes:
            return nama
    return f"X{len(nodes)}"


def reset_globals():
    alg.n = 0
    alg.asal = ""
    alg.node = []
    alg.kecepatan = 0
    alg.kapasitas = 0
    alg.deadline = []
    alg.prioritas = []
    alg.volume = []
    alg.jarak = []
    alg.rute = []
    alg.sisa_kapasitas = 0
    alg.idx_paket_tersedia = []
    alg.waktu_tempuh = []
    alg.hasil_efisien = []


def buat_template_excel(jumlah_node: int = 20) -> bytes:
    nodes = buat_daftar_nama(jumlah_node)

    adj = np.full((jumlah_node, jumlah_node), -1, dtype=int)
    np.fill_diagonal(adj, 0)

    for i in range(jumlah_node):
        for j in range(i + 1, jumlah_node):
            if j == i + 1 or (i % 4 == 0 and j == i + 4) or (i % 5 == 0 and j == i + 5):
                jarak = ((i + j) % 7 + 1) * 5
                adj[i, j] = adj[j, i] = jarak

    df_adj = pd.DataFrame(adj, index=nodes, columns=nodes)

    df_paket = pd.DataFrame({
        "Node": nodes,
        "Volume (m2)": [0 if i == 0 else (i % 5) + 3 for i in range(jumlah_node)],
        "Prioritas (1-3)": [0 if i == 0 else ((i % 3) + 1) for i in range(jumlah_node)],
        "Deadline (jam)": [0.0 if i == 0 else round(1.5 + (i % 6) * 0.5, 1) for i in range(jumlah_node)],
    })

    df_info = pd.DataFrame({
        "Petunjuk": [
            "1. Sheet 'Adjacency': isi jarak antar node. 0 = node sendiri, -1 = tidak terhubung, >0 = jarak (km).",
            "2. Sheet 'Paket': isi data paket per node. Node asal/deposit: Volume=0, Prioritas=0, Deadline=0.",
            "3. Node asal/deposit = A (baris pertama). Pilih depot di sidebar aplikasi.",
            "4. Matriks adjacency harus simetris (jarak A->B = B->A).",
            "5. Template berisi 20 lokasi: A s/d T.",
        ]
    })

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_info.to_excel(writer, sheet_name="Petunjuk", index=False)
        df_adj.to_excel(writer, sheet_name="Adjacency")
        df_paket.to_excel(writer, sheet_name="Paket", index=False)
    buffer.seek(0)
    return buffer.getvalue()


def pastikan_template_ada():
    if not TEMPLATE_PATH.exists():
        TEMPLATE_PATH.write_bytes(buat_template_excel(20))


def baca_excel(file) -> dict:
    xls = pd.ExcelFile(file)

    if "Adjacency" not in xls.sheet_names:
        raise ValueError("Sheet 'Adjacency' tidak ditemukan di file Excel.")

    df_adj = pd.read_excel(xls, sheet_name="Adjacency", index_col=0)
    nodes = [str(x).strip() for x in df_adj.index.tolist()]
    columns = [str(x).strip() for x in df_adj.columns.tolist()]

    if nodes != columns:
        raise ValueError("Nama baris dan kolom di sheet Adjacency harus sama.")

    if len(nodes) < 2:
        raise ValueError("Minimal harus ada 2 node.")

    jarak = df_adj.astype(float).fillna(-1).astype(int).values.tolist()
    n = len(nodes)

    for i in range(n):
        jarak[i][i] = 0

    prioritas = [0] * n
    volume = [0] * n
    deadline = [0.0] * n

    if "Paket" in xls.sheet_names:
        df_paket = pd.read_excel(xls, sheet_name="Paket")
        df_paket.columns = [str(c).strip().lower() for c in df_paket.columns]

        col_node = next((c for c in df_paket.columns if "node" in c), None)
        col_vol = next((c for c in df_paket.columns if "volume" in c), None)
        col_prio = next((c for c in df_paket.columns if "prioritas" in c), None)
        col_deadline = next((c for c in df_paket.columns if "deadline" in c), None)

        if col_node:
            paket_map = {}
            for _, row in df_paket.iterrows():
                nama = str(row[col_node]).strip()
                paket_map[nama] = row

            for i, nama in enumerate(nodes):
                if nama in paket_map:
                    row = paket_map[nama]
                    if col_vol:
                        volume[i] = int(row[col_vol])
                    if col_prio:
                        prioritas[i] = int(row[col_prio])
                    if col_deadline:
                        deadline[i] = float(row[col_deadline])

    return {
        "nodes": nodes,
        "jarak": jarak,
        "volume": volume,
        "prioritas": prioritas,
        "deadline": deadline,
    }


def set_data_algoritma(nodes, jarak, volume, prioritas, deadline, asal, kecepatan, kapasitas):
    reset_globals()
    alg.n = len(nodes)
    alg.node = nodes
    alg.jarak = jarak
    alg.volume = volume
    alg.prioritas = prioritas
    alg.deadline = deadline
    alg.asal = asal
    alg.kecepatan = kecepatan
    alg.kapasitas = kapasitas
    alg.sisa_kapasitas = kapasitas
    alg.hasil_efisien = [asal]


def tampilkan_matriks(jarak, nodes):
    df = pd.DataFrame(jarak, index=nodes, columns=nodes)
    st.dataframe(df, use_container_width=True)


def buat_graf(nodes, jarak):
    graf = nx.Graph()
    for nama in nodes:
        graf.add_node(nama)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if jarak[i][j] > 0:
                graf.add_edge(nodes[i], nodes[j], weight=jarak[i][j])
    return graf


def pisahkan_node(pos, min_jarak=1.0, tetap=None, iterasi=200):
    """Dorong node yang terlalu rapat agar tidak saling timpa."""
    tetap = set(tetap or [])
    nodes = list(pos.keys())
    pos_arr = {n: np.array(pos[n], dtype=float) for n in nodes}

    for _ in range(iterasi):
        ada_geser = False
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                delta = pos_arr[a] - pos_arr[b]
                dist = float(np.linalg.norm(delta))
                if dist >= min_jarak or dist < 1e-9:
                    continue
                dorong = (min_jarak - dist) / 2.0 * (delta / dist)
                if a not in tetap:
                    pos_arr[a] += dorong
                    ada_geser = True
                if b not in tetap:
                    pos_arr[b] -= dorong
                    ada_geser = True
        if not ada_geser:
            break
    return pos_arr


def layout_graf(graf, n_node, asal=None):
    """Layout organik dengan jarak antar node cukup lebar."""
    skala = max(12.0, n_node * 1.1)
    k = skala / max(n_node ** 0.3, 1.5)

    try:
        if nx.is_connected(graf):
            pos = nx.kamada_kawai_layout(graf, scale=skala)
        else:
            raise nx.NetworkXError
    except (nx.NetworkXError, ValueError, ImportError, ModuleNotFoundError):
        pos = nx.spring_layout(graf, seed=42, k=k, iterations=600, scale=skala)

    min_jarak = 1.4 + n_node * 0.07
    pos = pisahkan_node(pos, min_jarak=min_jarak)

    if asal and asal in pos:
        lain = [n for n in pos if n != asal]
        if lain:
            cx = np.mean([pos[n][0] for n in lain])
            cy = np.mean([pos[n][1] for n in lain])
            for n in pos:
                pos[n] = np.array(pos[n]) - np.array([cx, cy])

        pos[asal] = np.array([0.0, skala * 0.65])
        for n in lain:
            x, y = pos[n]
            pos[n] = np.array([x * 1.35, y * 1.35 - skala * 0.45])

        pos = pisahkan_node(pos, min_jarak=min_jarak, tetap=[asal])

    return pos


def style_edge(u, v, is_rute, node_terpilih=None):
    if is_rute:
        return WARNA_RUTE, 3.5
    if node_terpilih and (u == node_terpilih or v == node_terpilih):
        return "#3b82f6", 3.0  # Biru untuk rute/koneksi lokasi yang diklik
    return WARNA_EDGE, 1.2


def kumpulkan_edge_dari_rute(detail_pengiriman):
    edges = set()
    for item in detail_pengiriman:
        path = [p.strip() for p in item["rute"].split(" -> ")]
        for i in range(len(path) - 1):
            edges.add(tuple(sorted((path[i], path[i + 1]))))
    return edges


def status_node(n, asal, paket_berhasil, paket_gagal):
    if n == asal:
        return "Depot / Asal"
    if n in paket_berhasil:
        return "Paket terkirim"
    if n in paket_gagal:
        return "Paket tidak terkirim"
    return "Lokasi pengiriman"


def warna_node(n, asal, paket_berhasil, paket_gagal):
    if n == asal:
        return WARNA_DEPOT
    if n in paket_berhasil:
        return WARNA_TERTERIMA
    if n in paket_gagal:
        return WARNA_GAGAL
    return WARNA_NORMAL


def ukuran_node(n, asal, n_node):
    if n == asal:
        return 32 if n_node <= 15 else 26
    if n_node <= 10:
        return 22
    if n_node <= 20:
        return 16
    return 14


def tetangga_node(idx, nodes, jarak):
    daftar = []
    for j, nama in enumerate(nodes):
        if idx != j and jarak[idx][j] > 0:
            daftar.append(f"{nama} ({jarak[idx][j]} km)")
    return daftar


def buat_figure_graf(
    nodes,
    jarak,
    asal=None,
    paket_berhasil=None,
    paket_gagal=None,
    detail_pengiriman=None,
    judul="Peta Rute Pengantaran Paket",
    node_terpilih=None,
):
    paket_berhasil = paket_berhasil or []
    paket_gagal = paket_gagal or []
    detail_pengiriman = detail_pengiriman or []

    graf = buat_graf(nodes, jarak)
    pos = layout_graf(graf, len(nodes), asal=asal)
    edge_rute = kumpulkan_edge_dari_rute(detail_pengiriman)
    n_node = len(nodes)

    fig = go.Figure()

    for u, v, data in graf.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        berat = data.get("weight", 0)
        key = tuple(sorted((u, v)))
        is_rute = key in edge_rute
        warna_edge, lebar_edge = style_edge(u, v, is_rute, node_terpilih)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2

        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=warna_edge, width=lebar_edge),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[mx],
                y=[my],
                mode="text",
                text=[str(berat)],
                textfont=dict(size=10, color="#ced4da"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    node_x, node_y, node_warna, node_label, node_size = [], [], [], [], []
    anotasi = []
    for i, n in enumerate(graf.nodes()):
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        node_warna.append(warna_node(n, asal, paket_berhasil, paket_gagal))
        node_label.append(n)
        node_size.append(ukuran_node(n, asal, n_node))

        sudut = 2 * np.pi * i / max(n_node, 1)
        offset_y = -0.55 - 0.08 * n_node
        offset_x = 0.35 * np.cos(sudut)
        anotasi.append(
            dict(
                x=x + offset_x,
                y=y + offset_y,
                text=n,
                showarrow=False,
                font=dict(size=10, color="#e9ecef"),
                xanchor="center",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            marker=dict(
                size=node_size,
                color=node_warna,
                line=dict(width=1.5, color="#495057"),
            ),
            customdata=node_label,
            hovertemplate="<b>%{customdata}</b><extra></extra>",
            showlegend=False,
        )
    )

    xs, ys = node_x, node_y
    pad = max(2.0, n_node * 0.35)

    fig.update_layout(
        title=dict(text=judul, x=0.5, font=dict(color="#e9ecef", size=16)),
        paper_bgcolor=BG_GRAF,
        plot_bgcolor=BG_GRAF,
        annotations=anotasi,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[min(xs) - pad, max(xs) + pad],
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[min(ys) - pad, max(ys) + pad],
        ),
        margin=dict(l=30, r=30, t=50, b=30),
        height=max(600, n_node * 38),
        dragmode="pan",
        hovermode="closest",
    )
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    return fig


def tampilkan_info_node(node, nodes, jarak, asal, volume, prioritas, deadline, hasil=None):
    idx = nodes.index(node)
    paket_berhasil = hasil.get("paket_berhasil", []) if hasil else []
    paket_gagal = hasil.get("paket_gagal", []) if hasil else []
    status = status_node(node, asal, paket_berhasil, paket_gagal)
    tetangga = tetangga_node(idx, nodes, jarak)

    st.markdown(f"#### {node}")
    st.markdown(f"**Status:** {status}")

    if node != asal and volume and prioritas is not None and deadline is not None:
        prio_label = {0: "-", 1: "Rendah", 2: "Sedang", 3: "Tinggi"}.get(prioritas[idx], str(prioritas[idx]))
        st.markdown(f"**Volume:** {volume[idx]} m²")
        st.markdown(f"**Prioritas:** {prio_label}")
        st.markdown(f"**Deadline:** {deadline[idx]} jam")

    if tetangga:
        st.markdown("**Tetangga:** " + ", ".join(tetangga))
    else:
        st.markdown("**Tetangga:** tidak ada koneksi")

    if hasil:
        for item in hasil.get("detail", []):
            if item["tujuan"] == node:
                st.markdown(f"**Rute pengiriman:** {item['rute']}")
                st.markdown(f"**Jarak tempuh:** {item['jarak']} km")
                break


@st.fragment
def tampilkan_visualisasi_graf(
    nodes,
    jarak,
    asal=None,
    hasil=None,
    volume=None,
    prioritas=None,
    deadline=None,
):
    if len(nodes) < 2:
        st.info("Tambahkan minimal 2 node di sidebar untuk menampilkan graf.")
        return

    # Tentukan node terpilih sebelum merender grafik
    node_terpilih = None
    state_val = st.session_state.get("graf_utama")
    if state_val and "selection" in state_val and state_val["selection"].get("points"):
        point = state_val["selection"]["points"][0]
        node_terpilih = point.get("customdata")
        if not node_terpilih:
            idx_pt = point["point_index"]
            node_terpilih = nodes[idx_pt] if idx_pt < len(nodes) else None
        st.session_state.node_terpilih = node_terpilih
    elif st.session_state.get("node_terpilih") in nodes:
        node_terpilih = st.session_state.node_terpilih

    judul = (
        "Peta Rute Pengantaran Paket — Hasil Simulasi"
        if hasil
        else "Peta Rute Pengantaran Paket"
    )
    
    fig = buat_figure_graf(
        nodes,
        jarak,
        asal=asal,
        paket_berhasil=hasil.get("paket_berhasil", []) if hasil else [],
        paket_gagal=hasil.get("paket_gagal", []) if hasil else [],
        detail_pengiriman=hasil.get("detail", []) if hasil else [],
        judul=judul,
        node_terpilih=node_terpilih,
    )

    st.caption("Scroll untuk zoom · drag untuk geser · double-click reset zoom · klik node untuk info")

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="graf_utama",
        config={
            "scrollZoom": True,
            "doubleClick": "reset",
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
        },
    )


    c1, v1 = None, None  # Placeholder if needed, but let's just keep the original columns block below

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f"<span style='color:{WARNA_DEPOT}'>●</span> Depot", unsafe_allow_html=True)
    c2.markdown(f"<span style='color:{WARNA_TERTERIMA}'>●</span> Terkirim", unsafe_allow_html=True)
    c3.markdown(f"<span style='color:{WARNA_GAGAL}'>●</span> Gagal", unsafe_allow_html=True)
    c4.markdown(f"<span style='color:{WARNA_NORMAL}'>●</span> Lokasi paket", unsafe_allow_html=True)
    c5.markdown(f"<span style='color:{WARNA_RUTE}'>—</span> Rute kurir", unsafe_allow_html=True)
    c6.markdown(f"<span style='color:#3b82f6'>—</span> Koneksi lokasi terpilih", unsafe_allow_html=True)

    if node_terpilih:
        with st.container(border=True):
            tampilkan_info_node(
                node_terpilih, nodes, jarak, asal, volume, prioritas, deadline, hasil
            )


def init_session():
    if st.session_state.get("inited"):
        return
    st.session_state.inited = True
    st.session_state.nodes = ["A", "B", "C", "D"]
    st.session_state.jarak = [
        [0, 10, -1, 15],
        [10, 0, 5, -1],
        [-1, 5, 0, 8],
        [15, -1, 8, 0],
    ]
    st.session_state.volume = [0, 5, 4, 6]
    st.session_state.prioritas = [0, 2, 1, 2]
    st.session_state.deadline = [0.0, 2.0, 3.0, 2.5]
    st.session_state.asal = "A"
    st.session_state.kecepatan = 40
    st.session_state.kapasitas = 50
    st.session_state.hasil_simulasi = None
    st.session_state.sim_run_done = False
    st.session_state.node_terpilih = None
    st.session_state._jarak_nodes = ["A", "B", "C", "D"]


def sync_list_size():
    n = len(st.session_state.nodes)
    for key, default in [("volume", 5), ("prioritas", 2), ("deadline", 2.0)]:
        lst = st.session_state[key]
        while len(lst) < n:
            lst.append(default)
        del lst[n:]


def sync_jarak_matrix():
    nodes = st.session_state.nodes
    n = len(nodes)
    old = st.session_state.jarak
    baru = [[0 if i == j else -1 for j in range(n)] for i in range(n)]
    old_nodes = st.session_state.get("_jarak_nodes", nodes[: len(old)] if old else [])

    for i, ni in enumerate(nodes):
        for j, nj in enumerate(nodes):
            if i == j:
                continue
            if ni in old_nodes and nj in old_nodes:
                oi, oj = old_nodes.index(ni), old_nodes.index(nj)
                if oi < len(old) and oj < len(old[oi]):
                    baru[i][j] = old[oi][oj]
    st.session_state.jarak = baru
    st.session_state._jarak_nodes = list(nodes)


def tambah_node(nama):
    if not nama or nama in st.session_state.nodes:
        return False
    st.session_state.nodes.append(nama)
    sync_list_size()
    sync_jarak_matrix()
    st.session_state.hasil_simulasi = None
    return True


def hapus_node(nama):
    if nama not in st.session_state.nodes or len(st.session_state.nodes) <= 2:
        return False
    idx = st.session_state.nodes.index(nama)
    st.session_state.nodes.pop(idx)
    for key in ("volume", "prioritas", "deadline"):
        st.session_state[key].pop(idx)
    sync_jarak_matrix()
    if st.session_state.asal == nama:
        st.session_state.asal = st.session_state.nodes[0]
    if st.session_state.node_terpilih == nama:
        st.session_state.node_terpilih = None
    st.session_state.hasil_simulasi = None
    return True


def set_edge(dari, ke, jarak_km):
    nodes = st.session_state.nodes
    if dari not in nodes or ke not in nodes or dari == ke:
        return False
    i, j = nodes.index(dari), nodes.index(ke)
    st.session_state.jarak[i][j] = int(jarak_km)
    st.session_state.jarak[j][i] = int(jarak_km)
    st.session_state._jarak_nodes = list(nodes)
    st.session_state.hasil_simulasi = None
    return True


def load_sample():
    data = baca_excel(TEMPLATE_PATH)
    st.session_state.nodes = data["nodes"]
    st.session_state.jarak = data["jarak"]
    st.session_state.volume = data["volume"]
    st.session_state.prioritas = data["prioritas"]
    st.session_state.deadline = data["deadline"]
    st.session_state.asal = data["nodes"][0]
    st.session_state._jarak_nodes = list(data["nodes"])
    st.session_state.hasil_simulasi = None
    st.session_state.sim_run_done = False
    st.session_state.node_terpilih = None


def jalankan_simulasi_sidebar():
    nodes = st.session_state.nodes
    asal = st.session_state.asal
    idx = nodes.index(asal)
    vol = list(st.session_state.volume)
    prio = list(st.session_state.prioritas)
    dl = list(st.session_state.deadline)
    vol[idx] = 0
    prio[idx] = 0
    dl[idx] = 0.0
    set_data_algoritma(
        nodes,
        st.session_state.jarak,
        vol,
        prio,
        dl,
        asal,
        int(st.session_state.kecepatan),
        int(st.session_state.kapasitas),
    )
    st.session_state.hasil_simulasi = alg.jalankan_simulasi()


def sidebar_input():
    st.sidebar.header("Konfigurasi Kendaraan")
    
    old_kecepatan = st.session_state.kecepatan
    new_kecepatan = st.sidebar.number_input(
        "Kecepatan (km/jam)", min_value=1, value=int(st.session_state.kecepatan)
    )
    
    old_kapasitas = st.session_state.kapasitas
    new_kapasitas = st.sidebar.number_input(
        "Kapasitas (m²)", min_value=1, value=int(st.session_state.kapasitas)
    )

    nodes = st.session_state.nodes
    idx_asal = nodes.index(st.session_state.asal) if st.session_state.asal in nodes else 0
    
    old_asal = st.session_state.asal
    new_asal = st.sidebar.selectbox("Depot Asal", nodes, index=idx_asal)

    # Cek jika ada parameter yang berubah untuk langsung update rute
    changed = (new_kecepatan != old_kecepatan) or (new_kapasitas != old_kapasitas) or (new_asal != old_asal)
    
    if changed:
        st.session_state.kecepatan = new_kecepatan
        st.session_state.kapasitas = new_kapasitas
        st.session_state.asal = new_asal
        if st.session_state.get("sim_run_done"):
            try:
                jalankan_simulasi_sidebar()
                st.session_state.sim_error = None
            except Exception as e:
                st.session_state.sim_error = str(e)
            st.rerun()

    st.sidebar.divider()
    tab_jaringan, tab_paket, tab_excel = st.sidebar.tabs(["Jaringan", "Paket", "Excel"])

    with tab_jaringan:
        if st.button("Load Sample (20 Node)", use_container_width=True):
            load_sample()
            st.rerun()

        st.subheader("Manajemen Lokasi")
        saran = nama_node_baru(nodes)
        nama_baru = st.text_input("Nama lokasi", placeholder=f"e.g. {saran}", value="")
        if st.button("Tambah Lokasi", use_container_width=True):
            tambah = nama_baru.strip().upper() or saran
            if tambah_node(tambah):
                st.rerun()

        st.caption(f"Daftar Lokasi ({len(nodes)})")
        for baris in range(0, len(nodes), 4):
            cols = st.columns(4)
            for col, nama in zip(cols, nodes[baris : baris + 4]):
                with col:
                    if st.button(f"{nama} ✕", key=f"del_{nama}", use_container_width=True):
                        if hapus_node(nama):
                            st.rerun()

        st.subheader("Koneksi Jalan")
        if len(nodes) >= 2:
            dari = st.selectbox("Dari Node", nodes, key="edge_dari")
            tujuan_opsi = [n for n in nodes if n != dari]
            ke = st.selectbox("Ke Node", tujuan_opsi, key="edge_ke")
            jarak_km = st.number_input("Jarak (km)", min_value=1, value=10, key="edge_jarak")
            if st.button("Tambah Koneksi", use_container_width=True):
                if set_edge(dari, ke, jarak_km):
                    st.rerun()
        else:
            st.caption("Butuh minimal 2 node untuk menambah koneksi.")

        st.divider()
        if st.button("Jalankan Simulasi", type="primary", use_container_width=True):
            try:
                jalankan_simulasi_sidebar()
                st.session_state.sim_run_done = True
                st.session_state.sim_error = None
            except Exception as e:
                st.session_state.sim_error = str(e)
            st.rerun()

    with tab_paket:
        sync_list_size()
        df_paket = pd.DataFrame({
            "Node": st.session_state.nodes,
            "Volume": st.session_state.volume,
            "Prioritas": st.session_state.prioritas,
            "Deadline": st.session_state.deadline,
        })
        edited = st.data_editor(df_paket, num_rows="fixed", use_container_width=True, key="editor_paket")
        st.session_state.volume = edited["Volume"].astype(int).tolist()
        st.session_state.prioritas = edited["Prioritas"].astype(int).tolist()
        st.session_state.deadline = edited["Deadline"].astype(float).tolist()

    with tab_excel:
        st.download_button(
            "Download Template",
            data=TEMPLATE_PATH.read_bytes(),
            file_name="template_adjacency_20node.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        uploaded = st.file_uploader("Import Excel", type=["xlsx"], key="upload_excel")
        if uploaded:
            try:
                data = baca_excel(uploaded)
                st.session_state.nodes = data["nodes"]
                st.session_state.jarak = data["jarak"]
                st.session_state.volume = data["volume"]
                st.session_state.prioritas = data["prioritas"]
                st.session_state.deadline = data["deadline"]
                st.session_state.asal = data["nodes"][0]
                st.session_state._jarak_nodes = list(data["nodes"])
                st.session_state.hasil_simulasi = None
                st.session_state.sim_run_done = False
                st.success(f"Loaded {len(data['nodes'])} node")
                st.rerun()
            except Exception as e:
                st.error(str(e))


def main():
    st.set_page_config(
        page_title="Simulasi Rute Kurir",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Sembunyikan Deploy, MainMenu (titik 3), Header, Footer, dan Status widget (logo running)
    st.markdown("""
        <style>
        header {visibility: hidden; display: none !important;}
        [data-testid="stHeader"] {visibility: hidden; display: none !important;}
        .stDeployButton {display: none !important;}
        #MainMenu {visibility: hidden; display: none !important;}
        footer {visibility: hidden; display: none !important;}
        [data-testid="stStatusWidget"] {visibility: hidden; display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    pastikan_template_ada()
    init_session()
    sync_list_size()
    sync_jarak_matrix()

    sidebar_input()

    st.title("Sistem Rute Pengantaran Paket")
    st.caption("Dijkstra + Greedy · Peta lokasi & rute kurir otomatis refresh dari sidebar")

    nodes = st.session_state.nodes
    hasil = st.session_state.get("hasil_simulasi")

    tampilkan_visualisasi_graf(
        nodes,
        st.session_state.jarak,
        asal=st.session_state.asal,
        hasil=hasil,
        volume=st.session_state.volume,
        prioritas=st.session_state.prioritas,
        deadline=st.session_state.deadline,
    )

    if st.session_state.get("sim_error"):
        st.error(f"Error simulasi: {st.session_state.sim_error}")

    if hasil:
        st.divider()
        st.subheader("Hasil Simulasi")
        c1, c2, c3 = st.columns(3)
        c1.metric("Volume Terkirim", f"{hasil['volume_terkirim']} m²")
        c2.metric("Sisa Kapasitas", f"{hasil['sisa_kapasitas']} m²")
        c3.metric("Paket Berhasil", len(hasil["paket_berhasil"]))
        st.markdown(f"**Rute Pengantaran:** `{hasil['rute_pengantaran']}`")

        if hasil["detail"]:
            st.dataframe(pd.DataFrame(hasil["detail"]), use_container_width=True)

        col_ok, col_fail = st.columns(2)
        with col_ok:
            st.markdown("**Paket Terkirim**")
            for p in hasil["paket_berhasil"] or ["_Tidak ada_"]:
                st.write(f"- {p}")
        with col_fail:
            st.markdown("**Paket Tidak Terkirim**")
            for p in hasil["paket_gagal"] or ["_Semua terkirim_"]:
                st.write(f"- {p}")


if __name__ == "__main__":
    main()
