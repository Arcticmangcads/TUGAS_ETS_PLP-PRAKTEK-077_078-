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
4. 
5. 

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Pencarian alias dilakukan dari scope terdalam ke scope terluar. | Mencari alias dari scope terluar terlebih dahulu. | Scope terdalam harus diprioritaskan agar alias lokal dapat melakukan shadowing terhadap alias pada scope luar. Jika alias tidak ditemukan, pencarian dilanjutkan ke scope parent. |

| 2 | Kolom tanpa qualifier hanya diperiksa pada scope terdalam. Jika hanya ada satu sumber tabel, kolom dihubungkan ke sumber tersebut. Jika terdapat lebih dari satu sumber, Resolver memberikan warning karena kolom ambigu. | Mencari sumber tabel sampai ke scope luar atau memilih salah satu tabel secara otomatis ketika terdapat beberapa sumber. | Keputusan ini mengikuti aturan resolusi pada spesifikasi. Memilih tabel secara otomatis berisiko menghasilkan hubungan kolom dan tabel yang salah ketika terdapat beberapa sumber dalam satu scope. |

| 3 | Scope yang dibuat ketika memproses DELETE harus ditutup menggunakan _pop() setelah proses resolusi selesai. | Membiarkan scope tetap aktif setelah statement DELETE selesai. | Setiap statement harus memiliki batas scope yang jelas. Penutupan scope mencegah alias dari statement sebelumnya terbawa dan memengaruhi proses resolusi statement berikutnya. |

| 4 | | | |

| 5 | | | |
