# Plan 003: Recovery usable, status jujur, dan setup desktop jelas

Status IN PROGRESS (local recovery/UX automated; interim captions and hardware validation remain). Plan 001's Deepgram reconnect scope is rejected; this plan is reconciled to local Whisper. Prioritas P1 historis. Planned at `37c7332`, 2 Oktober 2026.

Whisper runs locally, so network disconnect/reconnect and provider connection epochs do not apply. This implementation keeps the WAV authoritative, journals queue-overflow ranges, offers separate saved-WAV transcription, reloads one explicit settings file before each session, and exposes status/recovery actions in the tray. The preview shows the latest final segment; stable interim captions are still unavailable from this windowed trial and are intentionally not claimed.

## Tujuan

Ketika jaringan putus, perekaman lokal tetap berjalan dan pengguna mengetahui transkripsi terhenti. Reconnect harus memulihkan live STT, sedangkan audio gap harus mempunyai jalur pemrosesan ulang yang tidak menggandakan transcript/notes. Partial transcript tampil sesuai PRD §9.2. Setup harus memberi tahu mode transcript-only, konfigurasi tidak valid, dan cara membuka hasil.

## Scope, drift, conventions

Files: `latchnote-app/src/latchnote/{__main__,stt_client,session,config,hotkey_listener,structurer}.py`, recovery helper dari 002 jika ada, `latchnote-app/.env.example`, tes terkait, README desktop baru bila perlu, serta status di `plans/README.md`. Jangan mengubah journal schema tanpa migration yang diuji. Tidak membangun main dashboard, account, pricing, atau mengganti toolkit.

```powershell
git diff --stat 37c7332..HEAD -- latchnote-app/src/latchnote latchnote-app/tests latchnote-app/.env.example
git status --short
& .\latchnote-app\.venv\Scripts\python.exe -m pytest -q latchnote-app/tests
```

Bandingkan live code dengan hasil 001/002 dahulu; plan ini merencanakan perubahan sesudah keduanya. Python 3.12+, editable `.[dev]`; tests memakai assert sederhana. Reuse `MicroNoteController.show_requested = Signal()` sebagai pola mengirim event dari worker ke Qt GUI thread. Existing pystray dipertahankan. Commit/push hanya jika diminta.

## Current state dan bukti

Bagian ini adalah bukti historical pada baseline Deepgram `37c7332`, bukan keadaan kode saat ini. Untuk eksekusi, gunakan bagian **Adaptasi untuk implementasi lokal**: reconnect/auth retry tidak berlaku; current implementation memakai worker Whisper lokal dan task recovery Plan 002.

`stt_client.py:103` mempunyai `retry()` tetapi tidak dipanggil controller. `_handle_error()` hanya mengisi `last_error`/logging. `session.py:121` mempunyai `retry_failed()` tetapi tidak ada caller aplikasi. Tray `_refresh()` hanya dipanggil setelah action Start/Stop. `_handle_message()` mengabaikan interim. `config.py` membaca `.env` relatif cwd dan default model `claude-sonnet-5` belum diverifikasi tersedia. `main()` memuat settings sekali; pesan yang meminta mengisi key lalu Start lagi tidak reload. Hotkey membuka popup pada idle tetapi `add_micro_note()` tidak menulis ketika orchestrator tidak ada.

## Perilaku target

### Adaptasi untuk implementasi lokal

- Config eksplisit via `--config` direload sebelum sesi; process environment menang atas isi file dan dotenv tidak mengubah process environment.
- Tray menyediakan status runtime, preview final terbaru, Open Notes/Recovery, Retry Pending AI, serta mode Transcript only ketika provider dinonaktifkan/konfigurasinya belum lengkap.
- Queue overflow menyimpan range sumber yang diketahui ke journal. WAV tetap sumber recovery; `--transcribe-file` membuat sesi terpisah dan tidak merge transcript secara otomatis.
- Idle hotkey diabaikan. Signal Qt menyampaikan teks dari worker ke jendela preview tanpa membuka jendela otomatis.
- Reconnect STT dan interim captions tidak diimplementasikan: transport STT tidak memakai jaringan dan Whisper trial hanya menghasilkan final per window.

| Kondisi | Perilaku |
|---|---|
| Idle | Start aktif; hotkey tidak membuka input yang akan dibuang |
| Recording | WAV berjalan; final ke journal/Markdown; preview menunjukkan final terbaru |
| Local STT gagal/tertinggal | WAV tetap berjalan; tray menyebut masalah transkripsi; gap yang diketahui ditandai durable |
| Local decoder gagal | Status actionable error dengan path WAV; pengguna masih bisa Stop dan memproses WAV terpisah |
| STT reconnect | Tidak berlaku pada Whisper lokal; pemrosesan ulang WAV menghasilkan sesi terpisah tanpa merge otomatis |
| Claude gagal | Transcript/manual tetap tersedia; structured task pending dapat retry, tidak mengulang task sukses |
| Anthropic kosong | Mode transcript-only jelas; jangan menjadwalkan request AI gagal per chunk |
| Stop/restart | Artefak pending dapat ditemukan dan diproses/rebuild, tanpa menghapus output lama |

## Langkah

Implementasi cloud di bawah adalah handoff historical. Untuk kode saat ini, ikuti daftar adaptasi lokal di atas; khususnya jangan menambah reconnect/auth retry Deepgram.

1. **Validasi konfigurasi dan session actions.** Gunakan satu lokasi config yang eksplisit/didokumentasikan, atau opsi `--config`; jangan scan home/repo mencari secret. Reload sebelum sesi baru tanpa menimpa environment asli dengan nilai stale dari dotenv. Tunjukkan nama setting yang kurang, bukan nilainya. Verifikasi model/language terhadap SDK/provider saat smoke; jangan mengklaim default valid berdasarkan nama. Gate hotkey berdasarkan sesi aktif; tawarkan Open Notes dan Open Recovery melalui fasilitas OS yang ada. Verifikasi: full pytest plus config tests environment precedence, reload file berubah, cwd berbeda melalui path eksplisit, key kosong, AI kosong; idle hotkey tidak membuang input.
2. **Error event dan retry bounded.** Kirim error/state/transcript melalui signal/callback ke controller, lalu marshal ke GUI thread untuk UI. Gunakan satu retry owner, contoh 3 percobaan dengan backoff 1/2/4 detik yang dapat dibatalkan Stop, bukan nested retry berlipat. Pisahkan auth/config error dari gangguan transient sesuai exception SDK sebenarnya. Update tray pada event runtime, bukan menunggu user klik. Verifikasi: offline controller tests dengan small fake adapter/Event, failure → retrying → recording, exhaustion → actionable error, Stop saat backoff tanpa reconnect setelah sesi berakhir.
3. **Gap recovery explicit.** Simpan range audio yang tidak berhasil diproses, connection epoch, serta progress ke artefak 002. Reconnect live memakai offset sample/frame; jangan replay gap sambil menggeser waktu live. Jalur paling sederhana adalah CLI recovery untuk WAV/pending session setelah Stop, dengan explicit session ID dan progress. PCM replay boleh memakai adapter yang sama, harus sesuai rate/channels, di-throttle bila transport membutuhkannya. Gap replay tidak boleh menggandakan final event yang sudah committed; jika mapping range provider ambigu, simpan hasil recovery terpisah dengan label dan jangan merge otomatis. Verifikasi: offline restart/replay check melewati gap range, retry dua kali idempotent pada output; provider smoke mendokumentasikan hasil recovered vs live dan biaya tambahan.
4. **Partial transcript minimal.** Tambahkan tampilan PySide6 kecil yang bisa dibuka dari tray, menampilkan current interim + final terbaru + state. Reuse toolkit; bukan rich overlay. UI tidak menulis interim ke journal output dan tidak mencuri focus video pada tiap event. Sinkronkan timestamp dari audio source seperti 001. Verifikasi: tes handler interim/final dan UI-thread dispatch, lalu manual audio menunjukkan partial <=10 detik; ukur nilai aktual, jangan mencentang hanya karena parameter interim enabled.
5. **Integrasikan pending AI retry dan error UX.** Reuse worker/task dari 002, satu aksi Retry Pending; jangan otomatis mengulang successful task. Beri timeout provider yang jelas dan guard transcript-only. Tulis setup/run/recovery command yang benar di README desktop. Verifikasi: full pytest; manual transcript-only menghasilkan transcript/manual tanpa permintaan Claude, reconnect/gap dan AI failure tetap menyisakan artefak readable.

Perintah verifikasi semua langkah: `& .\latchnote-app\.venv\Scripts\python.exe -m pytest -q latchnote-app/tests`. Uji manual dari `latchnote-app/`: `.\.venv\Scripts\python.exe -m latchnote --title "Recovery smoke"`. Sintaks recovery/config baru harus dipilih implementer, dicatat pada `--help`/README, dan diuji lewat command yang sama; jangan menulis dokumentasi flag yang belum dibuat.

## Done criteria

- [x] Config/state/retry/gap checks lulus offline tanpa jaringan/biaya (28 tes); interim behavior tetap belum tersedia pada Whisper windowed.
- [ ] Disconnect/reconnect provider smoke. Tidak berlaku untuk transport Whisper lokal; decoder failure dan WAV retention diuji offline.
- [x] Restart dapat menemukan gap/pending dan menjalankan recovery melalui command yang didokumentasikan; replay membuat sesi terpisah.
- [x] Source timestamps dipertahankan untuk transkrip live; gap ditandai incomplete, bukan complete.
- [ ] Partial muncul <=10 detik pada smoke dan tidak dipersist sebagai final.
- [ ] Hotkey/tray/audio validation manual; automated idle gating, mode status, preview wiring, and retry pass. Enter/Esc popup behavior belum diuji ulang.
- [x] `git diff --check` exit 0; status plan mencatat bukti automated dan manual terpisah.

## STOP conditions dan maintenance

Stop jika recovery membutuhkan guessing alignment yang berisiko menimpa transcript lama, toolkit callback menyentuh GUI dari worker, atau provider multilingual/model tidak mendukung konfigurasi yang diasumsikan. Laporkan incompatibility; jangan mengganti provider atau mengeklaim ID/EN berhasil tanpa audio uji. Belum perlu dashboard atau backend recovery. Bedakan retained, pending, recovered, dan complete; keberadaan WAV saja tidak berarti recovery sukses.
