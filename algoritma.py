# algoritma.py
import numpy as np

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

        print("\nPengiriman Selanjutnya")
        print(f"Tujuan          : {tujuan}")
        print(f"Rute            : {rute[idx_terpilih]}")
        print(f"Volume Paket    : {volume[idx_terpilih]}")
        print(f"Sisa Kapasitas  : {sisa_kapasitas}")
        print(f"Skor Paket      : {round(skor, 2)}")
        asal = tujuan


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

def main():
    global n, asal, kecepatan, kapasitas, sisa_kapasitas
    print("=== SIMULASI DISTRIBUSI PAKET ===\n")
    n = int(input("Jumlah node : "))
    print("\nMasukkan nama node")
    input_node()
    print(f"\nDaftar node : {node}")

    while True:
        asal_input = input("\nNode asal : ")
        if asal_input in node:
            asal = asal_input
            hasil_pengiriman.append(asal)
            break
        print("Node tidak ditemukan.")

    print("\nData kendaraan")
    kecepatan = int(input("Kecepatan truk (km/jam) : "))
    kapasitas = int(input("Kapasitas maksimal : "))

    sisa_kapasitas = kapasitas

    input_data_paket()
    input_jarak()
    tampil_matrix()
    tampil_data_paket()
    proses_pengiriman()
    tampil_ringkasan()


if __name__ == '__main__':
    n = 0
    asal = ""
    node = []
    kecepatan = 0
    kapasitas = 0
    sisa_kapasitas = 0
    deadline = []
    prioritas = []
    volume = []
    jarak = []
    rute = []
    idx_paket_tersedia = []
    waktu_tempuh = []
    hasil_pengiriman = []
    main()