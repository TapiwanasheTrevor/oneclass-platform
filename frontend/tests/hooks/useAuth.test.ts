/**
 * Tests for useAuth and related authentication hooks
 * Comprehensive testing of authentication state management
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi, type MockedFunction } from 'vitest'
import { useAuth } from '@/hooks/useAuth'
import { useClerkAuth } from '@/hooks/useClerkAuth'
import { useSchoolContext } from '@/hooks/useSchoolContext'

// Mock dependencies
vi.mock('@/hooks/useClerkAuth')
vi.mock('@/hooks/useSchoolContext')
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/dashboard'
  })
}))

const mockUseClerkAuth = useClerkAuth as MockedFunction<typeof useClerkAuth>
const mockUseSchoolContext = useSchoolContext as MockedFunction<typeof useSchoolContext>

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Authentication States', () => {
    it('should return loading state initially', () => {
      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: true
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: true
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.loading).toBe(true)
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })

    it('should return authenticated state with user data', () => {
      const mockUser = {
        id: 'user-123',
        email: 'teacher@peterhouse.ac.zw',
        fullName: 'John Doe',
        role: 'teacher',
        permissions: ['sis:read', 'academic:write'],
        schoolId: 'school-123'
      }

      const mockSchoolContext = {
        school_id: 'school-123',
        school_name: 'Peterhouse School',
        school_code: 'PETERHOUSE',
        subscription_tier: 'professional',
        enabled_modules: ['sis', 'academic', 'finance']
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        schoolContext: mockSchoolContext,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: mockSchoolContext,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn((module) => mockSchoolContext.enabled_modules.includes(module)),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.loading).toBe(false)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.schoolContext).toEqual(mockSchoolContext)
    })

    it('should return unauthenticated state', () => {
      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.loading).toBe(false)
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(result.current.schoolContext).toBeNull()
    })
  })

  describe('Permission Checks', () => {
    it('should check user permissions correctly', () => {
      const mockUser = {
        id: 'user-123',
        email: 'teacher@school.com',
        fullName: 'Teacher User',
        role: 'teacher',
        permissions: ['sis:read', 'academic:write', 'attendance:mark'],
        schoolId: 'school-123'
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasPermission('sis:read')).toBe(true)
      expect(result.current.hasPermission('academic:write')).toBe(true)
      expect(result.current.hasPermission('attendance:mark')).toBe(true)
      expect(result.current.hasPermission('finance:write')).toBe(false)
      expect(result.current.hasPermission('settings:admin')).toBe(false)
    })

    it('should grant all permissions to super admin', () => {
      const mockUser = {
        id: 'user-123',
        email: 'admin@platform.com',
        fullName: 'Super Admin',
        role: 'super_admin',
        permissions: ['*'],
        schoolId: '*'
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasPermission('any:permission')).toBe(true)
      expect(result.current.hasPermission('finance:delete')).toBe(true)
      expect(result.current.hasPermission('settings:admin')).toBe(true)
    })

    it('should return false for permissions when not authenticated', () => {
      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasPermission('sis:read')).toBe(false)
      expect(result.current.hasPermission('any:permission')).toBe(false)
    })
  })

  describe('Role Checks', () => {
    it('should identify admin roles correctly', () => {
      const testCases = [
        { role: 'super_admin', expectedIsAdmin: true },
        { role: 'platform_admin', expectedIsAdmin: true },
        { role: 'school_admin', expectedIsAdmin: true },
        { role: 'admin', expectedIsAdmin: true },
        { role: 'teacher', expectedIsAdmin: false },
        { role: 'student', expectedIsAdmin: false },
        { role: 'parent', expectedIsAdmin: false }
      ]

      testCases.forEach(({ role, expectedIsAdmin }) => {
        const mockUser = {
          id: 'user-123',
          email: 'user@school.com',
          fullName: 'Test User',
          role,
          permissions: [],
          schoolId: 'school-123'
        }

        mockUseClerkAuth.mockReturnValue({
          isAuthenticated: true,
          user: mockUser,
          schoolContext: null,
          signIn: vi.fn(),
          signOut: vi.fn(),
          loading: false
        })

        const { result } = renderHook(() => useAuth())
        expect(result.current.isAdmin).toBe(expectedIsAdmin)
      })
    })

    it('should check specific roles correctly', () => {
      const mockUser = {
        id: 'user-123',
        email: 'teacher@school.com',
        fullName: 'Teacher User',
        role: 'teacher',
        permissions: [],
        schoolId: 'school-123'
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasRole('teacher')).toBe(true)
      expect(result.current.hasRole('admin')).toBe(false)
      expect(result.current.hasRole('student')).toBe(false)
    })
  })

  describe('Feature Access', () => {
    it('should check feature access based on school modules', () => {
      const mockSchoolContext = {
        school_id: 'school-123',
        school_name: 'Test School',
        school_code: 'TEST',
        subscription_tier: 'professional',
        enabled_modules: ['sis', 'academic', 'finance']
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: {
          id: 'user-123',
          email: 'user@school.com',
          fullName: 'Test User',
          role: 'teacher',
          permissions: [],
          schoolId: 'school-123'
        },
        schoolContext: mockSchoolContext,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: mockSchoolContext,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn((module) => mockSchoolContext.enabled_modules.includes(module)),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasFeature('sis')).toBe(true)
      expect(result.current.hasFeature('academic')).toBe(true)
      expect(result.current.hasFeature('finance')).toBe(true)
      expect(result.current.hasFeature('advanced_reporting')).toBe(false)
    })

    it('should return false for features when not authenticated', () => {
      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasFeature('sis')).toBe(false)
      expect(result.current.hasFeature('finance')).toBe(false)
    })
  })

  describe('Authentication Actions', () => {
    it('should call signIn function', async () => {
      const mockSignIn = vi.fn()

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: mockSignIn,
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.signIn({ email: 'test@school.com', password: 'password' })
      })

      expect(mockSignIn).toHaveBeenCalledWith({ email: 'test@school.com', password: 'password' })
    })

    it('should call signOut function', async () => {
      const mockSignOut = vi.fn()

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: {
          id: 'user-123',
          email: 'user@school.com',
          fullName: 'Test User',
          role: 'teacher',
          permissions: [],
          schoolId: 'school-123'
        },
        schoolContext: null,
        signIn: vi.fn(),
        signOut: mockSignOut,
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.signOut()
      })

      expect(mockSignOut).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle authentication errors gracefully', async () => {
      const mockSignIn = vi.fn().mockRejectedValue(new Error('Invalid credentials'))

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: mockSignIn,
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      await expect(async () => {
        await act(async () => {
          await result.current.signIn({ email: 'test@school.com', password: 'wrong' })
        })
      }).rejects.toThrow('Invalid credentials')
    })

    it('should handle missing user data gracefully', () => {
      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: null, // User data missing
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.isAuthenticated).toBe(false) // Should fall back to false
      expect(result.current.hasPermission('any:permission')).toBe(false)
      expect(result.current.isAdmin).toBe(false)
    })
  })

  describe('State Updates', () => {
    it('should update when authentication state changes', async () => {
      const mockSignIn = vi.fn()
      let authState = {
        isAuthenticated: false,
        user: null,
        schoolContext: null,
        signIn: mockSignIn,
        signOut: vi.fn(),
        loading: false
      }

      mockUseClerkAuth.mockImplementation(() => authState)
      mockUseSchoolContext.mockReturnValue({
        schoolContext: null,
        updateSchoolContext: vi.fn(),
        hasModule: vi.fn(),
        loading: false
      })

      const { result, rerender } = renderHook(() => useAuth())

      expect(result.current.isAuthenticated).toBe(false)

      // Simulate successful authentication
      authState = {
        isAuthenticated: true,
        user: {
          id: 'user-123',
          email: 'user@school.com',
          fullName: 'Test User',
          role: 'teacher',
          permissions: ['sis:read'],
          schoolId: 'school-123'
        },
        schoolContext: null,
        signIn: mockSignIn,
        signOut: vi.fn(),
        loading: false
      }

      rerender()

      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user?.id).toBe('user-123')
    })
  })

  describe('Complex Permission Scenarios', () => {
    it('should handle multiple permission formats', () => {
      const mockUser = {
        id: 'user-123',
        email: 'user@school.com',
        fullName: 'Test User',
        role: 'teacher',
        permissions: [
          'sis:read',
          'sis:write:own_classes',
          'academic:*',
          'finance:read:reports'
        ],
        schoolId: 'school-123'
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.hasPermission('sis:read')).toBe(true)
      expect(result.current.hasPermission('sis:write:own_classes')).toBe(true)
      expect(result.current.hasPermission('academic:read')).toBe(true) // Should match academic:*
      expect(result.current.hasPermission('academic:write')).toBe(true) // Should match academic:*
      expect(result.current.hasPermission('finance:read:reports')).toBe(true)
      expect(result.current.hasPermission('finance:write')).toBe(false)
    })

    it('should handle role-based permission inheritance', () => {
      const mockUser = {
        id: 'user-123',
        email: 'admin@school.com',
        fullName: 'School Admin',
        role: 'school_admin',
        permissions: ['school:*'], // School admin has all school permissions
        schoolId: 'school-123'
      }

      mockUseClerkAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        schoolContext: null,
        signIn: vi.fn(),
        signOut: vi.fn(),
        loading: false
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.isAdmin).toBe(true)
      expect(result.current.hasPermission('sis:read')).toBe(true) // Should inherit from school:*
      expect(result.current.hasPermission('finance:manage')).toBe(true)
      expect(result.current.hasPermission('settings:update')).toBe(true)
    })
  })
})