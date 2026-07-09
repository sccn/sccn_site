# SCCN Site 2 — "Clean Institutional"

Data-driven rebuild of the SCCN website: content lives in `src/data/*.json`,
`scripts/build_site.py` generates a fully static `dist/` (pages, redirect
stubs, `search-index.json`), and `public/` is copied through verbatim
(legacy mirror, images, fonts).

## Build and preview

```bash
npm run build      # python3 scripts/build_site.py  → dist/
npm run preview    # python3 scripts/serve.py 8173  → http://127.0.0.1:8173/
npm run check-links
```

Publish the contents of `dist/` — it is self-contained (redirects are
meta-refresh stubs, no server logic required).

## GitHub Pages URL prefix

The site is published as a GitHub Pages *project* site
(`https://arnodelorme.github.io/sccn_site2/`), so the build bakes the
`/sccn_site2` prefix into every root-absolute `href`/`src`/`action` and
meta-refresh redirect in `dist/`.

- The prefix lives in **`.baseurl`** (one line, next to `package.json`).
  Edit it and rebuild to change it; empty it to serve at a domain root.
- Rewriting is done by the shared `../tools/bake_prefix.py` as the final
  build step; the baked state is recorded in `dist/.baseurl`.
- `src/scripts/site.js` derives the prefix at runtime from its own
  `<script src>` (search fetch, result links, and query URLs), so the JS
  never needs rebaking.
- `scripts/serve.py` previews `dist/` the way Pages serves it: the baked
  prefix works, redirects stay under the prefix, and directories without
  `index.html` return 404 (no listings).
- `public/.nojekyll` is copied into `dist/` so Pages skips Jekyll
  processing (which would drop underscore-prefixed files).

**Note:** there is no login gating in this build — anything in `dist/` is
public once published.
