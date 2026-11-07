# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

## Bug 1: Keyword huruf kecil dibaca sebagai IDENT

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** `tokenize("select id from t")` menghasilkan token pertama `IDENT 'select'`. Menurut SPESIFIKASI.md bagian 2.2, keyword tidak peka huruf besar/kecil: `select`, `Select`, dan `SELECT` harus sama-sama `KEYWORD` dengan nilai `SELECT`. Test visible `test_keyword_huruf_kecil` gagal.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select 1
```

**Akar masalah.** 
Pada Bab 4 bagian 4.7. Scanner itu membaca kata utuh lebih dulu baru dicocokkan dengan tabel cadangan yang ada. Sementara pada kode lama, kata utuh itu langsung dicocokan ke KEYWORDS aslinya, Sedangkan pada tabel menggunakan huruf besar semua. Di Spesifikasi 2.2 meminta pencocokkan bisa dilakukan pada huruf besar maupun kecil. Perbaikkannya: Cocokkan dengan versi huruf besarnya lalu simpan nilai token dalam huruf besar.

**Perbaikan.** `crud/lexer.py`, fungsi `_word`: pencocokan ke `KEYWORDS` memakai `text.upper()` dan nilai token keyword disimpan dalam huruf besar; `IDENT` tidak diubah. Alternatif yang dipertimbangkan: membuat `KEYWORDS` berisi semua variasi huruf; tidak dipilih karena tidak praktis dan mudah ketinggalan. Alternatif lain: menormalisasi seluruh teks sumber ke huruf besar; tidak dipilih karena akan merusak isi string dan nama pengenal.

**Test regresi.** 
test_keyword_tidak_peka_huruf_besar_kecil.

**Peran AI.** AI memberi kode perbaikan dan penjelasan konsep. Diverifikasi dengan memanggil `tokenize` pada `select Select selection fromage` dan dengan test visible `test_keyword_huruf_kecil`. (Lihat `docs/LOG_AI.md`.)

---

## Bug 2: Operator `<>` terpecah menjadi `<` dan `>`

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** `a <> b` menghasilkan dua token `OP '<'` lalu `OP '>'`. Menurut SPESIFIKASI.md bagian 2.5, lexer harus mengambil operator terpanjang yang cocok (maximal munch), jadi `<>` adalah satu token. Akibat turunan: parser gagal pada `laporan_penjualan.sql` dengan pesan `diharapkan ekspresi, ditemukan '>'`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE a <> 1
```

**Akar masalah.**
Bab 4 bagian 4.6 (Longer Lexemes) memakai match untuk memeriksa apakah karakter berikutnya melanjutkan operator, dan prinsip maximal munch menyatakan aturan yang menelan karakter terbanyak harus menang. Pada lexer yang lama, Cabang < hanya memeriksa untuk satu kemungkinan yaitu = sebagai <= dan tidak memeriksa > sebagai <>. akibatnya kalau kita menulis <> akan dibaca < dan >. Ketika di parser nantinya akan error karena membaca bahwa > adalah ekspresi asing.

**Perbaikan.** `crud/lexer.py`, cabang `<`: setelah `<`, cek `=` untuk `<=`, lalu cek `>` untuk `<>`, selain itu `<`. Alternatif yang dipertimbangkan: membiarkan lexer memecah `<` dan `>` lalu menggabungkannya di parser; tidak dipilih karena membuat parser harus tahu detail leksikal dan melanggar pembagian tugas lexer/parser.

**Test regresi.**
test_operator_tidak_sama_dengan_satu_token.

**Peran AI.** AI memberi kode perbaikan. Diverifikasi dengan `tokenize` pada `a<>b`, `a<b`, `a<=b`, `a!=b`, dan dengan `test_matrix_laporan_penjualan` yang sebelumnya gagal karena `>`.

---

## Bug 3: Dua kutip di dalam string (`''`) memutus string

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** `'O''Brien'` menghasilkan dua token `STRING`. Menurut SPESIFIKASI.md bagian 2.4, `''` di dalam string mewakili satu karakter kutip, sehingga hasil yang benar adalah satu `STRING` bernilai `O'Brien`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT 'O''Brien'
```

**Akar masalah.**
Akar masalah. Bab 4 bagian 4.6.1 membedakan lexeme (teks mentah beserta kutip) dari nilai literal (isi string), dan scanner memakai lookahead peek() untuk melihat karakter berikutnya tanpa mengonsumsinya. Pada kode lama mebaca ' sebagai penutup string tanpa membaca apa yang ada setelahnya. Sementara pada spesifikasi 2.4 meminta untuk dua kutip berturut-turut itu dinyatakan sebagai satu kutip. Makanya diawal kata 'O''Brien' itu malah dibaca sebagai 2 string. Perbaikannya, lihat terlebih dulu apakah setelah ' ada ' lagi? jika ada maka simpan kutip hanya sebagai satu string.

**Perbaikan.** `crud/lexer.py`, fungsi `_string`: saat bertemu `'`, bila karakter berikutnya juga `'`, konsumsi yang kedua dan tambahkan satu `'` ke isi string, lalu lanjut; bila tidak, string berakhir. Alternatif yang dipertimbangkan: memakai regex untuk mengambil string; tidak dipilih karena melanggar pendekatan scanner karakter-demi-karakter yang dipakai proyek dan lebih sulit melaporkan baris/kolom error.

**Test regresi.** 
test_escape_dua_kutip_di_dalam_string.

**Peran AI.** AI memberi kode perbaikan. Diverifikasi dengan `tokenize` pada `'O''Brien'`, `''` (string kosong), dan `'abc` (harus `LexError`).

---

## Bug 4: Presedensi `AND` dan `OR` sama

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** `a = 1 OR b = 2 AND c = 3` diparse sebagai `(a = 1 OR b = 2) AND c = 3`. Menurut SPESIFIKASI.md bagian 3.1, `AND` mengikat lebih kuat daripada `OR`, jadi hasil yang benar adalah `a = 1 OR (b = 2 AND c = 3)`. Gejala terlihat di pohon baris 2 `audit.sql`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3
```

**Akar masalah.**
Bab 6 bagian 6.1 menjelaskan bahwa presedensi menentukan operator mana yang dikerjakan lebih dulu, dan bagian 6.2 menunjukkan bahwa parser recursive descent menerjemahkan setiap aturan grammar menjadi satu fungsi, dengan * menjadi loop while. Pada spesifikasi Grammar And dan Or menjadi dua aturan dan aturan yang lebih lemah memanggil yang lebih kuat. Sementara pada kode lama menaruh And dan Or menjadi satu fungsi dalam satu loop, alhasil dibacanya dari kiri ke kanan dan setingkat. yang dimana a = 1 OR b = 2 AND c = 3 menjadi (a = 1 OR b = 2) AND c = 3.

**Perbaikan.** `crud/parser.py`: fungsi `_logical` dipecah menjadi `_or` (loop untuk `OR`, memanggil `_and`) dan `_and` (loop untuk `AND`, memanggil `_not`); `_expr` kini memanggil `_or`. Alternatif yang dipertimbangkan: tetap satu fungsi dengan tabel presedensi (gaya Pratt); tidak dipilih karena grammar spesifikasi sudah berbentuk satu aturan per tingkat dan proyek memakai recursive descent, sehingga pemetaan fungsi ke aturan lebih mudah dicek.

**Test regresi.**
_where(sql).
test_and_lebih_kuat_dari_or.
test_between_and_tidak_terganggu_presedensi.

**Peran AI.** AI memberi kode perbaikan. Diverifikasi dengan `--ast` pada `t.sql` dan `audit.sql` (puncak pohon `OR`, anak kanan `AND`), dan seluruh test lama tetap lulus.

---

## Bug 5: `LEFT OUTER JOIN` ditolak

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** `... LEFT OUTER JOIN u ON ...` menghasilkan error `diharapkan JOIN, ditemukan 'OUTER'`. Grammar `join` di SPESIFIKASI.md bagian 3 menulis `[ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN"`, jadi `OUTER` setelah `LEFT` bersifat opsional dan harus diterima.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t LEFT OUTER JOIN u ON t.id = u.id
```

**Akar masalah.**
Bab 6 bagian 6.2 memetakan unsur grammar ke kode: terminal menjadi pencocokan token, dan unsur opsional (?, dalam spesifikasi ditulis [ ... ]) menjadi pernyataan if. Grammar Join menulis "LEFT" [ "OUTER" ] sebagai sebuah satu opsional jadi mau pake kata Outer atau tidak itu tidak masalah. Namun pada Fungsi Join yang lama, opsional ini tidak ada. Jadinya kalau kita menulis LEFT, ia akan menuntuk join dan outer akan ditolak. 

**Perbaikan.** `crud/parser.py`, fungsi `_join`: setelah `LEFT`, tambahkan `self._match_kw("OUTER")` sebelum menuntut `JOIN`. Alternatif yang dipertimbangkan: menjadikan `LEFT OUTER` satu token di lexer; tidak dipilih karena lexer tidak seharusnya tahu urutan kata antar-token, itu tugas parser.

**Test regresi.**
test_left_outer_join_diterima.
test_outer_join_tanpa_left_tetap_error.

**Peran AI.** AI memberi satu baris perbaikan. Diverifikasi dengan `--ast` pada `LEFT OUTER JOIN` (`Join kind='LEFT'`, tanpa error), dan dicek bahwa `OUTER JOIN` tanpa `LEFT` tetap error. AI sempat keliru soal `RIGHT JOIN` (lihat `docs/LOG_AI.md`): ternyata `RIGHT` dibaca sebagai alias tabel karena bukan keyword.

---

## Bug 6: Error recovery membuang seluruh sisa file

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** Pada `SELEC x; SELECT a FROM t; DELETE FROM q;` hanya satu error yang dilaporkan, tetapi dua statement valid sesudahnya tidak diproses (hasil matrix kosong). SPESIFIKASI.md bagian 6 meminta panic mode: buang token sampai dan termasuk `;` berikutnya, lalu lanjutkan dengan statement sesudahnya; setiap statement rusak menghasilkan tepat satu error. Hasil yang benar: 1 error dan matrix `{q: D, t: R}`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELEC x;
SELECT a FROM t;
```

**Akar masalah.**
Bab 6 bagian 6.3.1 menjelaskan panic mode: setelah error, parser membuang token sampai titik sinkronisasi, lalu melanjutkan. Bagian 6.3.3 menunjukkan bahwa titik sinkronisasi tradisional ada di batas antar-statement, dan versi buku berhenti setelah token titik koma.Fungsi Synchronize yang lama itu hanya punya satu kondisi berhenti. Jadi kalau satu statement rusak maka akan membuang file sisanya. Sementara pada spesifikasi bagian 6 meminta berhenti setelah tanda ; supaya statemnet selanjutnya tetap valid diproses.

**Perbaikan.** `crud/parser.py`, fungsi `_synchronize`: loop membuang token satu per satu dan berhenti (return) setelah membuang token `;`. Alternatif yang dipertimbangkan: berhenti di kata awal statement (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) seperti variasi di buku; tidak dipilih karena kata `SELECT` juga muncul di dalam subquery dan `INSERT ... SELECT`, sehingga bisa memotong statement di tengah dan menimbulkan error beruntun.

**Test regresi.**
test_error_recovery_berhenti_di_titik_koma.
test_error_recovery_token_error_adalah_titik_koma.

**Peran AI.** AI memberi kode perbaikan. Diverifikasi dengan `campuran_error.sql` (satu error di baris 4, statement sesudahnya tetap terproses) dan kasus tepi: token error berupa `;`, dua statement menyatu tanpa `;`, dan file tanpa `;` di akhir.

---
## Bug 7: Alias pada scope terdalam tidak diprioritaskan

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

## Bug 8: Scope DELETE tidak ditutup setelah statement selesai

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

## Bug 9: Subquery di `UPDATE` diberi operasi `U`, bukan `R`

**Ditemukan oleh:** Rasyad · **Diperbaiki oleh:** Rasyad

**Gejala.** Pada `UPDATE a SET x = (SELECT y FROM b) WHERE id IN (SELECT id FROM c)`, tabel `b` dan `c` ikut ditandai `U`. Menurut SPESIFIKASI.md bagian 5, membaca tabel lewat subquery selalu `R`, apa pun jenis statement luarnya. Hasil yang benar: `{a: U, b: R, c: R}`. Gejala turunan: `pesanan` tercatat `RUD`, bukan `RD`, pada `laporan_penjualan.sql`, sehingga `test_matrix_laporan_penjualan` gagal.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
UPDATE a SET x = (SELECT y FROM b)
```

**Akar masalah.**
Bab 5 bagian 5.3 itu menjelaskan bahwa Analyzer harus menelusuri AST. Juga pada spesifiksi bagian 5, aturan CRUD proyek menyatakan bahwa tabel yang lewat subquery selalu R. Pada kode yang lama label "U" itu diteruskan hingga SET dan WHERE sehingga label "U" terbawa ke subquery dan melabelkan b dan c sebagai "U". Padahal hanya tabel target yang boleh dilabelu "U".

**Perbaikan.** `crud/analyzer.py`, cabang `ast.Update` di `analyze_statement`: pemanggilan `_collect` untuk nilai assignment dan `WHERE` diubah dari `"U"` menjadi `"R"`; hanya tabel target yang ditandai `U`. Alternatif yang dipertimbangkan: memindahkan penentuan operasi ke dalam `_collect` agar setiap subquery otomatis `R`; tidak dipilih karena perubahan lebih besar dan berisiko mengubah cabang lain yang sudah benar.

**Test regresi.** 
test_subquery_di_update_hanya_dibaca

**Peran AI.** AI memberi kode perbaikan.

---

## Catatan TODO T1: `INSERT ... SELECT` belum didukung
**Dikerjakan oleh:** Rasyad

**Kondisi awal.** `INSERT INTO arsip (id) SELECT id FROM pesanan` ditolak dengan pesan `INSERT ... SELECT belum didukung`. Grammar `insert_stmt` di SPESIFIKASI.md bagian 3 menerima `VALUES` atau `select_stmt`.

**Penyelesaian.** `crud/parser.py`, fungsi `_insert`: cabang `SELECT` memanggil `_select()` dan membentuk `ast.Insert(table, columns, [], query, line=start.line)`. Field `values` diisi `[]` (bukan `None`) karena resolver dan analyzer melakukan loop pada `values`. Hasil analyzer: `{arsip: C, pesanan: R}`.

> **Panduan konsep (hapus).** Bab 6 bagian 6.2: nonterminal menjadi pemanggilan fungsi aturannya (di sini `_select`), sehingga tidak perlu menulis ulang logika select. Bab 5 bagian 5.2: node AST `Insert` punya field `query` untuk menyimpan subpohon select.

**Verifikasi.** `test_insert_select` lulus; `analyze_source` pada `INSERT INTO arsip (id) SELECT id FROM pesanan WHERE total > 10;` menghasilkan `[] {'arsip': 'C', 'pesanan': 'R'}`. 

**Peran AI:** AI memberi kode pengganti baris `raise`; diverifikasi dengan test dan keluaran tersebut.


---

## Catatan TODO T2: Kolom tanpa qualifier tidak ter-resolve

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

## Catatan TODO T3: Lexer belum menangani komentar blok

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