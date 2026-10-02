# Plan 004: Landing page siap menerima waitlist dengan klaim sesuai bukti

Status TODO. Prioritas P1/P2. Effort M. Risiko MED untuk endpoint, LOW untuk copy. Kategori UX/docs/distribusi. Dependensi: copy/UI independen; klaim fitur desktop menunggu 003/005. Planned at `37c7332`, 2 Oktober 2026.

## Konteks dan tujuan

Landing page sudah mempunyai route Inggris `/` dan Indonesia `/id/`, demo React, dark mode, output Markdown, FAQ, dan survei harga. Ini alat validasi demand; harga belum diputuskan. Yang perlu diselesaikan adalah integritas demo/copy, interaksi usable, endpoint waitlist yang terbukti menyimpan data, dan runtime/build yang reproducible. Tidak membangun payment atau dashboard.

## Scope dan commands

Files: `landing-page/src/{content/copy.ts,components/WaitlistForm.tsx,components/LiveSessionDemo.tsx,components/HotkeyDemo.tsx,components/Nav.astro,components/Landing.astro,layouts/Base.astro}`, styles existing hanya jika responsive fix memerlukan, `public/` untuk aset nyata, `.env.example`, `astro.config.mjs`, README, serta status plan di `plans/README.md`. Manifest/lockfile hanya jika diperlukan untuk documented verification tooling, bukan upgrade massal. Tidak mengubah desktop/source rules, menyiapkan custom backend, atau deploy otomatis.

```powershell
git diff --stat 37c7332..HEAD -- landing-page
git status --short
node --version
npm --version
# Setelah Node sesuai engines package, dari landing-page/:
npm ci
npm run build
npm run astro -- dev --background
```

Saat audit Node v20.20.2, minimum manifest >=22.12.0; build belum dijalankan ulang. `npm ci` dan build adalah langkah implementasi, bukan hasil audit. Build di runtime sesuai harus exit 0 dan menghasilkan `dist/index.html` serta `dist/id/index.html`. Tidak ada skrip typecheck/lint saat ini; jangan menyebut build sebagai typecheck. Bila menambah pemeriksaan Astro/TS, gunakan tooling resmi dan catat perubahan dependency, bukan memasang framework tes baru untuk copy.

## Current state

`WaitlistForm.tsx:24`: endpoint berasal dari `PUBLIC_WAITLIST_ENDPOINT`. `submit()` melakukan fetch JSON tanpa timeout, dan config error mengekspos nama environment ke pengunjung. `LiveSessionDemo.tsx:70–75,101–105` mengatur completed pada reduced motion, tetapi Replay reset ke step 0 sementara timer dimatikan. `copy.ts` mengatakan "See a real session", "at the speed it actually appears", dan app runs end-to-end, tanpa bukti yang mendukung. Demo menyajikan bullet sebelum sumber terkait muncul; source harus dibenahi agar contoh juga menunjukkan AI grounded. `Landing.astro:106` memakai foto acak dengan alt student yang belum tentu cocok. `Base.astro:49` dan Nav aria-label masih English pada route ID.

Conventions: reuse dictionary `Copy`, React islands `client:idle`/`client:visible`, native `<details>`/forms, token CSS existing, Phosphor SVG build-time. Jangan menambah komponen abstrak atau library form. `InlineIcon` static data bukan temuan XSS.

## Langkah dan verifikasi

1. **Copy sesuai tahap produk.** Label contoh sebagai simulasi dipercepat, ubah CTA real session menjadi sample notes jika belum ada output nyata, batasi FAQ reliability/ID-EN pada hasil yang sudah terbukti. Jangan mengubah active recall research menjadi janji retensi dari dua kata; hapus statistik dari landing sampai sumber primer dan relevansinya diverifikasi. Pricing tetap survei, tanpa angka/paket palsu. Verifikasi: `rg -n 'real session|sesi aslinya|at the speed|sebagaimana aslinya|80%|36%|runs end to end|berjalan utuh' src` tidak menemukan klaim lama kecuali bukti valid tercatat; build kedua route sukses.
2. **Demo accessible dan grounded.** Reduced-motion Replay harus tetap menampilkan finished state, atau hilangkan Replay jika tidak mempunyai arti. Source transcript semua bullet harus muncul sebelum structured result; timestamp AI adalah chunk start, bukan waktu render. Hindari word-by-word live announcement ke screen reader, gunakan announcement per final block/status. Tambahkan tombol Try pada desktop selain shortcut; jangan menangkap Ctrl+Space saat editing/composing field lain; restore focus setelah close. Periksa 320/375/768/1280 px, termasuk filename panjang/footer demo/Nav, serta EN/ID label. Verifikasi: browser manual Replay dengan reduced-motion on/off, keyboard Enter/Esc/Tab, focus visible/restore, shortcut saat mengisi email, tidak ada page horizontal overflow; catat hasil dan console error.
3. **Aset dan identity nyata.** Ganti/hapus foto placeholder, pastikan alt cocok dengan gambar, gunakan local optimized asset; ganti favicon starter. Canonical/hreflang harus merujuk domain yang benar-benar dipilih pemilik, bukan asumsi `latchnote.app`. Tambah OG asset jika akan dibagikan. Verifikasi: build lalu `rg -n 'picsum.photos' src` menghasilkan nol match; browser load kedua route tidak 404 pada aset, alt/deskripsi tepat. Jika domain/aset belum tersedia, tandai pending tanpa memalsukan kepemilikan/foto.
4. **Satu endpoint waitlist yang sesuai contract.** Gunakan hosted receiver yang menerima POST JSON email, stable pricing preference (`byo-key`, `monthly-hours`, `undecided`), dan language. Pilihan translated label tidak boleh menjadi identifier analytics. Pastikan anti-abuse/dedupe dilakukan service, bukan menganggap regex frontend sebagai security boundary. Endpoint PUBLIC adalah URL publik, bukan tempat credential. Operator menyediakan endpoint/service account; jika belum ada, halaman menyampaikan waitlist belum dibuka tanpa pesan env internal atau fake success. Tambahkan request timeout yang dapat dibatalkan dan reset loading di failure. Verifikasi: approved test submission terlihat di storage, response 4xx/network/timeout menunjukkan retryable error, request ganda tidak menambah record tak terkendali; config missing tidak mengirim request. Jangan mengirim email atau daftar dummy ke layanan eksternal tanpa instruksi operator.
5. **Dokumentasikan preview dan launch gate.** Ganti README starter dengan runtime, `npm ci`, build/preview, locale, endpoint build-time, payload, fallback, deployment config dan smoke checklist. Isi `.env` hanya lokal; jangan menyimpan email penguji di source. Verifikasi: clean setup mengikuti README pada runtime sesuai, build dan preview kedua route lulus. Pengujian fetch lokal dapat memakai native browser/devtools; tidak perlu framework baru jika check manual terdokumentasi cukup.

## Done criteria

- [ ] Build EN/ID exit 0 pada Node sesuai minimum; generated routes benar.
- [ ] Mobile/desktop, reduced-motion Replay, keyboard/focus dan hotkey editing checks tercatat lulus.
- [ ] Copy mengungkap simulasi serta batas AI/API/local storage; tidak ada klaim benchmark produk tanpa bukti.
- [ ] Endpoint nyata menerima submission yang disetujui operator; saved payload dan failure/timeout diuji.
- [ ] Aset placeholder/starter dihapus atau diganti, canonical sesuai domain operator.
- [ ] README operasional, `git diff --check` exit 0, status index diperbarui. Deployment publik tetap tindakan terpisah.

## STOP conditions dan maintenance

Stop pada incompatibility Node/framework yang tidak dapat diselesaikan dengan runtime yang didukung, endpoint memerlukan secret di browser, atau pilihan domain/service belum tersedia untuk external setup. Lanjutkan pekerjaan copy/UI independen dan catat blocker endpoint. Waitlist publik bisa dibuka sebelum desktop selesai hanya dengan stage copy yang jujur. Pertahankan dua bahasa sinkron; tambah form backend sendiri hanya jika hosted endpoint terbukti tidak memenuhi kebutuhan.
