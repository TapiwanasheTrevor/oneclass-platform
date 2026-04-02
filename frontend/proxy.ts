/**
 * Next.js Proxy for Multi-Tenant Subdomain Routing
 * Integrates Clerk authentication with school-based multi-tenancy.
 */

import { NextRequest, NextResponse } from 'next/server'
import { clerkMiddleware } from '@clerk/nextjs/server'

interface SchoolInfo {
  id: string
  name: string
  subdomain: string
  is_active: boolean
  subscription_tier: string
  enabled_modules: string[]
  custom_domain?: string
}

interface UserContext {
  user_id: string
  school_id?: string
  role: string
  permissions: string[]
  school_memberships: Array<{
    school_id: string
    school_name: string
    school_subdomain: string
    role: string
    permissions: string[]
    status: string
  }>
}

const PUBLIC_ROUTES = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/accept-invitation',
  '/verify-email',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/auth',
  '/api/platform/school/resolve',
  '/api/users/invitations/accept',
  '/api/health',
  '/api/webhooks(.*)',
  '/_next(.*)',
  '/favicon.ico',
  '/public(.*)',
  '/tenant-not-found',
  '/tenant-suspended',
  '/user-not-found',
  '/unauthorized',
  '/upgrade',
]

const ADMIN_ROUTES = ['/admin', '/platform']

const ROLE_DASHBOARDS: Record<string, string> = {
  super_admin: '/admin/platform',
  platform_admin: '/admin/platform',
  principal: '/admin',
  deputy_principal: '/admin',
  school_admin: '/admin',
  registrar: '/staff',
  teacher: '/staff',
  bursar: '/staff',
  staff: '/staff',
  student: '/student',
  parent: '/parent',
}

function extractSubdomain(hostname: string): string | null {
  const cleanHostname = hostname.split(':')[0]

  if (cleanHostname === 'localhost' || cleanHostname === '127.0.0.1') {
    return null
  }

  const parts = cleanHostname.split('.')
  if (parts.length >= 3) {
    const potentialSubdomain = parts[0]
    const domain = parts.slice(1).join('.')
    const validDomains = [
      'oneclass.ac.zw',
      'oneclass-staging.com',
      'oneclass.dev',
      'oneclass.local',
    ]
    if (validDomains.includes(domain) && potentialSubdomain !== 'www') {
      return potentialSubdomain
    }
  }

  return null
}

async function getSchoolBySubdomain(subdomain: string): Promise<SchoolInfo | null> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${apiUrl}/api/v1/platform/schools/by-subdomain/${subdomain}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(5000),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (error) {
    console.error('Failed to fetch school by subdomain:', error)
    return null
  }
}

async function getUserContext(token: string): Promise<UserContext | null> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(5000),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (error) {
    console.error('Error fetching user context:', error)
    return null
  }
}

function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some((route) => {
    if (route.includes('(.*)')) {
      const base = route.replace('(.*)', '')
      return pathname.startsWith(base)
    }
    return pathname === route || pathname.startsWith(route + '/')
  })
}

function isAdminRoute(pathname: string): boolean {
  return ADMIN_ROUTES.some((route) => pathname.startsWith(route))
}

function getRoleDashboard(role: string): string {
  return ROLE_DASHBOARDS[role] || '/dashboard'
}

function addSchoolHeaders(
  response: NextResponse,
  school: SchoolInfo,
  userCtx?: UserContext | null
): NextResponse {
  response.headers.set('X-School-ID', school.id)
  response.headers.set('X-School-Name', school.name)
  response.headers.set('X-School-Subdomain', school.subdomain)
  response.headers.set('X-School-Tier', school.subscription_tier)

  if (userCtx) {
    response.headers.set('X-User-ID', userCtx.user_id)
    response.headers.set('X-User-Role', userCtx.role)
  }

  return response
}

function isClerkConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  return !!key && !key.includes('your-') && key.startsWith('pk_')
}

async function devProxy(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/_next/') || pathname.startsWith('/api/health') || pathname === '/favicon.ico') {
    return NextResponse.next()
  }

  return NextResponse.next()
}

const clerkAuthProxy = clerkMiddleware(async (auth, request: NextRequest) => {
  const { pathname } = request.nextUrl
  const hostname = request.headers.get('host') || 'localhost'

  if (pathname.startsWith('/_next/') || pathname.startsWith('/api/health') || pathname === '/favicon.ico') {
    return NextResponse.next()
  }

  const subdomain = extractSubdomain(hostname)

  if (!subdomain) {
    if (isAdminRoute(pathname) || pathname === '/' || isPublicRoute(pathname)) {
      return NextResponse.next()
    }

    const { userId } = await auth()
    if (!userId) {
      return NextResponse.redirect(new URL('/sign-in', request.url))
    }

    return NextResponse.next()
  }

  const school = await getSchoolBySubdomain(subdomain)

  if (!school) {
    return NextResponse.redirect(new URL('/tenant-not-found', request.url))
  }

  if (!school.is_active) {
    return NextResponse.redirect(new URL('/tenant-suspended', request.url))
  }

  if (isPublicRoute(pathname)) {
    const response = NextResponse.next()
    return addSchoolHeaders(response, school)
  }

  const { userId, getToken } = await auth()

  if (!userId) {
    const loginUrl = new URL('/sign-in', request.url)
    loginUrl.searchParams.set('redirect_url', pathname)
    return NextResponse.redirect(loginUrl)
  }

  const token = await getToken()
  const userCtx = token ? await getUserContext(token) : null

  if (!userCtx) {
    return NextResponse.redirect(new URL('/user-not-found', request.url))
  }

  const membership = userCtx.school_memberships?.find(
    (m) => m.school_id === school.id && m.status === 'active'
  )

  if (!membership && userCtx.role !== 'super_admin' && userCtx.role !== 'platform_admin') {
    return NextResponse.redirect(new URL('/unauthorized?error=no_school_access', request.url))
  }

  if (pathname === '/') {
    const role = membership?.role || userCtx.role
    return NextResponse.redirect(new URL(getRoleDashboard(role), request.url))
  }

  if (isAdminRoute(pathname)) {
    const role = membership?.role || userCtx.role
    const adminRoles = ['super_admin', 'platform_admin', 'principal', 'deputy_principal', 'school_admin']
    if (!adminRoles.includes(role)) {
      return NextResponse.redirect(new URL(getRoleDashboard(role), request.url))
    }
  }

  const response = NextResponse.next()
  return addSchoolHeaders(response, school, userCtx)
})

export default function proxy(request: NextRequest) {
  if (isClerkConfigured()) {
    return clerkAuthProxy(request, {} as any)
  }
  return devProxy(request)
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
