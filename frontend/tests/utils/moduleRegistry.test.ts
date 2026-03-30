import { describe, expect, it, beforeEach } from 'vitest'

// We need to test the module registry logic without side effects from the actual registration
// So we'll test the logic in isolation

describe('moduleRegistry', () => {
  describe('getModules', () => {
    it('should return registered modules', async () => {
      const { getModules } = await import('~/utils/moduleRegistry')

      const modules = getModules()
      expect(modules).toBeDefined()
      expect(Array.isArray(modules)).toBe(true)
      // Clinical and settings modules are registered by default
      expect(modules.length).toBeGreaterThanOrEqual(2)
    })

    it('should include clinical module', async () => {
      const { getModules } = await import('~/utils/moduleRegistry')

      const modules = getModules()
      const clinical = modules.find(m => m.name === 'clinical')

      expect(clinical).toBeDefined()
      expect(clinical?.label).toBe('Clínico')
      expect(clinical?.navigation.length).toBeGreaterThan(0)
    })

    it('should include settings module', async () => {
      const { getModules } = await import('~/utils/moduleRegistry')

      const modules = getModules()
      const settings = modules.find(m => m.name === 'settings')

      expect(settings).toBeDefined()
      expect(settings?.label).toBe('Configuración')
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
