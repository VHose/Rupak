# app.py
import streamlit as st
from algoritma import hitung_dijkstra, urutkan_paket_greedy

st.title("Simulasi Rute Kurir Paket Optimal 🚚")

# Input dari pengguna di sidebar
st.sidebar.header("Pengaturan Simulasi")
kapasitas_awal = st.sidebar.number_input("Kapasitas Maksimal Kendaraan", min_value=10, max_value=100)
posisi_awal = st.sidebar.selectbox("Posisi Awal Kurir (Node)", [0, 1, 2, 3, 4, 5])

# Tombol untuk menjalankan simulasi
if st.button("Mulai Pengiriman"):
    st.write(f"Kurir berangkat dari Node {posisi_awal} dengan kapasitas {kapasitas_awal}...")
    
    # Panggil fungsi logikamu di sini
    # jarak, rute = hitung_dijkstra(graf_data, posisi_awal)
    
    # Tampilkan hasilnya
    st.success("Simulasi Selesai!")
    st.subheader("Rute Perjalanan:")
    # st.write(rute)
    