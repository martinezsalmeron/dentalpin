/**
 * Build-time generator for the in-app help fragments (Fase 5).
 *
 * After VitePress finishes building, we walk every screen markdown file
 * under `docs/user-manual/<lang>/<module>/screens/*.md`, render its body
 * with markdown-it, and emit a standalone HTML fragment at
 * `dist/<lang>/help/<route-slug>.html`. The frontend `<HelpButton />`
 * drawer points an iframe at this URL.
 *
 * Slug from route:
 *   /patients               → patients
 *   /patients/[id]          → patients_[id]
 *   /settings/verifactu/queue → settings_verifactu_queue
 *   /                       → index
 */
import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, resolve } from "node:path";
import MarkdownIt from "markdown-it";

const HERE = fileURLToPath(new URL(".", import.meta.url));
// docs/portal/.vitepress/ → /docs/.
const DOCS_ROOT = resolve(HERE, "..", "..");
const USER_MANUAL_ROOT = join(DOCS_ROOT, "user-manual");

const LOCALES = ["en", "es"] as const;

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: false,
});

interface Frontmatter {
  module?: string;
  route?: string;
  screen?: string;
  [key: string]: unknown;
}

function parseFrontmatter(text: string): { fm: Frontmatter; body: string } {
  if (!text.startsWith("---")) return { fm: {}, body: text };
  const end = text.indexOf("\n---", 3);
  if (end === -1) return { fm: {}, body: text };
  const block = text.slice(3, end).trim();
  const body = text.slice(end + 4).replace(/^\s*\n/, "");
  const fm: Frontmatter = {};
  let listKey: string | null = null;
  for (const raw of block.split("\n")) {
    if (!raw.trim() || raw.trimStart().startsWith("#")) continue;
    if (raw.startsWith("  - ")) {
      if (!listKey) continue;
      const arr = (fm[listKey] as string[] | undefined) ?? [];
      arr.push(raw.slice(4).trim().replace(/^["']|["']$/g, ""));
      fm[listKey] = arr;
      continue;
    }
    if (raw.startsWith("- ")) continue;
    const colon = raw.indexOf(":");
    if (colon === -1) continue;
    const key = raw.slice(0, colon).trim();
    const value = raw.slice(colon + 1).trim();
    if (value === "") {
      listKey = key;
      fm[key] = [];
    } else {
      listKey = null;
      fm[key] = value.replace(/^["']|["']$/g, "");
    }
  }
  return { fm, body };
}

export function routeToSlug(route: string): string {
  const trimmed = route.replace(/^\/+|\/+$/g, "");
  if (!trimmed) return "index";
  // Strip `[` `]` so the source MD filename does not collide with
  // VitePress' dynamic-route convention (`*[*].md` would expect a
  // companion `.paths.{js,ts}` file). The route itself keeps the
  // brackets — only the slug used as filename / fragment URL drops them.
  return trimmed.replace(/\//g, "_").replace(/[[\]]/g, "");
}

async function collectScreens(): Promise<
  Array<{ locale: string; module: string; route: string; body: string; file: string }>
> {
  const out: Array<{
    locale: string;
    module: string;
    route: string;
    body: string;
    file: string;
  }> = [];

  for (const locale of LOCALES) {
    const localeRoot = join(USER_MANUAL_ROOT, locale);
    if (!existsSync(localeRoot)) continue;
    const moduleEntries = await readdir(localeRoot, { withFileTypes: true });
    for (const moduleEntry of moduleEntries) {
      if (!moduleEntry.isDirectory()) continue;
      const screensDir = join(localeRoot, moduleEntry.name, "screens");
      if (!existsSync(screensDir)) continue;
      const screenFiles = await readdir(screensDir);
      for (const name of screenFiles) {
        if (!name.endsWith(".md")) continue;
        const filePath = join(screensDir, name);
        const text = await readFile(filePath, "utf-8");
        const { fm, body } = parseFrontmatter(text);
        if (!fm.route || typeof fm.route !== "string") continue;
        out.push({
          locale,
          module: moduleEntry.name,
          route: fm.route,
          body,
          file: filePath,
        });
      }
    }
  }

  return out;
}

const FRAGMENT_SHELL = (locale: string, title: string, body: string): string => `<!doctype html>
<html lang="${locale}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(title)}</title>
<link rel="stylesheet" href="/help-fragment.css">
</head>
<body class="help-fragment">
<article>
${body}
</article>
</body>
</html>
`;

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export async function buildHelpFragments(distDir: string): Promise<number> {
  const screens = await collectScreens();
  let written = 0;

  for (const screen of screens) {
    const slug = routeToSlug(screen.route);
    const outDir = join(distDir, screen.locale, "help");
    await mkdir(outDir, { recursive: true });
    const html = md.render(screen.body);
    // First H1 in the body is the title; fall back to module + route.
    const titleMatch = screen.body.match(/^#\s+(.+)$/m);
    const title = titleMatch
      ? titleMatch[1].trim()
      : `${screen.module} — ${screen.route}`;
    const out = FRAGMENT_SHELL(screen.locale, title, html);
    await writeFile(join(outDir, `${slug}.html`), out, "utf-8");
    written++;
  }

  return written;
}
