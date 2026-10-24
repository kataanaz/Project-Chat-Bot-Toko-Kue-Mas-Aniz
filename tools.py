import json
import os
import re

def _muat_katalog():
    """Memuat data katalog dari file JSON lokal."""
    jalur_file = os.path.join(os.path.dirname(__file__), "data", "katalog.json")
    with open(jalur_file, "r", encoding="utf-8") as f:
        return json.load(f)

def _bersihkan_teks(teks):
    """Menormalisasi teks: huruf kecil dan menghapus spasi berlebih."""
    if teks is None:
        return ""
    return " ".join(str(teks).strip().lower().split())

def _cocokkan_nama(nama_input, nama_katalog):
    """
    Mencocokkan nama input pelanggan dengan nama produk/paket di katalog.
    Mendukung pencocokan persis, pembersihan tanda kurung porsi (misal 'isi 6'),
    dan pencocokan kata kunci fleksibel.
    """
    n_in = _bersihkan_teks(nama_input)
    n_kat = _bersihkan_teks(nama_katalog)
    if not n_in or not n_kat:
        return False
    if n_in == n_kat:
        return True
    n_kat_dasar = _bersihkan_teks(re.sub(r'\(.*?\)', '', n_kat))
    if n_in == n_kat_dasar:
        return True
    if len(n_in) >= 4 and (n_in in n_kat or n_kat_dasar in n_in):
        return True
    return False

def cari_produk(kata_kunci=None, kategori=None, maks_harga=None):
    """
    Mencari produk atau paket berdasarkan kata kunci, kategori, dan harga maksimum.
    Mengembalikan dict dengan status ditemukan dan daftar hasil (tanpa satuan 'pcs').
    """
    katalog = _muat_katalog()
    hasil = []
    
    kata_kunci_norm = _bersihkan_teks(kata_kunci)
    kategori_norm = _bersihkan_teks(kategori)

    # 1. Cari pada produk satuan
    for p in katalog.get("produk", []):
        # Filter kategori jika ada
        if kategori_norm and _bersihkan_teks(p.get("kategori")) != kategori_norm:
            continue
        
        # Filter harga maksimum jika ada
        if maks_harga is not None and p.get("harga", 0) > maks_harga:
            continue
        
        # Filter kata kunci jika ada (mencocokkan nama, deskripsi, atau kategori)
        if kata_kunci_norm:
            nama_cocok = kata_kunci_norm in _bersihkan_teks(p.get("nama"))
            deskripsi_cocok = kata_kunci_norm in _bersihkan_teks(p.get("deskripsi"))
            kategori_cocok = kata_kunci_norm in _bersihkan_teks(p.get("kategori"))
            if not (nama_cocok or deskripsi_cocok or kategori_cocok):
                continue
        
        hasil.append({
            "nama": p["nama"],
            "kategori": p["kategori"],
            "harga": p["harga"],
            "stok": p["stok"],
            "sebutan": p["sebutan"],
            "alergen": p.get("alergen", []),
            "deskripsi": p.get("deskripsi", ""),
            "terlaris": p.get("terlaris", False)
        })

    # 2. Cari pada paket (jika kategori kosong atau kategori = "paket")
    if not kategori_norm or kategori_norm == "paket":
        for pak in katalog.get("paket", []):
            if maks_harga is not None and pak.get("harga", 0) > maks_harga:
                continue

            if kata_kunci_norm:
                nama_cocok = kata_kunci_norm in _bersihkan_teks(pak.get("nama"))
                paket_cocok = kata_kunci_norm in "paket"
                if not (nama_cocok or paket_cocok):
                    continue
            
            # Hitung stok paket (minimum dari stok komponen yang tersedia)
            stok_komponen = []
            for item in pak.get("isi", []):
                produk_nama = item.get("produk")
                jumlah_perlu = item.get("jumlah", 1)
                stok_prod = 0
                for p in katalog.get("produk", []):
                    if _bersihkan_teks(p.get("nama")) == _bersihkan_teks(produk_nama):
                        stok_prod = p.get("stok", 0)
                        break
                stok_komponen.append(stok_prod // max(1, jumlah_perlu))
            
            stok_paket = min(stok_komponen) if stok_komponen else 0

            hasil.append({
                "nama": pak["nama"],
                "kategori": "paket",
                "harga": pak["harga"],
                "stok": stok_paket,
                "sebutan": pak["sebutan"],
                "isi": [f"{item['jumlah']} {item['produk']}" for item in pak.get("isi", [])]
            })

    if not hasil:
        return {
            "ditemukan": False,
            "pesan": "Tidak ada produk yang cocok dengan pencarian.",
            "hasil": []
        }

    return {
        "ditemukan": True,
        "total": len(hasil),
        "hasil": hasil
    }

def cek_stok(nama):
    """
    Mengecek stok produk atau paket.
    Untuk paket, stok dihitung dari stok minimum komponen pembentuknya.
    """
    if not nama:
        return {"ditemukan": False, "pesan": "Nama produk tidak boleh kosong."}

    katalog = _muat_katalog()
    nama_norm = _bersihkan_teks(nama)

    # Cek di produk satuan
    for p in katalog.get("produk", []):
        if _cocokkan_nama(nama, p.get("nama")):
            return {
                "ditemukan": True,
                "nama": p["nama"],
                "stok": p["stok"],
                "sebutan": p["sebutan"]
            }

    # Cek di paket
    for pak in katalog.get("paket", []):
        if _cocokkan_nama(nama, pak.get("nama")):
            stok_komponen = []
            for item in pak.get("isi", []):
                prod_target = item.get("produk")
                jml_target = item.get("jumlah", 1)
                stok_item = 0
                for p in katalog.get("produk", []):
                    if _cocokkan_nama(prod_target, p.get("nama")):
                        stok_item = p.get("stok", 0)
                        break
                stok_komponen.append(stok_item // max(1, jml_target))

            stok_paket = min(stok_komponen) if stok_komponen else 0
            return {
                "ditemukan": True,
                "nama": pak["nama"],
                "stok": stok_paket,
                "sebutan": pak["sebutan"]
            }

    return {
        "ditemukan": False,
        "pesan": f"Produk atau paket '{nama}' tidak ditemukan."
    }

def info_alergen(nama):
    """
    Mengambil informasi alergen suatu produk atau paket.
    Jika paket, menggabungkan alergen dari seluruh komponen di dalamnya.
    """
    if not nama:
        return {"ditemukan": False, "pesan": "Nama produk tidak boleh kosong."}

    katalog = _muat_katalog()

    # Cek di produk satuan
    for p in katalog.get("produk", []):
        if _cocokkan_nama(nama, p.get("nama")):
            return {
                "ditemukan": True,
                "nama": p["nama"],
                "alergen": p.get("alergen", []),
                "sebutan": p["sebutan"]
            }

    # Cek di paket
    for pak in katalog.get("paket", []):
        if _cocokkan_nama(nama, pak.get("nama")):
            semua_alergen = set()
            for item in pak.get("isi", []):
                prod_target = item.get("produk")
                for p in katalog.get("produk", []):
                    if _cocokkan_nama(prod_target, p.get("nama")):
                        for al in p.get("alergen", []):
                            semua_alergen.add(al)
                        break
            return {
                "ditemukan": True,
                "nama": pak["nama"],
                "alergen": sorted(list(semua_alergen)),
                "sebutan": pak["sebutan"]
            }

    return {
        "ditemukan": False,
        "pesan": f"Produk atau paket '{nama}' tidak ditemukan."
    }

def daftar_terlaris():
    """
    Mengambil daftar produk yang memiliki tanda terlaris (terlaris = True).
    """
    katalog = _muat_katalog()
    hasil = []
    for p in katalog.get("produk", []):
        if p.get("terlaris") is True:
            hasil.append({
                "nama": p["nama"],
                "kategori": p["kategori"],
                "harga": p["harga"],
                "stok": p["stok"],
                "sebutan": p["sebutan"],
                "alergen": p.get("alergen", []),
                "deskripsi": p.get("deskripsi", "")
            })

    return {
        "ditemukan": True,
        "total": len(hasil),
        "hasil": hasil
    }

def inisialisasi_stok():
    """Mengembalikan dictionary salinan stok awal dari katalog.json."""
    katalog = _muat_katalog()
    return {p["nama"]: p["stok"] for p in katalog.get("produk", [])}

def _cari_item_katalog(nama):
    """Mencari entitas produk atau paket dari katalog berdasarkan nama."""
    katalog = _muat_katalog()
    for p in katalog.get("produk", []):
        if _cocokkan_nama(nama, p.get("nama")):
            return {"tipe": "produk", "data": p}
    for pak in katalog.get("paket", []):
        if _cocokkan_nama(nama, pak.get("nama")):
            return {"tipe": "paket", "data": pak}
    return None

def hitung_stok_tersedia(nama, stok_aktif):
    """Menghitung sisa stok aktual yang tersedia berdasarkan stok_aktif."""
    item = _cari_item_katalog(nama)
    if not item:
        return 0
    if item["tipe"] == "produk":
        return stok_aktif.get(item["data"]["nama"], 0)
    elif item["tipe"] == "paket":
        katalog = _muat_katalog()
        komponen_stok = []
        for isi in item["data"].get("isi", []):
            stok_komp = stok_aktif.get(isi.get("produk"), 0)
            komponen_stok.append(stok_komp // max(1, isi.get("jumlah", 1)))
        return min(komponen_stok) if komponen_stok else 0

def tambah_ke_keranjang(keranjang, stok_aktif, nama, jumlah):
    """
    Menambahkan produk atau paket ke dalam keranjang.
    Validasi: jumlah 1-20, batas ketersediaan stok, dan nama harus ada di katalog.
    """
    if not isinstance(jumlah, int) or jumlah < 1 or jumlah > 20:
        return {
            "berhasil": False,
            "pesan": "Jumlah pesanan harus berupa bilangan bulat antara 1 sampai 20."
        }

    item = _cari_item_katalog(nama)
    if not item:
        return {
            "berhasil": False,
            "pesan": f"Menu '{nama}' tidak ditemukan di katalog toko kami."
        }

    nama_asli = item["data"]["nama"]
    sebutan = item["data"]["sebutan"]
    harga = item["data"]["harga"]

    # Hitung jumlah yang sudah ada di keranjang untuk item ini
    jumlah_di_keranjang = 0
    for el in keranjang:
        if el["nama"] == nama_asli:
            jumlah_di_keranjang = el["jumlah"]
            break

    total_diminta = jumlah_di_keranjang + jumlah
    stok_tersedia = hitung_stok_tersedia(nama_asli, stok_aktif)

    if total_diminta > stok_tersedia:
        return {
            "berhasil": False,
            "pesan": f"Maaf kak, stok untuk '{nama_asli}' tidak mencukupi. Tersedia {stok_tersedia} {sebutan}."
        }

    # Perbarui atau tambahkan ke keranjang
    ditemukan = False
    for el in keranjang:
        if el["nama"] == nama_asli:
            el["jumlah"] += jumlah
            el["subtotal"] = el["jumlah"] * harga
            ditemukan = True
            break

    if not ditemukan:
        keranjang.append({
            "nama": nama_asli,
            "jumlah": jumlah,
            "harga": harga,
            "sebutan": sebutan,
            "subtotal": harga * jumlah
        })

    total_keranjang = sum(el["subtotal"] for el in keranjang)
    return {
        "berhasil": True,
        "pesan": f"Berhasil menambahkan {jumlah} {sebutan} {nama_asli} ke keranjang. Subtotal: Rp{harga * jumlah:,}, Total keranjang: Rp{total_keranjang:,}.",
        "item": nama_asli,
        "jumlah_ditambahkan": jumlah,
        "total_keranjang": total_keranjang
    }

def hapus_dari_keranjang(keranjang, nama):
    """Menghapus item dari keranjang berdasarkan nama."""
    nama_norm = _bersihkan_teks(nama)
    indeks_dihapus = None
    nama_dihapus = ""

    for i, el in enumerate(keranjang):
        if _cocokkan_nama(nama, el["nama"]):
            indeks_dihapus = i
            nama_dihapus = el["nama"]
            break

    if indeks_dihapus is not None:
        keranjang.pop(indeks_dihapus)
        total_keranjang = sum(el["subtotal"] for el in keranjang)
        return {
            "berhasil": True,
            "pesan": f"'{nama_dihapus}' berhasil dihapus dari keranjang.",
            "total_keranjang": total_keranjang
        }

    return {
        "berhasil": False,
        "pesan": f"Item '{nama}' tidak ditemukan di dalam keranjang belanja."
    }

def lihat_keranjang(keranjang):
    """Melihat rincian isi keranjang belanja beserta subtotal dan total harga."""
    if not keranjang:
        return {
            "kosong": True,
            "pesan": "Keranjang belanja Kakak masih kosong.",
            "daftar_item": [],
            "total_harga": 0
        }

    total = sum(el["subtotal"] for el in keranjang)
    daftar = []
    for el in keranjang:
        daftar.append({
            "nama": el["nama"],
            "jumlah": el["jumlah"],
            "sebutan": el["sebutan"],
            "harga_satuan": el["harga"],
            "subtotal": el["subtotal"]
        })

    return {
        "kosong": False,
        "total_item": len(keranjang),
        "daftar_item": daftar,
        "total_harga": total,
        "pesan": f"Total belanja di keranjang adalah Rp{total:,}."
    }

def ringkas_pesanan(keranjang):
    """Menyiapkan ringkasan pesanan akhir untuk konfirmasi pelanggan."""
    if not keranjang:
        return {
            "kosong": True,
            "pesan": "Keranjang belanja masih kosong, belum ada pesanan yang dapat diringkas.",
            "total_harga": 0
        }

    total = sum(el["subtotal"] for el in keranjang)
    rincian = [f"{el['jumlah']} {el['sebutan']} {el['nama']} (Rp{el['subtotal']:,})" for el in keranjang]

    return {
        "kosong": False,
        "rincian_pesanan": rincian,
        "total_harga": total,
        "pesan": f"Ringkasan pesanan: {', '.join(rincian)}. Total pembayaran: Rp{total:,}. Mohon konfirmasi apakah pesanan sudah sesuai, Kak?"
    }

def kirim_ke_kasir(keranjang, stok_aktif, counter_pesanan):
    """
    Mengirim pesanan ke kasir: memotong stok aktual dan membuat data pesanan kasir.
    Hanya dijalankan saat konfirmasi akhir disetujui.
    """
    if not keranjang:
        return {
            "berhasil": False,
            "pesan": "Keranjang kosong, tidak ada pesanan untuk dikirim ke kasir."
        }

    katalog = _muat_katalog()
    nomor_pesanan = f"A-{counter_pesanan:03d}"
    total = sum(el["subtotal"] for el in keranjang)
    rincian_kasir = []

    # Potong stok aktual untuk setiap item
    for el in keranjang:
        nama_item = el["nama"]
        jumlah_beli = el["jumlah"]
        rincian_kasir.append(f"{jumlah_beli} {el['sebutan']} {nama_item}")

        # Cek apakah produk tunggal atau paket
        item = _cari_item_katalog(nama_item)
        if item and item["tipe"] == "produk":
            stok_aktif[nama_item] = max(0, stok_aktif.get(nama_item, 0) - jumlah_beli)
        elif item and item["tipe"] == "paket":
            for isi in item["data"].get("isi", []):
                prod_nama = isi.get("produk")
                butuh = isi.get("jumlah", 1) * jumlah_beli
                stok_aktif[prod_nama] = max(0, stok_aktif.get(prod_nama, 0) - butuh)

    data_pesanan = {
        "nomor": nomor_pesanan,
        "daftar_item": rincian_kasir,
        "total_harga": total,
        "status": "Diterima Kasir"
    }

    return {
        "berhasil": True,
        "pesanan": data_pesanan,
        "pesan": f"Pesanan {nomor_pesanan} berhasil diteruskan ke kasir toko. Total: Rp{total:,}."
    }
