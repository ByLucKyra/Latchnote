# Plan 002: Simpan sesi aman, durable, dan kronologis

Status TODO. Prioritas P0/P1. Effort L. Risiko HIGH karena jalur penyimpanan. Kategori bug/reliability. Dependensi 001. Planned at `37c7332`, 2 Oktober 2026.

## Tujuan

Dua sesi dengan judul sama tidak boleh menghapus hasil lama. Transkrip/manual note harus tersimpan saat diterima; hasil AI yang terlambat harus dapat ditempatkan pada timestamp sumber dan diproses ulang setelah restart. Gunakan artefak lokal stdlib, satu worker AI, dan export Markdown; tidak perlu database atau queue service.

## Scope dan baseline

Files: `latchnote-app/src/latchnote/{writer,session,structurer,__main__,audio_capture}.py`, tests writer/session dan satu recovery test bila perlu; `.agents/rules/latchnote.md`, `prd.md`, `task.md` hanya untuk menyamakan kontrak output; status di `plans/README.md`. Metadata recovery dapat ditempatkan dalam module existing; jika satu helper lokal sangat diperlukan, batasi pada satu file `recovery.py` dan jelaskan tanggung jawabnya. Tidak mengubah frontend, STT transport, accounts, auto-delete, atau provider stack.

```powershell
git diff --stat 37c7332..HEAD -- latchnote-app/src/latchnote latchnote-app/tests prd.md task.md .agents/rules/latchnote.md
git status --short
& .\latchnote-app\.venv\Scripts\python.exe -m pytest -q latchnote-app/tests
```

001 akan mengubah controller; baca versi setelah 001 sebelum edit. Baseline awal 4 passed; jumlah sesudah 001 bertambah. Match typed Python, logging, `StructuringError`, dan assert tests `tests/test_writer.py`/`test_session.py`. Jangan commit/push kecuali diminta.

## Current state

`writer.py:25–26`:

```python
filename = f"{session.started_at:%Y-%m-%d}_{_safe_filename(session.title)}.md"
self.path.write_text(...)
```

`session.py:135–139` membuat daemon `Thread` per chunk; `wait_for_structuring()` menghapus daftar thread lalu join dengan timeout per thread. `_failed_chunks` hanya list dalam RAM. Hasil AI ditulis dengan `chunk.start_seconds` tetapi writer hanya append: completion order tidak sama dengan chronological order. Rules meminta time range, tetapi PRD §9.5 dan task meminta `[HH:MM:SS]`.

## Kontrak yang harus dihasilkan

- Session ID stabil dan unik untuk WAV, journal, task recovery, serta Markdown. Pertahankan prefix tanggal/judul; pakai exclusive create dan suffix collision, jangan sekadar `exists()` lalu overwrite. Nama Windows invalid/reserved dan judul kosong harus ditangani.
- Journal append-only JSONL menyimpan final transcript/manual/structured events beserta session ID, event ID, source timestamp, sequence, type, text. Tulis/flush event sebelum hasil dianggap tersimpan. Tidak menyimpan API keys. Pembaca boleh memulihkan baris terakhir yang terpotong dengan warning, tidak diam-diam melewati corruption di tengah.
- Task AI pending mempunyai chunk ID stabil dan source text/range; persist sebelum request. Gunakan file JSON atomic atau journal task events, pilih satu, jangan dua store yang harus disinkronkan. Success dicatat durable sebelum task dianggap selesai. Crash di antara request dan pencatatan bisa menyebabkan request ulang berbayar; jelaskan ceiling ini, tetapi jangan menggandakan structured output.
- `.md` live dapat append agar hasil segera terlihat. Pada Stop dan explicit rebuild, sort by `(source_timestamp, sequence)` lalu render ke temporary file di direktori sama dan `os.replace`; journal tetap authoritative jika export gagal. Uji Windows open-file error dan pertahankan export lama.
- Format akhir: `[HH:MM:SS]`, transcript mentah tersedia, `### Structured notes`, `📌 **manual note**`; AI timestamp awal chunk. Tambahkan status incomplete/pending dan duration yang benar, bukan klaim sesi selesai ketika task belum berhasil.

## Langkah dan verifikasi

1. **Non-overwrite allocation.** Ubah shared writer/session allocation dan WAV agar satu sesi memakai identity yang sama. Tambahkan tes dua instance same title/date, rapid start, reserved name, dan failure membuat directory. Verifikasi: `pytest -q latchnote-app/tests/test_writer.py` dari root dengan interpreter venv; dua output berbeda dan konten file pertama identik dengan sebelum sesi kedua.
2. **Journal + rebuild.** Persist event lalu append Markdown; buat recovery reader/rebuild dengan validasi schema/version dan sorting stabil. Tambahkan check restart, Unicode ID/EN, late AI/manual, truncated tail, middle corruption, failed replace. Verifikasi: full pytest lulus; membaca journal baru dan rebuild menghasilkan konten sama, tanpa hilangnya event lama.
3. **Satu worker AI dan pending durable.** Ganti thread per chunk dengan satu antrean stdlib/satu worker. Lindungi operasi add/flush chunker terhadap final event bersamaan Stop. Batasi request timeout/retry dan simpan pending ketika worker tidak selesai; gunakan deadline total shutdown, bukan 10 detik dikali jumlah chunk. Error Claude tidak menghentikan capture atau membuang transcript. Idempotency berbasis chunk ID. Verifikasi: tes gagal → restart → retry sukses menghasilkan satu structured event; completion tertunda tidak menghalangi manual note; flush bersamaan final event tidak hilang/dobel.
4. **Samakan kontrak dokumentasi.** Update contoh rules, task acceptance, dan bagian PRD output terkait identity/suffix/live vs final. Jangan menghapus raw transcript demi tampilan rapi. Verifikasi: `rg -n 'HH:MM:SS|chronolog|kronolog|collision|suffix|journal' prd.md task.md .agents/rules/latchnote.md` menunjukkan definisi yang konsisten; full pytest dan `git diff --check` lulus.

Perintah tes semua: `& .\latchnote-app\.venv\Scripts\python.exe -m pytest -q latchnote-app/tests`. Setup jika perlu: Python >=3.12, venv, editable `.[dev]` sesuai pyproject. Tidak ada dependency runtime baru.

## Done criteria

- [ ] Collision/check Windows naming lulus; file lama tidak berubah.
- [ ] Restart/rebuild dan pending retry tests lulus; export monotonik berdasarkan timestamp sumber.
- [ ] Artefak task dan journal dapat dibaca tanpa key atau jaringan; raw text tidak hilang pada failure AI.
- [ ] Duplicate successful retry tidak menggandakan output; queue/thread count tidak bertambah per chunk.
- [ ] Shutdown mempunyai deadline total; pekerjaan belum selesai ditandai dan disimpan.
- [ ] Kriteria live/final output tertulis konsisten; status index diperbarui.

## STOP conditions dan maintenance

Stop jika writer membutuhkan destructive overwrite, recovery format tidak dapat dibangun ulang secara deterministik, disk penuh ditangani sebagai sukses, atau scope memerlukan database/service baru. Pelihara version field pada schema; jangan menulis parser Markdown untuk merekonstruksi task bila journal sudah ada. Jangan menjanjikan zero-loss terhadap power failure: flush/fsync dan crash recovery diuji pada gate 005, keterbatasan hardware dicatat. Retensi WAV tetap manual sampai kebijakan diputuskan.
