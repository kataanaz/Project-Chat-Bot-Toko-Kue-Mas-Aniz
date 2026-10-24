import json
import tools

def periksa_tidak_ada_pcs(obj):
    """Fungsi rekursif untuk memastikan tidak ada string 'pcs' di dict/list hasil fungsi."""
    teks_json = json.dumps(obj).lower()
    assert "pcs" not in teks_json, f"Ditemukan 'pcs' dalam output: {obj}"

def test_pencarian_normal():
    # Pencarian kata kunci normal
    res = tools.cari_produk(kata_kunci="Brownies")
    assert res["ditemukan"] is True
    assert len(res["hasil"]) >= 1
    assert res["hasil"][0]["nama"] == "Brownies Panggang"
    assert res["hasil"][0]["sebutan"] == "potong"
    periksa_tidak_ada_pcs(res)

def test_nama_tidak_ada():
    # Pencarian produk yang tidak ada di katalog
    res = tools.cari_produk(kata_kunci="Kue Keju Tart Tart")
    assert res["ditemukan"] is False
    assert res["hasil"] == []
    periksa_tidak_ada_pcs(res)

    res_stok = tools.cek_stok("Kue Gaib")
    assert res_stok["ditemukan"] is False
    periksa_tidak_ada_pcs(res_stok)

    res_alergen = tools.info_alergen("Kue Gaib")
    assert res_alergen["ditemukan"] is False
    periksa_tidak_ada_pcs(res_alergen)

def test_huruf_besar_kecil_dan_spasi():
    # Toleran huruf besar/kecil dan spasi berlebih
    res_stok = tools.cek_stok("   bRoWnIeS    pAnGgAnG   ")
    assert res_stok["ditemukan"] is True
    assert res_stok["nama"] == "Brownies Panggang"
    assert res_stok["stok"] == 20
    assert res_stok["sebutan"] == "potong"
    periksa_tidak_ada_pcs(res_stok)

    res_alergen = tools.info_alergen("  kUe LuMpUr (IsI 5) ")
    assert res_alergen["ditemukan"] is True
    assert "santan" in res_alergen["alergen"]
    periksa_tidak_ada_pcs(res_alergen)

def test_filter_kategori_dan_harga():
    # Filter kategori cake
    res_cake = tools.cari_produk(kategori="cake")
    assert res_cake["ditemukan"] is True
    for item in res_cake["hasil"]:
        assert item["kategori"] == "cake"
    periksa_tidak_ada_pcs(res_cake)

    # Filter harga maksimum 15000
    res_harga = tools.cari_produk(maks_harga=15000)
    assert res_harga["ditemukan"] is True
    for item in res_harga["hasil"]:
        assert item["harga"] <= 15000
    periksa_tidak_ada_pcs(res_harga)

    # Kombinasi kategori asin dan harga <= 20000
    res_asin = tools.cari_produk(kategori="asin", maks_harga=20000)
    assert res_asin["ditemukan"] is True
    assert res_asin["hasil"][0]["nama"] == "Risoles Ragout (isi 3)"
    periksa_tidak_ada_pcs(res_asin)

def test_stok_paket():
    # Paket Ngopi Sore = 1 Brownies (stok 20) + 1 Pukis (stok 12) -> min = 12
    res_paket = tools.cek_stok("Paket Ngopi Sore")
    assert res_paket["ditemukan"] is True
    assert res_paket["nama"] == "Paket Ngopi Sore"
    assert res_paket["stok"] == 12
    assert res_paket["sebutan"] == "paket"
    periksa_tidak_ada_pcs(res_paket)

    # Paket Arisan = 1 Donat (stok 10) + 1 Kue Lumpur (stok 12) -> min = 10
    res_arisan = tools.cek_stok("Paket Arisan")
    assert res_arisan["ditemukan"] is True
    assert res_arisan["stok"] == 10
    assert res_arisan["sebutan"] == "paket"
    periksa_tidak_ada_pcs(res_arisan)

def test_daftar_terlaris():
    res_terlaris = tools.daftar_terlaris()
    assert res_terlaris["ditemukan"] is True
    assert res_terlaris["total"] == 3
    nama_terlaris = [p["nama"] for p in res_terlaris["hasil"]]
    assert "Brownies Panggang" in nama_terlaris
    assert "Donat Gula (isi 6)" in nama_terlaris
    assert "Kue Lumpur (isi 5)" in nama_terlaris
    periksa_tidak_ada_pcs(res_terlaris)

def test_ketiadaan_kata_pcs_di_semua_fungsi():
    # Uji eksplisit pada seluruh produk dan paket
    semua = tools.cari_produk()
    periksa_tidak_ada_pcs(semua)
    for p in semua["hasil"]:
        stok_res = tools.cek_stok(p["nama"])
        periksa_tidak_ada_pcs(stok_res)
        alergen_res = tools.info_alergen(p["nama"])
        periksa_tidak_ada_pcs(alergen_res)

def test_keranjang_dan_pesanan():
    stok = tools.inisialisasi_stok()
    keranjang = []

    # 1. Tambah normal
    res1 = tools.tambah_ke_keranjang(keranjang, stok, "Brownies Panggang", 2)
    assert res1["berhasil"] is True
    assert res1["total_keranjang"] == 30000
    assert len(keranjang) == 1
    periksa_tidak_ada_pcs(res1)

    # 2. Tambah paket
    res2 = tools.tambah_ke_keranjang(keranjang, stok, "Paket Ngopi Sore", 1)
    assert res2["berhasil"] is True
    assert res2["total_keranjang"] == 57000
    assert len(keranjang) == 2
    periksa_tidak_ada_pcs(res2)

    # 3. Validasi jumlah di luar 1-20
    res_nol = tools.tambah_ke_keranjang(keranjang, stok, "Brownies Panggang", 0)
    assert res_nol["berhasil"] is False
    res_minus = tools.tambah_ke_keranjang(keranjang, stok, "Brownies Panggang", -5)
    assert res_minus["berhasil"] is False
    res_lebih20 = tools.tambah_ke_keranjang(keranjang, stok, "Brownies Panggang", 25)
    assert res_lebih20["berhasil"] is False

    # 4. Validasi melebihi stok
    res_over = tools.tambah_ke_keranjang(keranjang, stok, "Lapis Legit", 10) # stok cuma 6
    assert res_over["berhasil"] is False

    # 5. Lihat keranjang
    res_lihat = tools.lihat_keranjang(keranjang)
    assert res_lihat["kosong"] is False
    assert res_lihat["total_harga"] == 57000
    periksa_tidak_ada_pcs(res_lihat)

    # 6. Ringkas pesanan
    res_ringkas = tools.ringkas_pesanan(keranjang)
    assert res_ringkas["kosong"] is False
    assert res_ringkas["total_harga"] == 57000
    periksa_tidak_ada_pcs(res_ringkas)

    # 7. Kirim ke kasir
    stok_sebelum_brownies = stok["Brownies Panggang"] # 20
    stok_sebelum_pukis = stok["Pukis Cokelat (isi 5)"] # 12
    res_kasir = tools.kirim_ke_kasir(keranjang, stok, 1)
    assert res_kasir["berhasil"] is True
    assert res_kasir["pesanan"]["nomor"] == "A-001"
    assert res_kasir["pesanan"]["total_harga"] == 57000
    assert res_kasir["pesanan"]["status"] == "Diterima Kasir"
    periksa_tidak_ada_pcs(res_kasir)

    # Verifikasi pemotongan stok aktual
    # 2 Brownies langsung + 1 Brownies dari Paket Ngopi Sore = 3 terpotong
    assert stok["Brownies Panggang"] == stok_sebelum_brownies - 3
    # 1 Pukis dari Paket Ngopi Sore = 1 terpotong
    assert stok["Pukis Cokelat (isi 5)"] == stok_sebelum_pukis - 1

if __name__ == "__main__":
    print("Menjalankan pengujian tools.py...")
    test_pencarian_normal()
    test_nama_tidak_ada()
    test_huruf_besar_kecil_dan_spasi()
    test_filter_kategori_dan_harga()
    test_stok_paket()
    test_daftar_terlaris()
    test_ketiadaan_kata_pcs_di_semua_fungsi()
    test_keranjang_dan_pesanan()
    print("SEMUA PENGUJIAN tools.py LOLOS 100%!")
