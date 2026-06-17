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
waktu_layanan = 10     # Waktu bongkar muat/layanan per paket (menit)
waktu_muat_depot = 20  # Waktu pemuatan awal dan isi ulang di depot (menit)
jam_kerja_maks = 8     # Batas maksimal jam kerja kurir (jam)


def hitung_dijkstra(start_node):
    global jarak, rute, n, node

    n = len(node)
    if start_node not in node:
        raise ValueError(f"Node '{start_node}' tidak ditemukan.")
    idx_asal = node.index(start_node)
    dijkstra = [float('inf')] * n
    dijkstra[idx_asal] = 0

    visited = []
    rute = [[] for _ in range(n)]
    rute[idx_asal] = [start_node]

    while len(visited) < n:
        min_jarak = float('inf')
        idx_visited = -1
        for i in range(n):
            if node[i] not in visited and dijkstra[i] < min_jarak:
                min_jarak = dijkstra[i]
                idx_visited = i
        if idx_visited == -1:
            break
        visited.append(node[idx_visited])
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

def proses_pengiriman():
    global asal, sisa_kapasitas, waktu_layanan, jam_kerja_maks, waktu_muat_depot
    riwayat_langkah = []
    
    origin = asal 
    total_waktu_menit = waktu_muat_depot  
    kecepatan_per_menit = kecepatan / 60 if kecepatan > 0 else 1.0
    
    while sisa_kapasitas > 0:

        hasil = hitung_dijkstra(asal)
        filter_volume()
        filter_deadline(hasil)

        for idx in list(idx_paket_tersedia):
            waktu_perjalanan = hasil[idx] / kecepatan_per_menit
            waktu_estimasi = total_waktu_menit + waktu_perjalanan + waktu_layanan
            if waktu_estimasi > jam_kerja_maks * 60:
                idx_paket_tersedia.remove(idx)

        if not idx_paket_tersedia:
            has_undelivered = any(node[i] not in hasil_pengiriman and node[i] != origin for i in range(n))
            if has_undelivered and asal != origin:
                idx_origin = node.index(origin)
                dist_to_origin = hasil[idx_origin]
                time_to_origin = (dist_to_origin / kecepatan) * 60 if kecepatan > 0 else 0.0
                if total_waktu_menit + time_to_origin + waktu_muat_depot <= jam_kerja_maks * 60:
                    total_waktu_menit += time_to_origin + waktu_muat_depot
                    sisa_kapasitas = kapasitas
                    
                    langkah_reload = {
                        "tujuan": origin,
                        "rute": list(rute[idx_origin]),
                        "volume_paket": 0,
                        "sisa_kapasitas": sisa_kapasitas,
                        "skor": 0.0,
                        "asal_sebelumnya": asal,
                        "jarak": dist_to_origin,
                        "waktu_tempuh": time_to_origin,
                        "waktu_layanan": waktu_muat_depot,
                        "waktu_kumulatif": total_waktu_menit
                    }
                    riwayat_langkah.append(langkah_reload)
                    hasil_pengiriman.append(origin)
                    
                    print(f"\nKembali ke {origin} untuk memuat ulang paket (Reload)")
                    asal = origin
                    continue 
            
            print("\nTidak ada paket yang bisa dikirim lagi.")
            break

        idx_terpilih, skor = filter_skor(hasil)

        if idx_terpilih is None:
            break

        tujuan = node[idx_terpilih]
        hasil_pengiriman.append(tujuan)
        sisa_kapasitas -= volume[idx_terpilih]
        jarak_tempuh = hasil[idx_terpilih]
        waktu_menit = (jarak_tempuh / kecepatan) * 60 if kecepatan > 0 else 0.0
        
        total_waktu_menit += waktu_menit + waktu_layanan
        
        langkah = {
            "tujuan": tujuan,
            "rute": list(rute[idx_terpilih]),
            "volume_paket": volume[idx_terpilih],
            "sisa_kapasitas": sisa_kapasitas,
            "skor": skor,
            "asal_sebelumnya": asal,
            "jarak": jarak_tempuh,
            "waktu_tempuh": waktu_menit,
            "waktu_layanan": waktu_layanan,
            "waktu_kumulatif": total_waktu_menit
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

def get_file_reader(file_source):
    if isinstance(file_source, str):
        if not os.path.exists(file_source):
            raise FileNotFoundError(f"File tidak ditemukan di path: {file_source}")
        return open(file_source, mode='r', encoding='utf-8', newline='')
    elif hasattr(file_source, 'read'):
        content = file_source.read()
        if hasattr(file_source, 'seek'):
            file_source.seek(0) 
            
        if isinstance(content, bytes):
            text_content = content.decode('utf-8')
        else:
            text_content = content
        return io.StringIO(text_content)
    else:
        raise TypeError("Sumber file harus berupa path (string) atau file-like object.")

def baca_data_distribusi_tunggal(file_source):
    f = get_file_reader(file_source)
    try:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            raise ValueError("File CSV kosong atau tidak memiliki header.")
        required = ['tipe', 'node', 'volume', 'prioritas', 'deadline', 'kecepatan', 'kapasitas']
        for r in required:
            if r not in headers:
                raise ValueError(f"Kolom header wajib '{r}' tidak ditemukan dalam file CSV.")
        node_headers_matrix = [n.strip() for n in headers[7:]]
        if not node_headers_matrix:
            raise ValueError("Kolom node matriks jarak tidak terdeteksi di bagian kanan header CSV.")
        config_data = {}
        nodes_list = []
        volume_list = []
        prioritas_list = []
        deadline_list = []
        jarak_rows = {}
        
        seen_nodes_paket = set()
        
        for idx, row in enumerate(reader, start=2):
            tipe = row.get('tipe')
            if not tipe:
                continue
            tipe = tipe.strip().lower()
            
            if tipe == 'konfigurasi':
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
                
        if not config_data:
            raise ValueError("Data konfigurasi distribusi tidak ditemukan dalam file CSV.")
            
        if not nodes_list:
            raise ValueError("Data paket tidak ditemukan dalam file CSV.")
        if set(nodes_list) != set(node_headers_matrix):
            raise ValueError("Daftar node pada data paket tidak cocok dengan kolom matriks jarak pada header.")
            
        if set(nodes_list) != set(jarak_rows.keys()):
            missing_rows = set(nodes_list) - set(jarak_rows.keys())
            raise ValueError(f"Baris data untuk node berikut tidak ditemukan di matriks jarak: {missing_rows}")
        
        n_size = len(nodes_list)
        matriks_jarak = np.full((n_size, n_size), -1, dtype=int)
        
        for i in range(n_size):
            u = nodes_list[i]
            for j in range(n_size):
                v = nodes_list[j]
                val = jarak_rows[u][v]
                if i == j and val != 0:
                    raise ValueError(f"Jarak dari node ke dirinya sendiri (diagonal '{u}' -> '{v}') harus bernilai 0.")
                    
                matriks_jarak[i][j] = val
                
        for i in range(n_size):
            for j in range(n_size):
                if matriks_jarak[i][j] != matriks_jarak[j][i]:
                    raise ValueError(f"Matriks jarak tidak simetris pada hubungan '{nodes_list[i]}' dan '{nodes_list[j]}'.")
                    
        asal = config_data["asal"]
        if asal not in nodes_list:
            raise ValueError(f"Node asal '{asal}' pada konfigurasi tidak terdaftar dalam data paket.")
            
        return nodes_list, volume_list, prioritas_list, deadline_list, matriks_jarak, asal, config_data["kecepatan"], config_data["kapasitas"]
    finally:
        if isinstance(file_source, str):
            f.close()

