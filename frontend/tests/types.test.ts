import { describe, expect, it } from 'vitest'
import type { User, Patient, Appointment, NavigationItem, ModuleDefinition } from '~/types'

describe('Type definitions', () => {
  describe('User type', () => {
    it('should allow valid user object', () => {
      const user: User = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        is_active: true
      }

      expect(user.id).toBeDefined()
      expect(user.email).toContain('@')
      expect(user.is_active).toBe(true)
    })

    it('should allow optional fields', () => {
      const user: User = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        is_active: true,
        professional_id: 'COL12345'
      }

      expect(user.professional_id).toBe('COL12345')
    })
  })

  describe('Patient type', () => {
    it('should allow valid patient object', () => {
      const patient: Patient = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        clinic_id: '123e4567-e89b-12d3-a456-426614174001',
        first_name: 'Maria',
        last_name: 'Garcia',
        status: 'active',
        consent_signed: false,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z'
      }

      expect(patient.first_name).toBe('Maria')
      expect(patient.status).toBe('active')
    })

    it('should allow medical history', () => {
      const patient: Patient = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        clinic_id: '123e4567-e89b-12d3-a456-426614174001',
        first_name: 'Juan',
        last_name: 'Lopez',
        status: 'active',
        consent_signed: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        medical_history: {
          allergies: ['penicillin'],
          medications: ['aspirin'],
          conditions: ['diabetes'],
          notes: 'Patient has controlled diabetes'
        }
      }

      expect(patient.medical_history?.allergies).toContain('penicillin')
    })
  })

  describe('Appointment type', () => {
    it('should allow valid appointment object', () => {
      const appointment: Appointment = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        clinic_id: '123e4567-e89b-12d3-a456-426614174001',
        professional_id: '123e4567-e89b-12d3-a456-426614174002',
        cabinet: 'Gabinete 1',
        start_time: '2026-04-01T10:00:00Z',
        end_time: '2026-04-01T10:30:00Z',
        status: 'scheduled'
      }

      expect(appointment.cabinet).toBe('Gabinete 1')
      expect(appointment.status).toBe('scheduled')
    })

    it('should allow different statuses', () => {
      const statuses: Appointment['status'][] = [
        'scheduled',
        'confirmed',
        'in_progress',
        'completed',
        'cancelled',
        'no_show'
      ]

      statuses.forEach((status) => {
        const appointment: Appointment = {
          id: '123',
          clinic_id: '123',
          professional_id: '123',
          cabinet: 'Gabinete 1',
          start_time: '2026-04-01T10:00:00Z',
          end_time: '2026-04-01T10:30:00Z',
          status
        }
        expect(appointment.status).toBe(status)
      })
    })
  })

  describe('NavigationItem type', () => {
    it('should allow valid navigation item', () => {
      const navItem: NavigationItem = {
        label: 'nav.dashboard',
        icon: 'i-lucide-home',
        to: '/'
      }

      expect(navItem.label).toBe('nav.dashboard')
      expect(navItem.icon).toContain('i-lucide')
      expect(navItem.to).toBe('/')
    })
  })

  describe('ModuleDefinition type', () => {
    it('should allow valid module definition', () => {
      const module: ModuleDefinition = {
        name: 'test-module',
        label: 'Test Module',
        icon: 'i-lucide-test',
        navigation: [
          { label: 'Test', icon: 'i-lucide-test', to: '/test' }
        ]
      }

      expect(module.name).toBe('test-module')
      expect(module.navigation).toHaveLength(1)
    })
  })
})
