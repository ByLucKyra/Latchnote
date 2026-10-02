export type Lang = "en" | "id";

const en = {
  htmlLang: "en",
  meta: {
    title: "Latchnote - local course audio into Markdown notes",
    description:
      "A Windows prototype that transcribes system audio locally and saves Markdown notes, with optional AI formatting and personal notes.",
  },
  nav: {
    how: "How it works",
    output: "Output",
    pricing: "Pricing",
    faq: "FAQ",
    cta: "Join the waitlist",
    otherLangLabel: "Bahasa Indonesia",
    otherLangShort: "ID",
    otherLangHref: "/id/",
    themeLabel: "Switch colour theme",
  },
  hero: {
    eyebrow: "Early access",
    headlineTop: "Watch the course.",
    headlineBottom: "Keep your notes close.",
    sub: "Latchnote captures Windows system audio, transcribes it locally, and saves Markdown on your machine. AI formatting is optional.",
    ctaPrimary: "Join the waitlist",
    ctaSecondary: "See sample notes",
  },
  demo: {
    sessionTitle: "Backend Fundamentals",
    recording: "Recording",
    finished: "Session saved",
    transcript: "Transcript",
    structured: "Structured notes",
    manual: "Your note",
    replay: "Replay",
    caption: "Illustrative simulation, accelerated; not a live recording or product output.",
  },
  problem: {
    heading: "Pausing to write means losing the thread.",
    body1:
      "You can stop every minute to type, and lose the flow of the lecture. Or you can stay with the video, and lose most of what was said.",
    body2:
      "Tools that summarise a video after you finish do not help while you are still watching. Meeting overlays were built for job interviews, not for studying alone.",
  },
  how: {
    heading: "What happens during a session",
    steps: [
      {
        name: "Capture",
        body: "WASAPI loopback takes the audio your speakers are already playing. No microphone, no virtual cable, no browser extension.",
      },
      {
        name: "Transcribe",
        body: "Local Whisper transcribes captured system audio. Language detection can be tested with multilingual models; quality is still being validated.",
      },
      {
        name: "Structure",
        body: "Optional AI formatting sends transcript text—not audio—to a configured OpenAI-compatible provider. Output still needs review.",
      },
      {
        name: "Save",
        body: "Everything lands in one Markdown file per session, readable in Obsidian, Notion, or any text editor.",
      },
    ],
  },
  hotkey: {
    heading: "One key. Your own words.",
    body: "Full automation takes you out of your own notes. Latchnote leaves a small opening instead: press Ctrl+Space, type two words, keep watching.",
    evidence: "Adding your own note is an interaction example, not a claim about learning outcomes.",
    hintDesktop: "Try the note demo (Ctrl+Space)",
    hintTouch: "Tap to try it",
    inputLabel: "Micro-note",
    inputPlaceholder: "two or three words",
    submit: "Save note",
    cancel: "Press Esc to cancel",
    emptyState: "Your notes will appear here, marked with a pin.",
  },
  output: {
    heading: "Plain Markdown. Nothing locked in.",
    body: "One file per session, named by date and title. Your own notes carry a pin, so you can always tell them apart from the generated ones.",
    filename: "2026-08-29_Backend Fundamentals.md",
    copy: "Copy",
    copied: "Copied",
  },
  comparison: {
    heading: "Where Latchnote sits",
    columns: ["Latchnote", "Meeting overlays", "Post-hoc summarisers"],
    rows: [
      {
        label: "When it works",
        values: [
          "Live, while you watch",
          "Live, built for interviews",
          "After the video, via upload",
        ],
      },
      {
        label: "Your involvement",
        values: ["A hotkey and two words", "None, or focused on hiding usage", "None"],
      },
      {
        label: "Where notes live",
        values: ["A Markdown file on your disk", "Usually their cloud", "Usually their cloud"],
      },
    ],
  },
  waitlist: {
    heading: "Pricing is not decided yet.",
    body: "Latchnote is an early prototype. Pricing is still undecided, and this short survey helps us understand which model may fit future use.",
    pollQuestion: "Which would you rather pay for?",
    pollOptions: [
      "I bring my own API keys and pay once for the app",
      "A monthly plan with a set number of hours",
      "I am not sure yet",
    ],
    emailLabel: "Email",
    emailPlaceholder: "nama@email.com",
    emailHelp: "Windows 10 and 11 only for now.",
    submit: "Join the waitlist",
    submitting: "Sending",
    success: "You are on the list. You will get one email before early access opens.",
    errorGeneric: "That did not go through. Please try again.",
    errorEmail: "Please enter a valid email address.",
    errorPoll: "Pick the option closest to what you would do.",
    privacy: "One email when early access opens. Nothing else.",
    unconfigured: "The waitlist is not open yet. Please check back later.",
  },
  faq: {
    heading: "Questions worth asking first",
    items: [
      {
        q: "Does my audio leave my computer?",
        a: "Audio is captured and transcribed locally with Whisper. If you enable optional AI formatting, transcript text is sent to your configured provider; recordings are not sent for that step. Notes are written to disk.",
      },
      {
        q: "Is it Windows only?",
        a: "Yes. Audio capture uses WASAPI loopback, which is a Windows feature. macOS and mobile are not planned for the first release.",
      },
      {
        q: "Does it handle mixed Indonesian and English?",
        a: "The app uses multilingual Whisper models, but mixed Indonesian/English accuracy has not yet been validated across real sessions.",
      },
      {
        q: "What happens if my connection drops?",
        a: "The app retains a WAV recovery file and journals known gaps, but recovery and long-session behavior still need real-device validation.",
      },
      {
        q: "Can I use it for meetings?",
        a: "Technically it captures any system audio. It is designed for solo study, and it has no features for hiding that it is running.",
      },
      {
        q: "When can I try it?",
        a: "It is an early prototype. Core behavior and real-device reliability are still being validated; the waitlist is not open yet.",
      },
    ],
  },
  footer: {
    tagline: "A local notes companion for people who learn by listening.",
    builtBy: "Built by Lucky Ramadhan",
    rights: "All rights reserved.",
  },
};

export type Copy = typeof en;

const id: Copy = {
  htmlLang: "id",
  meta: {
    title: "Latchnote - audio kelas jadi catatan Markdown lokal",
    description:
      "Prototipe Windows yang mentranskrip audio sistem secara lokal dan menyimpan catatan Markdown, dengan format AI opsional.",
  },
  nav: {
    how: "Cara kerja",
    output: "Hasil",
    pricing: "Harga",
    faq: "Tanya jawab",
    cta: "Gabung waitlist",
    otherLangLabel: "English",
    otherLangShort: "EN",
    otherLangHref: "/",
    themeLabel: "Ganti tema warna",
  },
  hero: {
    eyebrow: "Akses awal",
    headlineTop: "Fokus ke materinya.",
    headlineBottom: "Simpan catatanmu sendiri.",
    sub: "Latchnote merekam audio sistem Windows, mentranskripnya secara lokal, lalu menyimpan Markdown di komputermu. Pemformatan AI opsional.",
    ctaPrimary: "Gabung waitlist",
    ctaSecondary: "Lihat contoh catatan",
  },
  demo: {
    sessionTitle: "Backend Fundamentals",
    recording: "Merekam",
    finished: "Sesi tersimpan",
    transcript: "Transkrip",
    structured: "Catatan terstruktur",
    manual: "Catatanmu",
    replay: "Ulangi",
    caption: "Simulasi ilustratif yang dipercepat; bukan rekaman langsung atau hasil produk.",
  },
  problem: {
    heading: "Berhenti buat nulis berarti kehilangan alurnya.",
    body1:
      "Kamu bisa berhenti tiap menit buat ngetik, dan kehilangan alur kelasnya. Atau tetap ikut videonya, dan kehilangan sebagian besar yang barusan dijelaskan.",
    body2:
      "Alat yang merangkum video setelah selesai tidak menolong saat kamu masih nonton. Overlay meeting dibuat untuk wawancara kerja, bukan untuk belajar sendirian.",
  },
  how: {
    heading: "Yang terjadi selama satu sesi",
    steps: [
      {
        name: "Rekam",
        body: "WASAPI loopback mengambil audio yang sudah keluar dari speaker kamu. Tanpa mikrofon, tanpa virtual cable, tanpa ekstensi browser.",
      },
      {
        name: "Transkrip",
        body: "Whisper lokal mentranskrip audio sistem. Deteksi bahasa dapat diuji dengan model multilingual; kualitasnya masih divalidasi.",
      },
      {
        name: "Susun",
        body: "Pemformatan AI opsional mengirim teks transkrip—bukan audio—ke penyedia OpenAI-compatible yang dikonfigurasi. Hasilnya tetap perlu ditinjau.",
      },
      {
        name: "Simpan",
        body: "Semuanya masuk ke satu file Markdown per sesi, bisa dibuka di Obsidian, Notion, atau editor teks apa pun.",
      },
    ],
  },
  hotkey: {
    heading: "Satu tombol. Kata-katamu sendiri.",
    body: "Otomatisasi penuh justru mengeluarkan kamu dari catatanmu sendiri. Latchnote menyisakan celah kecil: tekan Ctrl+Space, ketik dua kata, lanjut nonton.",
    evidence: "Menambahkan catatan sendiri adalah contoh interaksi, bukan klaim hasil belajar.",
    hintDesktop: "Coba demo catatan (Ctrl+Space)",
    hintTouch: "Ketuk untuk mencobanya",
    inputLabel: "Catatan singkat",
    inputPlaceholder: "dua atau tiga kata",
    submit: "Simpan catatan",
    cancel: "Tekan Esc untuk batal",
    emptyState: "Catatanmu akan muncul di sini, ditandai dengan pin.",
  },
  output: {
    heading: "Markdown biasa. Tidak ada yang dikunci.",
    body: "Satu file per sesi, dinamai berdasarkan tanggal dan judul. Catatanmu sendiri ditandai pin, jadi selalu gampang dibedakan dari yang dihasilkan AI.",
    filename: "2026-08-29_Backend Fundamentals.md",
    copy: "Salin",
    copied: "Tersalin",
  },
  comparison: {
    heading: "Posisi Latchnote",
    columns: ["Latchnote", "Overlay meeting", "Perangkum setelah selesai"],
    rows: [
      {
        label: "Kapan bekerja",
        values: [
          "Langsung, saat kamu nonton",
          "Langsung, tapi dibuat untuk wawancara",
          "Setelah video selesai, lewat unggahan",
        ],
      },
      {
        label: "Keterlibatanmu",
        values: [
          "Satu hotkey dan dua kata",
          "Tidak ada, atau fokus menyembunyikan pemakaian",
          "Tidak ada",
        ],
      },
      {
        label: "Catatan disimpan",
        values: ["File Markdown di komputermu", "Biasanya cloud mereka", "Biasanya cloud mereka"],
      },
    ],
  },
  waitlist: {
    heading: "Harganya belum ditentukan.",
    body: "Latchnote masih prototipe awal. Harga belum ditentukan; survei singkat ini membantu memahami model yang mungkin cocok untuk penggunaan nanti.",
    pollQuestion: "Kamu lebih milih bayar yang mana?",
    pollOptions: [
      "Aku pakai API key sendiri dan bayar sekali untuk aplikasinya",
      "Langganan bulanan dengan jatah jam tertentu",
      "Belum tahu",
    ],
    emailLabel: "Email",
    emailPlaceholder: "nama@email.com",
    emailHelp: "Baru untuk Windows 10 dan 11.",
    submit: "Gabung waitlist",
    submitting: "Mengirim",
    success: "Kamu sudah masuk daftar. Nanti ada satu email sebelum akses awal dibuka.",
    errorGeneric: "Gagal terkirim. Coba lagi ya.",
    errorEmail: "Masukkan alamat email yang valid.",
    errorPoll: "Pilih opsi yang paling mendekati.",
    privacy: "Satu email saat akses awal dibuka. Tidak ada yang lain.",
    unconfigured: "Waitlist belum dibuka. Silakan cek lagi nanti.",
  },
  faq: {
    heading: "Pertanyaan yang wajar ditanyakan duluan",
    items: [
      {
        q: "Apakah audioku keluar dari komputer?",
        a: "Audio direkam dan ditranskrip secara lokal dengan Whisper. Jika pemformatan AI opsional diaktifkan, teks transkrip dikirim ke penyedia yang kamu konfigurasi; rekaman tidak dikirim untuk langkah itu. Catatan disimpan ke disk.",
      },
      {
        q: "Cuma untuk Windows?",
        a: "Ya. Perekaman audionya memakai WASAPI loopback yang merupakan fitur Windows. macOS dan mobile belum direncanakan untuk rilis pertama.",
      },
      {
        q: "Bisa menangani campuran bahasa Indonesia dan Inggris?",
        a: "Aplikasi memakai model Whisper multilingual, tetapi akurasi campuran Indonesia/Inggris belum divalidasi di beragam sesi nyata.",
      },
      {
        q: "Kalau koneksiku putus gimana?",
        a: "Aplikasi menyimpan file WAV untuk pemulihan dan mencatat gap yang diketahui, tetapi pemulihan dan sesi panjang masih perlu divalidasi di perangkat nyata.",
      },
      {
        q: "Bisa dipakai buat meeting?",
        a: "Secara teknis dia merekam audio sistem apa pun. Tapi desainnya untuk belajar sendiri, dan tidak ada fitur untuk menyembunyikan bahwa dia sedang berjalan.",
      },
      {
        q: "Kapan bisa dicoba?",
        a: "Ini masih prototipe awal. Perilaku inti dan keandalan di perangkat nyata masih divalidasi; waitlist belum dibuka.",
      },
    ],
  },
  footer: {
    tagline: "Pendamping catatan lokal untuk yang belajar dengan mendengar.",
    builtBy: "Dibuat oleh Lucky Ramadhan",
    rights: "Seluruh hak dilindungi.",
  },
};

export const copy: Record<Lang, Copy> = { en, id };
