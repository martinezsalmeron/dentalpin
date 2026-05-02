# DentalPin documentation portal

VitePress site that renders `/docs` as a public documentation portal at
`docs.dentalpin.com`.

The markdown source under `/docs` is the single source of truth — this folder
only contains the build pipeline (config, theme, Dockerfile). Authors edit
markdown in the same PR as the code change; the portal picks it up at the
next build.

See ADR [0009](../adr/0009-documentation-portal.md) for the architecture
decision.

## Local development

```bash
cd docs/portal
npm install
npm run dev          # http://localhost:5173
npm run build        # produces .vitepress/dist/
npm run preview      # serves the built site locally
```

VitePress reads its config from `.vitepress/config.ts`. The sidebar and top
nav are generated from the `/docs` filesystem at build time
(`.vitepress/sidebar.ts`) — there is no hand-maintained nav array.

## Deployment

The `Dockerfile` is a multi-stage build:

1. **Builder** — Node 20 Alpine, runs `npm ci` and `npm run build` from the
   repository root context (so it can see `/docs` content).
2. **Runtime** — `nginx:alpine` serving `/usr/share/nginx/html` over `:80`,
   with `nginx.conf` configured for clean URLs and CORS for the in-app help
   drawer (added in fase 5).

Coolify on the existing Hetzner host pulls the image and exposes it at
`docs.dentalpin.com`. TLS is handled by Coolify (Let's Encrypt). No data,
no auth — purely static.

## Project layout

```
docs/portal/
├── .vitepress/
│   ├── config.ts          # VitePress config (srcDir = .., reads /docs)
│   └── sidebar.ts         # Auto-generates sidebar from /docs filesystem
├── Dockerfile             # Multi-stage build: node → nginx
├── nginx.conf             # CORS + clean URLs
├── package.json
└── README.md              # this file
```

`srcDir: ".."` makes VitePress treat `/docs` as the source root, so every
existing markdown file lives in the rendered site. `srcExclude` keeps the
portal folder itself out of the build.
