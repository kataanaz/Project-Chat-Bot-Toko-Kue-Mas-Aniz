import json
import os

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
        if _bersihkan_teks(p.get("nama")) == nama_norm:
            return {
                "ditemukan": True,
                "nama": p["nama"],
                "stok": p["stok"],
                "sebutan": p["sebutan"]
            }

    # Cek di paket
    for pak in katalog.get("paket", []):
        if _bersihkan_teks(pak.get("nama")) == nama_norm:
            stok_komponen = []
            for item in pak.get("isi", []):
                prod_target = _bersihkan_teks(item.get("produk"))
                jml_target = item.get("jumlah", 1)
                stok_item = 0
                for p in katalog.get("produk", []):
                    if _bersihkan_teks(p.get("nama")) == prod_target:
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
    nama_norm = _bersihkan_teks(nama)

    # Cek di produk satuan
    for p in katalog.get("produk", []):
        if _bersihkan_teks(p.get("nama")) == nama_norm:
            return {
                "ditemukan": True,
                "nama": p["nama"],
                "alergen": p.get("alergen", []),
                "sebutan": p["sebutan"]
            }

    # Cek di paket
    for pak in katalog.get("paket", []):
        if _bersihkan_teks(pak.get("nama")) == nama_norm:
            semua_alergen = set()
            for item in pak.get("isi", []):
                prod_target = _bersihkan_teks(item.get("produk"))
                for p in katalog.get("produk", []):
                    if _bersihkan_teks(p.get("nama")) == prod_target:
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
