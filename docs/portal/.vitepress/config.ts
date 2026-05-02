import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { defineConfig } from "vitepress";
import { generateNav, generateSidebar } from "./sidebar.js";
import { checkStale } from "./staleness.js";

// docs/portal/.vitepress/ → /docs/ root (one up from project, two up from this file).
const DOCS_ROOT = resolve(fileURLToPath(new URL(".", import.meta.url)), "..", "..");

// Resolve vue's package directory relative to this config so Rollup can find
// it during SSR bundling. Required because `srcDir: ".."` makes the source
// tree (/docs) sit *outside* the project root, and Rollup walks up from
// each markdown file looking for `node_modules/vue/...` — which lives under
// `docs/portal/node_modules/`, not on that walk path.
const VUE_DIR = fileURLToPath(new URL("../node_modules/vue", import.meta.url));

// Source root is /docs (one level up from this portal project), so all
// existing markdown is rendered without copies. The portal folder itself
// is excluded so VitePress does not try to render its own scaffolding.
export default defineConfig({
  title: "DentalPin Docs",
  description:
    "Open-source dental clinic management software — developer reference and user manual.",
  lang: "en-US",
  cleanUrls: true,
  lastUpdated: true,
  srcDir: "..",
  outDir: "./.vitepress/dist",
  cacheDir: "./.vitepress/cache",
  srcExclude: [
    "portal/**",
    "**/node_modules/**",
    "**/CHANGELOG.md",
    // Author-facing templates that contain `<placeholder>` patterns Vue
    // would try to parse as components.
    "**/TEMPLATE.md",
    "**/*-template.md",
  ],
  // Treat the existing /docs/README.md as the home page.
  rewrites: {
    "README.md": "index.md",
  },
  // The /docs source predates the portal: some markdown links point to
  // files outside /docs (root CLAUDE.md, backend module CLAUDE.md files)
  // or to section indexes that don't exist yet. Accept those patterns so
  // the build passes; real broken links *inside* /docs still fail.
  // TODO(fase 2): create section README.md/index.md files and rewrite
  // outbound links to GitHub URLs so this list shrinks.
  ignoreDeadLinks: [
    /^https?:\/\/localhost/,
    /\.\.\/\.\.\//,
    /\.\.\/CLAUDE$/,
    /backend\/app\/modules\/[^/]+\/CLAUDE$/,
    /\/(index|README)$/,
  ],
  themeConfig: {
    nav: generateNav(),
    sidebar: generateSidebar(),
    search: {
      provider: "local",
    },
    outline: {
      level: [2, 3],
    },
    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/martinezsalmeron/dentalpin",
      },
    ],
    editLink: {
      pattern:
        "https://github.com/martinezsalmeron/dentalpin/edit/main/docs/:path",
      text: "Edit this page on GitHub",
    },
    footer: {
      message:
        'Source: <a href="https://github.com/martinezsalmeron/dentalpin">github.com/martinezsalmeron/dentalpin</a>',
      copyright: "BSL 1.1 (converts to Apache 2.0 after 4 years)",
    },
  },
  markdown: {
    lineNumbers: false,
  },
  // Per-page transform: detect staleness from `last_verified_commit` and
  // inject `staleSince` / `staleDiffUrl` into the frontmatter so the
  // theme override (`theme/StaleBadge.vue`) can render the badge.
  transformPageData(pageData) {
    const fm = (pageData.frontmatter ?? {}) as Record<string, unknown>;
    if (!fm.last_verified_commit || !pageData.filePath) return;
    const absolute = resolve(DOCS_ROOT, pageData.filePath);
    const result = checkStale(fm, absolute);
    if (result?.stale) {
      pageData.frontmatter.staleSince = result.verifiedSha;
      pageData.frontmatter.staleDiffUrl = result.diffUrl;
      pageData.frontmatter.staleCommits = result.staleCommits;
    }
  },
  vite: {
    resolve: {
      alias: [
        { find: /^vue$/, replacement: `${VUE_DIR}/index.mjs` },
        {
          find: /^vue\/server-renderer$/,
          replacement: `${VUE_DIR}/server-renderer/index.mjs`,
        },
      ],
    },
  },
});
