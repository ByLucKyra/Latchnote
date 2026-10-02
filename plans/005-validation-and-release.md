# Plan 005: Validasi MVP dan putuskan kesiapan early access

Status TODO. Prioritas P1. Effort L, bergantung waktu penguji. Risiko LOW untuk dokumentasi, MED untuk sesi berbayar nyata. Kategori tests/docs/direction. Dependensi 001–003; 004 diperlukan untuk waitlist publik. Planned at `37c7332`, 2 Oktober 2026.

## Tujuan dan current state

PRD §12 meminta tiga orang menyelesaikan sesi belajar nyata, catatan layak dibuka kembali, tidak ada crash yang mengakhiri sesi, dan feedback per penguji. Task M2/M3 meminta 30 menit capture dan ID/EN; M7 minimal satu sesi 60 menit. Runbook sekarang belum mempunyai hasil: tiga baris kosong, satu file Smoke Test hanya 58 byte. Empat tes core lulus tidak membuktikan WASAPI/STT/UI/provider bekerja. README frontend masih scaffold; root/desktop onboarding belum lengkap. Rencana ini menghasilkan bukti dan keputusan release, bukan centang berdasarkan dugaan.

## Scope, drift, conventions

Dokumentasi: `prd.md`, `task.md`, `latchnote-app/VALIDATION.md`, root `README.md` baru, desktop README jika dibuat 003, landing README terkait launch, `.agents/rules/latchnote.md` hanya sinkronisasi kontrak. Bukti teranonimisasi dapat ditulis `plans/validation-results.md`. Satu launcher Windows sederhana boleh ditambahkan hanya setelah flow CLI terbukti dan operator meminta distribusi; installer/packager dependency tetap keputusan berikutnya. Bug source yang ditemukan kembali ke plan 001–003, bukan disembunyikan dengan mengganti kriteria. Status di `plans/README.md` diperbarui.

```powershell
git diff --stat 37c7332..HEAD -- prd.md task.md latchnote-app/VALIDATION.md
git status --short
& .\latchnote-app\.venv\Scripts\python.exe -m pytest -q latchnote-app/tests
# Dari landing-page/, dengan Node sesuai package engines:
npm run build
```

Baseline audit hanya full pytest 4 passed; build frontend belum diverifikasi ulang karena Node 20 di environment audit, bukan Node minimum 22.12. Tidak ada lint/typecheck scripts atau CI. Label setiap hasil command dengan tanggal, versi runtime, commit, exit code dan cakupan. Jangan commit/push/deploy tanpa instruksi. Ikuti Markdown existing dan bahasa Indonesia untuk catatan planning.

## Langkah dan verification gates

### 1. Siapkan baseline dan runbook yang bisa diikuti

Tulis setup Python >=3.12, venv/editable install, cwd/config path eksplisit, key lokal, mode transcript-only, title, start/stop/hotkey, lokasi notes/WAV, retry/recovery, dan cara membersihkan rekaman secara manual. Jangan membaca/mencetak nilai key; cek status configured saja. Fresh-machine test harus terpisah dari mesin founder.

**Verify:** full pytest/build command di atas exit 0; tester lain dapat mengikuti command README hingga tray muncul. Jika gagal, catat failure dan kembalikan ke plan terkait, jangan tandai milestone selesai.

### 2. Jalankan smoke 5–10 menit

Gunakan materi teknis campuran ID/EN yang operator berhak putar. Tambahkan minimal dua micro-note, ukur partial/final latency, Stop, buka `.md` dan WAV. Jalankan sesi judul sama lagi untuk collision check. Catat request/token/durasi dan error, bukan credential/raw content pribadi.

**Verify:** command desktop dari `latchnote-app/`: `.\.venv\Scripts\python.exe -m latchnote --title "Validation smoke"`. Output mempunyai final transcript non-empty, structured notes jika AI aktif, dua pin sesuai waktu, final timestamp monotonik, WAV playable, file sesi pertama tidak berubah. Catat langkah pemeriksaan file dan durasi wave dengan `wave` stdlib dalam hasil.

### 3. Jalankan matriks failure/recovery

| Skenario | Bukti wajib |
|---|---|
| Normal Stop/Quit | Semua audio antrean difinalisasi atau ditandai pending; WAV dan notes readable |
| Network disconnect dan reconnect | WAV tetap bertambah, status berubah, live pulih, gap recovery tercatat |
| Invalid STT auth/config | Error actionable tanpa retry tak terbatas; resource terlepas atau recording-local jelas |
| Claude error/timeout | Raw/manual tersimpan, task pending durable, retry tidak menggandakan hasil |
| Restart setelah failure | Session lama ditemukan; rebuild/recovery command menghasilkan output yang benar |
| Controlled forced termination | Artefak yang sudah committed dapat dibaca; tail corruption ditangani dan batas kehilangan didokumentasikan |
| Queue penuh / slow transport | Tidak deadlock; gap ditandai; WAV authoritative tetap ada |
| Export path tidak writable | Error terlihat dan journal/output lama tidak dianggap terhapus/sukses palsu |

**Verify:** jalankan tes regression terkait dari 001–003 dan command recovery yang telah dibuat 003; lampirkan pass/fail per skenario serta file artefak anonim. Forced termination hanya pada sesi uji yang ditentukan, bukan proses aplikasi user lain. Jika scenario belum dijalankan, status NOT RUN.

### 4. Jalankan sesi 30/60 menit dengan tiga orang

Minimal tiga peserta berbeda termasuk founder, masing-masing menyelesaikan sesi nyata; minimal satu >=60 menit. Tes 30 menit capture dan bahasa dapat merupakan bagian sesi tersebut, tetapi tandai dua criterion terpisah. Uji setidaknya dua mesin/device jika tersedia untuk risiko WASAPI; jangan mengklaim multi-machine bila belum ada.

Untuk kualitas, pilih >=50 important words/identifiers dari audio rujukan dengan anotasi manual. Catat jumlah preserved benar / total; target PRD >=90%. Ini metrik sampel istilah, bukan WER keseluruhan atau benchmark universal. Audit structured note terhadap transcript untuk fakta tambahan, technical identifier dan filler; prompt saja bukan bukti non-hallucination. Ukur latency partial <=10 detik dan structuring sekitar 5–10 detik setelah boundary, menggunakan source/reception/request/completion time tanpa isi sensitif. Catat apakah hotkey mengganggu, mengembalikan focus video, serta rendering Obsidian/plain editor.

**Verify:** isi tabel berikut pada `VALIDATION.md`/hasil anonim, tanpa email/key/transcript sensitif.

| ID peserta | Mesin/device | Materi/bahasa | Durasi | Crash | Max partial delay | Structuring latency | Important terms benar/total | Notes layak dibuka kembali? | Hotkey friction | Artefak/recovery | Biaya aktual | Perbaikan berikut |
|---|---|---|---:|---|---:|---|---|---|---|---|---|---|
| A | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| B | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |
| C | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |

Angka pending tidak boleh diganti estimasi. Setiap peserta memberikan minimal satu feedback spesifik; tandai masalah blocker vs non-blocker.

### 5. Sinkronkan dokumen dan buat keputusan release

Perbarui task agar setiap item mempunyai implemented/automated/manual evidence, PRD last-updated/status sesuai keadaan, contoh rules sama dengan writer, serta README root yang menghubungkan app/landing/plans. Tambahkan checklist early access: pipeline, recovery, key handling, biaya, fresh setup, known limitations, waitlist storage dan copy. Jangan mengklaim installer tersedia bila hanya CLI. Jika setup terminal masih menjadi blocker non-teknis, buat keputusan scoped launcher/packaging berikutnya; jangan memperluas scope ke account/subscription.

**Verify:** `git diff --check` exit 0; `rg -n '60-minute|60 menit|90%|10 seconds|10 detik|HH:MM:SS|recovery' prd.md task.md latchnote-app/VALIDATION.md README.md` menunjukkan contract/metrik konsisten. Review dokumen terhadap hasil A/B/C; setiap checkbox manual yang dicentang harus mempunyai evidence reference.

## Pricing dan cost decision sesudah bukti

Catat per sesi durasi audio, token/request AI sukses dan retry, kredit/provider charge aktual, serta mode config. Bedakan credit gratis dari biaya produksi. Jangan menetapkan harga berdasarkan estimasi percakapan lama atau jumlah panggilan saja. Gabungkan biaya per jam terukur dengan distribusi jam belajar dan survei waitlist; pilih BYO-key/kuota sebagai keputusan produk berikutnya. Budget sesi/structuring optional dipertimbangkan setelah biaya terukur; tidak membangun billing sekarang.

## Done criteria dan keputusan akhir

- [ ] Regression suite dan build runtime sesuai lulus, hasil dicatat.
- [ ] Smoke pendek dan collision check lulus.
- [ ] Failure matrix selesai dengan bukti; pending/gap tidak dilabel complete.
- [ ] Capture 30 menit dan mixed ID/EN 30 menit lulus.
- [ ] Tiga peserta selesai; satu sesi >=60 menit; tidak ada session-ending crash; setiap peserta memberikan feedback dan menilai catatan layak dibuka kembali.
- [ ] Accuracy sampel istilah >=90%, latency memenuhi target atau penyimpangan tercatat sebagai blocker/keputusan revisi requirement eksplisit.
- [ ] Plain editor/Obsidian dan setup mesin kedua terverifikasi atau batas distribusi dicatat.
- [ ] PRD/task/rules/runbook konsisten; release verdict GO/NO-GO ditulis dengan blocker serta next owner/action.

001–004 dapat DONE pada implementation gates masing-masing, tetapi 005 tidak DONE sampai sesi nyata selesai. NO-GO dengan bug belum diperbaiki bukan validasi MVP sukses; catat task validasi yang selesai dan pekerjaan yang masih wajib. Jangan menghapus requirement supaya status terlihat hijau.

## STOP conditions dan maintenance

Hentikan sesi/pengujian berbayar bila budget operator tercapai, terjadi overwrite/data loss, atau bukti crash/recovery tidak aman. Tetap simpan artefak dan laporkan. Tidak ada penguji/key/service account bukan alasan mengarang hasil; tandai BLOCKED/NOT RUN hanya pada langkah yang membutuhkan pihak tersebut. Scope riset pasar/ilmiah, payment dan release publik tetap terpisah. Update baseline SHA setelah batch implementasi agar rencana berikutnya tidak bertumpu pada source lama.
