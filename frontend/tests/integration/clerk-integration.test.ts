/**
 * Integration tests for Clerk authentication with multi-tenancy
 * Tests school context injection, user metadata, and permissions
 */

import { describe, it, expect, beforeEach, vi, type MockedFunction } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { useUser, useAuth } from '@clerk/nextjs'
import { useAuth as useCustomAuth } from '@/hooks/useClerkAuth'

// Mock Clerk
vi.mock('@clerk/nextjs', () => ({
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="clerk-provider">{children}</div>,
  useUser: vi.fn(),
  useAuth: vi.fn(),
  useOrganization: vi.fn(),
}))

// Mock school context
vi.mock('@/hooks/useSchoolContext', () => ({
  useSchoolContext: vi.fn(),
}))

import { useSchoolContext } from '@/hooks/useSchoolContext'

const mockUseUser = useUser as MockedFunction<typeof useUser>
const mockUseAuth = useAuth as MockedFunction<typeof useAuth>
const mockUseSchoolContext = useSchoolContext as MockedFunction<typeof useSchoolContext>

// Test component for auth testing
function TestAuthComponent() {
  const { user, isLoaded, isSignedIn, hasPermission, hasFeature } = useCustomAuth()
  
  if (!isLoaded) return <div data-testid="loading">Loading...</div>
  if (!isSignedIn) return <div data-testid="signed-out">Not signed in</div>
  
  return (
    <div data-testid="user-info">
      <div data-testid="user-name">{user?.firstName} {user?.lastName}</div>
      <div data-testid="user-email">{user?.email}</div>
      <div data-testid="user-role">{user?.role}</div>
      <div data-testid="school-name">{user?.school_name}</div>
      <div data-testid="can-manage-finance">{hasPermission('finance:manage').toString()}</div>
      <div data-testid="has-finance-module">{hasFeature('finance_management').toString()}</div>
    </div>
  )
}

describe('Clerk Integration with Multi-Tenancy', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('User Authentication', () => {
    it('should load user with school context', async () => {
      const mockSchool = {
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        subscription_tier: 'professional',
        configuration: {
          features: {
            enabled_modules: ['sis', 'finance', 'academic']
          }
        }
      }

      const mockUser = {
        id: 'user-123',
        firstName: 'John',
        lastName: 'Doe',
        emailAddresses: [{ emailAddress: 'john.doe@peterhouse.oneclass.ac.zw' }],
        publicMetadata: {
          school_id: 'school-123',
          role: 'teacher',
          permissions: ['finance:manage', 'academic:read'],
          features: ['finance_management', 'academic_management']
        },
        lastSignInAt: new Date('2024-07-18').getTime(),
        createdAt: new Date('2024-01-15').getTime(),
        update: vi.fn()
      }

      mockUseUser.mockReturnValue({
        user: mockUser,
        isLoaded: true,
        isSignedIn: true
      })

      mockUseAuth.mockReturnValue({
        isLoaded: true,
        signOut: vi.fn()
      })

      mockUseSchoolContext.mockReturnValue({
        school: mockSchool,
        isLoading: false
      })

      render(<TestAuthComponent />)

      await waitFor(() => {
        expect(screen.getByTestId('user-name')).toHaveTextContent('John Doe')
        expect(screen.getByTestId('user-email')).toHaveTextContent('john.doe@peterhouse.oneclass.ac.zw')
        expect(screen.getByTestId('user-role')).toHaveTextContent('teacher')
        expect(screen.getByTestId('school-name')).toHaveTextContent('Peterhouse School')
        expect(screen.getByTestId('can-manage-finance')).toHaveTextContent('true')
        expect(screen.getByTestId('has-finance-module')).toHaveTextContent('true')
      })
    })

    it('should handle user without school metadata', async () => {
      const mockSchool = {
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        subscription_tier: 'basic',
        configuration: {
          features: {
            enabled_modules: ['sis']
          }
        }
      }

      const mockUser = {
        id: 'user-123',
        firstName: 'Jane',
        lastName: 'Smith',
        emailAddresses: [{ emailAddress: 'jane.smith@example.com' }],
        publicMetadata: {}, // No school metadata
        update: vi.fn().mockResolvedValue(undefined)
      }

      mockUseUser.mockReturnValue({
        user: mockUser,
        isLoaded: true,
        isSignedIn: true
      })

      mockUseAuth.mockReturnValue({
        isLoaded: true,
        signOut: vi.fn()
      })

      mockUseSchoolContext.mockReturnValue({
        school: mockSchool,
        isLoading: false
      })

      render(<TestAuthComponent />)

      await waitFor(() => {
        expect(screen.getByTestId('user-name')).toHaveTextContent('Jane Smith')
        expect(screen.getByTestId('school-name')).toHaveTextContent('Peterhouse School')
      })

      // Should update user metadata with school context
      expect(mockUser.update).toHaveBeenCalledWith({
        publicMetadata: {
          school_id: 'school-123',
          school_name: 'Peterhouse School',
          subdomain: 'peterhouse'
        }
      })
    })

    it('should reject user from wrong school', async () => {
      const mockSchool = {
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse'
      }

      const mockUser = {
        id: 'user-123',
        firstName: 'Wrong',
        lastName: 'User',
        emailAddresses: [{ emailAddress: 'wrong@otherschool.com' }],
        publicMetadata: {
          school_id: 'different-school-456', // Different school
          role: 'teacher'
        }
      }

      const mockSignOut = vi.fn()
      const mockPush = vi.fn()

      mockUseUser.mockReturnValue({
        user: mockUser,
        isLoaded: true,
        isSignedIn: true
      })

      mockUseAuth.mockReturnValue({
        isLoaded: true,
        signOut: mockSignOut
      })

      mockUseSchoolContext.mockReturnValue({
        school: mockSchool,
        isLoading: false
      })

      // Mock router
      vi.mock('next/navigation', () => ({
        useRouter: () => ({ push: mockPush })
      }))

      render(<TestAuthComponent />)

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled()
        expect(mockPush).toHaveBeenCalledWith('/unauthorized?error=wrong_school')
      })
    })
  })

  describe('Permission System', () => {
    it('should check permissions correctly for different roles', async () => {
      const testCases = [
        {
          role: 'platform_admin',
          permissions: [],
          expectedFinanceAccess: true, // Platform admin has all permissions
          description: 'platform admin'
        },
        {
          role: 'admin',
          permissions: ['school:manage'],
          expectedFinanceAccess: true, // School admin has school-level permissions
          description: 'school admin'
        },
        {
          role: 'teacher',
          permissions: ['finance:manage'],
          expectedFinanceAccess: true,
          description: 'teacher with finance permission'
        },
        {
          role: 'teacher',
          permissions: ['academic:read'],
          expectedFinanceAccess: false,
          description: 'teacher without finance permission'
        }
      ]

      for (const testCase of testCases) {
        const mockSchool = {
          id: 'school-123',
          name: 'Test School',
          subdomain: 'test',
          subscription_tier: 'professional',
          configuration: {
            features: {
              enabled_modules: ['finance_management']
            }
          }
        }

        const mockUser = {
          id: 'user-123',
          firstName: 'Test',
          lastName: 'User',
          emailAddresses: [{ emailAddress: 'test@test.com' }],
          publicMetadata: {
            school_id: 'school-123',
            role: testCase.role,
            permissions: testCase.permissions,
            features: ['finance_management']
          },
          update: vi.fn()
        }

        mockUseUser.mockReturnValue({
          user: mockUser,
          isLoaded: true,
          isSignedIn: true
        })

        mockUseSchoolContext.mockReturnValue({
          school: mockSchool,
          isLoading: false
        })

        const { unmount } = render(<TestAuthComponent />)

        await waitFor(() => {
          expect(screen.getByTestId('can-manage-finance')).toHaveTextContent(
            testCase.expectedFinanceAccess.toString()
          )
        })

        unmount()
      }
    })
  })

  describe('Feature Gates', () => {
    it('should check feature availability based on subscription tier', async () => {
      const testCases = [
        {
          tier: 'basic',
          modules: ['sis'],
          feature: 'finance_management',
          expected: false,
          description: 'basic tier without finance module'
        },
        {
          tier: 'professional', 
          modules: ['sis', 'finance_management'],
          feature: 'finance_management',
          expected: true,
          description: 'professional tier with finance module'
        },
        {
          tier: 'enterprise',
          modules: ['sis', 'finance_management', 'advanced_reporting'],
          feature: 'advanced_reporting',
          expected: true,
          description: 'enterprise tier with advanced features'
        }
      ]

      for (const testCase of testCases) {
        const mockSchool = {
          id: 'school-123',
          name: 'Test School',
          subdomain: 'test',
          subscription_tier: testCase.tier,
          configuration: {
            features: {
              enabled_modules: testCase.modules
            }
          }
        }

        const mockUser = {
          id: 'user-123',
          firstName: 'Test',
          lastName: 'User',
          emailAddresses: [{ emailAddress: 'test@test.com' }],
          publicMetadata: {
            school_id: 'school-123',
            role: 'admin',
            permissions: ['finance:manage'],
            features: testCase.modules
          },
          update: vi.fn()
        }

        mockUseUser.mockReturnValue({
          user: mockUser,
          isLoaded: true,
          isSignedIn: true
        })

        mockUseSchoolContext.mockReturnValue({
          school: mockSchool,
          isLoading: false
        })

        const { unmount } = render(<TestAuthComponent />)

        await waitFor(() => {
          expect(screen.getByTestId('has-finance-module')).toHaveTextContent(
            testCase.expected.toString()
          )
        })

        unmount()
      }
    })
  })

  describe('Loading States', () => {
    it('should show loading state while auth is loading', () => {
      mockUseUser.mockReturnValue({
        user: null,
        isLoaded: false,
        isSignedIn: false
      })

      mockUseAuth.mockReturnValue({
        isLoaded: false,
        signOut: vi.fn()
      })

      mockUseSchoolContext.mockReturnValue({
        school: null,
        isLoading: true
      })

      render(<TestAuthComponent />)

      expect(screen.getByTestId('loading')).toBeInTheDocument()
    })

    it('should show signed out state when not authenticated', () => {
      mockUseUser.mockReturnValue({
        user: null,
        isLoaded: true,
        isSignedIn: false
      })

      mockUseAuth.mockReturnValue({
        isLoaded: true,
        signOut: vi.fn()
      })

      mockUseSchoolContext.mockReturnValue({
        school: null,
        isLoading: false
      })

      render(<TestAuthComponent />)

      expect(screen.getByTestId('signed-out')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const mockSchool = {
        id: 'school-123',
        name: 'Test School',
        subdomain: 'test'
      }

      const mockUser = {
        id: 'user-123',
        firstName: 'Test',
        lastName: 'User',
        emailAddresses: [{ emailAddress: 'test@test.com' }],
        publicMetadata: {
          school_id: 'school-123',
          role: 'teacher'
        },
        update: vi.fn().mockRejectedValue(new Error('API Error'))
      }

      mockUseUser.mockReturnValue({
        user: mockUser,
        isLoaded: true,
        isSignedIn: true
      })

      mockUseAuth.mockReturnValue({
        isLoaded: true,
        signOut: vi.fn()
      })

      mockUseSchoolContext.mockReturnValue({
        school: mockSchool,
        isLoading: false
      })

      // Should not throw error, should handle gracefully
      expect(() => render(<TestAuthComponent />)).not.toThrow()
    })
  })
})