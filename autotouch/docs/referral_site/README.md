# Referral site (comparison microsite)

This is a separate Vite/React project that lives under `ads/referral_site/`. It hosts an editorial comparison article (Autotouch ranked as top pick) and is used for referral/SEO traffic.

## Project location
- Code: `ads/referral_site/`
- Project docs: `ads/referral_site/docs/`

## Run locally
```bash
cd ads/referral_site
npm install
npm run dev
```

## Build / preview
```bash
cd ads/referral_site
npm run build
npm run preview
```

## Key content locations
- Main article: `ads/referral_site/src/pages/Article.jsx`
- Home page: `ads/referral_site/src/pages/Home.jsx`
- SEO tokens: `ads/referral_site/src/data/seo.js`
- G2 quotes cache: `ads/referral_site/src/data/g2Quotes.json`

## Data refreshes
G2 quotes are pulled via RapidAPI and written to `src/data/g2Quotes.json`.

From repo root:
```bash
cd ads/referral_site
node scripts/fetch-g2-quotes.mjs
```

Requires `RAPID_API_KEY` (see `ads/referral_site/docs/data/g2.md`).

## Tracking
Outbound clicks push `dataLayer` events:
- Event name: `outbound_click`
- Params: `vendor`, `url`, `placement`

## Docs inside the project
Start here:
- `ads/referral_site/docs/README.md`

Key sub-docs:
- `ads/referral_site/docs/website/overview.md`
- `ads/referral_site/docs/website/content.md`
- `ads/referral_site/docs/design/style-system.md`
- `ads/referral_site/docs/data/g2.md`
- `ads/referral_site/docs/data/seo.md`
- `ads/referral_site/docs/operations/maintenance.md`

## Notes
- This project is distinct from the main Autotouch website in `/website`.
- Keep the comparison article properly cited (see `content.md`).
