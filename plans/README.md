# Rencana Pengembangan Latchnote

Tanggal: **2 Oktober 2026 (Asia/Jakarta)**. Baseline: commit **`37c7332`**. Status: **planning, belum diimplementasikan**.

Dokumen ini merupakan rencana lanjutan berdasarkan audit kode dan dokumen lokal, bukan bukti bahwa perbaikan telah selesai. Dibuat menggunakan skill `improve`. Baca rencana terkait sepenuhnya sebelum implementasi.

> **Perubahan arah, 2 Oktober 2026:** user memilih raw transcription dengan Whisper lokal untuk laptop entry-level RAM 8 GB. Percobaan sudah memakai faster-whisper `base` CPU INT8; penyusunan catatan opsional melalui endpoint OpenAI-compatible, dengan aturan faktual standar + file format custom. Lihat `latchnote-app/README.md` untuk konfigurasi, hasil smoke, dan batasnya. Plan 001 khusus Deepgram tidak lagi menjadi jalur implementasi; Plan 003 perlu direkonsiliasi untuk local backlog/recovery, bukan reconnect STT cloud. Jangan mengimplementasikan kembali Deepgram dari baseline lama. Storage/durability 002, waitlist 004, dan real-user validation 005 masih relevan. Core smoke bukan bukti sesi 60 menit atau `.exe` siap rilis.

## Tujuan dan hubungan dengan dokumen lama

Tujuan tetap mengikuti `prd.md`: pendamping belajar Windows, audio sistem ke transkrip dan catatan Markdown lokal, dengan micro-note melalui hotkey. Fokus sekarang adalah membuktikan pipeline bekerja, melindungi hasil belajar, dan mengumpulkan feedback sebelum monetisasi.

- `prd.md`: acuan kebutuhan produk dan batas MVP. Header menyebut 24 Juli 2026, tetapi perubahan terakhir di Git tercatat 30 Agustus 2026.
- `task.md`: catatan milestone implementasi lama; 31/39 checkbox dicentang. Centang bukan bukti acceptance criteria terpenuhi.
- `latchnote-app/VALIDATION.md`: runbook manual; tiga baris feedback masih kosong.
- `plans/README.md`: urutan kerja, keputusan perencanaan terbaru, dan status rencana lanjutan.
- `plans/001-*.md` sampai `005-*.md`: handoff implementasi dan validasi yang bisa dikerjakan tanpa konteks percakapan.

Dokumen lama dipertahankan sebagai baseline. Saat implementasi terkait selesai, sinkronkan PRD, task, rules, dan runbook; jangan mencentang tes manual berdasarkan tes unit. Jika implementer menemukan perubahan kebutuhan produk, catat keputusan dan alasannya, jangan diam-diam mengubah scope.

## Baseline yang benar-benar diperiksa

| Area | Bukti | Kesimpulan |
|---|---|---|
| Desktop | Python, PyAudioWPatch, Deepgram, Anthropic, PySide6, keyboard, pystray | Modul utama tersedia, integrasi belum dapat dinyatakan selesai |
| Tes | `latchnote-app/.venv/Scripts/python.exe -m pytest -q latchnote-app/tests` | 4 tes lulus, terakhir 0,07 detik; hanya core logic |
| SDK | Probe tanpa jaringan pada Deepgram SDK 7.8.0 | `connect(model='nova-3')` menghasilkan `_GeneratorContextManager`; tidak punya `.on()`/`.start_listening()` |
| Sesi nyata | `latchnote-app/notes/2026-08-29_Smoke Test.md`, 58 byte | Hanya header; bukan bukti pipeline end-to-end |
| Frontend | Astro + React islands + Tailwind + Motion; `/` dan `/id/` | Source tersedia; build dan interaksi browser belum diverifikasi ulang dalam audit ini |
| Runtime frontend | `node --version`: v20.20.2; package mengharuskan >=22.12.0 | Environment audit belum memenuhi minimum package; riwayat build lama bukan baseline baru |
| Git | Working tree bersih saat audit dimulai, HEAD `37c7332` | Planning berangkat dari snapshot tersebut |
| Tooling | Tidak ditemukan CI, root README, skrip lint/typecheck frontend | Verifikasi utama sekarang pytest desktop dan build frontend pada runtime yang sesuai |

Nilai `.env` tidak dibaca atau disalin. Keberadaan credential valid, endpoint waitlist aktif, model Claude tersedia, deployment publik, dan akurasi bahasa belum dikonfirmasi.

## Improvement berdasarkan bukti

Effort: S = beberapa jam; M = sekitar 1–2 hari; L = beberapa hari termasuk uji integrasi. Angka ini estimasi relatif, bukan deadline. Confidence HIGH berarti perilaku terlihat di kode/probe; MED berarti perlu reproduksi runtime.

| ID | Improvement / dampak sekarang | Bukti | Prioritas | Effort | Risiko fix | Confidence | Plan |
|---|---|---|---|---|---|---|---|
| F01 | Perbaiki lifecycle SDK; `.on()` pada context manager dapat gagal sebelum STT berjalan | `stt_client.py:52–65`; SDK lokal `listen/v1/client.py:75–76` | P0 | M | MED | HIGH | 001 |
| F02 | Pindahkan listener blocking dari jalur Start; sender saat ini dibuat sesudah listener | `stt_client.py:65–73`; SDK lokal `socket_client.py:150` | P0 | M | MED | HIGH | 001 |
| F03 | Stop capture sebelum drain STT; jangan kehilangan antrean/final response | `__main__.py:94–99`, `stt_client.py:86–116` | P0 | M | HIGH | HIGH | 001 |
| F04 | Hilangkan kemungkinan deadlock: Stop menahan lock yang dibutuhkan callback audio | `audio_capture.py:87–106` | P0 | S | MED | MED | 001 |
| F05 | Lindungi file dari overwrite pada dua sesi dengan tanggal/judul sama | `writer.py:25–26`; WAV slug `__main__.py:65` hanya sampai detik | P0 | S | LOW | HIGH | 002 |
| F06 | Simpan event/task recovery dan hasil akhir kronologis; append hasil AI sekarang mengikuti completion order | `writer.py:41–47`, `session.py:98–152` | P1 | L | HIGH | HIGH | 002 |
| F07 | Ganti thread per chunk dengan satu worker; timeout sekarang per thread dan daftar thread dibuang saat join | `session.py:128–139` | P1 | M | MED | HIGH | 002 |
| F08 | Sambungkan retry, gap recovery, dan error ke controller/tray; fungsi retry saat ini tidak dipanggil aplikasi | `stt_client.py:103`, `session.py:121`, `__main__.py:47–114` | P1 | L | HIGH | HIGH | 003 |
| F09 | Gunakan waktu audio sebagai timestamp; callback sekarang hanya mengirim teks dan memakai waktu respons diterima | `stt_client.py:20–23`, `__main__.py:75`, `session.py:98–103` | P1 | M | MED | HIGH | 001/003 |
| F10 | Tampilkan interim dan konfigurasi yang jelas; PRD meminta partial <=10 detik, handler membuang non-final | `stt_client.py:120–122`, `prd.md` §9.2; `config.py:21–27` | P1 | M | MED | HIGH | 003 |
| F11 | Gating hotkey pada sesi aktif; popup sekarang bisa terbuka idle, tetapi submit tidak disimpan | `__main__.py:107–110,188–191` | P1 | S | LOW | HIGH | 003 |
| F12 | Samakan format output, recovery, dan status milestone antar dokumen | `.agents/rules/latchnote.md` memakai time range; PRD/task memakai `[HH:MM:SS]` | P1 | S | LOW | HIGH | 002/005 |
| F13 | Siapkan waitlist yang benar-benar menyimpan data dan failure/timeout UX | `WaitlistForm.tsx:24,61–89`; tidak ada handler dalam repo | P1 | M | MED | HIGH | 004 |
| F14 | Selaraskan klaim marketing dengan bukti; demo bukan output nyata, FAQ menjanjikan error tray/end-to-end | `copy.ts:27,37,149,161,194,204,328`; `Landing.astro:104–107` | P1 | S | LOW | HIGH | 004 |
| F15 | Perbaiki Replay reduced-motion; reset ke 0 sementara effect berhenti menjalankan timer | `LiveSessionDemo.tsx:70–75,101–105` | P2 | S | LOW | HIGH | 004 |
| F16 | Lengkapi onboarding, uji 30/60 menit, kualitas bahasa, biaya aktual, dan feedback tiga pengguna | `VALIDATION.md`; `task.md` M2/M3/M7; README frontend masih starter | P1 | L | LOW | HIGH | 005 |

Path Python di tabel relatif ke `latchnote-app/src/latchnote/`; path frontend relatif ke `landing-page/src/components/`, kecuali `copy.ts` di `src/content/`. Line number mengacu baseline dan akan berubah setelah implementasi.

## Urutan eksekusi dan status

| Plan | Hasil yang dituju | Prioritas | Estimasi | Dependensi | Status |
|---|---|---|---|---|---|
| [001](001-streaming-lifecycle.md) | STT Deepgram start/finalize/stop | P0 | M | Tidak ada | REJECTED: diganti trial Whisper lokal; lihat README desktop |
| [002](002-storage-and-structuring.md) | Sesi unik, recovery durable, Markdown kronologis, AI worker terkendali | P0/P1 | L | Trial Whisper lokal | DONE: 23 tes automated-verified; provider nyata dan sesi hardware belum diuji |
| [003](003-recovery-and-desktop-ux.md) | Error/backlog terlihat, recovery usable, transcript preview dan setup | P1 | L | Trial Whisper lokal, 002 | IN PROGRESS: config/recovery/tray automated; interim captions dan hardware smoke belum |
| [004](004-waitlist-readiness.md) | Landing page jujur, accessible, waitlist terverifikasi | P1/P2 | M | Independen untuk copy/UI; klaim fitur menunggu 003 | TODO |
| [005](005-validation-and-release.md) | Bukti tiga pengguna dan release checklist; keputusan pricing berbasis biaya | P1 | L | 001–003; 004 untuk distribusi waitlist | TODO |

Status yang diperbolehkan: TODO, IN PROGRESS, DONE, BLOCKED (sertakan sebab), REJECTED (sertakan alasan). Setelah perubahan arah, lanjutkan benchmark Whisper pada hardware target sebelum durability 002; jangan menjalankan plan Deepgram yang sudah ditolak. 004 boleh paralel selama copy tidak menjanjikan fitur yang belum lolos validasi.

## Keputusan produk untuk rencana ini

1. Windows dan local Markdown tetap scope utama; stack desktop dipertahankan.
2. Format canonical mengikuti PRD §9.5: header event `[HH:MM:SS]`, timestamp AI = awal chunk, micro-note = waktu submit; final export diurutkan stabil. Live export boleh sementara mengikuti event kedatangan, tetapi harus diberi status sementara dan dapat dibangun ulang.
3. WAV, event transcript/manual, dan task AI pending dipertahankan untuk recovery. Tidak ada penghapusan otomatis sampai pengguna menyetujui kebijakan retensi.
4. Recovery bukan sekadar keberadaan WAV: harus ada langkah yang bisa menghasilkan kembali transcript/notes serta menandai gap dan menghindari duplikasi.
5. STT memakai Whisper lokal tanpa key. AI cleanup opsional menggunakan endpoint chat-completions OpenAI-compatible; tanpa konfigurasi atau dengan `--raw-only`, tidak ada panggilan AI.
6. Harga belum ditentukan. Landing page tetap waitlist + survei model harga; tidak ada pembayaran, akun, lisensi, atau subscription backend dalam rencana ini.
7. Bedakan status pekerjaan: implemented, automated-verified, manual-verified. Milestone selesai hanya setelah acceptance criteria dan bukti terpenuhi.

## Gate pengembangan

| Gate | Bukti wajib sebelum lanjut |
|---|---|
| G0 — Pipeline | Start/Stop pendek tidak macet, real audio menghasilkan final transcript; SDK sesuai versi terpasang |
| G1 — Data | Dua sesi sama tidak overwrite; final Markdown sorted; failure/restart bisa rebuild dari artefak lokal |
| G2 — Recovery/UX | Disconnect terlihat di tray, reconnect/gap recovery usable, interim terlihat, hotkey tidak membuang catatan idle |
| G3 — Dogfooding | Capture 30 menit + campuran ID/EN 30 menit; tiga pengguna, satu sesi >=60 menit, feedback terisi |
| G4 — Distribusi | Waitlist masuk storage, FAQ sesuai bukti, fresh-machine setup berhasil, tidak ada credential dalam paket/log |

## Arah sesudah validasi, bukan komitmen build

- **Onboarding tanpa terminal:** PRD M6 menarget pengguna non-teknis, tetapi entry saat ini CLI. Mulai launcher dokumentasi; pilih packaging hanya sesudah mesin kedua dapat menjalankan pipeline. Trade-off: installer mempermudah distribusi tetapi menambah pekerjaan build/update.
- **Recovery rekaman sebagai pengalaman pengguna:** WAV sudah tersedia, sehingga aksi memproses ulang lebih relevan daripada dashboard atau cloud sync. Prioritasnya data terselamatkan; bukan file browser kompleks.
- **Pricing berdasarkan usage:** survei waitlist tersedia dan chunk size diketahui. Catat menit audio, request/token AI, retry, serta biaya provider aktual dalam dogfooding, lalu putuskan BYO-key atau kuota. Jangan menetapkan unlimited atau angka margin dari asumsi.

## Dipertimbangkan dan ditolak/ditunda

- Rewrite desktop ke Electron/Tauri/Next.js: tidak menyelesaikan masalah lifecycle dan kehilangan data.
- Backend custom untuk waitlist: endpoint hosted yang menerima JSON cukup; bangun backend hanya jika kebutuhan nyata tidak terpenuhi.
- Cloud sync, akun, OCR, macOS/mobile, flashcard/quiz: di luar PRD MVP; belum ada feedback pengguna yang membenarkan perluasan.
- Framework testing/mocking besar dan coverage target persentase: tambah regression check kecil pada jalur data/lifecycle, uji hardware/API nyata terpisah.
- `dangerouslySetInnerHTML` pada InlineIcon sebagai temuan XSS: ditolak; data berasal dari paket ikon statis saat build, bukan input user. Tinjau ulang hanya jika sumber berubah.
- Bug typing bilingual melalui `as unknown`: ditolak pada snapshot ini; dictionary Indonesia sudah menggunakan `const id: Copy` tanpa cast tersebut.
- Mengganti Motion atau semua dependensi frontend: ditunda sampai pengukuran browser memperlihatkan masalah; bukan blocker pipeline.

## Batas audit

Audit mencakup source desktop/frontend, konfigurasi, tes, Git, PRD/task/runbook, aturan lokal, dan lifecycle SDK yang terpasang. Tidak mencakup sesi audio nyata, koneksi provider berbayar, model/language support di layanan aktif, browser visual/accessibility testing, deployment, audit vulnerability paket online, instalasi pada mesin kedua, atau riset ulang klaim ilmiah/kompetitor. Temuan lokal tidak membuktikan angka riset PRD atau klaim provider masih berlaku.

## Cara memakai planning

Implementer membaca satu plan, memeriksa drift terhadap `37c7332` dan perubahan worktree, menjalankan baseline, lalu mengikuti langkah dan verifikasinya. Hindari dependency runtime baru; gunakan stdlib dan paket yang ada. Jangan commit/push/deploy atau mengirim email tanpa instruksi. Setelah hasil lolos, update status di tabel ini dan catat bukti; gunakan `005` untuk menyelaraskan dokumen lama.
