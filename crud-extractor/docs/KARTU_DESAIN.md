# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

Topik Kartu Desain : 
1. Mengapa pencarian alias dimulai dari scope terdalam ke scope terluar.
2. Mengapa kolom tanpa qualifier hanya diperiksa pada scope terdalam dan bagaimana menangani kolom ambigu.
3. Mengapa scope harus ditutup menggunakan _pop() setelah proses DELETE selesai.
4. Mengapa presedensi AND/OR dinyatakan sebagai dua fungsi parser bertingkat (_or memanggil _and).
5. Mengapa error recovery berhenti setelah ';', bukan di keyword SELECT berikutnya.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Pencarian alias dilakukan dari scope terdalam ke scope terluar. | Mencari alias dari scope terluar terlebih dahulu. | Scope terdalam harus diprioritaskan agar alias lokal dapat melakukan shadowing terhadap alias pada scope luar. Jika alias tidak ditemukan, pencarian dilanjutkan ke scope parent. |

| 2 | Kolom tanpa qualifier hanya diperiksa pada scope terdalam. Jika hanya ada satu sumber tabel, kolom dihubungkan ke sumber tersebut. Jika terdapat lebih dari satu sumber, Resolver memberikan warning karena kolom ambigu. | Mencari sumber tabel sampai ke scope luar atau memilih salah satu tabel secara otomatis ketika terdapat beberapa sumber. | Keputusan ini mengikuti aturan resolusi pada spesifikasi. Memilih tabel secara otomatis berisiko menghasilkan hubungan kolom dan tabel yang salah ketika terdapat beberapa sumber dalam satu scope. |

| 3 | Scope yang dibuat ketika memproses DELETE harus ditutup menggunakan _pop() setelah proses resolusi selesai. | Membiarkan scope tetap aktif setelah statement DELETE selesai. | Setiap statement harus memiliki batas scope yang jelas. Penutupan scope mencegah alias dari statement sebelumnya terbawa dan memengaruhi proses resolusi statement berikutnya. |

| 4 | Presedensi `AND`/`OR` dinyatakan sebagai dua fungsi bertingkat: `_or` (loop untuk `OR`) memanggil `_and` (loop untuk `AND`), lalu `_and` memanggil `_not`. | Satu fungsi dan satu loop untuk `AND` dan `OR` sekaligus (kode lama); atau satu fungsi dengan tabel presedensi bergaya Pratt parser. | Grammar spesifikasi memisahkan `or_expr` dan `and_expr`, dan recursive descent menerjemahkan satu aturan grammar menjadi satu fungsi (Bab 6), sehingga fungsi yang dipanggil lebih dalam mengikat lebih kuat. Satu loop membuat `AND` dan `OR` setara. Pendekatan tabel presedensi (Bab 17) memang ringkas, tetapi memutus pemetaan fungsi-ke-grammar yang membuat kode mudah dicocokkan dengan spesifikasi baris demi baris. |

| 5 | Setelah error, `_synchronize` membuang token sampai dan termasuk `;`, lalu parsing dilanjutkan dengan statement berikutnya. | Berhenti di keyword awal statement berikutnya (`SELECT`, `INSERT`, `UPDATE`, `DELETE`); atau berhenti di akhir file (kode lama). | `;` adalah satu-satunya batas statement yang pasti. Keyword `SELECT` juga muncul di dalam subquery dan `INSERT ... SELECT`, sehingga berhenti di sana bisa memotong statement yang masih utuh dan memunculkan error beruntun. Berhenti di akhir file membuang statement valid sesudahnya, padahal spesifikasi meminta satu error per statement rusak. |