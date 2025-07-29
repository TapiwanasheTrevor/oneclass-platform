/**
 * Next.js Middleware for Multi-Tenant Subdomain Routing
 * Enhanced with role-based access control and tenant-specific authentication
 */

import { NextRequest, NextResponse } from 'next/server'
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// Types
interface SchoolInfo {
  id: string
  name: string
  subdomain: string
  is_active: boolean
  subscription_tier: string
  enabled_modules: string[]
  custom_domain?: string
}

interface UserSession {
  user_id: string
  school_id: string
  role: string
  permissions: string[]
  features: string[]
  email: string
  first_name: string
  last_name: string
}

// Configuration
const PUBLIC_ROUTES = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/accept-invitation',
  '/verify-email',
  '/api/auth',
  '/api/platform/school/resolve',
  '/api/users/invitations/accept',
  '/api/health',
  '/api/webhooks',
  '/_next',
  '/favicon.ico',
  '/public',
  '/tenant-not-found',
  '/tenant-suspended',
  '/user-not-found',
  '/unauthorized',
  '/upgrade'
]

const ADMIN_ROUTES = [
  '/admin',
  '/platform'
]

// Role-based route configurations
const ROLE_DASHBOARDS = {
  platform_admin: '/admin/platform',
  school_admin: '/admin',
  registrar: '/staff',
  teacher: '/staff',
  staff: '/staff',
  student: '/student',
  parent: '/parent',
}

// Feature-gated routes
const FEATURE_ROUTES = {
  finance_module: ['/finance', '/billing', '/payments'],
  ai_assistance: ['/ai-tutor', '/ai-insights'],
  ministry_reporting: ['/ministry', '/reports/ministry'],
  advanced_analytics: ['/analytics', '/reports/advanced'],
  bulk_operations: ['/bulk-import', '/bulk-export'],
  custom_integrations: ['/integrations', '/webhooks'],
}

// Subscription tier requirements
const SUBSCRIPTION_ROUTES = {
  premium: ['/analytics', '/reports/advanced', '/ai-tutor'],
  enterprise: ['/ministry', '/integrations', '/webhooks'],
}

/**
 * Extract subdomain from hostname
 */
function extractSubdomain(hostname: string): string | null {
  // Remove port if present
  const cleanHostname = hostname.split(':')[0]
  
  // Handle different environments
  if (cleanHostname === 'localhost' || cleanHostname === '127.0.0.1') {
    return null // No subdomain in local development
  }
  
  // For production: school.oneclass.ac.zw
  // For staging: school.oneclass-staging.com
  const parts = cleanHostname.split('.')
  
  if (parts.length >= 3) {
    // Check if it's a valid subdomain pattern
    const potentialSubdomain = parts[0]
    const domain = parts.slice(1).join('.')
    
    // Valid domains
    const validDomains = [
      'oneclass.ac.zw',
      'oneclass-staging.com',
      'oneclass.dev',
      'oneclass.local'
    ]
    
    if (validDomains.includes(domain) && potentialSubdomain !== 'www') {
      return potentialSubdomain
    }
  }
  
  return null
}

/**
 * Fetch school information by subdomain
 */
async function getSchoolBySubdomain(subdomain: string): Promise<SchoolInfo | null> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${apiUrl}/api/v1/schools/by-subdomain/${subdomain}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout
      signal: AbortSignal.timeout(5000)
    })
    
    if (!response.ok) {
      return null
    }
    
    return await response.json()
  } catch (error) {
    console.error('Failed to fetch school by subdomain:', error)
    return null
  }
}

/**
 * Check if route is public (doesn't require authentication)
 */
function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route => 
    pathname.startsWith(route) || pathname === route
  )
}

/**
 * Check if route requires admin access
 */
function isAdminRoute(pathname: string): boolean {
  return ADMIN_ROUTES.some(route => 
    pathname.startsWith(route)
  )
}

/**
 * Check if user has permission for the requested route
 */
function hasRoutePermission(userSession: UserSession, pathname: string): boolean {
  // Admin routes require platform admin role
  if (isAdminRoute(pathname)) {
    return userSession.role === 'platform_admin'
  }
  
  // School-specific route permissions
  if (pathname.startsWith('/finance')) {
    return userSession.features.includes('finance_management') ||
           userSession.permissions.includes('finance:read')
  }
  
  if (pathname.startsWith('/academic')) {
    return userSession.features.includes('academic_management') ||
           userSession.permissions.includes('academic:read')
  }
  
  if (pathname.startsWith('/sis')) {
    return userSession.features.includes('student_information_system') ||
           userSession.permissions.includes('sis:read')
  }
  
  if (pathname.startsWith('/settings')) {
    return userSession.role === 'admin' || 
           userSession.permissions.includes('school:manage')
  }
  
  // Default access for authenticated users
  return true
}

/**
 * Create response with school context headers
 */
function createResponseWithSchoolContext(
  response: NextResponse, 
  school: SchoolInfo, 
  userSession?: UserSession
): NextResponse {
  // Add school context to headers
  response.headers.set('X-School-ID', school.id)
  response.headers.set('X-School-Name', school.name)
  response.headers.set('X-School-Subdomain', school.subdomain)
  response.headers.set('X-School-Tier', school.subscription_tier)
  
  if (userSession) {
    response.headers.set('X-User-ID', userSession.user_id)
    response.headers.set('X-User-Role', userSession.role)
    response.headers.set('X-User-Permissions', JSON.stringify(userSession.permissions))
    response.headers.set('X-User-Features', JSON.stringify(userSession.features))
  }
  
  return response
}

/**
 * Get user session from API
 */
async function getUserSession(userId: string, schoolId: string): Promise<UserSession | null> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/me`, {
      headers: {
        'Authorization': `Bearer ${userId}`,
        'x-school-id': schoolId,
      },
    })
    
    if (!response.ok) {
      return null
    }
    
    return await response.json()
  } catch (error) {
    console.error('Error fetching user session:', error)
    return null
  }
}

/**
 * Get role-based dashboard
 */
function getRoleDashboard(role: string): string {
  return ROLE_DASHBOARDS[role as keyof typeof ROLE_DASHBOARDS] || '/dashboard'
}

/**
 * Check route permissions
 */
function checkRoutePermissions(
  pathname: string,
  userSession: UserSession,
  school: SchoolInfo
): { allowed: boolean; redirectTo?: string } {
  
  // Check feature-gated routes
  for (const [feature, routes] of Object.entries(FEATURE_ROUTES)) {
    if (routes.some(route => pathname.startsWith(route))) {
      if (!school.enabled_modules.includes(feature)) {
        return { allowed: false, redirectTo: '/upgrade' }
      }
    }
  }
  
  // Check subscription-gated routes
  for (const [tier, routes] of Object.entries(SUBSCRIPTION_ROUTES)) {
    if (routes.some(route => pathname.startsWith(route))) {
      if (!hasSubscriptionTier(school.subscription_tier, tier)) {
        return { allowed: false, redirectTo: '/upgrade' }
      }
    }
  }
  
  // Check admin routes
  if (isAdminRoute(pathname)) {
    if (!['school_admin', 'platform_admin'].includes(userSession.role)) {
      return { allowed: false, redirectTo: getRoleDashboard(userSession.role) }
    }
  }
  
  // Check role-specific permissions
  if (!hasRoutePermission(userSession, pathname)) {
    return { allowed: false, redirectTo: '/unauthorized' }
  }
  
  return { allowed: true }
}

/**
 * Check subscription tier hierarchy
 */
function hasSubscriptionTier(currentTier: string, requiredTier: string): boolean {
  const tierHierarchy = ['trial', 'basic', 'premium', 'enterprise']
  const currentIndex = tierHierarchy.indexOf(currentTier)
  const requiredIndex = tierHierarchy.indexOf(requiredTier)
  
  return currentIndex >= requiredIndex
}

// Create a route matcher for public routes
const isPublicRouteMatcher = createRouteMatcher(PUBLIC_ROUTES)

/**
 * Enhanced middleware with Clerk authentication and tenant routing
 */
export default clerkMiddleware(async (auth, request: NextRequest) => {
  const { pathname } = request.nextUrl
  const hostname = request.headers.get('host') || 'localhost'
  
  // Skip middleware for Next.js internal routes and API routes
  if (pathname.startsWith('/_next/') || pathname.startsWith('/api/health') || pathname === '/favicon.ico') {
    return NextResponse.next()
  }
  
  // Extract subdomain
  const subdomain = extractSubdomain(hostname)
  
  // Handle root domain (no subdomain) - redirect to marketing site or platform admin
  if (!subdomain) {
    // Check if it's an admin route on root domain
    if (isAdminRoute(pathname)) {
      // Allow platform admin access on root domain
      return NextResponse.next()
    }
    
    // For root domain, show landing page (marketing site)
    if (pathname === '/') {
      return NextResponse.next()
    }
    
    // Allow public routes on root domain
    if (isPublicRoute(pathname)) {
      return NextResponse.next()
    }
    
    // Redirect to onboarding for other routes
    return NextResponse.redirect(new URL('/onboarding', request.url))
  }
  
  // Fetch school information
  const school = await getSchoolBySubdomain(subdomain)
  
  if (!school) {
    // Invalid subdomain - redirect to not found
    return NextResponse.redirect(new URL('/tenant-not-found', request.url))
  }
  
  if (!school.is_active) {
    // School is deactivated
    return NextResponse.redirect(new URL('/tenant-suspended', request.url))
  }
  
  // Handle public routes - no authentication required
  if (isPublicRoute(pathname)) {
    const response = NextResponse.next()
    return createResponseWithSchoolContext(response, school)
  }
  
  // Get auth state
  const { userId } = await auth()
  
  // Handle unauthenticated users
  if (!userId) {
    // Redirect to login with return URL
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  // Get user session
  const userSession = school ? await getUserSession(userId, school.id) : null
  
  if (school && !userSession) {
    return NextResponse.redirect(new URL('/user-not-found', request.url))
  }
  
  // Handle root path redirect based on user role
  if (pathname === '/') {
    const dashboardUrl = userSession ? getRoleDashboard(userSession.role) : '/dashboard'
    return NextResponse.redirect(new URL(dashboardUrl, request.url))
  }
  
  // Check route permissions for authenticated users
  if (userSession && school) {
    const routeCheck = checkRoutePermissions(pathname, userSession, school)
    if (!routeCheck.allowed) {
      const redirectUrl = routeCheck.redirectTo || '/unauthorized'
      return NextResponse.redirect(new URL(redirectUrl, request.url))
    }
  }
  
  // Create response with context
  const response = NextResponse.next()
  response.headers.set('x-user-id', userId)
  
  if (school && userSession) {
    return createResponseWithSchoolContext(response, school, userSession)
  }
  
  return response
}, {
  // Public routes configuration
  publicRoutes: PUBLIC_ROUTES,
  
  // Ignored routes
  ignoredRoutes: [
    '/api/webhooks/(.*)',
  ],
})

/**
 * Middleware configuration
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}