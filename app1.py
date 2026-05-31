import io
from pathlib import Path

import algoritma as alg
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

TEMPLATE_PATH = Path(__file__).parent / "template_adjacency_20node.xlsx"

WARNA_DEPOT = "#e74c3c"
WARNA_TERTERIMA = "#27ae60"
WARNA_GAGAL = "#95a5a6"
WARNA_NORMAL = "#3498db"
WARNA_EDGE = "#bdc3c7"
WARNA_RUTE = "#e67e22"


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
    nodes = [f"Node{i + 1}" for i in range(jumlah_node)]

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
            "3. Node asal di aplikasi = baris pertama di sheet Paket (Node1) atau pilih manual di sidebar.",
            "4. Matriks adjacency harus simetris (jarak A->B = B->A).",
            "5. Minimal 20 node sudah disediakan, bisa ditambah/diubah namanya asalkan konsisten antar sheet.",
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


def layout_graf(graf, n_node):
    if n_node <= 12:
        return nx.spring_layout(graf, seed=42, k=1.8 / max(n_node ** 0.5, 1))
    if nx.is_connected(graf):
        return nx.kamada_kawai_layout(graf)
    return nx.spring_layout(graf, seed=42, k=2.0 / max(n_node ** 0.5, 1))


def kumpulkan_edge_dari_rute(detail_pengiriman):
    edges = set()
    for item in detail_pengiriman:
        path = [p.strip() for p in item["rute"].split(" -> ")]
        for i in range(len(path) - 1):
            edges.add(tuple(sorted((path[i], path[i + 1]))))
    return edges


def gambar_graf(
    nodes,
    jarak,
    asal=None,
    paket_berhasil=None,
    paket_gagal=None,
    detail_pengiriman=None,
    judul="Visualisasi Graf Jaringan",
):
    paket_berhasil = paket_berhasil or []
    paket_gagal = paket_gagal or []
    detail_pengiriman = detail_pengiriman or []

    graf = buat_graf(nodes, jarak)
    pos = layout_graf(graf, len(nodes))
    edge_rute = kumpulkan_edge_dari_rute(detail_pengiriman)

    fig, ax = plt.subplots(figsize=(12, 8))

    node_colors = []
    node_sizes = []
    for n in graf.nodes():
        if n == asal:
            node_colors.append(WARNA_DEPOT)
            node_sizes.append(900)
        elif n in paket_berhasil:
            node_colors.append(WARNA_TERTERIMA)
            node_sizes.append(700)
        elif n in paket_gagal:
            node_colors.append(WARNA_GAGAL)
            node_sizes.append(550)
        else:
            node_colors.append(WARNA_NORMAL)
            node_sizes.append(600)

    edge_normal = [(u, v) for u, v in graf.edges() if tuple(sorted((u, v))) not in edge_rute]
    edge_highlight = [(u, v) for u, v in graf.edges() if tuple(sorted((u, v))) in edge_rute]

    nx.draw_networkx_edges(graf, pos, edgelist=edge_normal, width=1.5, edge_color=WARNA_EDGE, alpha=0.7, ax=ax)
    if edge_highlight:
        nx.draw_networkx_edges(
            graf, pos, edgelist=edge_highlight, width=3.5, edge_color=WARNA_RUTE, alpha=0.95, ax=ax
        )

    nx.draw_networkx_nodes(graf, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_labels(graf, pos, font_size=9, font_weight="bold", ax=ax)

    edge_labels = nx.get_edge_attributes(graf, "weight")
    nx.draw_networkx_edge_labels(graf, pos, edge_labels=edge_labels, font_size=7, ax=ax)

    ax.set_title(judul, fontsize=14, fontweight="bold", pad=16)
    ax.axis("off")

    legend_items = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=WARNA_DEPOT, markersize=12, label="Depot / Asal"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=WARNA_TERTERIMA, markersize=12, label="Paket terkirim"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=WARNA_GAGAL, markersize=12, label="Paket tidak terkirim"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=WARNA_NORMAL, markersize=12, label="Node lain"),
        plt.Line2D([0], [0], color=WARNA_RUTE, linewidth=3, label="Jalur rute pengiriman"),
        plt.Line2D([0], [0], color=WARNA_EDGE, linewidth=1.5, label="Jalur graf (km)"),
    ]
    ax.legend(handles=legend_items, loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8)

    fig.tight_layout()
    return fig


def tampilkan_visualisasi_graf(nodes, jarak, asal=None, hasil=None):
    with st.expander("Visualisasi Graf Jaringan", expanded=hasil is not None):
        if hasil:
            fig = gambar_graf(
                nodes,
                jarak,
                asal=asal,
                paket_berhasil=hasil.get("paket_berhasil", []),
                paket_gagal=hasil.get("paket_gagal", []),
                detail_pengiriman=hasil.get("detail", []),
                judul="Graf Jaringan + Rute Pengiriman",
            )
        else:
            fig = gambar_graf(nodes, jarak, asal=asal, judul="Graf Jaringan (Adjacency)")
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "Angka pada garis = jarak (km). "
            "Garis oranye tebal = jalur yang dilalui kurir berdasarkan Dijkstra."
        )


def main():
    st.set_page_config(page_title="Simulasi Rute Kurir", page_icon="🚚", layout="wide")
    pastikan_template_ada()

    st.title("Simulasi Rute Kurir Paket Optimal")
    st.caption("Berdasarkan algoritma Dijkstra + filter greedy (volume, deadline, skor)")

    tab_manual, tab_excel = st.tabs(["Input Manual", "Import Excel"])

    if "sim_data" not in st.session_state:
        st.session_state.sim_data = None

    with tab_excel:
        st.subheader("Import Data dari Excel")
        st.markdown(
            "Upload file Excel dengan sheet *Adjacency* (matriks jarak) dan *Paket* (volume, prioritas, deadline)."
        )

        col_dl, col_up = st.columns([1, 2])
        with col_dl:
            template_bytes = TEMPLATE_PATH.read_bytes()
            st.download_button(
                label="Download Template Excel (20 Node)",
                data=template_bytes,
                file_name="template_adjacency_20node.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with col_up:
            uploaded = st.file_uploader(
                "Upload file Excel (.xlsx)",
                type=["xlsx"],
                key="upload_excel",
            )

        if uploaded:
            try:
                data = baca_excel(uploaded)
                st.session_state.sim_data = data

                st.success(f"Berhasil membaca {len(data['nodes'])} node dari Excel.")
                st.write("*Daftar Node:*", ", ".join(data["nodes"]))
                st.write("*Matriks Adjacency:*")
                tampilkan_matriks(data["jarak"], data["nodes"])

                df_paket = pd.DataFrame({
                    "Node": data["nodes"],
                    "Volume": data["volume"],
                    "Prioritas": data["prioritas"],
                    "Deadline": data["deadline"],
                })
                st.write("*Data Paket:*")
                st.dataframe(df_paket, use_container_width=True)
            except Exception as e:
                st.error(f"Gagal membaca Excel: {e}")

    with tab_manual:
        st.subheader("Input Manual")
        n_manual = st.number_input("Jumlah Node", min_value=2, max_value=50, value=5, step=1)

        nama_nodes = []
        cols = st.columns(min(int(n_manual), 4))
        for i in range(int(n_manual)):
            with cols[i % len(cols)]:
                nama = st.text_input(f"Node {i + 1}", value=f"Node{i + 1}", key=f"node_{i}")
            nama_nodes.append(nama.strip())

        if len(set(nama_nodes)) != len(nama_nodes):
            st.warning("Nama node harus unik.")
        else:
            st.write("*Matriks Adjacency* (0 = diri sendiri, -1 = tidak terhubung, >0 = jarak km)")
            jarak_manual = []
            for i in range(int(n_manual)):
                row = []
                cols_j = st.columns(int(n_manual))
                for j in range(int(n_manual)):
                    default = 0 if i == j else -1
                    with cols_j[j]:
                        val = st.number_input(
                            f"{nama_nodes[i]}-{nama_nodes[j]}",
                            value=default,
                            step=1,
                            key=f"adj_{i}_{j}",
                            label_visibility="collapsed",
                        )
                    row.append(int(val))
                jarak_manual.append(row)

            st.write("*Data Paket per Node*")
            vol_m, prio_m, dl_m = [], [], []
            for i, nama in enumerate(nama_nodes):
                c1, c2, c3 = st.columns(3)
                with c1:
                    v = st.number_input(f"Volume {nama}", min_value=0, value=5, key=f"vol_{i}")
                with c2:
                    p = st.number_input(f"Prioritas {nama}", min_value=0, max_value=3, value=2, key=f"prio_{i}")
                with c3:
                    d = st.number_input(f"Deadline {nama} (jam)", min_value=0.0, value=2.0, step=0.5, key=f"dl_{i}")
                vol_m.append(int(v))
                prio_m.append(int(p))
                dl_m.append(float(d))

            if st.button("Gunakan Input Manual", key="btn_manual"):
                st.session_state.sim_data = {
                    "nodes": nama_nodes,
                    "jarak": jarak_manual,
                    "volume": vol_m,
                    "prioritas": prio_m,
                    "deadline": dl_m,
                }
                st.success("Data manual tersimpan. Scroll ke bawah untuk menjalankan simulasi.")

    st.divider()
    st.subheader("Pengaturan Truk & Simulasi")

    sim_data = st.session_state.sim_data
    if sim_data and sim_data.get("nodes"):
        nodes = sim_data["nodes"]
        jarak = sim_data["jarak"]
        volume = sim_data["volume"]
        prioritas = sim_data["prioritas"]
        deadline = sim_data["deadline"]
        asal = st.selectbox("Node Asal (Depot)", nodes)
        kecepatan = st.number_input("Kecepatan Truk (km/jam)", min_value=1, value=40)
        kapasitas = st.number_input("Kapasitas Maksimal (m²)", min_value=1, value=50)

        idx_asal = nodes.index(asal)
        if volume[idx_asal] != 0 or prioritas[idx_asal] != 0:
            st.info(f"Node asal '{asal}' akan dianggap depot (tanpa paket).")

        tampilkan_visualisasi_graf(nodes, jarak, asal=asal)

        if st.button("Mulai Simulasi Pengiriman", type="primary"):
            vol_copy = list(volume)
            prio_copy = list(prioritas)
            dl_copy = list(deadline)
            vol_copy[idx_asal] = 0
            prio_copy[idx_asal] = 0
            dl_copy[idx_asal] = 0.0

            set_data_algoritma(
                nodes, jarak, vol_copy, prio_copy, dl_copy, asal, int(kecepatan), int(kapasitas)
            )

            try:
                hasil = alg.jalankan_simulasi()
                st.session_state.hasil_simulasi = hasil

                st.success("Simulasi selesai!")
                c1, c2, c3 = st.columns(3)
                c1.metric("Volume Terkirim", f"{hasil['volume_terkirim']} m²")
                c2.metric("Sisa Kapasitas", f"{hasil['sisa_kapasitas']} m²")
                c3.metric("Paket Berhasil", len(hasil["paket_berhasil"]))

                st.markdown(f"*Rute Pengantaran:* {hasil['rute_pengantaran']}")

                tampilkan_visualisasi_graf(nodes, jarak, asal=asal, hasil=hasil)

                if hasil["detail"]:
                    st.write("*Detail Tiap Pengiriman:*")
                    st.dataframe(pd.DataFrame(hasil["detail"]), use_container_width=True)

                col_ok, col_fail = st.columns(2)
                with col_ok:
                    st.write("*Paket Terkirim:*")
                    if hasil["paket_berhasil"]:
                        for p in hasil["paket_berhasil"]:
                            st.write(f"- {p}")
                    else:
                        st.write("Tidak ada")

                with col_fail:
                    st.write("*Paket Tidak Terkirim:*")
                    if hasil["paket_gagal"]:
                        for p in hasil["paket_gagal"]:
                            st.write(f"- {p}")
                    else:
                        st.write("Semua paket terkirim")

            except Exception as e:
                st.error(f"Error simulasi: {e}")
    else:
        st.info("Silakan isi data di tab *Input Manual* atau *Import Excel* terlebih dahulu.")


if __name__ == "__main__":
    main()