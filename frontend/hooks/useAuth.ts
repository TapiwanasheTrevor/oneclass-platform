'use client';

// =====================================================
// Consolidated Authentication Hook
// Bridges Clerk identity → backend /auth/me → school context
// File: frontend/hooks/useAuth.ts
// =====================================================

import { useUser, useAuth as useClerkAuthHook } from '@clerk/nextjs';
import { api, setAuthTokenGetter, setCurrentSchoolId } from '@/lib/api';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo } from 'react';
import { buildSchoolUrl, getCurrentSubdomain } from '@/utils/subdomain';

// ---- Enums (aligned with backend) ----

export enum GlobalRole {
  SUPER_ADMIN = 'super_admin',
  PLATFORM_ADMIN = 'platform_admin',
  REGIONAL_ADMIN = 'regional_admin',
  EDUCATION_OFFICER = 'education_officer',
  SYSTEM_USER = 'system_user',
}

export enum SchoolRole {
  PRINCIPAL = 'principal',
  DEPUTY_PRINCIPAL = 'deputy_principal',
  ACADEMIC_HEAD = 'academic_head',
  DEPARTMENT_HEAD = 'department_head',
  TEACHER = 'teacher',
  FORM_TEACHER = 'form_teacher',
  REGISTRAR = 'registrar',
  BURSAR = 'bursar',
  LIBRARIAN = 'librarian',
  IT_SUPPORT = 'it_support',
  SECURITY = 'security',
  PARENT = 'parent',
  GUARDIAN = 'guardian',
  STUDENT = 'student',
  PREFECT = 'prefect',
  SCHOOL_ADMIN = 'school_admin',
  SUPPORT_STAFF = 'support_staff',
  VOLUNTEER = 'volunteer',
}

export enum MembershipStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
  ARCHIVED = 'archived',
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING_VERIFICATION = 'pending_verification',
  ARCHIVED = 'archived',
}

// ---- Interfaces ----

export interface SchoolMembership {
  school_id: string;
  school_name: string;
  school_subdomain: string;
  role: SchoolRole;
  permissions: string[];
  status: MembershipStatus;
  joined_date: string;

  // Role-specific
  student_id?: string;
  current_grade?: string;
  admission_date?: string;
  employee_id?: string;
  department?: string;
  hire_date?: string;
  children_ids?: string[];
}

export interface PlatformUser {
  id: string;
  email: string;
  school_id?: string;
  school_name?: string;
  token?: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  display_name?: string;
  platform_role?: GlobalRole | string;
  global_role: GlobalRole | string;
  role?: string;
  status: UserStatus;
  primary_school_id?: string;
  current_school_id?: string;
  school_memberships: SchoolMembership[];
  clerk_user_id?: string;
  is_email_verified: boolean;
  last_login_at?: string;
  login_count: number;
  profile?: Record<string, any>;
  current_school?: {
    school_id: string;
    school_name: string;
    school_subdomain: string;
    subdomain?: string;
    subscription_tier?: string;
    role?: string;
  } | null;
  contact_information?: Record<string, any>;
  personal_profile?: Record<string, any>;
  user_preferences?: Record<string, any>;
}

export interface AuthContextType {
  // Identity (from Clerk)
  isLoaded: boolean;
  isSignedIn: boolean;

  // Platform user (from backend /auth/me)
  user: PlatformUser | null;
  isLoading: boolean;
  loading: boolean;
  isAuthenticated: boolean;

  // School context
  currentSchool: SchoolMembership | null;
  availableSchools: SchoolMembership[];
  switchSchool: (schoolId: string) => Promise<void>;

  // Permission & role checks
  hasPermission: (permission: string, schoolId?: string) => boolean;
  hasRole: (role: SchoolRole, schoolId?: string) => boolean;
  isPlatformAdmin: boolean;
  isSchoolAdmin: (schoolId?: string) => boolean;

  // Auth actions
  signOut: () => Promise<void>;
}

// ---- Helper: check if Clerk is configured ----
function isClerkConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  return !!key && !key.includes('your-') && key.startsWith('pk_');
}

// ---- Main Hook ----

export function useAuth(): AuthContextType {
  const queryClient = useQueryClient();

  // Clerk identity — only call hooks if Clerk is configured
  // When Clerk is not configured, we fall back to localStorage token (dev mode)
  const clerkConfigured = isClerkConfigured();

  // Always call hooks (React rules) — they return safe defaults when Clerk isn't mounted
  const { user: clerkUser, isLoaded: clerkLoaded, isSignedIn: clerkSignedIn } = useUser();
  const { getToken, signOut: clerkSignOut } = useClerkAuthHook();

  // Determine effective auth state
  const isLoaded = clerkConfigured ? clerkLoaded : true;
  const isSignedIn = clerkConfigured ? !!clerkSignedIn : !!(typeof window !== 'undefined' && localStorage.getItem('auth_token'));

  // Wire up the API client's token getter.
  useEffect(() => {
    if (clerkConfigured) {
      setAuthTokenGetter(() => getToken());
    } else {
      setAuthTokenGetter(null);
    }
  }, [clerkConfigured, getToken]);

  // Fetch platform user from backend
  const { data: user = null, isLoading } = useQuery({
    queryKey: ['platform-user', clerkConfigured ? clerkUser?.id : 'local'],
    queryFn: async (): Promise<PlatformUser | null> => {
      if (!isSignedIn) return null;
      const response = await api.get('/api/v1/auth/me');
      return response.data as PlatformUser;
    },
    enabled: isLoaded && isSignedIn,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 401) return false;
      return failureCount < 2;
    },
  });

  // Current school from localStorage or primary
  const storedSchoolId = typeof window !== 'undefined'
    ? localStorage.getItem('current_school_id')
    : null;

  const currentSchool = useMemo(() => {
    if (!user) return null;
    const active = user.school_memberships.filter(m => m.status === MembershipStatus.ACTIVE);
    const preferredSchoolId = storedSchoolId || user.current_school_id || user.primary_school_id;
    // 1. stored selection, 2. backend session/current school, 3. primary, 4. first active
    return active.find(m => m.school_id === preferredSchoolId)
      || active[0]
      || null;
  }, [user, storedSchoolId]);

  const availableSchools = useMemo(
    () => user?.school_memberships.filter(m => m.status === MembershipStatus.ACTIVE) || [],
    [user],
  );

  // Keep API client's school header in sync
  useEffect(() => {
    setCurrentSchoolId(currentSchool?.school_id ?? null);
  }, [currentSchool?.school_id]);

  // Switch school
  const switchSchool = useCallback(async (schoolId: string) => {
    const targetSchool = user?.school_memberships.find(m => m.school_id === schoolId);
    if (!targetSchool) return;

    try {
      const resp = await api.post('/api/v1/auth/switch-school', { school_id: schoolId });
      const { access_token, current_school } = resp.data || {};
      const newSchoolId = current_school?.school_id || schoolId;

      if (typeof window !== 'undefined') {
        localStorage.setItem('current_school_id', newSchoolId);
        if (access_token) {
          localStorage.setItem('auth_token', access_token);
        }
      }

      setCurrentSchoolId(newSchoolId);

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['platform-user'] }),
        queryClient.invalidateQueries({ queryKey: ['school-context'] }),
        queryClient.invalidateQueries({ queryKey: ['school-config'] }),
      ]);

      const targetSubdomain =
        current_school?.school_subdomain ||
        current_school?.subdomain ||
        targetSchool.school_subdomain;
      const currentSubdomain = getCurrentSubdomain();

      if (
        typeof window !== 'undefined' &&
        targetSubdomain &&
        targetSubdomain !== currentSubdomain
      ) {
        window.location.href = buildSchoolUrl(targetSubdomain, window.location.pathname);
      }
    } catch (e) {
      console.error('Failed to switch school', e);
    }
  }, [user, queryClient]);

  // Sign out
  const signOut = useCallback(async () => {
    try {
      await api.post('/api/v1/auth/logout');
    } catch (e) {
      console.error('Backend sign out error:', e);
    }

    try {
      if (clerkConfigured) {
        await clerkSignOut();
      }
    } catch (e) {
      console.error('Sign out error:', e);
    }
    // Clean up local state regardless
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('current_school_id');
    }
    setCurrentSchoolId(null);
    queryClient.setQueryData(['platform-user', clerkConfigured ? clerkUser?.id : 'local'], null);
    queryClient.clear();
  }, [clerkConfigured, clerkSignOut, clerkUser?.id, queryClient]);

  // Permission checking
  const hasPermission = useCallback((permission: string, schoolId?: string): boolean => {
    if (!user) return false;
    if (user.global_role === GlobalRole.SUPER_ADMIN || user.global_role === GlobalRole.PLATFORM_ADMIN) return true;

    const targetId = schoolId || currentSchool?.school_id;
    if (!targetId) return false;

    const membership = user.school_memberships.find(m => m.school_id === targetId);
    if (!membership) return false;
    return membership.permissions.includes(permission) || membership.permissions.includes('*');
  }, [user, currentSchool]);

  const hasRole = useCallback((role: SchoolRole, schoolId?: string): boolean => {
    if (!user) return false;
    const targetId = schoolId || currentSchool?.school_id;
    if (!targetId) return false;
    const membership = user.school_memberships.find(m => m.school_id === targetId);
    return membership?.role === role;
  }, [user, currentSchool]);

  const isPlatformAdmin = user?.global_role === GlobalRole.SUPER_ADMIN
    || user?.global_role === GlobalRole.PLATFORM_ADMIN;

  const isSchoolAdmin = useCallback((schoolId?: string): boolean => {
    if (!user) return false;
    if (isPlatformAdmin) return true;
    const targetId = schoolId || currentSchool?.school_id;
    if (!targetId) return false;
    const membership = user.school_memberships.find(m => m.school_id === targetId);
    return membership?.role === SchoolRole.PRINCIPAL
      || membership?.role === SchoolRole.DEPUTY_PRINCIPAL
      || membership?.role === SchoolRole.SCHOOL_ADMIN;
  }, [user, isPlatformAdmin, currentSchool]);

  return {
    isLoaded,
    isSignedIn,
    user,
    isLoading,
    loading: isLoading,
    isAuthenticated: !!user,
    currentSchool,
    availableSchools,
    switchSchool,
    hasPermission,
    hasRole,
    isPlatformAdmin,
    isSchoolAdmin,
    signOut,
  };
}

// ---- Helper hooks ----

export function usePermissions() {
  const { hasPermission, hasRole, isPlatformAdmin, isSchoolAdmin } = useAuth();

  return {
    hasPermission,
    hasRole,
    isPlatformAdmin,
    isSchoolAdmin,
    canManageUsers: (schoolId?: string) => hasPermission('users.manage', schoolId) || isSchoolAdmin(schoolId),
    canManageFinance: (schoolId?: string) => hasPermission('finance.manage', schoolId) || hasRole(SchoolRole.BURSAR, schoolId),
    canViewReports: (schoolId?: string) => hasPermission('reports.view', schoolId) || isSchoolAdmin(schoolId),
    canManageSettings: (schoolId?: string) => hasPermission('settings.manage', schoolId) || isSchoolAdmin(schoolId),
  };
}

export default useAuth;
