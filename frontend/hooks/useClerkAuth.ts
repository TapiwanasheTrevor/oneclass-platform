/**
 * Clerk Authentication Hook with Multi-Tenant Support
 * Integrates Clerk authentication with school context and permissions
 */

import { useUser, useAuth as useClerkAuth, useOrganization } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useSchoolContext } from './useSchoolContext'
import { toast } from 'sonner'

export interface UserWithSchoolContext {
  id: string
  email: string
  firstName: string
  lastName: string
  role: string
  permissions: string[]
  features: string[]
  school_id: string
  school_name: string
  subscription_tier: string
  lastSignIn?: Date
  createdAt: Date
}

export interface AuthState {
  user: UserWithSchoolContext | null
  isLoaded: boolean
  isSignedIn: boolean
  isLoading: boolean
  error: string | null
}

export function useAuth(): AuthState & {
  signOut: () => Promise<void>
  updateUserMetadata: (metadata: Record<string, any>) => Promise<void>
  hasPermission: (permission: string) => boolean
  hasFeature: (feature: string) => boolean
  checkSchoolAccess: () => Promise<boolean>
} {
  const { user, isLoaded: userLoaded, isSignedIn } = useUser()
  const { signOut: clerkSignOut, isLoaded: authLoaded } = useClerkAuth()
  const { organization } = useOrganization()
  const { school, isLoading: schoolLoading } = useSchoolContext()
  const router = useRouter()
  
  const [authUser, setAuthUser] = useState<UserWithSchoolContext | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const isLoaded = userLoaded && authLoaded && !schoolLoading
  
  // Transform Clerk user to our user format with school context
  useEffect(() => {
    const transformUser = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        if (!user || !isSignedIn || !school) {
          setAuthUser(null)
          return
        }
        
        // Validate user belongs to the current school
        const userSchoolId = user.publicMetadata?.school_id as string
        if (userSchoolId && userSchoolId !== school.id) {
          setError('User does not belong to this school')
          await clerkSignOut()
          router.push('/unauthorized?error=wrong_school')
          return
        }
        
        // Get user role and permissions from metadata
        const role = user.publicMetadata?.role as string || 'student'
        const permissions = user.publicMetadata?.permissions as string[] || []
        const features = user.publicMetadata?.features as string[] || []
        
        // Create user object with school context
        const userWithContext: UserWithSchoolContext = {
          id: user.id,
          email: user.emailAddresses[0]?.emailAddress || '',
          firstName: user.firstName || '',
          lastName: user.lastName || '',
          role,
          permissions,
          features,
          school_id: school.id,
          school_name: school.name,
          subscription_tier: school.subscription_tier || 'basic',
          lastSignIn: user.lastSignInAt ? new Date(user.lastSignInAt) : undefined,
          createdAt: new Date(user.createdAt),
        }
        
        setAuthUser(userWithContext)
        
        // Update user metadata with current school context if missing
        if (!userSchoolId) {
          await user.update({
            publicMetadata: {
              ...user.publicMetadata,
              school_id: school.id,
              school_name: school.name,
              subdomain: school.subdomain,
            },
          })
        }
        
      } catch (err) {
        console.error('Error transforming user:', err)
        setError('Failed to load user information')
      } finally {
        setIsLoading(false)
      }
    }
    
    if (isLoaded) {
      transformUser()
    }
  }, [user, isSignedIn, school, isLoaded, clerkSignOut, router])
  
  // Sign out function
  const signOut = async () => {
    try {
      await clerkSignOut()
      setAuthUser(null)
      router.push('/sign-in')
      toast.success('Signed out successfully')
    } catch (err) {
      console.error('Sign out error:', err)
      toast.error('Failed to sign out')
    }
  }
  
  // Update user metadata
  const updateUserMetadata = async (metadata: Record<string, any>) => {
    try {
      if (!user) throw new Error('No user found')
      
      await user.update({
        publicMetadata: {
          ...user.publicMetadata,
          ...metadata,
        },
      })
      
      toast.success('Profile updated successfully')
    } catch (err) {
      console.error('Update metadata error:', err)
      toast.error('Failed to update profile')
      throw err
    }
  }
  
  // Check if user has specific permission
  const hasPermission = (permission: string): boolean => {
    if (!authUser) return false
    
    // Platform admins have all permissions
    if (authUser.role === 'platform_admin') return true
    
    // School admins have all school-level permissions
    if (authUser.role === 'admin') {
      return !permission.startsWith('platform:')
    }
    
    return authUser.permissions.includes(permission)
  }
  
  // Check if user has access to specific feature
  const hasFeature = (feature: string): boolean => {
    if (!authUser || !school) return false
    
    // Check if feature is enabled for the school
    const schoolFeatures = school.configuration?.features?.enabled_modules || []
    if (!schoolFeatures.includes(feature)) return false
    
    // Check if user has access to the feature
    return authUser.features.includes(feature) || authUser.role === 'admin'
  }
  
  // Check if user has access to current school
  const checkSchoolAccess = async (): Promise<boolean> => {
    if (!authUser || !school) return false
    
    try {
      // Verify user's school access
      const response = await fetch('/api/auth/verify-school-access', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: authUser.id,
          school_id: school.id,
        }),
      })
      
      return response.ok
    } catch (err) {
      console.error('School access check failed:', err)
      return false
    }
  }
  
  return {
    user: authUser,
    isLoaded,
    isSignedIn: Boolean(authUser),
    isLoading,
    error,
    signOut,
    updateUserMetadata,
    hasPermission,
    hasFeature,
    checkSchoolAccess,
  }
}

/**
 * Hook for role-based access control
 */
export function useRoleAccess() {
  const { user, hasPermission, hasFeature } = useAuth()
  
  const roles = {
    isPlatformAdmin: user?.role === 'platform_admin',
    isSchoolAdmin: user?.role === 'admin',
    isTeacher: user?.role === 'teacher',
    isStudent: user?.role === 'student',
    isParent: user?.role === 'parent',
    isStaff: ['admin', 'teacher', 'staff'].includes(user?.role || ''),
  }
  
  const permissions = {
    canManageSchool: hasPermission('school:manage'),
    canManageUsers: hasPermission('users:manage'),
    canManageFinance: hasPermission('finance:manage'),
    canViewFinance: hasPermission('finance:read'),
    canManageAcademic: hasPermission('academic:manage'),
    canViewAcademic: hasPermission('academic:read'),
    canManageSIS: hasPermission('sis:manage'),
    canViewSIS: hasPermission('sis:read'),
  }
  
  const features = {
    hasFinanceModule: hasFeature('finance_management'),
    hasAcademicModule: hasFeature('academic_management'),
    hasSISModule: hasFeature('student_information_system'),
    hasReportingModule: hasFeature('reporting'),
    hasIntegrationsModule: hasFeature('integrations'),
  }
  
  return {
    user,
    roles,
    permissions,
    features,
  }
}

/**
 * Hook for checking feature gates
 */
export function useFeatureGate(feature: string) {
  const { hasFeature, user } = useAuth()
  const { school } = useSchoolContext()
  
  const isFeatureEnabled = hasFeature(feature)
  const subscriptionTier = school?.subscription_tier || 'basic'
  
  const getUpgradeInfo = () => {
    const featureRequirements: Record<string, string> = {
      'advanced_reporting': 'professional',
      'api_access': 'professional',
      'custom_integrations': 'enterprise',
      'advanced_analytics': 'enterprise',
      'white_label': 'enterprise',
    }
    
    return {
      required_tier: featureRequirements[feature] || 'professional',
      current_tier: subscriptionTier,
      needs_upgrade: !isFeatureEnabled,
    }
  }
  
  return {
    isEnabled: isFeatureEnabled,
    upgradeInfo: getUpgradeInfo(),
    user,
  }
}

export default useAuth
