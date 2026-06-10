# Laporan Progress Project

## Identitas
* **Nama Anggota**: 
  1. Hans Maulana Budiputra (NRP: 2472052)
  2. Valentino Hose (NRP: [Isi NRP Valentino])
  3. [Nama Anda / Sikma] (NRP: 2472020)
* **Topik**: Sistem Optimasi Distribusi Paket Menggunakan Algoritma Dijkstra dan Greedy
* **Nama Project**: Sistem Optimasi Distribusi Paket
* **Link GitHub**: https://github.com/VHose/Rupak.git (Private)

## Ringkasan Topik
Proyek ini membangun sistem simulasi distribusi paket untuk menentukan rute pengiriman yang paling efisien dengan menggabungkan algoritma Dijkstra (untuk mencari rute terpendek) dan pendekatan Greedy Heuristik (untuk menyeleksi urutan paket berdasarkan berat, prioritas, deadline, serta batas waktu operasional kurir).

---

## Progress Pengerjaan Saat Ini
Saat ini project sudah masuk tahap integrasi penuh antara core logic algoritma dan tampilan UI web interaktif. Berkas utama yang digunakan dalam sistem ini adalah app2.py untuk antarmuka pengguna (UI) dan algorithma.py untuk core logic simulasi rute.
* **Estimasi progress project saat ini**: sekitar 90%.
* **Bagian yang masih belum selesai**:
  - Testing skenario batas (testing dengan jumlah node yang sangat besar dan penanganan node terisolasi).
  - Penyusunan dokumentasi akhir serta laporan formal projek.

---

## Fitur yang Sudah Dikerjakan

Berikut adalah rincian tugas dan fitur yang telah berhasil diselesaikan oleh masing-masing anggota kelompok beserta potongan code dan penjelasannya:

### A. Dikerjakan oleh Hans Maulana Budiputra (NRP: 2472052)

#### 1. Implementasi Algoritma Dijkstra Teroptimasi
Bagian ini digunakan untuk mencari jarak terpendek dari node asal ke semua node tujuan dengan penanganan tipe data yang lebih aman.
* **Potongan code**:
```python
dijkstra = [float('inf')] * n
dijkstra[idx_asal] = 0

while len(visited) < n:
    min_jarak = float('inf')
    for i in range(n):
        if node[i] not in visited and dijkstra[i] < min_jarak:
            min_jarak = dijkstra[i]
            idx_visited = i
```
* **Penjelasan**:
Program mencari node dengan jarak paling kecil yang belum dikunjungi menggunakan inisialisasi float('inf') standar Python untuk mencegah infinite loop jika ada node yang tidak terhubung sama sekali pada graf.

#### 2. Filter Deadline Akumulatif & Batas Operasional Kurir
Program menghitung estimasi waktu tempuh akumulatif kurir lalu membandingkannya dengan deadline paket dan jam operasional harian.
* **Potongan code**:
```python
waktu_leg = hasil[idx] / kecepatan_per_menit
waktu_tiba = waktu_akumulasi + waktu_leg
deadline_paket = deadline[idx] * 60

if waktu_tiba > deadline_paket:
    idx_paket_tersedia.remove(idx)
elif waktu_tiba > batas_menit:
    idx_paket_tersedia.remove(idx)
```
* **Penjelasan**:
Penyaringan tidak lagi didasarkan pada waktu tempuh per kaki perjalanan (leg) melainkan waktu akumulasi kedatangan kurir terhitung dari depot keberangkatan. Jika waktu tiba melebihi deadline atau melampaui sisa jam kerja kurir, paket otomatis dibatalkan dari daftar.

#### 3. Pemilihan Paket Greedy dengan Penyesuaian Urgensi
Program mengevaluasi kelayakan paket terbaik berdasarkan kombinasi bobot prioritas dan deadline yang lebih mendesak.
* **Potongan code**:
```python
# Deadline yang lebih cepat (kecil) diprioritaskan dengan tanda minus
skor = (prioritas[idx] * 10) - (deadline[idx] * 2) - (volume[idx] / 10) - (waktu_tiba / 10)
```
* **Penjelasan**:
Skor dihitung dengan mengurangi nilai jika tenggat waktu paket (deadline) semakin lama. Ini memastikan paket dengan tenggat waktu terdekat akan mendapatkan skor tertinggi untuk dikirim terlebih dahulu.

#### 4. Rekonstruksi Rute Fisik Kurir
Program melacak rute fisik kurir secara komprehensif, mencakup titik transit/node perantara hasil Dijkstra.
* **Potongan code**:
```python
# Reconstruksi rute fisik kaki ini
rute_leg = rute[idx_terpilih]
if len(rute_leg) > 1:
    rute_fisik_list.extend(rute_leg[1:])
```
* **Penjelasan**:
Bagian ini digunakan untuk menggabungkan jalur fisik yang sesungguhnya dilewati oleh kurir, membedakan antara rute penurunan paket dengan rute perjalanan fisik yang dilalui kendaraan kurir.

---

### B. Dikerjakan oleh [Nama Anda / Sikma] (NRP: 2472020)

#### 1. Desain Tampilan UI Dashboard Premium
Program mengimplementasikan layout multi-tab modern menggunakan framework Streamlit dengan kustomisasi visual CSS.
* **Potongan code**:
```python
st.set_page_config(
    page_title="Simulasi Rute Kurir Paket Optimal",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)
```
* **Penjelasan**:
Konfigurasi ini membagi layar menjadi layout lebar (wide) dengan menu kontrol di sebelah kiri (sidebar) dan ruang visualisasi utama di bagian kanan untuk mempermudah operasional simulator.

#### 2. Visualisasi Graf Jaringan Logistik Interaktif (Plotly)
Program menggambar graf jaringan jalan dan rute logistik menggunakan library Plotly agar lebih interaktif.
* **Potongan code**:
```python
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
```
* **Penjelasan**:
Fungsi ini membangun graf hubungan logistik menggunakan Plotly go.Scatter. Jalur rute optimal kurir ditandai secara visual dengan garis tebal oranye yang interaktif.

#### 3. Interaktivitas Klik Node & Detail Status
Program mendeteksi node graf yang diklik oleh pengguna untuk menampilkan informasi detail lokasi pengiriman secara instan.
* **Potongan code**:
```python
state_val = st.session_state.get("graf_utama")
if state_val and "selection" in state_val and state_val["selection"].get("points"):
    point = state_val["selection"]["points"][0]
    node_terpilih = point.get("customdata")
```
* **Penjelasan**:
Program menangkap koordinat titik yang diklik oleh kursor pengguna pada bagan Plotly dan mengubah status node terpilih untuk memicu pembaruan data informasi detail lokasi pengantaran.

#### 4. Pengelolaan Lokasi Logistik Dinamis
Program memungkinkan penambahan dan penghapusan lokasi pengantaran secara langsung dari menu antarmuka web.
* **Potongan code**:
```python
def tambah_node(nama):
    if not nama or nama in st.session_state.nodes:
        return False
    st.session_state.nodes.append(nama)
    sync_list_size()
    sync_jarak_matrix()
    st.session_state.hasil_simulasi = None
    return True
```
* **Penjelasan**:
Ketika lokasi baru ditambahkan dari antarmuka, program menyinkronkan ukuran daftar variabel paket dan meregenerasi matriks jarak agar lokasi baru siap terhubung dengan rute logistik.

---

### C. Dikerjakan oleh Valentino Hose (NRP: [Isi NRP Valentino])

#### 1. Integrasi Unggah & Pembacaan Data Excel
Program membaca konfigurasi matriks jarak dan spesifikasi paket langsung dari file Excel yang diunggah pengguna.
* **Potongan code**:
```python
uploaded = st.file_uploader("Import Excel", type=["xlsx"], key="upload_excel")
if uploaded:
    try:
        data = baca_excel(uploaded)
        st.session_state.nodes = data["nodes"]
        st.session_state.jarak = data["jarak"]
```
* **Penjelasan**:
Fungsi file uploader menerima berkas Excel eksternal dan memparsing sheet Adjacency serta Paket ke dalam memori aplikasi secara langsung tanpa input manual berulang.

#### 2. Unduh Template Konfigurasi Jaringan
Program memfasilitasi pembuatan dan pengunduhan template data Excel untuk mempermudah input massal.
* **Potongan code**:
```python
st.download_button(
    "Download Template",
    data=TEMPLATE_PATH.read_bytes(),
    file_name="template_adjacency_20node.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
```
* **Penjelasan**:
Tombol ini mengekspor berkas spreadsheet biner berformat xlsx yang sudah dilengkapi dengan data contoh 20 node jalan dan paket sebagai dasar pengisian bagi pengguna.

---

## Kendala Selama Pengerjaan
Beberapa kendala yang ditemui selama pengerjaan:
* Membedakan pelacakan rute pengantaran logis dengan rute transit fisik yang dilalui kendaraan kurir.
* Mengubah perhitungan deadline agar menggunakan akumulasi waktu kedatangan di lokasi (waktu_tiba) ketimbang waktu tempuh satu kaki pengantaran.
* Formulasi bobot skor greedy agar secara akurat menyeimbangkan parameter prioritas paket dengan kedekatan batas waktu (deadline) paket.
* Transisi visualisasi graf dari statis matplotlib menjadi dinamis menggunakan plotly agar mendukung interaksi klik node dan pergeseran koordinat.

---

## Yang Akan Dikerjakan Selanjutnya

### 1. Testing Skenario Ekstrim dan Validasi Input
* **Estimasi**: 1–2 hari
* **Target**:
  - Menguji performa sistem pada graf >30 node
  - Mengidentifikasi ketahanan sistem saat ada node yang terisolasi
  - Memvalidasi input angka agar tidak bernilai negatif atau berisi karakter ilegal

### 2. Pembersihan dan Refaktorisasi Codebase
* **Estimasi**: 1 hari
* **Target**:
  - Melakukan pembersihan berkas cadangan/usang (seperti app1.py, app.py lama, algoritma.py lama)
  - Menyinkronkan daftar pustaka dependensi pada requirements.txt
  - Merapikan penataan dokumentasi komentar internal kode

### 3. Penyusunan Dokumentasi Akhir (ReadMe)
* **Estimasi**: 1–2 hari
* **Target**:
  - Menulis berkas ReadMe untuk petunjuk instalasi dan kebutuhan environment sistem
  - Mendokumentasikan spesifikasi format masukan file Excel
  - Membuat petunjuk pengoperasian dashboard Streamlit

### 4. Finalisasi Laporan Projek dan Persiapan Presentasi
* **Estimasi**: 1 hari
* **Target**:
  - Menyusun berkas slide presentasi
  - Mempersiapkan simulasi skenario demo aplikasi untuk presentasi akhir di depan penguji

---

## Kesimpulan
Core logic simulator logistik pada berkas algorithma.py dan dashboard antarmuka pada berkas app2.py sudah berhasil diintegrasikan dengan kemajuan 90%. Sistem saat ini mampu menentukan rute terpendek menggunakan Dijkstra, memfilter kelayakan pengiriman paket berdasarkan kapasitas kendaraan dan deadline akumulatif, menyeleksi urgensi paket menggunakan Greedy, serta memvisualisasikannya secara interaktif di halaman web. Tahap berikutnya akan difokuskan pada pengujian batas, pembersihan codebase, dan penyusunan berkas dokumentasi penunjang.
