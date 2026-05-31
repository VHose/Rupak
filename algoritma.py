# algoritma.py
import numpy as np
import csv
import os
import io

# ==========================================
# Inisialisasi Variabel Global
# ==========================================
n = 0                  # Jumlah total node
asal = ""              # Node asal pengiriman
node = []              # Daftar nama node
kecepatan = 0          # Kecepatan kendaraan (km/jam)
kapasitas = 0          # Kapasitas maksimal kendaraan
sisa_kapasitas = 0     # Sisa kapasitas kendaraan saat pengiriman
deadline = []          # Batas waktu paket masing-masing node (jam)
prioritas = []         # Tingkat prioritas paket masing-masing node (1-3)
volume = []            # Volume paket masing-masing node
jarak = []             # Adjacency matrix (numpy array) yang menyimpan jarak antar node
rute = []              # Jalur terpendek hasil Dijkstra ke masing-masing node
idx_paket_tersedia = []# Indeks paket yang memenuhi kriteria pengiriman berikutnya
waktu_tempuh = []      # Waktu tempuh ke masing-masing node
hasil_pengiriman = []  # Urutan rute pengiriman yang berhasil dilakukan

def hitung_dijkstra(start_node):
    global jarak, rute, n, node

    n = len(node)
    if start_node not in node:
        raise ValueError(f"Node '{start_node}' tidak ditemukan.")
    idx_asal = node.index(start_node)
    # jarak awal semua node dianggap belum terjangkau
    dijkstra = [float('inf')] * n
    dijkstra[idx_asal] = 0

    visited = []
    # simpan jalur ke tiap node
    rute = [[] for _ in range(n)]
    rute[idx_asal] = [start_node]

    while len(visited) < n:
        min_jarak = float('inf')
        idx_visited = -1
        # cari node dengan jarak paling kecil
        for i in range(n):
            if node[i] not in visited and dijkstra[i] < min_jarak:
                min_jarak = dijkstra[i]
                idx_visited = i
        # berhenti kalau tidak ada node yang bisa dilanjutkan
        if idx_visited == -1:
            break
        visited.append(node[idx_visited])
        # update jarak ke node tetangga
        for y in range(n):
            if (
                node[y] not in visited
                and jarak[idx_visited][y] > 0
            ):
                jarak_baru = (
                    dijkstra[idx_visited]
                    + jarak[idx_visited][y]
                )
                if jarak_baru < dijkstra[y]:
                    dijkstra[y] = jarak_baru
                    rute[y] = (
                        rute[idx_visited]
                        + [node[y]]
                    )
    return dijkstra


def filter_volume():
    global volume,sisa_kapasitas,idx_paket_tersedia,n,node,hasil_pengiriman,asal
    
    idx_paket_tersedia.clear()
    for i in range(n):
        kapasitas_cukup = volume[i] <= sisa_kapasitas
        belum_dikirim = node[i] not in hasil_pengiriman
        bukan_asal = node[i] != asal
        if kapasitas_cukup and belum_dikirim and bukan_asal:
            idx_paket_tersedia.append(i)


def filter_deadline(hasil):
    global kecepatan,deadline,idx_paket_tersedia,waktu_tempuh
    
    waktu_tempuh.clear()
    kecepatan_per_menit = kecepatan / 60

    for idx in list(idx_paket_tersedia):
        waktu = hasil[idx] / kecepatan_per_menit
        batas_waktu = deadline[idx] * 60
        if waktu > batas_waktu:
            idx_paket_tersedia.remove(idx)
        else:
            waktu_tempuh.append(waktu)


def filter_skor(hasil):
    global idx_paket_tersedia,volume, prioritas,deadline,kecepatan
    
    skor_terbaik = -float('inf')
    idx_terpilih = None
    kecepatan_per_menit = kecepatan / 60

    for idx in idx_paket_tersedia:
        waktu = hasil[idx] / kecepatan_per_menit
        skor = (
            (prioritas[idx] * 10)
            + (deadline[idx] / 100)
            - (volume[idx] / 10)
            - (waktu / 10)
        )
        if skor > skor_terbaik:
            skor_terbaik = skor
            idx_terpilih = idx
    return idx_terpilih, skor_terbaik


def input_node():
    while True:
        nama_node = input(f"Node {len(node) + 1}: ")

        if nama_node in node:
            print("Nama node sudah dipakai.")
        else:
            node.append(nama_node)
        if len(node) == n:
            break


def input_data_paket():
    for i in range(n):
        if node[i] == asal:
            prioritas.append(0)
            deadline.append(0.0)
            volume.append(0)
            continue
        print(f"\nData paket untuk node {node[i]}")

        vol = int(input("Volume paket : "))
        prio = int(input("Prioritas paket (1-3) : "))
        dline = float(input("Deadline paket (jam) : "))

        volume.append(vol)
        prioritas.append(prio)
        deadline.append(dline)


def input_jarak():
    global jarak

    jarak = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(jarak, 0)

    for i in range(n):
        print(f"\nKoneksi node {node[i]}")
        for j in range(i + 1, n):
            nilai = int(
                input(f"{node[i]} -> {node[j]} : ")
            )
            if nilai > 0:
                jarak[i][j] = nilai
                jarak[j][i] = nilai


def tampil_matrix():
    print("\nAdjacency Matrix")
    for i in range(n):
        for j in range(n):
            print(f"{jarak[i][j]:4}", end=" ")
        print()


def tampil_data_paket():

    print("\nData Paket")
    for i in range(n):
        print(
            f"{node[i]} | "
            f"Volume: {volume[i]} | "
            f"Prioritas: {prioritas[i]} | "
            f"Deadline: {deadline[i]}"
        )


def proses_pengiriman():
    global asal, sisa_kapasitas
    riwayat_langkah = []
    
    while sisa_kapasitas > 0:

        hasil = hitung_dijkstra(asal)
        filter_volume()
        filter_deadline(hasil)

        if not idx_paket_tersedia:
            print("\nTidak ada paket yang bisa dikirim lagi.")
            break

        idx_terpilih, skor = filter_skor(hasil)

        if idx_terpilih is None:
            break

        tujuan = node[idx_terpilih]
        hasil_pengiriman.append(tujuan)
        sisa_kapasitas -= volume[idx_terpilih]

        # Simpan info langkah untuk visualisasi web
        jarak_tempuh = hasil[idx_terpilih]
        waktu_menit = (jarak_tempuh / kecepatan) * 60
        langkah = {
            "tujuan": tujuan,
            "rute": list(rute[idx_terpilih]),
            "volume_paket": volume[idx_terpilih],
            "sisa_kapasitas": sisa_kapasitas,
            "skor": skor,
            "asal_sebelumnya": asal,
            "jarak": jarak_tempuh,
            "waktu_tempuh": waktu_menit
        }
        riwayat_langkah.append(langkah)

        print("\nPengiriman Selanjutnya")
        print(f"Tujuan          : {tujuan}")
        print(f"Rute            : {rute[idx_terpilih]}")
        print(f"Volume Paket    : {volume[idx_terpilih]}")
        print(f"Sisa Kapasitas  : {sisa_kapasitas}")
        print(f"Skor Paket      : {round(skor, 2)}")
        asal = tujuan
        
    return riwayat_langkah


def tampil_ringkasan():
    print("\n===== RINGKASAN =====")
    print(
        f"Rute Pengiriman : "
        f"{' -> '.join(hasil_pengiriman)}"
    )
    print(
        f"Total Volume Terkirim : "
        f"{kapasitas - sisa_kapasitas}"
    )

    berhasil = hasil_pengiriman[1:]
    gagal = [
        node[i]
        for i in range(n)
        if node[i] not in hasil_pengiriman
        and node[i] != asal
    ]
    print(f"Paket Terkirim  : {', '.join(berhasil)}")
    print(f"Paket Gagal     : {', '.join(gagal)}")

# ==========================================
# Fungsi Modular untuk Pembacaan & Validasi CSV
# ==========================================

def get_file_reader(file_source):
    """
    Membantu membuka file CSV baik dari path string (lokal)
    maupun objek file-like (seperti st.file_uploader pada Streamlit).
    """
    if isinstance(file_source, str):
        if not os.path.exists(file_source):
            raise FileNotFoundError(f"File tidak ditemukan di path: {file_source}")
        return open(file_source, mode='r', encoding='utf-8', newline='')
    elif hasattr(file_source, 'read'):
        # Jika berupa file-like object (StringIO / BytesIO)
        content = file_source.read()
        if hasattr(file_source, 'seek'):
            file_source.seek(0) # Kembalikan kursor ke awal agar bisa dibaca ulang jika perlu
            
        if isinstance(content, bytes):
            text_content = content.decode('utf-8')
        else:
            text_content = content
        return io.StringIO(text_content)
    else:
        raise TypeError("Sumber file harus berupa path (string) atau file-like object.")


def baca_data_paket(file_source):
    """
    Membaca file CSV data paket.
    Kolom wajib: 'node', 'volume', 'prioritas', 'deadline'
    Mengembalikan tuple: (list_node, list_volume, list_prioritas, list_deadline)
    """
    f = get_file_reader(file_source)
    try:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            raise ValueError("File CSV data paket kosong atau tidak memiliki header.")
            
        # Validasi kecocokan kolom header
        required = ['node', 'volume', 'prioritas', 'deadline']
        for r in required:
            if r not in headers:
                raise ValueError(f"Kolom header wajib '{r}' tidak ditemukan pada CSV data paket.")
                
        nodes_list = []
        volume_list = []
        prioritas_list = []
        deadline_list = []
        seen_nodes = set()
        
        for idx, row in enumerate(reader, start=2):
            if not row.get('node'):
                raise ValueError(f"Nama node pada baris {idx} kosong.")
                
            node_name = row['node'].strip()
            if node_name in seen_nodes:
                raise ValueError(f"Nama node '{node_name}' duplikat pada baris {idx} CSV data paket.")
            seen_nodes.add(node_name)
            
            # Validasi volume (harus integer >= 0)
            try:
                vol = int(row['volume'])
                if vol < 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(f"Volume paket untuk '{node_name}' pada baris {idx} harus berupa integer non-negatif.")
                
            # Validasi prioritas (harus integer >= 0)
            try:
                prio = int(row['prioritas'])
                if prio < 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(f"Prioritas paket untuk '{node_name}' pada baris {idx} harus berupa integer non-negatif.")
                
            # Validasi deadline (harus float >= 0)
            try:
                dline = float(row['deadline'])
                if dline < 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(f"Deadline paket untuk '{node_name}' pada baris {idx} harus berupa angka non-negatif.")
                
            nodes_list.append(node_name)
            volume_list.append(vol)
            prioritas_list.append(prio)
            deadline_list.append(dline)
            
        if not nodes_list:
            raise ValueError("File CSV data paket tidak berisi baris data.")
            
        return nodes_list, volume_list, prioritas_list, deadline_list
    finally:
        if isinstance(file_source, str):
            f.close()


def baca_matriks_jarak(file_source, daftar_node):
    """
    Membaca matriks ketetanggaan/jarak dari file CSV.
    Memvalidasi kesesuaian node matriks dengan daftar_node dari paket.
    Mengembalikan numpy ndarray berisi nilai jarak.
    """
    f = get_file_reader(file_source)
    try:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            raise ValueError("File CSV matriks jarak kosong.")
            
        header_kolom = rows[0]
        if not header_kolom:
            raise ValueError("Header matriks jarak kosong.")
            
        # Kolom pertama biasanya nama baris/node, header kolom sesungguhnya mulai dari indeks 1
        node_header_kolom = [n.strip() for n in header_kolom[1:]]
        
        # Validasi jumlah kolom node
        if len(node_header_kolom) != len(daftar_node):
            raise ValueError(f"Jumlah kolom node pada matriks jarak ({len(node_header_kolom)}) tidak sama dengan jumlah node paket ({len(daftar_node)}).")
            
        # Validasi kecocokan set node
        if set(node_header_kolom) != set(daftar_node):
            raise ValueError(f"Daftar node pada kolom matriks jarak tidak cocok dengan daftar node paket.")
            
        n_size = len(daftar_node)
        matriks_jarak = np.full((n_size, n_size), -1, dtype=int)
        
        baris_data = rows[1:]
        if len(baris_data) != n_size:
            raise ValueError(f"Jumlah baris data pada matriks jarak ({len(baris_data)}) tidak sama dengan jumlah node paket ({n_size}).")
            
        seen_row_nodes = set()
        for idx, row in enumerate(baris_data, start=2):
            if not row:
                continue
            row_node = row[0].strip()
            if row_node not in daftar_node:
                raise ValueError(f"Nama node baris '{row_node}' pada baris {idx} tidak ditemukan di daftar node paket.")
            if row_node in seen_row_nodes:
                raise ValueError(f"Nama node baris '{row_node}' duplikat pada baris {idx} matriks jarak.")
            seen_row_nodes.add(row_node)
            
            # Dapatkan indeks baris sesuai urutan daftar_node agar terpetakan secara konsisten
            idx_baris = daftar_node.index(row_node)
            
            nilai_jarak = row[1:]
            if len(nilai_jarak) != n_size:
                raise ValueError(f"Jumlah kolom jarak pada baris '{row_node}' (baris {idx}) tidak cocok. Ditemukan {len(nilai_jarak)}, diharapkan {n_size}.")
                
            for j in range(n_size):
                col_node = node_header_kolom[j]
                idx_kolom = daftar_node.index(col_node)
                
                try:
                    val = int(nilai_jarak[j])
                except ValueError:
                    raise ValueError(f"Jarak dari '{row_node}' ke '{col_node}' pada baris {idx} kolom {j+2} harus berupa integer.")
                    
                # Validasi jarak tidak boleh negatif selain -1
                if val < -1:
                    raise ValueError(f"Jarak dari '{row_node}' ke '{col_node}' tidak boleh negatif selain -1 (ditemukan: {val}).")
                    
                # Diagonal utama harus bernilai 0
                if idx_baris == idx_kolom and val != 0:
                    raise ValueError(f"Jarak dari node ke dirinya sendiri (diagonal '{row_node}' -> '{col_node}') harus bernilai 0.")
                    
                matriks_jarak[idx_baris][idx_kolom] = val
                
        if len(seen_row_nodes) != n_size:
            missing_nodes = set(daftar_node) - seen_row_nodes
            raise ValueError(f"Baris data untuk node berikut tidak ditemukan di matriks jarak: {missing_nodes}")
            
        # Validasi matriks harus simetris (graf tidak berarah)
        for i in range(n_size):
            for j in range(n_size):
                if matriks_jarak[i][j] != matriks_jarak[j][i]:
                    raise ValueError(f"Matriks jarak tidak simetris pada hubungan '{daftar_node[i]}' dan '{daftar_node[j]}'.")
                    
        return matriks_jarak
    finally:
        if isinstance(file_source, str):
            f.close()


def baca_konfigurasi(file_source, daftar_node):
    """
    Membaca parameter konfigurasi dari file CSV.
    Kolom wajib: 'asal', 'kecepatan', 'kapasitas'
    Mengembalikan dict berisi nilai parameter.
    """
    f = get_file_reader(file_source)
    try:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            raise ValueError("File CSV konfigurasi kosong atau tidak memiliki header.")
            
        required = ['asal', 'kecepatan', 'kapasitas']
        for r in required:
            if r not in headers:
                raise ValueError(f"Kolom header wajib '{r}' tidak ditemukan pada CSV konfigurasi.")
                
        rows = list(reader)
        if not rows:
            raise ValueError("File CSV konfigurasi tidak memiliki baris data.")
            
        row = rows[0]
        asal_val = row.get('asal')
        if not asal_val:
            raise ValueError("Nilai 'asal' pada konfigurasi tidak boleh kosong.")
        asal_val = asal_val.strip()
        
        if asal_val not in daftar_node:
            raise ValueError(f"Node asal '{asal_val}' tidak terdaftar pada list node paket.")
            
        try:
            kecepatan_val = float(row.get('kecepatan', 0))
            if kecepatan_val <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError("Nilai 'kecepatan' pada konfigurasi harus berupa angka positif.")
            
        try:
            kapasitas_val = int(row.get('kapasitas', 0))
            if kapasitas_val <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError("Nilai 'kapasitas' pada konfigurasi harus berupa integer positif.")
            
        return {
            "asal": asal_val,
            "kecepatan": kecepatan_val,
            "kapasitas": kapasitas_val
        }
    finally:
        if isinstance(file_source, str):
            f.close()


def load_all_csv(path_paket, path_jarak, path_config):
    """
    Mengintegrasikan pembacaan ketiga file CSV ke variabel global sistem
    sehingga alur pengiriman paket dapat dijalankan.
    """
    global n, node, volume, prioritas, deadline, jarak, asal, kecepatan, kapasitas, sisa_kapasitas
    global rute, idx_paket_tersedia, waktu_tempuh, hasil_pengiriman
    
    # Reset seluruh state pengiriman sebelum memuat data baru
    node = []
    volume = []
    prioritas = []
    deadline = []
    jarak = []
    rute = []
    idx_paket_tersedia = []
    waktu_tempuh = []
    hasil_pengiriman = []
    
    # 1. Baca & Validasi file data paket
    list_node, list_volume, list_prioritas, list_deadline = baca_data_paket(path_paket)
    
    # 2. Baca & Validasi matriks jarak
    matriks_jarak = baca_matriks_jarak(path_jarak, list_node)
    
    # 3. Baca & Validasi konfigurasi
    config = baca_konfigurasi(path_config, list_node)
    
    # Pindahkan ke variabel global
    node = list_node
    n = len(node)
    volume = list_volume
    prioritas = list_prioritas
    deadline = list_deadline
    jarak = matriks_jarak
    
    asal = config["asal"]
    kecepatan = config["kecepatan"]
    kapasitas = config["kapasitas"]
    sisa_kapasitas = kapasitas
    
    # Rute awal pengiriman diisi dengan node asal
    hasil_pengiriman.append(asal)


def baca_data_distribusi_tunggal(file_source):
    """
    Membaca satu file CSV yang berisi tiga jenis data sekaligus:
    konfigurasi, data paket, dan matriks jarak.
    Mengembalikan tuple: (list_node, list_volume, list_prioritas, list_deadline, matriks_jarak, asal, kecepatan, kapasitas)
    """
    f = get_file_reader(file_source)
    try:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            raise ValueError("File CSV kosong atau tidak memiliki header.")
            
        # Validasi kolom header wajib (7 pertama)
        required = ['tipe', 'node', 'volume', 'prioritas', 'deadline', 'kecepatan', 'kapasitas']
        for r in required:
            if r not in headers:
                raise ValueError(f"Kolom header wajib '{r}' tidak ditemukan dalam file CSV.")
                
        # Node list dari kolom sisa (matriks jarak)
        node_headers_matrix = [n.strip() for n in headers[7:]]
        if not node_headers_matrix:
            raise ValueError("Kolom node matriks jarak tidak terdeteksi di bagian kanan header CSV.")
            
        # Penampung data
        config_data = {}
        nodes_list = []
        volume_list = []
        prioritas_list = []
        deadline_list = []
        
        # Penampung baris jarak
        jarak_rows = {}
        
        seen_nodes_paket = set()
        
        for idx, row in enumerate(reader, start=2):
            tipe = row.get('tipe')
            if not tipe:
                continue
            tipe = tipe.strip().lower()
            
            if tipe == 'konfigurasi':
                # Baca konfigurasi
                asal_val = row.get('node')
                if not asal_val:
                    raise ValueError(f"Baris konfigurasi (baris {idx}) harus mencantumkan node asal di kolom 'node'.")
                asal_val = asal_val.strip()
                
                try:
                    kecepatan_val = float(row.get('kecepatan') or 0)
                    if kecepatan_val <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"Kecepatan kendaraan pada baris {idx} harus berupa angka positif.")
                    
                try:
                    kapasitas_val = int(row.get('kapasitas') or 0)
                    if kapasitas_val <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"Kapasitas kendaraan pada baris {idx} harus berupa integer positif.")
                    
                config_data = {
                    "asal": asal_val,
                    "kecepatan": kecepatan_val,
                    "kapasitas": kapasitas_val
                }
                
            elif tipe == 'paket':
                node_name = row.get('node')
                if not node_name:
                    raise ValueError(f"Nama node pada baris paket (baris {idx}) tidak boleh kosong.")
                node_name = node_name.strip()
                
                if node_name in seen_nodes_paket:
                    raise ValueError(f"Duplikasi node paket '{node_name}' terdeteksi pada baris {idx}.")
                seen_nodes_paket.add(node_name)
                
                try:
                    vol = int(row.get('volume') or 0)
                    if vol < 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"Volume paket untuk '{node_name}' pada baris {idx} harus berupa integer non-negatif.")
                    
                try:
                    prio = int(row.get('prioritas') or 0)
                    if prio < 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"Prioritas paket untuk '{node_name}' pada baris {idx} harus berupa integer non-negatif.")
                    
                try:
                    dline = float(row.get('deadline') or 0)
                    if dline < 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"Deadline paket untuk '{node_name}' pada baris {idx} harus berupa angka non-negatif.")
                    
                nodes_list.append(node_name)
                volume_list.append(vol)
                prioritas_list.append(prio)
                deadline_list.append(dline)
                
            elif tipe == 'jarak':
                row_node = row.get('node')
                if not row_node:
                    raise ValueError(f"Nama node baris jarak pada baris {idx} tidak boleh kosong.")
                row_node = row_node.strip()
                
                if row_node in jarak_rows:
                    raise ValueError(f"Duplikasi baris matriks jarak untuk node '{row_node}' terdeteksi pada baris {idx}.")
                
                # Baca kolom-kolom jarak
                distances = {}
                for col in node_headers_matrix:
                    dist_str = row.get(col)
                    if dist_str is None or dist_str.strip() == '':
                        raise ValueError(f"Nilai jarak dari '{row_node}' ke '{col}' tidak ditemukan pada baris {idx}.")
                    try:
                        val = int(dist_str)
                    except ValueError:
                        raise ValueError(f"Jarak dari '{row_node}' ke '{col}' pada baris {idx} harus berupa integer.")
                    if val < -1:
                        raise ValueError(f"Jarak dari '{row_node}' ke '{col}' tidak boleh negatif selain -1 (ditemukan: {val}).")
                    distances[col] = val
                    
                jarak_rows[row_node] = distances
                
        # --- VALIDASI HUBUNGAN DATA ---
        if not config_data:
            raise ValueError("Data konfigurasi distribusi tidak ditemukan dalam file CSV.")
            
        if not nodes_list:
            raise ValueError("Data paket tidak ditemukan dalam file CSV.")
            
        # Pastikan set node pada paket cocok dengan header kolom matriks jarak
        if set(nodes_list) != set(node_headers_matrix):
            raise ValueError("Daftar node pada data paket tidak cocok dengan kolom matriks jarak pada header.")
            
        # Pastikan set node pada paket cocok dengan nama baris matriks jarak
        if set(nodes_list) != set(jarak_rows.keys()):
            missing_rows = set(nodes_list) - set(jarak_rows.keys())
            raise ValueError(f"Baris data untuk node berikut tidak ditemukan di matriks jarak: {missing_rows}")
            
        # Konversi ke matriks numpy array berdasarkan urutan nodes_list
        n_size = len(nodes_list)
        matriks_jarak = np.full((n_size, n_size), -1, dtype=int)
        
        for i in range(n_size):
            u = nodes_list[i]
            for j in range(n_size):
                v = nodes_list[j]
                val = jarak_rows[u][v]
                
                # Diagonal utama harus 0
                if i == j and val != 0:
                    raise ValueError(f"Jarak dari node ke dirinya sendiri (diagonal '{u}' -> '{v}') harus bernilai 0.")
                    
                matriks_jarak[i][j] = val
                
        # Validasi simetris
        for i in range(n_size):
            for j in range(n_size):
                if matriks_jarak[i][j] != matriks_jarak[j][i]:
                    raise ValueError(f"Matriks jarak tidak simetris pada hubungan '{nodes_list[i]}' dan '{nodes_list[j]}'.")
                    
        # Validasi node asal konfigurasi terdaftar
        asal = config_data["asal"]
        if asal not in nodes_list:
            raise ValueError(f"Node asal '{asal}' pada konfigurasi tidak terdaftar dalam data paket.")
            
        return nodes_list, volume_list, prioritas_list, deadline_list, matriks_jarak, asal, config_data["kecepatan"], config_data["kapasitas"]
    finally:
        if isinstance(file_source, str):
            f.close()


def load_single_csv(file_source):
    """
    Membaca satu file CSV distribusi tunggal dan memperbarui variabel global program.
    """
    global n, node, volume, prioritas, deadline, jarak, asal, kecepatan, kapasitas, sisa_kapasitas
    global rute, idx_paket_tersedia, waktu_tempuh, hasil_pengiriman
    
    # Reset seluruh state pengiriman sebelum memuat data baru
    node = []
    volume = []
    prioritas = []
    deadline = []
    jarak = []
    rute = []
    idx_paket_tersedia = []
    waktu_tempuh = []
    hasil_pengiriman = []
    
    # Baca & validasi
    list_node, list_volume, list_prioritas, list_deadline, matriks_jarak, asal_node, kec, kap = baca_data_distribusi_tunggal(file_source)
    
    # Pindahkan ke variabel global
    node = list_node
    n = len(node)
    volume = list_volume
    prioritas = list_prioritas
    deadline = list_deadline
    jarak = matriks_jarak
    asal = asal_node
    kecepatan = kec
    kapasitas = kap
    sisa_kapasitas = kapasitas
    
    # Rute awal pengiriman diisi dengan node asal
    hasil_pengiriman.append(asal)


def main():
    print("=== SIMULASI DISTRIBUSI PAKET (CSV INPUT TUNGGAL) ===\n")
    
    # Meminta path file CSV dengan nilai default jika kosong
    path_csv = input("Masukkan path file CSV distribusi tunggal (default: distribusi.csv): ").strip() or "distribusi.csv"
    
    print("\nMembaca dan memvalidasi file CSV...")
    try:
        load_single_csv(path_csv)
        print("Data berhasil dimuat dari file CSV!")
    except Exception as e:
        print(f"\n[ERROR] Gagal memuat data CSV:")
        print(f"Detail Kesalahan: {e}")
        print("Silakan perbaiki file CSV Anda dan coba lagi.")
        return
        
    # Menampilkan data yang dimuat
    tampil_matrix()
    tampil_data_paket()
    
    # Menjalankan proses pengiriman optimal
    proses_pengiriman()
    
    # Menampilkan ringkasan hasil simulasi
    tampil_ringkasan()


if __name__ == '__main__':
    main()