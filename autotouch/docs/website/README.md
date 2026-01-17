# Main website (autotouch.ai)

The main marketing website lives in `website/` and is a separate Vite/React app.

## Project location
- Code: `website/`
- Project docs: `website/docs/`

## Run locally
```bash
cd website
npm install
npm run dev
```

## Build / preview
```bash
cd website
npm run build
npm run preview
```

## Key content paths
- Content and brand tokens: `website/src/tokens.js`
- Page sections: `website/src/components/sections/`
- Layout: `website/src/components/layout/`
- SEO helpers: `website/src/utils/seo.js`
- Tracking helpers: `website/src/utils/tracking.js`

## Tracking + GTM
- Event schema: `website/tracking-data-layer.md`
- GTM API setup: `website/docs/gtm-api-setup.md`
- Ads/analytics runbook: `website/docs/ads-analytics-runbook.md`

## Markdown mirror
Some pages are mirrored to markdown for crawlers:
- Generator: `website/scripts/generate-markdown.mjs`
- Output: `website/public/md/`
- Docs: `website/docs/markdown-mirror.md`

## Docs inside the project
Start here:
- `website/README.md`

Also useful:
- `website/docs/website-structure.md`
- `website/docs/ads-analytics-runbook.md`
- `website/docs/gtm-api-setup.md`
- `website/tracking-data-layer.md`

## Notes
- The main website is separate from the referral site in `ads/referral_site/`.
- Use `npm run lint` before large refactors.
