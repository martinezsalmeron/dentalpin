/**
 * Auto-generates the VitePress sidebar from the /docs filesystem.
 *
 * Scans the `srcDir` (i.e. `/docs`) at build time and produces one sidebar
 * tree per top-level section. Folders are walked recursively; markdown files
 * become leaves. README.md is hoisted as the section's overview link.
 *
 * The portal folder itself, image folders, and dotfiles are skipped.
 */
import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import type { DefaultTheme } from "vitepress";

type SidebarMulti = DefaultTheme.SidebarMulti;
type SidebarItem = DefaultTheme.SidebarItem;

// `__dirname` equivalent in ESM. .vitepress lives at docs/portal/.vitepress/,
// so the docs root is two levels up.
const HERE = fileURLToPath(new URL(".", import.meta.url));
const DOCS_ROOT = join(HERE, "..", "..");

/** Pretty labels for top-level sections. Anything missing falls back to titleCase. */
const SECTION_LABELS: Record<string, string> = {
  technical: "Technical reference",
  "user-manual": "User manual",
  modules: "Modules",
  adr: "Architecture decisions",
  features: "Features",
  workflows: "Workflows",
  checklists: "Checklists",
  diagrams: "Diagrams",
};

/** Order in the rendered sidebar; sections not listed are appended alphabetically. */
const SECTIONS_ORDER = [
  "user-manual",
  "technical",
  "modules",
  "features",
  "workflows",
  "adr",
  "checklists",
  "diagrams",
];

/** Folders never included in the sidebar (assets, build output, vitepress internals). */
const SKIP = new Set([
  "portal",
  "screenshots",
  "node_modules",
  ".vitepress",
  ".git",
]);

function titleFromName(raw: string): string {
  const stem = raw.replace(/\.md$/i, "");
  return stem
    .split(/[-_]/)
    .filter(Boolean)
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

/** Filename patterns excluded from the rendered build (kept in sync with
 *  `srcExclude` in `config.ts`). The sidebar walker must ignore them too,
 *  otherwise the sidebar would link to non-existent pages. */
function isExcludedFile(name: string): boolean {
  const lower = name.toLowerCase();
  return (
    lower === "template.md" ||
    lower.endsWith("-template.md") ||
    lower === "changelog.md"
  );
}

function listEntries(dir: string): string[] {
  try {
    return readdirSync(dir).sort();
  } catch {
    return [];
  }
}

/** Build the sidebar items for a single directory, recursing into subfolders. */
function walk(dir: string, urlPrefix: string): SidebarItem[] {
  const entries = listEntries(dir);
  const items: SidebarItem[] = [];

  // Hoist README.md as the section overview if present.
  if (entries.includes("README.md")) {
    items.push({ text: "Overview", link: `${urlPrefix}/` });
  }

  for (const name of entries) {
    if (name.startsWith(".") || SKIP.has(name)) continue;
    if (name.toLowerCase() === "readme.md") continue;

    const full = join(dir, name);
    let st: ReturnType<typeof statSync>;
    try {
      st = statSync(full);
    } catch {
      continue;
    }

    if (st.isDirectory()) {
      const children = walk(full, `${urlPrefix}/${name}`);
      if (!children.length) continue;
      items.push({
        text: titleFromName(name),
        items: children,
        collapsed: true,
      });
    } else if (name.toLowerCase().endsWith(".md")) {
      if (isExcludedFile(name)) continue;
      items.push({
        text: titleFromName(name),
        link: `${urlPrefix}/${name.replace(/\.md$/i, "")}`,
      });
    }
  }

  return items;
}

export function generateSidebar(): SidebarMulti {
  const sidebar: SidebarMulti = {};

  const sectionsOnDisk = listEntries(DOCS_ROOT)
    .filter((name) => !name.startsWith(".") && !SKIP.has(name))
    .filter((name) => {
      try {
        return statSync(join(DOCS_ROOT, name)).isDirectory();
      } catch {
        return false;
      }
    });

  const ordered = [
    ...SECTIONS_ORDER.filter((s) => sectionsOnDisk.includes(s)),
    ...sectionsOnDisk.filter((s) => !SECTIONS_ORDER.includes(s)).sort(),
  ];

  for (const section of ordered) {
    const dir = join(DOCS_ROOT, section);
    const items = walk(dir, `/${section}`);
    if (!items.length) continue;
    sidebar[`/${section}/`] = [
      {
        text: SECTION_LABELS[section] ?? titleFromName(section),
        items,
      },
    ];
  }

  return sidebar;
}

export function generateNav(): DefaultTheme.NavItem[] {
  const sectionsOnDisk = listEntries(DOCS_ROOT).filter(
    (name) =>
      !name.startsWith(".") &&
      !SKIP.has(name) &&
      (() => {
        try {
          return statSync(join(DOCS_ROOT, name)).isDirectory();
        } catch {
          return false;
        }
      })(),
  );

  const visible = ["user-manual", "technical", "modules", "adr"].filter((s) =>
    sectionsOnDisk.includes(s),
  );

  return visible.map((section) => ({
    text: SECTION_LABELS[section] ?? titleFromName(section),
    link: `/${section}/`,
  }));
}
