# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---


---

## Bug 1: Kolom tanpa qualifier tidak ter-resolve

**Ditemukan oleh:** Fakhri · **Diperbaiki oleh:** Fakhri

**Gejala.** Ketika program memproses query `SELECT nama FROM pelanggan;`, atribut `resolved` pada `ColumnRef` untuk kolom `nama` tidak terisi (`None`). Seharusnya, karena hanya terdapat satu sumber tabel dalam scope tersebut, kolom `nama` dapat dihubungkan ke tabel `pelanggan`. Perilaku ini tidak sesuai dengan aturan resolusi kolom pada SPESIFIKASI.md bagian 4.5.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT nama FROM pelanggan;
```

**Akar masalah.** Fungsi `_column()` belum memiliki implementasi untuk menangani kolom tanpa qualifier. Resolver belum menentukan bagaimana sebuah kolom dihubungkan dengan sumber tabel ketika nama kolom tidak disertai alias atau nama tabel. Dalam konsep *Crafting Interpreters* Bab 11 (*Resolving and Binding*), resolver bertugas menentukan referensi nama agar dapat dihubungkan dengan deklarasi atau sumber yang sesuai. Pada proyek ini, aturan tersebut diterapkan dengan memeriksa sumber yang tersedia di scope terdalam.

**Perbaikan.** File `crud/resolver.py`, fungsi `_column()`. Ditambahkan logika untuk memeriksa jumlah sumber tabel pada scope terdalam. Jika hanya ada satu sumber, kolom dihubungkan ke sumber tersebut. Jika terdapat lebih dari satu sumber, diberikan warning karena kolom ambigu. Jika tidak ada sumber, diberikan warning bahwa kolom tidak memiliki sumber tabel. Alternatif yang dapat digunakan adalah selalu memilih salah satu tabel ketika terdapat beberapa sumber, tetapi pendekatan tersebut tidak dipilih karena dapat menghasilkan resolusi yang keliru.

**Test regresi.** `test_kolom_tanpa_qualifier_satu_tabel_regresi` pada `tests/test_tambahan.py`.

**Peran AI.** AI membantu menjelaskan aturan resolusi kolom tanpa qualifier dan memberikan arahan implementasi fungsi `_column()`. Implementasi kemudian disesuaikan dengan struktur Resolver dan SPESIFIKASI.md. Hasilnya diverifikasi melalui pengujian kolom tanpa qualifier pada satu tabel, beberapa tabel, dan tanpa sumber tabel.

---

## Bug 2: Alias pada scope terdalam tidak diprioritaskan

**Ditemukan oleh:** Fakhri · **Diperbaiki oleh:** Fakhri

**Gejala.** Ketika terdapat alias dengan nama yang sama pada query utama dan subquery, Resolver justru menggunakan alias dari scope luar. Seharusnya, alias pada scope terdalam diprioritaskan sebelum mencari ke scope luar. Hal ini menyebabkan kolom dapat terhubung ke tabel yang salah.

**Reproduksi minimal.**
```sql
SELECT x.id
FROM pelanggan x
WHERE x.id IN (
    SELECT x.pelanggan_id
    FROM pesanan x
);
```

**Akar masalah.** Fungsi `_lookup()` melakukan pencarian dari scope luar terlebih dahulu, kemudian menuju scope dalam. Urutan tersebut tidak sesuai dengan aturan pencarian nama pada scope bertingkat. Akibatnya, alias `x` pada subquery tidak dapat mengesampingkan alias `x` pada query utama.

**Perbaikan.** File `crud/resolver.py`, fungsi `_lookup()`. Urutan pencarian diubah agar dimulai dari scope saat ini, kemudian dilanjutkan ke parent scope. Dengan demikian, alias pada scope terdalam akan ditemukan terlebih dahulu.

**Test regresi.** `test_alias_shadowing_scope_terdalam_diprioritaskan` pada `tests/test_tambahan.py`.

**Peran AI.** AI membantu mengidentifikasi kesalahan urutan pencarian alias dan memberikan arahan perbaikan pada fungsi `_lookup()`. Perbaikan disesuaikan dengan struktur Resolver dan diverifikasi melalui pengujian alias pada scope bertingkat.

---

## Bug 3: Scope DELETE tidak ditutup setelah statement selesai

**Ditemukan oleh:** Fakhri · **Diperbaiki oleh:** Fakhri

**Gejala.** Scope yang dibuat ketika memproses statement `DELETE` tidak ditutup setelah proses resolusi selesai. Akibatnya, alias dari statement `DELETE` dapat terbawa ke statement berikutnya dan menyebabkan kolom dikenali menggunakan alias yang seharusnya sudah tidak berlaku.

**Reproduksi minimal.**
```sql
DELETE FROM sesi s WHERE s.id = 1;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** Fungsi `_delete()` memanggil `_push()` untuk membuat scope baru, tetapi tidak memanggil `_pop()` setelah kondisi `WHERE` selesai diproses. Akibatnya, scope DELETE masih aktif ketika Resolver memproses statement berikutnya.

**Perbaikan.** File `crud/resolver.py`, fungsi `_delete()`. Ditambahkan pemanggilan `_pop()` setelah ekspresi `WHERE` selesai diproses agar scope DELETE ditutup dan tidak memengaruhi statement berikutnya.

**Test regresi.** `test_scope_delete_tidak_bocor_ke_statement_berikutnya` pada `tests/test_tambahan.py`.

**Peran AI.** AI membantu menganalisis kemungkinan kebocoran scope pada proses resolusi DELETE dan memberikan arahan penambahan `_pop()`. Perbaikan diverifikasi dengan pengujian yang memastikan alias dari statement DELETE tidak terbawa ke statement berikutnya.

---

## Bug 4: Lexer belum menangani komentar blok

**Ditemukan oleh:** Fakhri · **Diperbaiki oleh:** Fakhri

**Gejala.** Lexer belum dapat melewati komentar blok yang menggunakan format `/* ... */`. Ketika menemukan karakter pembuka komentar, Lexer tidak mengenalinya sebagai komentar sehingga proses tokenisasi dapat menghasilkan error. Seharusnya, isi komentar dilewati dan proses tokenisasi dilanjutkan ke perintah SQL berikutnya.

**Reproduksi minimal.**
```sql
/* catatan */
SELECT id FROM pelanggan;
```

**Akar masalah.** Fungsi `_scan_token()` belum memiliki penanganan khusus untuk komentar blok. Lexer belum memeriksa pasangan karakter `/*` sebagai pembuka dan `*/` sebagai penutup komentar. Akibatnya, karakter komentar diproses seperti karakter SQL biasa.

**Perbaikan.** File `crud/lexer.py`. Pada fungsi `_scan_token()` ditambahkan pemeriksaan pembuka komentar blok dan pemanggilan fungsi `_block_comment()`. Fungsi `_block_comment()` bertugas melewati isi komentar hingga menemukan penutup `*/`. Jika penutup tidak ditemukan, Lexer menghasilkan `LexError`. Proses pembacaan menggunakan `_advance()` agar posisi baris dan kolom tetap diperbarui.

**Test regresi.** `test_lexer_mengabaikan_komentar_blok_multibaris` pada `tests/test_tambahan.py`.

**Peran AI.** AI membantu memberikan arahan implementasi penanganan komentar blok pada Lexer. Kode disesuaikan dengan struktur Lexer yang tersedia dan diverifikasi menggunakan pengujian komentar multibaris, komentar kosong, serta komentar yang tidak memiliki penutup.