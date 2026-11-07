# Laporan Akhir

## 1. Hasil evaluasi
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')

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

Kami membagi pekerjaan berdasarkan modul pipeline agar bisa berjalan paralel tanpa saling menunggu. Tiap anggota bekerja di branch sendiri, lalu hasilnya digabung ke repositori bersama (`git merge`) secara berkala.

| Area | Rasyad | Fakhriy |
| --- | --- | --- |
| Lexer | Bug 1 (keyword huruf kecil), bug 2 (`<>`), bug 3 (`''` di dalam string) | T3 (komentar blok `/* ... */`) |
| Parser | T1 (`INSERT ... SELECT`), bug 4 (presedensi `AND`/`OR`), bug 5 (`LEFT OUTER JOIN`), bug 6 (error recovery di `;`) | - |
| Resolver | - | T2 (kolom tanpa qualifier), bug 7 (prioritas scope terdalam), bug 8 (scope `DELETE` ditutup) |
| Analyzer | Bug 9 (subquery di `UPDATE` bernilai `R`) | - |
| Tes | Tes regresi bug 1-6 dan T1 | `tests/test_tambahan.py`: tes regresi bug 7, 8, 9, T2, T3 dan tes kasus tepi |
| Data | Label `audit.sql` dan `pemeliharaan.sql` di `data/ground_truth.csv` (manual, berdasarkan spesifikasi), serta menjalankan `evaluate.py` | - |
| Dokumen | `LAPORAN_BUG.md` (bug 1-6, 9, T1), Kartu Desain nomor 4-5, Laporan Akhir bagian 1 dan 4 | `LAPORAN_BUG.md` (bug 7, 8, T2, T3), Kartu Desain nomor 1-3, Laporan Akhir bagian 2 dan 3 |
| `LOG_AI.md` | Mencatat penggunaan AI miliknya | Mencatat penggunaan AI miliknya |

Nomor bug dan TODO mengikuti urutan pipeline (lexer, parser, resolver, analyzer) pada `docs/LAPORAN_BUG.md`.

**Cara kami memastikan kedua anggota memahami seluruh kode.**
Kami tidak melakukan pair programming bergantian setiap 30 menit seperti saran soal, dikarenakan tempat dan waktu yang tidak memungkinkan, agar waktu pengerjaan tetap efisien maka kami melakukan pembagian tupoksi kerja. Namun Untuk tetap tercapainya pemahaman 2 pihak, kami melakukan hal berikut:

- Setelah tiap merge, kami menjalankan `python -m pytest -q` bersama.
- Tiap anggota membaca laporan bug partner dan memastikan bisa menjelaskan akar masalahnya dengan kata-kata sendiri.
- Sebelum demo, kami saling menjelaskan modul partner: Rasyad menjelaskan resolver (scope, shadowing, penutupan scope), Fakhriy menjelaskan parser (presedensi, error recovery) dan lexer (komentar blok, `<>`, `''`).
