/**
 * Tenant-specific routing middleware
 * Handles subdomain-based routing and tenant context resolution
 */

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs';

interface TenantConfig {
  subdomain: string;
  schoolId: string;
  schoolName: string;
  subscriptionTier: string;
  enabledModules: string[];
  customDomain?: string;
  isActive: boolean;
}

interface RouteConfig {
  path: string;
  requiredPermissions: string[];
  requiredFeatures: string[];
  allowedRoles: string[];
  redirectTo?: string;
}

// Route configurations for different user roles
const routeConfigs: Record<string, RouteConfig[]> = {
  // Admin routes
  admin: [
    {
      path: '/admin',
      requiredPermissions: ['admin.access'],
      requiredFeatures: [],
      allowedRoles: ['school_admin', 'platform_admin'],
    },
    {
      path: '/admin/users',
      requiredPermissions: ['users.read'],
      requiredFeatures: [],
      allowedRoles: ['school_admin'],
    },
    {
      path: '/admin/settings',
      requiredPermissions: ['settings.update'],
      requiredFeatures: [],
      allowedRoles: ['school_admin'],
    },
  ],
  
  // Staff routes
  staff: [
    {
      path: '/staff',
      requiredPermissions: ['staff.access'],
      requiredFeatures: [],
      allowedRoles: ['teacher', 'staff', 'registrar'],
    },
    {
      path: '/staff/students',
      requiredPermissions: ['students.read'],
      requiredFeatures: [],
      allowedRoles: ['teacher', 'staff', 'registrar'],
    },
    {
      path: '/staff/attendance',
      requiredPermissions: ['attendance.mark'],
      requiredFeatures: ['attendance_tracking'],
      allowedRoles: ['teacher'],
    },
  ],
  
  // Student routes
  student: [
    {
      path: '/student',
      requiredPermissions: ['student.access'],
      requiredFeatures: [],
      allowedRoles: ['student'],
    },
    {
      path: '/student/grades',
      requiredPermissions: ['grades.view'],
      requiredFeatures: [],
      allowedRoles: ['student'],
    },
    {
      path: '/student/assignments',
      requiredPermissions: ['assignments.view'],
      requiredFeatures: [],
      allowedRoles: ['student'],
    },
  ],
  
  // Parent routes
  parent: [
    {
      path: '/parent',
      requiredPermissions: ['parent.access'],
      requiredFeatures: [],
      allowedRoles: ['parent'],
    },
    {
      path: '/parent/children',
      requiredPermissions: ['children.read'],
      requiredFeatures: [],
      allowedRoles: ['parent'],
    },
    {
      path: '/parent/payments',
      requiredPermissions: ['payments.make'],
      requiredFeatures: ['finance_module'],
      allowedRoles: ['parent'],
    },
  ],
};

// Feature-gated routes
const featureRoutes: Record<string, string[]> = {
  finance_module: ['/finance', '/billing', '/payments'],
  ai_assistance: ['/ai-tutor', '/ai-insights'],
  ministry_reporting: ['/ministry', '/reports/ministry'],
  advanced_analytics: ['/analytics', '/reports/advanced'],
  bulk_operations: ['/bulk-import', '/bulk-export'],
  custom_integrations: ['/integrations', '/webhooks'],
};

// Public routes that don't require authentication
const publicRoutes = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/accept-invitation',
  '/verify-email',
  '/api/health',
  '/api/auth',
];

// Routes that require specific subscription tiers
const subscriptionRoutes: Record<string, string[]> = {
  premium: ['/analytics', '/reports/advanced', '/ai-tutor'],
  enterprise: ['/ministry', '/integrations', '/webhooks'],
};

export class TenantRoutingMiddleware {
  private tenantCache = new Map<string, TenantConfig>();
  private cacheExpiry = 5 * 60 * 1000; // 5 minutes
  
  constructor() {
    // Initialize with default tenant configurations
    this.initializeTenantCache();
  }

  async middleware(request: NextRequest): Promise<NextResponse> {
    const { pathname } = request.nextUrl;
    const hostname = request.headers.get('host') || '';
    
    // Handle health checks and API routes
    if (pathname.startsWith('/api/health')) {
      return NextResponse.next();
    }
    
    // Extract tenant information
    const tenantInfo = await this.extractTenantInfo(hostname);
    
    // Handle tenant resolution
    if (!tenantInfo) {
      return this.handleTenantNotFound(request);
    }
    
    // Check if tenant is active
    if (!tenantInfo.isActive) {
      return this.handleInactiveTenant(request);
    }
    
    // Handle public routes
    if (this.isPublicRoute(pathname)) {
      return this.handlePublicRoute(request, tenantInfo);
    }
    
    // Check authentication
    const { userId } = auth();
    if (!userId) {
      return this.redirectToLogin(request, tenantInfo);
    }
    
    // Get user context
    const userContext = await this.getUserContext(userId, tenantInfo.schoolId);
    if (!userContext) {
      return this.handleUserNotFound(request);
    }
    
    // Check route permissions
    const routeCheck = await this.checkRoutePermissions(
      pathname,
      userContext,
      tenantInfo
    );
    
    if (!routeCheck.allowed) {
      return this.handleUnauthorized(request, routeCheck.redirectTo);
    }
    
    // Set tenant context headers
    const response = NextResponse.next();
    response.headers.set('x-tenant-id', tenantInfo.schoolId);
    response.headers.set('x-tenant-subdomain', tenantInfo.subdomain);
    response.headers.set('x-tenant-name', tenantInfo.schoolName);
    response.headers.set('x-user-role', userContext.role);
    response.headers.set('x-user-permissions', JSON.stringify(userContext.permissions));
    
    return response;
  }

  private async extractTenantInfo(hostname: string): Promise<TenantConfig | null> {
    // Extract subdomain from hostname
    const subdomain = this.extractSubdomain(hostname);
    
    if (!subdomain) {
      return null;
    }
    
    // Check cache first
    const cached = this.tenantCache.get(subdomain);
    if (cached) {
      return cached;
    }
    
    // Fetch tenant configuration
    const tenantConfig = await this.fetchTenantConfig(subdomain);
    
    if (tenantConfig) {
      // Cache the configuration
      this.tenantCache.set(subdomain, tenantConfig);
      setTimeout(() => {
        this.tenantCache.delete(subdomain);
      }, this.cacheExpiry);
    }
    
    return tenantConfig;
  }

  private extractSubdomain(hostname: string): string | null {
    // Remove port if present
    const host = hostname.split(':')[0];
    
    // Handle localhost and IP addresses
    if (host === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(host)) {
      return 'demo'; // Default to demo tenant for development
    }
    
    // Extract subdomain from domain
    const parts = host.split('.');
    if (parts.length >= 3) {
      return parts[0];
    }
    
    return null;
  }

  private async fetchTenantConfig(subdomain: string): Promise<TenantConfig | null> {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/platform/school/resolve/${subdomain}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        return null;
      }
      
      const data = await response.json();
      
      return {
        subdomain: data.subdomain,
        schoolId: data.id,
        schoolName: data.name,
        subscriptionTier: data.subscription_tier,
        enabledModules: data.enabled_modules || [],
        customDomain: data.custom_domain,
        isActive: data.is_active,
      };
    } catch (error) {
      console.error('Error fetching tenant config:', error);
      return null;
    }
  }

  private async getUserContext(userId: string, schoolId: string) {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/me`, {
        headers: {
          'Authorization': `Bearer ${userId}`,
          'x-school-id': schoolId,
        },
      });
      
      if (!response.ok) {
        return null;
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching user context:', error);
      return null;
    }
  }

  private async checkRoutePermissions(
    pathname: string,
    userContext: any,
    tenantInfo: TenantConfig
  ): Promise<{ allowed: boolean; redirectTo?: string }> {
    
    // Check feature-gated routes
    for (const [feature, routes] of Object.entries(featureRoutes)) {
      if (routes.some(route => pathname.startsWith(route))) {
        if (!tenantInfo.enabledModules.includes(feature)) {
          return { allowed: false, redirectTo: '/upgrade' };
        }
      }
    }
    
    // Check subscription-gated routes
    for (const [tier, routes] of Object.entries(subscriptionRoutes)) {
      if (routes.some(route => pathname.startsWith(route))) {
        if (!this.hasSubscriptionTier(tenantInfo.subscriptionTier, tier)) {
          return { allowed: false, redirectTo: '/upgrade' };
        }
      }
    }
    
    // Check role-based route access
    const roleRoutes = this.getRoleRoutes(userContext.role);
    const matchingRoute = roleRoutes.find(route => 
      pathname.startsWith(route.path)
    );
    
    if (matchingRoute) {
      // Check role permissions
      if (!matchingRoute.allowedRoles.includes(userContext.role)) {
        return { allowed: false, redirectTo: this.getDefaultDashboard(userContext.role) };
      }
      
      // Check user permissions
      const hasPermissions = matchingRoute.requiredPermissions.every(
        permission => userContext.permissions.includes(permission)
      );
      
      if (!hasPermissions) {
        return { allowed: false, redirectTo: '/unauthorized' };
      }
      
      // Check required features
      const hasFeatures = matchingRoute.requiredFeatures.every(
        feature => tenantInfo.enabledModules.includes(feature)
      );
      
      if (!hasFeatures) {
        return { allowed: false, redirectTo: '/upgrade' };
      }
    }
    
    return { allowed: true };
  }

  private getRoleRoutes(role: string): RouteConfig[] {
    // Return routes based on role hierarchy
    const routes: RouteConfig[] = [];
    
    if (role === 'school_admin') {
      routes.push(...routeConfigs.admin, ...routeConfigs.staff);
    } else if (['teacher', 'staff', 'registrar'].includes(role)) {
      routes.push(...routeConfigs.staff);
    } else if (role === 'student') {
      routes.push(...routeConfigs.student);
    } else if (role === 'parent') {
      routes.push(...routeConfigs.parent);
    }
    
    return routes;
  }

  private getDefaultDashboard(role: string): string {
    const dashboards = {
      school_admin: '/admin',
      registrar: '/staff',
      teacher: '/staff',
      staff: '/staff',
      student: '/student',
      parent: '/parent',
    };
    
    return dashboards[role as keyof typeof dashboards] || '/';
  }

  private hasSubscriptionTier(currentTier: string, requiredTier: string): boolean {
    const tierHierarchy = ['trial', 'basic', 'premium', 'enterprise'];
    const currentIndex = tierHierarchy.indexOf(currentTier);
    const requiredIndex = tierHierarchy.indexOf(requiredTier);
    
    return currentIndex >= requiredIndex;
  }

  private isPublicRoute(pathname: string): boolean {
    return publicRoutes.some(route => pathname.startsWith(route));
  }

  private handleTenantNotFound(request: NextRequest): NextResponse {
    const url = request.nextUrl.clone();
    url.pathname = '/tenant-not-found';
    return NextResponse.redirect(url);
  }

  private handleInactiveTenant(request: NextRequest): NextResponse {
    const url = request.nextUrl.clone();
    url.pathname = '/tenant-suspended';
    return NextResponse.redirect(url);
  }

  private handlePublicRoute(request: NextRequest, tenantInfo: TenantConfig): NextResponse {
    const response = NextResponse.next();
    response.headers.set('x-tenant-id', tenantInfo.schoolId);
    response.headers.set('x-tenant-subdomain', tenantInfo.subdomain);
    response.headers.set('x-tenant-name', tenantInfo.schoolName);
    return response;
  }

  private redirectToLogin(request: NextRequest, tenantInfo: TenantConfig): NextResponse {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('redirect', request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  private handleUserNotFound(request: NextRequest): NextResponse {
    const url = request.nextUrl.clone();
    url.pathname = '/user-not-found';
    return NextResponse.redirect(url);
  }

  private handleUnauthorized(request: NextRequest, redirectTo?: string): NextResponse {
    const url = request.nextUrl.clone();
    url.pathname = redirectTo || '/unauthorized';
    return NextResponse.redirect(url);
  }

  private initializeTenantCache(): void {
    // Initialize cache with common tenant configurations
    // This could be loaded from a configuration file or database
  }
}

// Export middleware instance
export const tenantRoutingMiddleware = new TenantRoutingMiddleware();