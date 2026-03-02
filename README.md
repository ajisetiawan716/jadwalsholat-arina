# 📖 Jadwal Sholat Arina (JSON Endpoint)

Repository ini menyediakan **jadwal sholat bulanan dalam format JSON** untuk seluruh kota/kabupaten di Indonesia berdasarkan data dari:

👉 [https://jadwalsholat.arina.id](https://jadwalsholat.arina.id)

Data di-generate otomatis setiap awal bulan melalui GitHub Actions dan dapat diakses langsung melalui endpoint raw GitHub.

---

## 📂 Struktur Data

Format folder:

```
jadwal/{kota}/{tahun}/{bulan}.json
```

Contoh:

```
jadwal/brebes/2026/02.json
```

---

## 🗂 Daftar Kota (`kota.json`)

Di root repository tersedia file:

```
kota.json
```

File ini berisi daftar seluruh slug kota/kabupaten yang tersedia dan digunakan dalam struktur folder `jadwal/`.

Contoh isi:

```json
[
  "acehbarat",
  "acehbaratdaya",
  "acehbesar",
  "acehjaya",
  "acehselatan",
  "acehsingkil"
]
```

### 🌐 Endpoint `kota.json`

Raw GitHub:

```
https://raw.githubusercontent.com/ajisetiawan716/jadwalsholat-arina/master/kota.json
```

Dengan endpoint ini, integrator cukup fetch sekali untuk mendapatkan seluruh daftar kota yang tersedia.

### Fungsi `kota.json`

* Menjadi referensi daftar kota yang didukung
* Digunakan oleh script generator untuk proses scraping
* Mempermudah integrasi eksternal tanpa perlu menebak slug
* Dapat dijadikan validasi sebelum request jadwal

---

## 📦 Format JSON

Contoh isi file jadwal:

```json
[
  {
    "tanggal": "2026-02-01",
    "imsyak": "04:16",
    "shubuh": "04:26",
    "terbit": "05:48",
    "dhuha": null,
    "dzuhur": "12:00",
    "ashr": "15:19",
    "magrib": "18:12",
    "isya": "19:25"
  }
]
```

---

## 🌐 Contoh Endpoint Jadwal

```
https://raw.githubusercontent.com/ajisetiawan716/jadwalsholat-arina/master/jadwal/brebes/2026/02.json
```

---

## ⚙️ Update Otomatis

* Update dijalankan setiap tanggal **1 jam 01:00 WIB**
* Hanya generate bulan berjalan
* File tidak akan ditimpa jika sudah ada
* Menyimpan histori maksimal 1 tahun (rolling)

---

## 🛠 Cara Menjalankan Manual

```bash
pip install requests lxml pytz
python script/parser.py
```

---

## ⚠ Catatan

* Data bersumber dari jadwalsholat.arina.id
* Repository ini hanya melakukan scraping dan konversi ke JSON
* Tidak menyediakan API resmi

---

## 📜 Lisensi

Gunakan dengan bijak sesuai kebutuhan pribadi atau non-komersial.

---