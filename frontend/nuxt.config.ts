// https://nuxt.com/docs/api/configuration/nuxt-config
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * Load Nuxt Layer paths from `modules.json`.
 *
 * The backend writes this file whenever a module with a declared
 * `manifest.frontend.layer_path` is installed. When absent (fresh
 * checkout, no community modules yet), returns an empty array.
 */
function loadModuleLayers(): string[] {
  const path = resolve(__dirname, 'modules.json')
  try {
    const raw = readFileSync(path, 'utf-8')
    const payload = JSON.parse(raw) as { layers?: string[] }
    return Array.isArray(payload.layers) ? payload.layers : []
  } catch (err: unknown) {
    const code = (err as { code?: string }).code
    if (code !== 'ENOENT') {
      // eslint-disable-next-line no-console
      console.warn('[nuxt.config] modules.json is malformed, using empty layers:', err)
    }
    return []
  }
}

const moduleLayers = loadModuleLayers()

export default defineNuxtConfig({

  extends: moduleLayers,

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@nuxtjs/i18n'
  ],

  components: [
    {
      path: '~/components',
      pathPrefix: false
    }
  ],

  devtools: {
    enabled: true
  },
  app: {
    head: {
      title: 'DentalPin',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }
      ]
    }
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    // Server-side only (for SSR inside Docker)
    apiBaseUrlServer: process.env.API_BASE_URL_SERVER || 'http://backend:8000',
    public: {
      // Client-side (browser)
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000'
    }
  },
  srcDir: 'app',

  compatibilityDate: '2025-01-15',

  vite: {
    optimizeDeps: {
      include: ['nprogress']
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

  i18n: {
    locales: [
      { code: 'en', name: 'English', file: 'en.json' },
      { code: 'es', name: 'Español', file: 'es.json' }
    ],
    defaultLocale: 'en',
    lazy: true,
    langDir: 'locales',
    strategy: 'no_prefix',
    detectBrowserLanguage: false
  }
})
