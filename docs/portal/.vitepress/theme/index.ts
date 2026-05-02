/**
 * Theme override that slots a stale-doc warning above the page body.
 *
 * The badge renders only when `transformPageData` (in `config.ts`) has set
 * `pageData.frontmatter.staleSince` for the current page.
 */
import DefaultTheme from "vitepress/theme";
import { h } from "vue";
import StaleBadge from "./StaleBadge.vue";
import type { Theme } from "vitepress";

export default {
  extends: DefaultTheme,
  Layout: () =>
    h(DefaultTheme.Layout, null, {
      "doc-before": () => h(StaleBadge),
    }),
} satisfies Theme;
