# algorithma.py

n = 0
asal = ""
node = []
kecepatan = 0
kapasitas = 0
deadline = []
prioritas = []
volume = []
jarak = []
rute = []
sisa_kapasitas = 0
idx_paket_tersedia = []
waktu_tempuh = []
hasil_efisien = []


# Fungsi untuk menghitung jarak terpendek menggunakan algoritma Dijkstra
def hitung_dijkstra(start_node):
    global jarak, rute, n, node

    n = len(node)
    if len(jarak) != n or any(len(row) != n for row in jarak):
        raise ValueError("Matriks jarak harus berukuran n x n sesuai jumlah node.")

    if start_node not in node:
        raise ValueError(f"Node asal '{start_node}' tidak ditemukan.")
    idx_asal = node.index(start_node)

    dijkstra = [999] * n
    dijkstra[idx_asal] = 0

    visited = []
    rute = [[] for _ in range(n)]
    rute[idx_asal] = [start_node]

    while len(visited) < n:
        min_jarak = 999
        idx_visited = -1

        for i in range(n):
            if node[i] not in visited and dijkstra[i] < min_jarak:
                min_jarak = dijkstra[i]
                idx_visited = i

        if idx_visited == -1 or min_jarak == 999:
            break

        visited.append(node[idx_visited])

        for y in range(n):
            if node[y] not in visited and jarak[idx_visited][y] > 0:
                jarak_alternatif = dijkstra[idx_visited] + jarak[idx_visited][y]

                if jarak_alternatif < dijkstra[y]:
                    dijkstra[y] = jarak_alternatif
                    rute[y] = rute[idx_visited] + [node[y]]

    return dijkstra


def filter_volume():
    global volume, sisa_kapasitas, idx_paket_tersedia, n, node, hasil_efisien, asal

    idx_paket_tersedia.clear()

    for i in range(n):
        if volume[i] <= sisa_kapasitas and node[i] not in hasil_efisien and node[i] != asal:
            idx_paket_tersedia.append(i)


def filter_deadline(hasil):
    global kecepatan, deadline, idx_paket_tersedia, waktu_tempuh, node

    waktu_tempuh.clear()
    kecepatan_per_menit = kecepatan / 60.0

    for idx in list(idx_paket_tersedia):
        if hasil[idx] >= 999:
            idx_paket_tersedia.remove(idx)
            continue
            
        waktu = hasil[idx] / kecepatan_per_menit
        deadline_paket = deadline[idx] * 60

        if waktu > deadline_paket:
            idx_paket_tersedia.remove(idx)
        else:
            waktu_tempuh.append(waktu)


def filter_skor(hasil):
    global idx_paket_tersedia, volume, prioritas, deadline, kecepatan

    kecepatan_per_menit = kecepatan / 60.0
    skor_terbaik = -9999
    idx_paket_terpilih = None

    for idx in idx_paket_tersedia:
        waktu = hasil[idx] / kecepatan_per_menit
        skor = (prioritas[idx] * 10) - (deadline[idx] * 2) - (volume[idx] / 10) - (waktu / 10)

        if skor > skor_terbaik:
            skor_terbaik = skor
            idx_paket_terpilih = idx

    return idx_paket_terpilih, skor_terbaik


def jalankan_simulasi():
    global asal, sisa_kapasitas, idx_paket_tersedia, hasil_efisien, rute

    log = []
    detail_pengiriman = []

    while sisa_kapasitas > 0:
        hasil = hitung_dijkstra(asal)
        filter_volume()
        filter_deadline(hasil)

        if not idx_paket_tersedia:
            log.append("Tidak ada paket lagi yang memenuhi kriteria kapasitas/deadline.")
            break

        idx_terpilih, skor_terbaik = filter_skor(hasil)

        if idx_terpilih is None:
            break

        hasil_efisien.append(node[idx_terpilih])
        sisa_kapasitas -= volume[idx_terpilih]

        detail_pengiriman.append({
            "tujuan": node[idx_terpilih],
            "rute": " -> ".join(rute[idx_terpilih]),
            "volume": volume[idx_terpilih],
            "skor": round(skor_terbaik, 2),
            "jarak": hasil[idx_terpilih],
        })

        asal = node[idx_terpilih]

    paket_berhasil = hasil_efisien[1:] if len(hasil_efisien) > 1 else []
    paket_gagal = [
        node[i] for i in range(n)
        if node[i] not in hasil_efisien and node[i] != hasil_efisien[0]
    ]

    total_jarak = sum(item["jarak"] for item in detail_pengiriman)

    return {
        "rute_pengantaran": " -> ".join(hasil_efisien),
        "volume_terkirim": kapasitas - sisa_kapasitas,
        "sisa_kapasitas": sisa_kapasitas,
        "paket_berhasil": paket_berhasil,
        "paket_gagal": paket_gagal,
        "detail": detail_pengiriman,
        "log": log,
        "total_jarak": total_jarak,
    }


def main():
    global node, asal, n, jarak, kecepatan, kapasitas, deadline, prioritas, volume
    global sisa_kapasitas, idx_paket_tersedia, waktu_tempuh, hasil_efisien

    import numpy as np

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
        print("Node tidak ditemukan!")

    print("Masukkan data truk: ")
    kecepatan = int(input("Kecepatan Truk(km/jam): "))
    sisa_kapasitas = kapasitas = int(input("Kapasitas Max: "))
    print()

    for i in range(n):
        if node[i] != asal:
            print(f"Masukkan data paket untuk node {node[i]}:")
            vol = int(input("berat paket (kg): "))
            prio = int(input("prioritas paket (1 rendah, 2 sedang, 3 tinggi): "))
            dline = float(input("deadline paket (jam): "))
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

    for i in range(n):
        print(f"Masukkan Adj Node {node[i]} (-1 jika tidak terhubung):")
        for j in range(i + 1, n):
            jarak_tempuh = int(input(f"{node[i]} -> {node[j]} :"))
            if jarak_tempuh > 0:
                jarak[i][j] = jarak[j][i] = jarak_tempuh

    jarak = jarak.tolist()

    print("Adjacency Matrix:")
    for i in range(n):
        for j in range(n):
            print(f"{jarak[i][j]:4}", end=" ")
        print()

    ringkasan = jalankan_simulasi()
    print("\n--- RINGKASAN PENGANTARAN ---")
    print(f"Rute Pengantaran: {ringkasan['rute_pengantaran']}")
    print(f"Volume Paket yang dikirim: {ringkasan['volume_terkirim']}")
    print(f"Paket yang berhasil dikirim: {', '.join(ringkasan['paket_berhasil'])}")
    print(f"Paket yang tidak dapat dikirim: {', '.join(ringkasan['paket_gagal'])}")


if __name__ == "__main__":
    main()
