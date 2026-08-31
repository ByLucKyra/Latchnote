export type Lang = "en" | "id";

const en = {
  htmlLang: "en",
  meta: {
    title: "Latchnote - live course audio into local Markdown notes",
    description:
      "A Windows companion that transcribes what you are watching, structures it into Markdown, and leaves room for your own notes with one hotkey.",
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
    headlineBottom: "The notes write themselves.",
    sub: "Latchnote listens to your Windows audio, transcribes it live, and saves structured Markdown that stays on your machine.",
    ctaPrimary: "Join the waitlist",
    ctaSecondary: "See a real session",
  },
  demo: {
    sessionTitle: "Backend Fundamentals",
    recording: "Recording",
    finished: "Session saved",
    transcript: "Transcript",
    structured: "Structured notes",
    manual: "Your note",
    replay: "Replay",
    caption: "A simulation of a running session, at the speed it actually appears.",
  },
  problem: {
    heading: "Pausing to write means losing the thread.",
    body1:
      "You can stop every minute to type, and lose the flow of the lecture. Or you can stay with the video, and lose most of what was said.",
    body2:
      "Tools that summarise a video after you finish do not help while you are still watching. Meeting overlays were built for job interviews, not for studying alone.",
    imageAlt: "A student watching a recorded lecture on a laptop at night",
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
        body: "The audio streams to Deepgram and comes back as timestamped text, with Indonesian and English detected automatically.",
      },
      {
        name: "Structure",
        body: "Every two to three minutes the new transcript goes to Claude, which turns it into bullets without inventing anything.",
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
    evidence:
      "Karpicke and Roediger (2008) measured 80% retention after a week from active recall, against 36% from passive re-reading.",
    hintDesktop: "Press Ctrl+Space to try it",
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
    body: "Latchnote is being tested on real study sessions right now. Every hour of audio costs real money in transcription and AI, so the plan has to match how people actually use it.",
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
    unconfigured:
      "The waitlist endpoint is not configured yet. Set PUBLIC_WAITLIST_ENDPOINT before deploying.",
  },
  faq: {
    heading: "Questions worth asking first",
    items: [
      {
        q: "Does my audio leave my computer?",
        a: "Yes, while a session is running. Audio is streamed to Deepgram for transcription, and the transcript text is sent to Claude for structuring. The finished notes are written to your disk and are not synced anywhere.",
      },
      {
        q: "Is it Windows only?",
        a: "Yes. Audio capture uses WASAPI loopback, which is a Windows feature. macOS and mobile are not planned for the first release.",
      },
      {
        q: "Does it handle mixed Indonesian and English?",
        a: "That is the case it was built for. Language detection runs automatically, so you never pick a language before a session starts.",
      },
      {
        q: "What happens if my connection drops?",
        a: "The recording keeps running and stays on disk. The tray icon reports the error, and the raw audio remains available, so nothing already captured is lost.",
      },
      {
        q: "Can I use it for meetings?",
        a: "Technically it captures any system audio. It is designed for solo study, and it has no features for hiding that it is running.",
      },
      {
        q: "When can I try it?",
        a: "The desktop app runs end to end today and is being validated on real course sessions. Early access goes to the waitlist first.",
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
    title: "Latchnote - audio kelas jadi catatan Markdown di komputermu",
    description:
      "Aplikasi Windows yang mentranskrip apa yang sedang kamu tonton, menyusunnya jadi Markdown, dan menyisakan ruang untuk catatanmu sendiri lewat satu hotkey.",
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
    headlineBottom: "Catatannya jalan sendiri.",
    sub: "Latchnote mendengarkan audio Windows kamu, mentranskripnya langsung, lalu menyimpan Markdown terstruktur yang tetap ada di komputermu.",
    ctaPrimary: "Gabung waitlist",
    ctaSecondary: "Lihat sesi aslinya",
  },
  demo: {
    sessionTitle: "Backend Fundamentals",
    recording: "Merekam",
    finished: "Sesi tersimpan",
    transcript: "Transkrip",
    structured: "Catatan terstruktur",
    manual: "Catatanmu",
    replay: "Ulangi",
    caption: "Simulasi sesi yang sedang berjalan, dengan kecepatan sebagaimana aslinya muncul.",
  },
  problem: {
    heading: "Berhenti buat nulis berarti kehilangan alurnya.",
    body1:
      "Kamu bisa berhenti tiap menit buat ngetik, dan kehilangan alur kelasnya. Atau tetap ikut videonya, dan kehilangan sebagian besar yang barusan dijelaskan.",
    body2:
      "Alat yang merangkum video setelah selesai tidak menolong saat kamu masih nonton. Overlay meeting dibuat untuk wawancara kerja, bukan untuk belajar sendirian.",
    imageAlt: "Mahasiswa menonton rekaman kuliah di laptop pada malam hari",
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
        body: "Audionya dikirim ke Deepgram dan kembali jadi teks bertimestamp, dengan bahasa Indonesia dan Inggris terdeteksi otomatis.",
      },
      {
        name: "Susun",
        body: "Setiap dua sampai tiga menit, transkrip barunya dikirim ke Claude untuk diubah jadi poin-poin tanpa menambah hal yang tidak diucapkan.",
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
    evidence:
      "Karpicke dan Roediger (2008) mengukur retensi 80% setelah seminggu dari active recall, dibanding 36% dari sekadar baca ulang.",
    hintDesktop: "Tekan Ctrl+Space untuk mencobanya",
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
    body: "Latchnote sedang diuji di sesi belajar yang nyata. Setiap jam audio memakan biaya nyata untuk transkripsi dan AI, jadi paketnya harus cocok dengan cara orang benar-benar memakainya.",
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
    unconfigured:
      "Endpoint waitlist belum dikonfigurasi. Isi PUBLIC_WAITLIST_ENDPOINT sebelum deploy.",
  },
  faq: {
    heading: "Pertanyaan yang wajar ditanyakan duluan",
    items: [
      {
        q: "Apakah audioku keluar dari komputer?",
        a: "Ya, selama sesi berjalan. Audio dikirim ke Deepgram untuk ditranskrip, dan teks transkripnya dikirim ke Claude untuk disusun. Catatan jadinya ditulis ke diskmu dan tidak disinkronkan ke mana pun.",
      },
      {
        q: "Cuma untuk Windows?",
        a: "Ya. Perekaman audionya memakai WASAPI loopback yang merupakan fitur Windows. macOS dan mobile belum direncanakan untuk rilis pertama.",
      },
      {
        q: "Bisa menangani campuran bahasa Indonesia dan Inggris?",
        a: "Justru itu kasus yang jadi alasan Latchnote dibuat. Deteksi bahasa berjalan otomatis, jadi kamu tidak perlu memilih bahasa sebelum sesi dimulai.",
      },
      {
        q: "Kalau koneksiku putus gimana?",
        a: "Perekaman tetap jalan dan tersimpan di disk. Ikon tray melaporkan errornya, dan audio mentahnya tetap ada, jadi yang sudah terekam tidak hilang.",
      },
      {
        q: "Bisa dipakai buat meeting?",
        a: "Secara teknis dia merekam audio sistem apa pun. Tapi desainnya untuk belajar sendiri, dan tidak ada fitur untuk menyembunyikan bahwa dia sedang berjalan.",
      },
      {
        q: "Kapan bisa dicoba?",
        a: "Aplikasi desktopnya sudah berjalan utuh dan sedang divalidasi di sesi kuliah nyata. Akses awal diberikan ke waitlist lebih dulu.",
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
