# algoritma.py

# Fungsi untuk menghitung jarak terpendek menggunakan algoritma Dijkstra
# Input: graf (representasi graf), start_node (node awal), kecepatan (kecepatan pengiriman)
# Output: jarak (array jarak dari node awal ke semua node), rute (array 2 dimensi rute dari node awal ke semua node)
def hitung_dijkstra(start_node):
    # Menggunakan variabel global yang didefinisikan di luar fungsi
    global jarak, rute, n, node
    
    print("Mulai perhitungan dijkstra...")
    
    # 1. Cari tahu indeks asli dari node asal
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
            if node[y] not in visited and jarak[idx_visited][y] != 999:
                # Hitung akumulasi jarak alternatif
                jarak_alternatif = dijkstra[idx_visited] + jarak[idx_visited][y]
                
                # Jika jalur baru ini lebih pendek, perbarui data
                if jarak_alternatif < dijkstra[y]:
                    dijkstra[y] = jarak_alternatif
                    
                    # Isi var rute global: rute menuju node ke-y adalah 
                    # rute ke node saat ini ditambah nama node ke-y itu sendiri
                    rute[y] = rute[idx_visited] + [node[y]]
                    
    return dijkstra

# Fungsi untuk mengurutkan paket berdasarkan pendekatan greedy
# Input: list_paket (daftar paket yang tersedia), jarak (array jarak dari node awal ke semua node), deadline (array batas waktu pengiriman), volume_paket (array volume setiap paket), kapasitas (kapasitas maksimal kendaraan)
# Output: list_paket_terurut (daftar paket yang diurutkan berdasarkan prioritas)
def filter_volume():
    global volume
    # Logika seleksi paket berdasarkan 
    for i in range(n):
        if volume[i] < sisa_kapasitas:
            idx_paket_tersedia.append(i)
    return 

# Fungsi untuk mengurutkan paket berdasarkan skor kombinasi (jarak, deadline, volume)
# Input: list_paket (daftar paket yang tersedia), jarak (array jarak
# dari node awal ke semua node), deadline (array batas waktu pengiriman), volume_paket (array volume setiap paket), kecepatan (kecepatan pengiriman)
# Output: tujuan_terpilih (indeks paket yang dipilih untuk dikirimkan selanjutnya)
def filter_deadline(hasil):
    """
    Memfilter paket di idx_paket_tersedia berdasarkan deadline.
    - start_node : node asal kurir
    - hasil : array jarak hasil dijkstra dari node asal ke semua node
    """
    global node, kecepatan, deadline, idx_paket_tersedia

    
    # Konversi kecepatan ke km/menit
    kecepatan_per_menit = kecepatan / 60.0
    
    # Loop semua paket yang tersedia
    for idx in list(idx_paket_tersedia):  # pakai list() supaya aman kalau dihapus
        # Estimasi waktu tempuh ke node tujuan (menit)
        waktu = hasil[idx] / kecepatan_per_menit
        
        # Deadline paket (menit)
        deadline_paket = deadline[idx]
        
        # Jika waktu tempuh lebih besar dari deadline, hapus paket dari daftar
        if waktu > deadline_paket:
            idx_paket_tersedia.remove(idx)
        else:
            waktu_tempuh.append(waktu)
    return

# jarak: array jarak dari node awal ke semua node
# rute: array 2 dimensi rute dari node awal ke semua node
# list_paket: daftar paket yang tersedia
# kapasitas: kapasitas maksimal kendaraan
# deadline: array batas waktu pengiriman (jam)
# volume_paket: array volume setiap paket
# kecepatan: kecepatan pengiriman (km/jam)
# Output: integer indeks paket yang dipilih untuk dikirimkan selanjutnya
def filter_skor(hasil):
    """
    Seleksi paket berdasarkan skor kombinasi (deadline, volume, prioritas, waktu tempuh).
    - start_node : node asal kurir
    - hasil : array jarak hasil dijkstra dari node asal ke semua node
    """
    global node, idx_paket_tersedia, volume, prioritas, deadline, waktu_tempuh, kecepatan
    
    # Konversi kecepatan ke km/menit
    kecepatan_per_menit = kecepatan / 60.0
    
    # Loop sampai tersisa 1 paket
    while len(idx_paket_tersedia) > 1:
        skor_terbaik = -1
        idx_paket_terpilih = None
        
        for idx in idx_paket_tersedia:
            # Hitung waktu tempuh (menit)
            waktu = hasil[idx] / kecepatan_per_menit
            
            # Ambil data deadline, volume, prioritas
            dline = deadline[idx]
            vol = volume[idx]
            prio = prioritas[idx]  # 1 rendah, 2 sedang, 3 tinggi
            
            # Contoh formula skor: prioritas lebih dominan, lalu deadline lebih kecil lebih baik
            skor = (prio * 10) + (dline / 100) - (vol / 10) - (waktu / 10)
            
            if skor > skor_terbaik:
                skor_terbaik = skor
                idx_paket_terpilih = idx
        
        # Hapus paket terpilih dari daftar
        idx_paket_tersedia.remove(idx_paket_terpilih)
        if idx_paket_tersedia:
            return idx_paket_tersedia[0]
        else:
            return None

def main():
    global node,asal,n
    n = int(input("Masukkan Jumlah Node: "))
    for i in range (n):
        nama_node = str(input("Nama Node: "))
        node.append(nama_node)
    while True:
        asal = str(input("Masukkan Node Asal: "))
        if asal in node:
            print(f"Node asal : {asal}")
            break
        else:
            print("Node tidak ditemukan!")
    
    kecepatan = int(input("Masukkan Kecepatan Truk(km/jam): "))
    sisa_kapasitas = kapasitas = int(input("Kapasitas Maximal: "))
    
    for i in range(n):
        if node[i] != asal:
            vol = int(input(f"Masukkan kapasitas paket {node[i]} (m^2): "))
            volume.append(vol)
    
    # if asal != node[0]:
    #     idx_asal = node.index(asal) 
    #     node[0], node[idx_asal] = node[idx_asal], node[0]
    jarak = np.zeros((n, n), dtype=int)
    rute = [[None]*n for _ in range(n)] 
    for i in range (n):
        print(f"Masukkan Adj Node {node[i]}:")
        for j in range(i+1,n):
            jarak_tempuh = int(input(f"Masukkan jarak dari node {node[i]} ke {node[j]} :"))
            jarak[i][j] = jarak[j][i] = jarak_tempuh
    while True: 
        idx_terpilih = -1 
        if sisa_kapasitas > 0 and idx_terpilih != None: 
            print("Menari Rute Selanjutnya.... ")
            hasil = hitung_dijkstra(asal)
            filter_volume(asal)
            filter_deadline(asal,hasil)
            idx_terpilih = filter_skor(asal,hasil)
            hasil_efisien.append(node[idx_terpilih])
            sisa_kapasitas -= volume[idx_terpilih]
            asal = node(idx_terpilih)
            print(f"Kirim paket {node[idx_terpilih]}")
            print(f"Lewat Rute {rute[idx_terpilih]}")
        else:
            break
    print("Rute Pengantaran: ")
    for paket in hasil_efisien:
        print(paket,end="")
    print()
    print(f"Volume Paket yang dikirim: {kapasitas-sisa_kapasitas}")
    
    return

if __name__=='__main__':
    import numpy as np
    n:int
    asal:str
    node = []
    kecepatan :int 
    kapasitas :int
    deadline = []
    prioritas = []
    volume = []
    jarak : list[list[int]]
    rute : list[list[str]]
    sisa_kapasitas :int
    idx_paket_tersedia : list[int]
    waktu_tempuh: list[int]
    hasil_efisien: list[str]
    main()
