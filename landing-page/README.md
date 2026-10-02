# Latchnote landing page

Astro + React page for the early Windows prototype, with English at `/` and
Bahasa Indonesia at `/id/`. Product limits and setup are documented in
[`../latchnote-app/README.md`](../latchnote-app/README.md).

## Local preview

Requires Node.js 22.12 or newer. From this directory:

```powershell
npm ci
npm run dev
npm run build
npm run preview
```

The static build writes both routes to `dist/`. Check them in preview at narrow
and wide widths, with reduced motion enabled, and by keyboard before publishing.

## Waitlist launch gate

The form stays closed unless `PUBLIC_WAITLIST_ENDPOINT` is set at build time.
Configure only an operator-approved public HTTPS receiver; never put a secret
in this browser-visible variable. The POST JSON contract is:

```json
{"email":"person@example.com","pricing_preference":"undecided","language":"en"}
```

`pricing_preference` is `byo-key`, `monthly-hours`, or `undecided`; `language`
is `en` or `id`. The receiver must validate and deduplicate submissions and
return a successful 2xx only after saving. No endpoint is currently configured
or externally tested, so the public waitlist must remain closed.

Canonical URLs and social previews are intentionally omitted until the owner
chooses and verifies a domain and real share image. Do not deploy as launch-ready
until those, the waitlist receiver, and the manual smoke checks are complete.
