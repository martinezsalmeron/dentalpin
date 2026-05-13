// Nuxt layer for the `payments` module.
//
// Issue #53. Pages live under ./pages, components under ./components
// with no folder-prefix so cross-layer auto-imports resolve.
export default defineNuxtConfig({
  components: [
    { path: './components', pathPrefix: false }
  ]
})
