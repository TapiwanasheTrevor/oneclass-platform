// =====================================================
// Enhanced Authentication Hook for Consolidated User System
// File: frontend/hooks/useAuth.ts
// =====================================================

import { api, wsManager } from '@/lib/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

// Platform roles
export enum PlatformRole {
  SUPER_ADMIN = "super_admin",
  SCHOOL_ADMIN = "school_admin",
  REGISTRAR = "registrar",
  TEACHER = "teacher",
  PARENT = "parent",
  STUDENT = "student",
  STAFF = "staff"
}

// School roles
export enum SchoolRole {
  PRINCIPAL = "principal",
  DEPUTY_PRINCIPAL = "deputy_principal",
  ACADEMIC_HEAD = "academic_head",
  DEPARTMENT_HEAD = "department_head",
  TEACHER = "teacher",
  FORM_TEACHER = "form_teacher",
  REGISTRAR = "registrar",
  BURSAR = "bursar",
  LIBRARIAN = "librarian",
  IT_SUPPORT = "it_support",
  SECURITY = "security",
  PARENT = "parent",
  STUDENT = "student"
}

// User status
export enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SUSPENDED = "suspended",
  PENDING_VERIFICATION = "pending_verification",
  ARCHIVED = "archived"
}

// User profile interface
interface UserProfile {
  phone_number?: string;
  profile_image_url?: string;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  bio?: string;
  preferred_language: string;
  timezone: string;
  notification_preferences: {
    email_notifications: boolean;
    sms_notifications: boolean;
    push_notifications: boolean;
    marketing_emails: boolean;
  };
}

// School membership interface
interface SchoolMembership {
  school_id: string;
  school_name: string;
  school_subdomain: string;
  role: SchoolRole;
  permissions: string[];
  joined_date: string;
  status: UserStatus;

  // Role-specific fields
  student_id?: string;
  current_grade?: string;
  admission_date?: string;
  graduation_date?: string;

  employee_id?: string;
  department?: string;
  hire_date?: string;
  contract_type?: string;

  children_ids?: string[];
}

// Consolidated user interface
interface PlatformUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  platform_role: PlatformRole;
  status: UserStatus;
  primary_school_id?: string;
  school_memberships: SchoolMembership[];
  profile?: UserProfile;
  created_at: string;
  last_login?: string;
  feature_flags: Record<string, boolean>;
  user_preferences: Record<string, any>;
}

interface AuthContextType {
  user: PlatformUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  currentSchool: SchoolMembership | null;
  availableSchools: SchoolMembership[];
  login: (email: string, password: string) => Promise<any>;
  logout: () => void;
  switchSchool: (schoolId: string) => void;
  hasPermission: (permission: string, schoolId?: string) => boolean;
  hasRole: (role: SchoolRole, schoolId?: string) => boolean;
  canAccessFeature: (feature: string) => boolean;
  isPlatformAdmin: boolean;
  isSchoolAdmin: (schoolId?: string) => boolean;
  token: string | null;
}

export function useAuth(): AuthContextType {
  const queryClient = useQueryClient();

  // Get token from localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;

  // Get current school from localStorage
  const currentSchoolId = typeof window !== 'undefined'
    ? localStorage.getItem('current_school_id')
    : null;

  // Get current user with new consolidated model
  const { data: user, isLoading } = useQuery({
    queryKey: ['current-user'],
    queryFn: async () => {
      if (!token) return null;

      const response = await api.get('/api/v1/auth/me');
      return response.data as PlatformUser;
    },
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on auth errors
      if (error?.response?.status === 401) return false;
      return failureCount < 2;
    },
  });

  // Get current school membership
  const currentSchool = user && currentSchoolId
    ? user.school_memberships.find(m => m.school_id === currentSchoolId) || null
    : user?.school_memberships.find(m => m.school_id === user.primary_school_id) || user?.school_memberships[0] || null;

  // Available schools for user
  const availableSchools = user?.school_memberships.filter(m => m.status === UserStatus.ACTIVE) || [];

  // Set up WebSocket connection when user is authenticated
  useEffect(() => {
    if (user && token) {
      wsManager.connect(token);
    } else {
      wsManager.disconnect();
    }

    return () => {
      wsManager.disconnect();
    };
  }, [user, token]);

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const response = await api.post('/api/v1/auth/login', { email, password });
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      queryClient.setQueryData(['current-user'], data.user);

      // Set default school
      if (data.user.primary_school_id) {
        localStorage.setItem('current_school_id', data.user.primary_school_id);
      } else if (data.user.school_memberships.length > 0) {
        localStorage.setItem('current_school_id', data.user.school_memberships[0].school_id);
      }

      queryClient.invalidateQueries({ queryKey: ['current-user'] });
    },
  });

  // Logout function
  const logout = async () => {
    try {
      // Call logout endpoint
      await api.post('/api/v1/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error);
    }

    // Clean up local storage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_school_id');

    // Disconnect WebSocket
    wsManager.disconnect();

    // Clear all cached data
    queryClient.setQueryData(['current-user'], null);
    queryClient.clear();
  };

  // Switch school context
  const switchSchool = async (schoolId: string) => {
    if (!user?.school_memberships.some(m => m.school_id === schoolId)) return;
    try {
      const resp = await api.post('/api/v1/auth/switch-school', { school_id: schoolId });
      const { access_token, current_school } = resp.data || {};
      if (access_token) {
        localStorage.setItem('auth_token', access_token);
      }
      if (current_school?.school_id) {
        localStorage.setItem('current_school_id', current_school.school_id);
      } else {
        localStorage.setItem('current_school_id', schoolId);
      }
      await queryClient.invalidateQueries();
    } catch (e) {
      console.error('Failed to switch school', e);
    }
  };

  // Permission checking
  const hasPermission = (permission: string, schoolId?: string): boolean => {
    if (!user) return false;

    // Super admin has all permissions
    if (user.platform_role === PlatformRole.SUPER_ADMIN) return true;

    const targetSchoolId = schoolId || currentSchool?.school_id;
    if (!targetSchoolId) return false;

    const membership = user.school_memberships.find(m => m.school_id === targetSchoolId);
    if (!membership) return false;

    return membership.permissions.includes(permission) || membership.permissions.includes('*');
  };

  // Role checking
  const hasRole = (role: SchoolRole, schoolId?: string): boolean => {
    if (!user) return false;

    const targetSchoolId = schoolId || currentSchool?.school_id;
    if (!targetSchoolId) return false;

    const membership = user.school_memberships.find(m => m.school_id === targetSchoolId);
    return membership?.role === role;
  };

  // Feature access checking
  const canAccessFeature = (feature: string): boolean => {
    if (!user) return false;

    // Check user feature flags
    if (user.feature_flags.hasOwnProperty(feature)) {
      return user.feature_flags[feature];
    }

    // Default feature access based on role
    const defaultFeatures: Record<PlatformRole, string[]> = {
      [PlatformRole.SUPER_ADMIN]: ['*'],
      [PlatformRole.SCHOOL_ADMIN]: [
        'student_management', 'staff_management', 'finance_module',
        'reports', 'settings', 'migration_services'
      ],
      [PlatformRole.REGISTRAR]: ['student_management', 'documents', 'reports'],
      [PlatformRole.TEACHER]: ['student_management', 'attendance', 'gradebook'],
      [PlatformRole.PARENT]: ['student_portal', 'payments', 'communication'],
      [PlatformRole.STUDENT]: ['student_portal', 'assignments'],
      [PlatformRole.STAFF]: ['basic_access']
    };

    const userFeatures = defaultFeatures[user.platform_role] || [];
    return userFeatures.includes('*') || userFeatures.includes(feature);
  };

  // Admin checks
  const isPlatformAdmin = user?.platform_role === PlatformRole.SUPER_ADMIN;

  const isSchoolAdmin = (schoolId?: string): boolean => {
    if (!user) return false;
    if (isPlatformAdmin) return true;

    const targetSchoolId = schoolId || currentSchool?.school_id;
    if (!targetSchoolId) return false;

    const membership = user.school_memberships.find(m => m.school_id === targetSchoolId);
    return membership?.role === SchoolRole.PRINCIPAL ||
      membership?.role === SchoolRole.DEPUTY_PRINCIPAL ||
      user.platform_role === PlatformRole.SCHOOL_ADMIN;
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    currentSchool,
    availableSchools,
    login: async (email: string, password: string) => {
      return await loginMutation.mutateAsync({ email, password });
    },
    logout,
    switchSchool,
    hasPermission,
    hasRole,
    canAccessFeature,
    isPlatformAdmin,
    isSchoolAdmin,
    token
  };
}

// Helper hooks for specific use cases
export function usePermissions() {
  const { hasPermission, hasRole, canAccessFeature, isPlatformAdmin, isSchoolAdmin } = useAuth();

  return {
    hasPermission,
    hasRole,
    canAccessFeature,
    isPlatformAdmin,
    isSchoolAdmin,

    // Common permission checks
    canManageUsers: (schoolId?: string) => hasPermission('users.manage', schoolId) || isSchoolAdmin(schoolId),
    canManageFinance: (schoolId?: string) => hasPermission('finance.manage', schoolId) || hasRole(SchoolRole.BURSAR, schoolId),
    canViewReports: (schoolId?: string) => hasPermission('reports.view', schoolId) || isSchoolAdmin(schoolId),
    canManageSettings: (schoolId?: string) => hasPermission('settings.manage', schoolId) || isSchoolAdmin(schoolId),
  };
}

// School context hook
export function useSchoolContext() {
  const { user, currentSchool, switchSchool, availableSchools } = useAuth();

  return {
    currentSchool,
    availableSchools,
    switchSchool,
    hasMultipleSchools: availableSchools.length > 1,

    // School-specific getters
    getCurrentSchoolId: () => currentSchool?.school_id,
    getCurrentSchoolName: () => currentSchool?.school_name,
    getUserRoleInCurrentSchool: () => currentSchool?.role,
    getUserPermissionsInCurrentSchool: () => currentSchool?.permissions || [],
  };
}