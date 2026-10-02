# Plan 001: Start dan Stop pipeline audio/STT dengan benar

Status: TODO. Prioritas P0. Effort M. Risiko MED/HIGH pada shutdown. Kategori bug/integrasi. Dependensi: tidak ada. Planned at `37c7332`, 2 Oktober 2026.

## Tujuan dan konteks

Latchnote adalah aplikasi Windows Python yang merekam system audio ke WAV, mengirim PCM ke Deepgram, lalu menulis final transcript ke Markdown. Pipeline ini belum terbukti berjalan. Audit tanpa jaringan pada Deepgram SDK lokal 7.8.0 menunjukkan `connect()` menghasilkan context manager, bukan socket; synchronous `start_listening()` menjalankan receive loop blocking. Kode saat ini memanggil `.on()` pada manager dan memulai sender setelah listener selesai. Selain itu Stop memutus sender sebelum queue dikuras, controller menutup STT sebelum menghentikan producer audio, dan audio Stop menahan lock callback.

## Scope dan drift

Ubah hanya `latchnote-app/src/latchnote/{stt_client,audio_capture,__main__,session}.py`, tes terkait di `latchnote-app/tests/`, serta baris status plan ini di `plans/README.md`. `session.py` hanya untuk meneruskan source timestamp. Tidak mengubah writer, frontend, dependency stack, pricing, atau melakukan panggilan berbayar tanpa operator yang menjalankan sesi.

Dari root:

```powershell
git diff --stat 37c7332..HEAD -- latchnote-app/src/latchnote latchnote-app/tests
git status --short
& .\latchnote-app\.venv\Scripts\python.exe -m pytest -q latchnote-app/tests
```

Baseline yang diperiksa: 4 passed. Bandingkan perubahan dengan excerpt; jika berbeda, rekonsiliasi sebelum edit. Jangan menimpa worktree user. Commit opsional hanya jika diminta; gaya repo `Fix ...`/`Add ...`; jangan push.

## Current state

`stt_client.py:52–73`:

```python
self._connection = client.listen.v1.connect(...)
self._connection.on(EventType.MESSAGE, self._handle_message)
self._connection.start_listening()
# sender thread starts afterward
```

`stt_client.py:90,109`: `_stopped.set()` pada Stop, loop sender `while not self._stopped.is_set()`. `__main__.py:94–99`: STT Stop sebelum capture Stop. `audio_capture.py:89–91`: `with self._lock` mengelilingi `stop_stream()`, padahal `_record_chunk()` juga mengambil lock. `TranscriptSegment` saat ini hanya mempunyai `text`.

Conventions: typed synchronous Python, public one-line docstrings, logging stdlib, specific error types `SttError`/`AudioCaptureError`. Pattern tes assert sederhana ada di `tests/test_session.py`; hindari framework baru. Untuk lifecycle gunakan local fake transport minimal/std­lib jika dibutuhkan, bukan simulasi akurasi provider/hardware.

## Langkah

1. **Periksa SDK yang terpasang dan buat check lifecycle offline.** Baca `latchnote-app/.venv/Lib/site-packages/deepgram/listen/v1/{client,socket_client}.py`. Buat regression test yang menangkap contract manager masuk/keluar, listener tidak memblokir Start, dan urutan drain/finalize/close. Gunakan `threading.Event` untuk sinkronisasi, bukan sleep arbitrer. Verifikasi: perintah pytest di atas harus menampilkan kegagalan baru yang sesuai sebelum fix, bukan error karena test setup.
2. **Miliki lifecycle manager/socket secara eksplisit.** Enter context di Start dan simpan owner hingga Stop; jalankan receive loop di worker tersendiri dan sender di worker lain. Pastikan startup error menutup resource yang sudah dibuka. Periksa exception yang benar-benar dikeluarkan SDK/websocket dan bungkus menjadi `SttError`, bukan menangkap semua exception tanpa membedakan bug. Verifikasi: tes start/context/listener baru lulus dan Start kembali tanpa menunggu koneksi ditutup.
3. **Perbaiki producer-stop → queue-drain → finalize → final-response → close.** Hentikan callback capture tanpa memegang lock selama `stop_stream()`. Setelah producer berhenti, sender harus menguras PCM yang diterima sebelum sentinel; jangan membuat sentinel hilang ketika queue penuh. Tunggu final response dengan batas waktu eksplisit sebelum close/context exit. Stop berulang aman; cleanup capture tetap berlangsung ketika finalize gagal. Timeout harus melaporkan bahwa STT belum lengkap dan mempertahankan WAV, bukan menandai sukses. Verifikasi: tes FIFO, queue penuh, Stop dua kali, gagal startup/finalize, dan callback menunggu lock lulus; tidak ada thread hidup yang masih memakai socket yang sudah ditutup.
4. **Pertahankan source timestamp.** Tambahkan start/duration audio dari event final ke `TranscriptSegment`, teruskan ke orchestrator. Jangan menganggap waktu response tiba sebagai waktu ucapan. Reconnect offset ditangani 003; untuk sesi pertama offset 0. Verifikasi: event final yang sengaja diterima terlambat tetap mendapatkan timestamp audio asal; interim belum ditulis ke Markdown.

Jalankan full pytest setelah setiap langkah yang mengubah kode; semua tes lama harus tetap lulus. Bila belum ada venv, setup dari `latchnote-app/` dengan Python 3.12+: `python -m venv .venv` lalu `.\.venv\Scripts\python.exe -m pip install -e '.[dev]'`; instalasi ini dilakukan implementer, bukan bagian audit planning.

## Uji nyata dan done criteria

Dari `latchnote-app/`: `.\.venv\Scripts\python.exe -m latchnote --title "Lifecycle smoke"`. Operator mengisi key secara lokal, putar audio 2–5 menit, Start, Stop, Quit, lalu ulangi. Ini bukan tes yang sudah dijalankan auditor.

- [ ] Full pytest exit 0, termasuk regression offline start/stop/error/timestamp.
- [ ] Tidak ada `.on()` yang dipanggil pada context manager dan receive loop tidak mengunci Start.
- [ ] Trace offline membuktikan urutan capture stop, drain, finalize, final event, close.
- [ ] Uji nyata menghasilkan non-empty transcript dan WAV playable; Stop/Quit tidak macet.
- [ ] Error timeout/connection dilaporkan; WAV tidak dihapus.
- [ ] `git diff --check` exit 0; tidak ada perubahan di luar scope; status plan diperbarui dengan bukti automated/manual terpisah.

## STOP conditions dan maintenance

Hentikan dan laporkan jika versi SDK bukan contract yang dibaca, receive loop tidak dapat dibatalkan dengan API yang tersedia, hardware Stop masih deadlock, atau fix memerlukan dependency/toolkit baru. Jangan downgrade SDK secara tebak-tebakan. Dukungan Nova multilingual dan model Claude belum diverifikasi; cek dokumentasi resmi/provider saat implementasi bila konfigurasi ditolak. Perubahan SDK berikutnya harus menjalankan kembali lifecycle check; mempertahankan recovery WAV tetap wajib walau drain gagal.
