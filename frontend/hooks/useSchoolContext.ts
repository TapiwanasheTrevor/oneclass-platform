// =====================================================
// School Configuration Hook
// Fetches school-level config (branding, features, limits)
// for the user's currently-active school.
// File: frontend/hooks/useSchoolContext.ts
// =====================================================

import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { api } from '@/lib/api';

// ---- Interfaces ----

export interface SchoolConfiguration {
  school_id: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  motto?: string;
  vision_statement?: string;
  mission_statement?: string;
  timezone: string;
  language_primary: string;
  language_secondary?: string;
  currency: string;
  date_format: string;
  features_enabled: Record<string, boolean>;
  subscription_tier: string;
  max_students: number;
  grading_system: Record<string, any>;
  notification_settings: Record<string, boolean>;
  student_id_format: string;
  academic_year_start_month: number;
  terms_per_year: number;
}

export interface SchoolContextData {
  school: {
    id: string;
    name: string;
    subdomain: string;
    type: string;
    config: SchoolConfiguration;
  };
  branding: {
    logo_url?: string;
    primary_color: string;
    secondary_color: string;
    accent_color: string;
    font_family: string;
  };
  features: Record<string, boolean>;
  subscription: {
    tier: string;
    limits: {
      max_students: number;
      max_staff: number;
      storage_limit_gb: number;
    };
  };
  academic: {
    year_start_month: number;
    terms_per_year: number;
    grading_system: Record<string, any>;
  };
  regional: {
    timezone: string;
    currency: string;
    date_format: string;
    primary_language: string;
    secondary_language?: string;
  };
  // Utility functions
  hasFeature: (feature: string) => boolean;
  canAccess: (permission: string) => boolean;
  formatCurrency: (amount: number) => string;
  formatDate: (date: Date) => string;
  getGradeDisplay: (grade: number) => string;
}

// ---- Main Hook ----

export function useSchoolConfig(): {
  school: SchoolContextData | null;
  isLoading: boolean;
} {
  const { currentSchool, hasPermission } = useAuth();
  const schoolId = currentSchool?.school_id;

  const { data: schoolData, isLoading } = useQuery({
    queryKey: ['school-config', schoolId],
    queryFn: async () => {
      if (!schoolId) return null;
      const response = await api.get(`/api/v1/schools/${schoolId}/context`);
      return response.data;
    },
    enabled: !!schoolId,
    staleTime: 5 * 60 * 1000,
  });

  if (!schoolData || !currentSchool) {
    return { school: null, isLoading };
  }

  const config: SchoolConfiguration = schoolData.config || schoolData;

  const contextData: SchoolContextData = {
    school: {
      id: schoolData.id || schoolId,
      name: schoolData.name || currentSchool.school_name,
      subdomain: schoolData.subdomain || currentSchool.school_subdomain,
      type: schoolData.type || 'secondary',
      config,
    },
    branding: {
      logo_url: config.logo_url,
      primary_color: config.primary_color || '#1a56db',
      secondary_color: config.secondary_color || '#7e3af2',
      accent_color: config.accent_color || '#0e9f6e',
      font_family: config.font_family || 'Inter',
    },
    features: config.features_enabled || {},
    subscription: {
      tier: config.subscription_tier || 'basic',
      limits: {
        max_students: config.max_students || 500,
        max_staff: 50,
        storage_limit_gb: 10,
      },
    },
    academic: {
      year_start_month: config.academic_year_start_month || 1,
      terms_per_year: config.terms_per_year || 3,
      grading_system: config.grading_system || {},
    },
    regional: {
      timezone: config.timezone || 'Africa/Harare',
      currency: config.currency || 'USD',
      date_format: config.date_format || 'DD/MM/YYYY',
      primary_language: config.language_primary || 'en',
      secondary_language: config.language_secondary,
    },
    hasFeature: (feature: string) => {
      return (config.features_enabled || {})[feature] === true;
    },
    canAccess: (permission: string) => {
      return hasPermission(permission);
    },
    formatCurrency: (amount: number) => {
      return new Intl.NumberFormat('en-ZW', {
        style: 'currency',
        currency: config.currency || 'USD',
        minimumFractionDigits: 2,
      }).format(amount);
    },
    formatDate: (date: Date) => {
      const locale = (config.language_primary || 'en') === 'en' ? 'en-ZW' : 'en-US';
      if ((config.date_format || 'DD/MM/YYYY') === 'DD/MM/YYYY') {
        return date.toLocaleDateString(locale, {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        });
      }
      return date.toLocaleDateString(locale);
    },
    getGradeDisplay: (grade: number) => {
      if (grade <= 7) return `Grade ${grade}`;
      if (grade === 12) return 'Form 5 (Lower 6)';
      if (grade === 13) return 'Form 6 (Upper 6)';
      return `Form ${grade - 6}`;
    },
  };

  return { school: contextData, isLoading };
}

// ---- Backward-compatible default export ----
// Components importing `useSchoolContext` from this file
// get the school configuration data.
export function useSchoolContext(): SchoolContextData | null {
  const { school } = useSchoolConfig();
  return school;
}

// ---- Convenience hooks ----

export function useFeatureAccess(feature: string) {
  const school = useSchoolContext();
  return {
    hasAccess: school?.hasFeature(feature) ?? false,
    tier: school?.subscription.tier ?? 'trial',
    upgradeRequired: !school?.hasFeature(feature),
  };
}

export function usePermissionAccess(permission: string) {
  const school = useSchoolContext();
  return {
    hasAccess: school?.canAccess(permission) ?? false,
  };
}

export function useSubscriptionLimits() {
  const school = useSchoolContext();
  return {
    maxStudents: school?.subscription.limits.max_students ?? 0,
    maxStaff: school?.subscription.limits.max_staff ?? 0,
    storageLimit: school?.subscription.limits.storage_limit_gb ?? 0,
    tier: school?.subscription.tier ?? 'trial',
    canUpgrade: school?.subscription.tier !== 'enterprise',
  };
}
