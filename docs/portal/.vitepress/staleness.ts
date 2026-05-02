/**
 * Stale-doc detection for the portal.
 *
 * For each markdown page with a `last_verified_commit` in its frontmatter,
 * we compute the set of code paths the doc claims to describe and ask git
 * whether anything has changed under those paths since the verified SHA.
 *
 * Path inference:
 *  1. If frontmatter declares `related_paths`, use those verbatim.
 *  2. Otherwise fall back to `backend/app/modules/<module>/` when the
 *     frontmatter declares a `module` (typical case for the screen MDs).
 *  3. Always include the doc file itself — if the doc was edited the
 *     author should have bumped the SHA.
 *
 * Output is consumed by `transformPageData` in `config.ts`, which mutates
 * `pageData.frontmatter.staleSince` / `staleDiffUrl` so the
 * `StaleBadge.vue` component can render the warning.
 */
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve, relative } from "node:path";

const HERE = fileURLToPath(new URL(".", import.meta.url));
// docs/portal/.vitepress/ → repo root is two levels above docs/.
const REPO_ROOT = resolve(HERE, "..", "..", "..");

const GH_REPO = "https://github.com/martinezsalmeron/dentalpin";

const GIT_LOG_CACHE = new Map<string, string[]>();

function runGit(args: string[]): string[] {
  const key = args.join("\u0000");
  const cached = GIT_LOG_CACHE.get(key);
  if (cached) return cached;
  try {
    const out = execFileSync("git", args, {
      cwd: REPO_ROOT,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    const lines = out.split("\n").filter(Boolean);
    GIT_LOG_CACHE.set(key, lines);
    return lines;
  } catch {
    GIT_LOG_CACHE.set(key, []);
    return [];
  }
}

export interface StalenessResult {
  stale: boolean;
  staleCommits: number;
  diffUrl: string | null;
  verifiedSha: string;
}

function asArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((v): v is string => typeof v === "string");
  return [];
}

function inferRelatedPaths(
  frontmatter: Record<string, unknown>,
  absolutePagePath: string,
): string[] {
  const paths = new Set<string>();

  const explicit = asArray(frontmatter.related_paths);
  if (explicit.length) {
    for (const p of explicit) paths.add(p);
  } else if (typeof frontmatter.module === "string") {
    paths.add(`backend/app/modules/${frontmatter.module}/`);
  }

  // The doc itself: bumping `last_verified_commit` should be required when
  // the doc body is edited too.
  try {
    paths.add(relative(REPO_ROOT, absolutePagePath));
  } catch {
    // Out-of-tree page — skip.
  }

  return Array.from(paths);
}

export function checkStale(
  frontmatter: Record<string, unknown>,
  absolutePagePath: string,
): StalenessResult | null {
  const sha = typeof frontmatter.last_verified_commit === "string"
    ? frontmatter.last_verified_commit.trim()
    : null;
  if (!sha) return null;

  const relatedPaths = inferRelatedPaths(frontmatter, absolutePagePath);
  if (!relatedPaths.length) return null;

  // Validate the SHA exists locally — shallow clones (CI) may lack history.
  const sanity = runGit(["rev-parse", "--verify", `${sha}^{commit}`]);
  if (!sanity.length) {
    return { stale: false, staleCommits: 0, diffUrl: null, verifiedSha: sha };
  }

  const lines = runGit(["log", "--oneline", `${sha}..HEAD`, "--", ...relatedPaths]);
  if (!lines.length) {
    return { stale: false, staleCommits: 0, diffUrl: null, verifiedSha: sha };
  }

  return {
    stale: true,
    staleCommits: lines.length,
    diffUrl: `${GH_REPO}/compare/${sha}...HEAD`,
    verifiedSha: sha,
  };
}
