# algoritma.py

# Fungsi untuk menghitung jarak terpendek menggunakan algoritma Dijkstra
# Input: graf (representasi graf), start_node (node awal), kecepatan (kecepatan pengiriman)
# Output: jarak (array jarak dari node awal ke semua node), rute (array 2 dimensi rute dari node awal ke semua node)
def hitung_dijkstra(graf, start_node, kecepatan):
    # Logika mencari jarak terpendek
    jarak = {}
    rute = {}
    visited = set()
    queue = [(0, start_node)]
    while queue:
        current_distance, current_node = queue.pop(0)
        if current_node in visited:
            continue
        visited.add(current_node)
        jarak[current_node] = current_distance
        
        for neighbor, weight in graf[current_node].items():
            if neighbor not in visited:
                total_distance = current_distance + weight / kecepatan
                queue.append((total_distance, neighbor))
                rute[neighbor] = current_node

    return jarak, rute

# Fungsi untuk mengurutkan paket berdasarkan pendekatan greedy
# Input: list_paket (daftar paket yang tersedia), jarak (array jarak dari node awal ke semua node), deadline (array batas waktu pengiriman), volume_paket (array volume setiap paket), kapasitas (kapasitas maksimal kendaraan)
# Output: list_paket_terurut (daftar paket yang diurutkan berdasarkan prioritas)
def filter_volume(list_paket, volume_paket, sisa_kapasitas):
    # Logika seleksi paket berdasarkan volume
    return paket_terpilih

# Fungsi untuk mengurutkan paket berdasarkan skor kombinasi (jarak, deadline, volume)
# Input: list_paket (daftar paket yang tersedia), jarak (array jarak
# dari node awal ke semua node), deadline (array batas waktu pengiriman), volume_paket (array volume setiap paket), kecepatan (kecepatan pengiriman)
# Output: tujuan_terpilih (indeks paket yang dipilih untuk dikirimkan selanjutnya)
def filter_deadline(list_paket, deadline, kecepatan, jarak):
    # Logika seleksi paket berdasarkan deadline
    return paket_terpilih

# jarak: array jarak dari node awal ke semua node
# rute: array 2 dimensi rute dari node awal ke semua node
# list_paket: daftar paket yang tersedia
# kapasitas: kapasitas maksimal kendaraan
# deadline: array batas waktu pengiriman (jam)
# volume_paket: array volume setiap paket
# kecepatan: kecepatan pengiriman (km/jam)
# Output: integer indeks paket yang dipilih untuk dikirimkan selanjutnya
def filter_skor(list_paket, jarak, deadline, kecepatan, volume_paket):
    # Logika seleksi paket berdasarkan skor kombinasi
    return tujuan_terpilih