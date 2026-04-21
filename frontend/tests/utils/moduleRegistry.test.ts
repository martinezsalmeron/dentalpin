import { describe, expect, it } from 'vitest'

// Tests the static fallback registry in `~/utils/moduleRegistry`.
// In normal runtime the sidebar is backend-driven via
// `GET /api/v1/modules/-/active`; this registry is only consulted if
// that fetch fails. Post Fase B the registry registers two entries:
// `host` (dashboard + settings) and `clinical` (the full nav tree).

describe('moduleRegistry', () => {
  describe('getModules', () => {
    it('should return registered modules', async () => {
      const { getModules } = await import('~/utils/moduleRegistry')

      const modules = getModules()
      expect(modules).toBeDefined()
      expect(Array.isArray(modules)).toBe(true)
      expect(modules.length).toBeGreaterThanOrEqual(2)
    })

    it('should include host module with dashboard + settings', async () => {
      const { getModules } = await import('~/utils/moduleRegistry')

      const modules = getModules()
      const host = modules.find(m => m.name === 'host')

      expect(host).toBeDefined()
      const paths = host?.navigation.map(n => n.to) ?? []
      expect(paths).toContain('/')
      expect(paths).toContain('/settings')
    })

    it('should include clinical module with patients + appointments', async () => {
      const { getModules } = await import('~/utils/moduleRegistry')

      const modules = getModules()
      const clinical = modules.find(m => m.name === 'clinical')

      expect(clinical).toBeDefined()
      expect(clinical?.navigation.length).toBeGreaterThan(0)
      const paths = clinical?.navigation.map(n => n.to) ?? []
      expect(paths).toContain('/patients')
      expect(paths).toContain('/appointments')
    })
  })

  describe('getNavigationItems', () => {
    it('should return navigation items from all modules', async () => {
      const { getNavigationItems } = await import('~/utils/moduleRegistry')

      const navItems = getNavigationItems()
      expect(navItems).toBeDefined()
      expect(Array.isArray(navItems)).toBe(true)
      expect(navItems.length).toBeGreaterThan(0)
    })

    it('should include dashboard navigation', async () => {
      const { getNavigationItems } = await import('~/utils/moduleRegistry')

      const navItems = getNavigationItems()
      const dashboard = navItems.find(item => item.to === '/')

      expect(dashboard).toBeDefined()
      expect(dashboard?.icon).toBe('i-lucide-home')
    })

    it('should include patients navigation', async () => {
      const { getNavigationItems } = await import('~/utils/moduleRegistry')

      const navItems = getNavigationItems()
      const patients = navItems.find(item => item.to === '/patients')

      expect(patients).toBeDefined()
      expect(patients?.icon).toBe('i-lucide-users')
    })
  })

  describe('registerModule', () => {
    it('should not register duplicate modules', async () => {
      const { registerModule, getModules } = await import('~/utils/moduleRegistry')

      const initialCount = getModules().length

      // Try to register a duplicate
      registerModule({
        name: 'clinical',
        label: 'Duplicate Clinical',
        icon: 'i-lucide-test',
        navigation: []
      })

      // Count should remain the same
      expect(getModules().length).toBe(initialCount)
    })
  })
})
