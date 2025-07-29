/**
 * Subdomain utilities for OneClass multi-tenant platform
 */

export interface SchoolSubdomain {
  subdomain: string;
  schoolName: string;
  schoolId: string;
}

/**
 * Get the current subdomain from the URL
 */
export function getCurrentSubdomain(): string | null {
  if (typeof window === 'undefined') return null;

  const hostname = window.location.hostname;

  // For localhost development, check for school query parameter
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const urlParams = new URLSearchParams(window.location.search);
    const schoolParam = urlParams.get('school');
    if (schoolParam) {
      return schoolParam;
    }
  }

  // Development: check for .local domains
  if (hostname.includes('.oneclass.local')) {
    const parts = hostname.split('.');
    if (parts.length >= 3 && parts[0] !== 'www') {
      return parts[0];
    }
  }

  // Production: check for .oneclass.ac.zw domains
  if (hostname.includes('.oneclass.ac.zw')) {
    const parts = hostname.split('.');
    if (parts.length >= 4 && parts[0] !== 'www') {
      return parts[0];
    }
  }

  return null;
}

/**
 * Check if we're on the main platform (no subdomain)
 */
export function isMainPlatform(): boolean {
  if (typeof window === 'undefined') return true;

  const hostname = window.location.hostname;

  // For localhost, check if there's no school query parameter
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const urlParams = new URLSearchParams(window.location.search);
    return !urlParams.get('school'); // Main platform if no school parameter
  }

  // Development
  if (hostname === 'oneclass.local') {
    return true;
  }
  
  // Production
  if (hostname === 'oneclass.ac.zw') {
    return true;
  }
  
  return false;
}

/**
 * Build URL for a specific school subdomain
 */
export function buildSchoolUrl(subdomain: string, path: string = '/'): string {
  if (typeof window === 'undefined') return path;
  
  const protocol = window.location.protocol;
  const port = window.location.port ? `:${window.location.port}` : '';
  
  // Development
  if (window.location.hostname.includes('localhost') || window.location.hostname.includes('.local')) {
    return `${protocol}//${subdomain}.oneclass.local${port}${path}`;
  }
  
  // Production
  return `${protocol}//${subdomain}.oneclass.ac.zw${path}`;
}

/**
 * Build URL for the main platform
 */
export function buildMainPlatformUrl(path: string = '/'): string {
  if (typeof window === 'undefined') return path;
  
  const protocol = window.location.protocol;
  const port = window.location.port ? `:${window.location.port}` : '';
  
  // Development
  if (window.location.hostname.includes('localhost') || window.location.hostname.includes('.local')) {
    return `${protocol}//oneclass.local${port}${path}`;
  }
  
  // Production
  return `${protocol}//oneclass.ac.zw${path}`;
}

/**
 * Redirect to school subdomain
 */
export function redirectToSchool(subdomain: string, path: string = '/dashboard'): void {
  if (typeof window === 'undefined') return;
  
  const url = buildSchoolUrl(subdomain, path);
  window.location.href = url;
}

/**
 * Redirect to main platform
 */
export function redirectToMainPlatform(path: string = '/'): void {
  if (typeof window === 'undefined') return;
  
  const url = buildMainPlatformUrl(path);
  window.location.href = url;
}

/**
 * Get school info from subdomain
 */
export async function getSchoolFromSubdomain(subdomain: string): Promise<SchoolSubdomain | null> {
  try {
    // Try the simple API first (bypasses tenant middleware)
    const response = await fetch(`/api/v1/platform/schools-simple/by-subdomain/${subdomain}`);
    if (!response.ok) {
      console.warn(`Simple API failed with status: ${response.status}`);
      return null;
    }

    const school = await response.json();
    return {
      subdomain: school.subdomain,
      schoolName: school.schoolName,
      schoolId: school.schoolId,
    };
  } catch (error) {
    console.error('Error fetching school by subdomain:', error);
    return null;
  }
}

/**
 * Get school subdomain from school membership data
 */
export async function getSchoolSubdomain(schoolId: string): Promise<string | null> {
  try {
    const response = await fetch(`/api/v1/platform/schools-simple/by-id/${schoolId}`);
    if (!response.ok) {
      console.warn(`Failed to get school subdomain for ID: ${schoolId}`);
      return null;
    }

    const school = await response.json();
    return school.subdomain;
  } catch (error) {
    console.error('Error fetching school subdomain:', error);
    return null;
  }
}

/**
 * Redirect user to their school's subdomain after login
 */
export function redirectToSchoolSubdomain(user: any): void {
  try {
    // Get the user's primary school or first school membership
    let targetSchoolId = user.primary_school_id;

    if (!targetSchoolId && user.school_memberships?.length > 0) {
      targetSchoolId = user.school_memberships[0].school_id;
    }

    if (!targetSchoolId) {
      console.warn('No school found for user, redirecting to main platform');
      window.location.href = '/dashboard';
      return;
    }

    // Find the school membership to get subdomain info
    const schoolMembership = user.school_memberships?.find(
      (membership: any) => membership.school_id === targetSchoolId
    );

    if (schoolMembership?.school_subdomain) {
      // Redirect to school subdomain
      const currentHost = window.location.host;
      const port = window.location.port ? `:${window.location.port}` : '';
      const protocol = window.location.protocol;

      // Handle different environments
      let targetUrl;
      if (currentHost.includes('localhost') || currentHost.includes('127.0.0.1')) {
        // Local development - use localhost with subdomain as query parameter
        targetUrl = `${protocol}//localhost${port}/dashboard?school=${schoolMembership.school_subdomain}`;
      } else if (currentHost.includes('oneclass.local')) {
        // Local development with dnsmasq
        targetUrl = `${protocol}//${schoolMembership.school_subdomain}.oneclass.local${port}/dashboard`;
      } else {
        // Production
        targetUrl = `${protocol}//${schoolMembership.school_subdomain}.oneclass.ac.zw/dashboard`;
      }

      console.log(`Redirecting to school subdomain: ${targetUrl}`);
      window.location.href = targetUrl;
    } else {
      // Fallback: try to get subdomain from API
      getSchoolSubdomain(targetSchoolId).then(subdomain => {
        if (subdomain) {
          const currentHost = window.location.host;
          const port = window.location.port ? `:${window.location.port}` : '';
          const protocol = window.location.protocol;

          let targetUrl;
          if (currentHost.includes('localhost') || currentHost.includes('127.0.0.1')) {
            targetUrl = `${protocol}//localhost${port}/dashboard?school=${subdomain}`;
          } else if (currentHost.includes('oneclass.local')) {
            targetUrl = `${protocol}//${subdomain}.oneclass.local${port}/dashboard`;
          } else {
            targetUrl = `${protocol}//${subdomain}.oneclass.ac.zw/dashboard`;
          }

          console.log(`Redirecting to school subdomain (via API): ${targetUrl}`);
          window.location.href = targetUrl;
        } else {
          console.warn('Could not determine school subdomain, redirecting to main dashboard');
          window.location.href = '/dashboard';
        }
      });
    }
  } catch (error) {
    console.error('Error redirecting to school subdomain:', error);
    window.location.href = '/dashboard';
  }
}

/**
 * Setup subdomain redirect after login
 */
export function setupSubdomainRedirect(userSchools: Array<{ subdomain: string; name: string; id: string }>) {
  // If user has only one school, redirect to it
  if (userSchools.length === 1) {
    const school = userSchools[0];
    redirectToSchool(school.subdomain);
    return;
  }
  
  // If user has multiple schools, show school selector
  // This would be handled by a school selector component
  console.log('User has multiple schools:', userSchools);
}

/**
 * Validate subdomain format
 */
export function isValidSubdomain(subdomain: string): boolean {
  // Subdomain rules:
  // - 3-63 characters
  // - Only lowercase letters, numbers, and hyphens
  // - Cannot start or end with hyphen
  // - Cannot contain consecutive hyphens
  
  const subdomainRegex = /^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$/;
  return subdomainRegex.test(subdomain);
}

/**
 * Generate subdomain from school name
 */
export function generateSubdomain(schoolName: string): string {
  return schoolName
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-') // Replace spaces with hyphens
    .replace(/-+/g, '-') // Replace multiple hyphens with single
    .replace(/^-|-$/g, '') // Remove leading/trailing hyphens
    .substring(0, 63); // Limit to 63 characters
}

/**
 * Check if current domain supports subdomains
 */
export function supportsSubdomains(): boolean {
  if (typeof window === 'undefined') return false;
  
  const hostname = window.location.hostname;
  
  // Support subdomains in development and production
  return hostname.includes('.local') || hostname.includes('.oneclass.ac.zw') || hostname === 'localhost';
}
