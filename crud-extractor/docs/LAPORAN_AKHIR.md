# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text

```

## 2. Tiga kasus di mana regex salah

**Kasus: Regex salah membaca perintah SQL yang berada di dalam komentar blok.**

SQL:
```sql
/* DELETE FROM transaksi WHERE status = 'batal'; */
SELECT id FROM pelanggan;
```

- **Kesalahan regex:** Jika regex tidak mengabaikan komentar blok, teks `DELETE FROM transaksi` dapat ikut terbaca sebagai perintah SQL. Akibatnya, tabel `transaksi` berpotensi salah terdeteksi memiliki operasi Delete (D).
- **Mengapa parser benar:** Lexer dapat mengenali komentar blok `/* ... */` dan melewatinya sebelum token diteruskan ke Parser. Dengan demikian, perintah DELETE di dalam komentar tidak dianggap sebagai bagian dari program SQL yang aktif.


## 3. Batas pendekatan kami

**1. Komentar blok bersarang belum didukung.**

Contoh SQL:
```sql
/* Komentar luar
   /* Komentar dalam */
*/
SELECT id FROM pelanggan;
```

- **Akibat pada CRUD Matrix:** Lexer hanya mengenali penutup komentar blok pertama. Sisa komentar dapat terbaca sebagai token SQL dan berpotensi menyebabkan kesalahan parsing atau hasil CRUD Matrix yang tidak sesuai.
- **Informasi yang dibutuhkan:** Lexer perlu mengetahui tingkat kedalaman komentar menggunakan penghitung (*nesting depth*), sehingga komentar baru dianggap selesai ketika seluruh tingkat komentar sudah ditutup.

**2. Kolom tanpa qualifier pada beberapa tabel belum dapat dipastikan sumbernya.**

Contoh SQL:
```sql
SELECT id
FROM pelanggan p
JOIN pesanan ps ON p.id = ps.pelanggan_id;
```

- **Akibat pada CRUD Matrix:** Resolver tidak dapat memastikan apakah kolom `id` berasal dari tabel `pelanggan` atau `pesanan`. Resolver memberikan warning dan membiarkan `resolved` bernilai `None`, sehingga sumber kolom tersebut tidak dapat ditentukan secara pasti.
- **Informasi yang dibutuhkan:** Diperlukan informasi skema database, khususnya daftar kolom pada setiap tabel, agar Resolver dapat menentukan tabel yang memiliki kolom tersebut. Jika kedua tabel memiliki kolom dengan nama sama, kolom tetap harus dinyatakan ambigu.


## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.
