# algoritma.py

# Fungsi untuk menghitung jarak terpendek menggunakan algoritma Dijkstra
# Input: start_node (node awal)
# Output: dijkstra (array jarak dari node awal ke semua node)
def hitung_dijkstra(start_node):
    # Menggunakan variabel global yang didefinisikan di luar fungsi
    global jarak, rute, n, node
    
    print("Mulai perhitungan dijkstra...")
    
    # Pastikan ukuran data sesuai dengan panjang daftar node
    n = len(node)
    if len(jarak) != n or any(len(row) != n for row in jarak):
        raise ValueError("Matriks jarak harus berukuran n x n sesuai jumlah node.")
    
    # 1. Cari tahu indeks asli dari node asal
    if start_node not in node:
        raise ValueError(f"Node asal '{start_node}' tidak ditemukan.")
    idx_asal = node.index(start_node)
    
    # 2. Inisialisasi array penampung jarak dijkstra dengan nilai tak hingga (999)
    dijkstra = [999] * n
    dijkstra[idx_asal] = 0  # Jarak ke node asal sendiri adalah 0
    
    # 3. Lacak node yang sudah selesai diproses secara final
    visited = []
    
    # 4. Inisialisasi struktur rute global sebagai list[list[str]]
    # Setiap node tujuan akan memiliki list rute perjalanannya sendiri
    rute = [[] for _ in range(n)]
    rute[idx_asal] = [start_node] # Rute menuju asal adalah dirinya sendiri
    
    # Lakukan pencarian hingga semua node masuk ke daftar visited
    while len(visited) < n:
        # Cari node dengan nilai terkecil di array 'dijkstra' yang belum di-visited
        min_jarak = 999
        idx_visited = -1
        
        for i in range(n):
            if node[i] not in visited and dijkstra[i] < min_jarak:
                min_jarak = dijkstra[i]
                idx_visited = i
                
        # Jika tidak ditemukan lagi node yang bisa dijangkau, keluar dari loop
        if idx_visited == -1 or min_jarak == 999:
            break
            
        # Tandai node terpilih sebagai sudah dikunjungi
        visited.append(node[idx_visited])
        
        # 5. Perbarui jarak ke semua tetangga yang belum dikunjungi
        for y in range(n):
            if idx_visited < 0 or idx_visited >= len(jarak):
                break
            if y >= len(jarak[idx_visited]):
                continue
                
            # Hanya proses rute yang valid (jarak > 0, mengabaikan -1 atau 0)
            if node[y] not in visited and jarak[idx_visited][y] > 0:
                # Hitung akumulasi jarak alternatif
                jarak_alternatif = dijkstra[idx_visited] + jarak[idx_visited][y]
                
                # Jika jalur baru ini lebih pendek, perbarui data
                if jarak_alternatif < dijkstra[y]:
                    dijkstra[y] = jarak_alternatif
                    
                    # Isi var rute global: rute menuju node ke-y adalah 
                    # rute ke node saat ini ditambah nama node ke-y itu sendiri
                    rute[y] = rute[idx_visited] + [node[y]]
    print("Perhitungan dijkstra selesai.")
    for i in range(n):
        print(f"Jarak dari {start_node} ke {node[i]}: {dijkstra[i]}")
        print(f"Rute: {rute[i]}")
    
                    
    return dijkstra

# Fungsi untuk mengurutkan paket berdasarkan pendekatan greedy
# Input: list_paket (daftar paket yang tersedia), jarak (array jarak dari node awal ke semua node), deadline (array batas waktu pengiriman), volume_paket (array volume setiap paket), kapasitas (kapasitas maksimal kendaraan)
# Output: list_paket_terurut (daftar paket yang diurutkan berdasarkan prioritas)
# Fungsi untuk mengurutkan paket berdasarkan pendekatan greedy (kapasitas)
def filter_volume():
    global volume, sisa_kapasitas, idx_paket_tersedia, n, node, hasil_efisien, asal
    print("Memfilter paket berdasarkan kapasitas...")
    # KOSONGKAN list setiap kali mencari paket baru agar tidak menumpuk
    idx_paket_tersedia.clear() 
    
    for i in range(n):
        # 1. Cek kapasitas cukup
        # 2. Pastikan node belum pernah dikirim (tidak ada di hasil_efisien)
        # 3. Pastikan tidak mengirim paket ke titik awal (depot)
        if volume[i] <= sisa_kapasitas and node[i] not in hasil_efisien and node[i] != asal:
            idx_paket_tersedia.append(i)
        else:
            if node[i] != asal:
                print(f"-> Paket di Node {node[i]} dihapus karena kapasitas ({volume[i]}) melebihi sisa kapasitas ({sisa_kapasitas}), atau sudah dikirim sebelumnya.")
    print("filter_volume selesai.")            
    print(f"Paket yang memenuhi kriteria kapasitas: {[node[i] for i in idx_paket_tersedia]}")

# Fungsi untuk memfilter berdasarkan deadline
def filter_deadline(hasil):
    global kecepatan, deadline, idx_paket_tersedia, waktu_tempuh
    print("Memfilter paket berdasarkan deadline...")
    # Kosongkan waktu tempuh lama
    waktu_tempuh.clear()
    kecepatan_per_menit = kecepatan / 60.0
    
    for idx in list(idx_paket_tersedia):  
        waktu = hasil[idx] / kecepatan_per_menit
        deadline_paket = deadline[idx] * 60  # Ubah jam ke menit agar setara
        
        if waktu > deadline_paket:
            idx_paket_tersedia.remove(idx)
            print(f"-> Paket di Node {node[idx]} dihapus karena waktu tempuh ({waktu:.2f} menit) melebihi deadline ({deadline_paket:.2f} menit).")
        else:
            waktu_tempuh.append(waktu)
    print("filter_deadline selesai.")
    for i in idx_paket_tersedia:
        print(f"Node {node[i]}: Deadline={deadline[i]}, Waktu Tempuh={waktu_tempuh[i] if i < len(waktu_tempuh) else 'N/A'}")
  

# Fungsi untuk mencari 1 paket dengan skor tertinggi
def filter_skor(hasil):
    global idx_paket_tersedia, volume, prioritas, deadline, kecepatan
    print("Mencari paket dengan skor tertinggi...")
    kecepatan_per_menit = kecepatan / 60.0
    skor_terbaik = -9999
    idx_paket_terpilih = None
    
    # Cukup cari nilai maksimum, tidak perlu pakai while loop dan remove
    for idx in idx_paket_tersedia:
        waktu = hasil[idx] / kecepatan_per_menit
        # Normalisasi satuan jika perlu, contoh formula:
        skor = (prioritas[idx] * 10) + (deadline[idx] / 100) - (volume[idx] / 10) - (waktu / 10)
        
        if skor > skor_terbaik:
            skor_terbaik = skor
            idx_paket_terpilih = idx
    print("filter_skor selesai.")
            
    return idx_paket_terpilih,skor_terbaik

def main():
    global node,asal,n,jarak,rute,kecepatan,kapasitas,deadline,prioritas,volume,sisa_kapasitas,idx_paket_tersedia,waktu_tempuh,hasil_efisien,asal_awal
    n = int(input("Masukkan Jumlah Node: "))
    print("Masukkan Nama Node: ")
    while True:
        nama_node = str(input(f"Node {len(node)+1}: "))
        if nama_node in node:
            print("Nama node sudah ada, masukkan nama lain!")
        else:
            node.append(nama_node)
            if len(node) == n:
                break
    print("Daftar Node: ", node)
    print()
    while True:
        asal = str(input("Masukkan Node Asal: "))
        if asal in node:
            print(f"Node asal : {asal}")
            hasil_efisien.append(asal)
            print()
            break
        else:
            print("Node tidak ditemukan!")
    
    print("Masukkan data truk: ")
    kecepatan = int(input("Kecepatan Truk(km/jam): "))
    sisa_kapasitas = kapasitas = int(input("Kapasitas Max: "))
    print()
    
    for i in range(n):
        
        if node[i] != asal:
            print(f"Masukkan data paket untuk node {node[i]}:")
            vol = int(input(f"kapasitas paket (m^2): "))
            prio = int(input(f"prioritas paket (1 rendah, 2 sedang, 3 tinggi): "))
            dline = float(input(f"deadline paket (jam): "))
            prioritas.append(prio)
            deadline.append(dline)
            volume.append(vol)
            print()
        else:
            prioritas.append(0) 
            deadline.append(0.0) 
            volume.append(0) 
    
   
    jarak = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(jarak, 0)
    rute = [[None]*n for _ in range(n)] 
    for i in range(n):
        print(f"Masukkan Adj Node {node[i]} (-1 jika tidak terhubung):")
        for j in range(i+1, n):
            jarak_tempuh = int(input(f"{node[i]} -> {node[j]} :"))
            if jarak_tempuh > 0:
                jarak[i][j] = jarak[j][i] = jarak_tempuh
    print("Adjacency Matrix:")
    for i in range(n):
        for j in range(n):
            print(f"{jarak[i][j]:4}", end=" ")
        print()
    print()
    print("Data Paket: ")
    for i in range(len(deadline)):
        print(f"Node {node[i]}: Deadline={deadline[i]}, Volume={volume[i]}, Prioritas={prioritas[i]}")

    while sisa_kapasitas > 0: 
        print("\nMencari Rute Selanjutnya.... ")
        hasil = hitung_dijkstra(asal)
        
        # Panggil fungsi filter (tanpa mengirim parameter berlebih)
        filter_volume()
        filter_deadline(hasil)
        
        # Jika tidak ada paket yang lolos filter volume & deadline, hentikan
        if not idx_paket_tersedia:
            print("-> Tidak ada paket lagi yang memenuhi kriteria kapasitas/deadline.")
            break
            
        # Pilih satu paket terbaik
        idx_terpilih, skor_terbaik = filter_skor(hasil)
        
        if idx_terpilih is not None:
            hasil_efisien.append(node[idx_terpilih])
            sisa_kapasitas -= volume[idx_terpilih]
            
            asal = node[idx_terpilih]
            
            print(f"Kirim paket ke Node: {node[idx_terpilih]}")
            print(f"Lewat Rute: {rute[idx_terpilih]}")
            print(f"Volume Paket: {volume[idx_terpilih]}")
            print(f"Sisa Kapasitas: {sisa_kapasitas}")
            print(f"Skor Terbaik: {skor_terbaik}")
        else:
            break
            
    print("\n--- RINGKASAN PENGANTARAN ---")
    print(f"Rute Pengantaran: {' -> '.join(hasil_efisien)}")
    print(f"Volume Paket yang dikirim: {kapasitas - sisa_kapasitas}")
    print(f"Paket yang berhasil dikirim: {', '.join(hasil_efisien[1:])}")
    print(f"Paket yang tidak dapat dikirim: {', '.join(node[i] for i in range(n) if node[i] not in hasil_efisien and node[i] != asal)}")
    
    return

if __name__=='__main__':
    import numpy as np
    n:int
    asal:str
    node :list[str] = []
    kecepatan :int 
    kapasitas :int
    deadline :list[float] = []
    prioritas :list[int] = []
    volume :list[int] = []
    jarak : list[list[int]] = []
    rute : list[list[str]] = []
    sisa_kapasitas :int
    idx_paket_tersedia : list[int] = []
    waktu_tempuh: list[int] = []
    hasil_efisien: list[str] = []
    main()