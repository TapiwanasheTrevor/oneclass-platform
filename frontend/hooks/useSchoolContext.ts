// =====================================================
// Unified School Context Hook
// Merges authenticated school membership state with canonical
// school configuration data from the backend.
// File: frontend/hooks/useSchoolContext.ts
// =====================================================

'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth, type SchoolMembership } from './useAuth';

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

export interface ResolvedSchoolInfo {
  id: string;
  name: string;
  subdomain: string;
  type: string;
  subscription_tier: string;
  config: SchoolConfiguration;
}

export interface ActiveSchoolSummary {
  school_id: string;
  school_name: string;
  school_subdomain: string;
  role?: string;
  subscription_tier?: string;
  enabled_modules: string[];
}

export interface UnifiedSchoolContext {
  school: ResolvedSchoolInfo | null;
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
  currentSchool: SchoolMembership | null;
  availableSchools: SchoolMembership[];
  schoolContext: ActiveSchoolSummary | null;
  isLoading: boolean;
  hasMultipleSchools: boolean;
  switchSchool: (schoolId: string) => Promise<void>;
  hasFeature: (feature: string) => boolean;
  canAccess: (permission: string) => boolean;
  formatCurrency: (amount: number) => string;
  formatDate: (date: Date) => string;
  getGradeDisplay: (grade: number) => string;
  getCurrentSchoolId: () => string | undefined;
  getCurrentSchoolName: () => string | undefined;
  getUserRoleInCurrentSchool: () => string | undefined;
  getUserPermissionsInCurrentSchool: () => string[];
}

interface SchoolContextApiResponse {
  id: string;
  name: string;
  subdomain: string;
  type?: string;
  subscription_tier?: string;
  config?: Partial<SchoolConfiguration>;
  enabled_modules?: string[];
  features_enabled?: Record<string, boolean>;
  schoolContext?: {
    school_id: string;
    school_name: string;
    school_subdomain: string;
    subscription_tier?: string;
    enabled_modules?: string[];
  };
}

const DEFAULT_CONFIG: SchoolConfiguration = {
  school_id: '',
  primary_color: '#2563eb',
  secondary_color: '#64748b',
  accent_color: '#10b981',
  font_family: 'ui-sans-serif',
  timezone: 'Africa/Harare',
  language_primary: 'en',
  currency: 'USD',
  date_format: 'DD/MM/YYYY',
  features_enabled: {},
  subscription_tier: 'basic',
  max_students: 500,
  grading_system: { system: 'zimbabwe' },
  notification_settings: {},
  student_id_format: 'AUTO',
  academic_year_start_month: 1,
  terms_per_year: 3,
};

const FEATURE_ALIASES: Record<string, string[]> = {
  finance_module: ['finance_module', 'finance_management'],
  sis: ['sis', 'student_information_system', 'sis_module'],
  academic: ['academic', 'academic_management'],
  parent_portal: ['parent_portal'],
  advanced_reporting: ['advanced_reporting'],
  ai_assistance: ['ai_assistance'],
  ministry_reporting: ['ministry_reporting'],
};

function resolveFeatureAliases(feature: string): string[] {
  return FEATURE_ALIASES[feature] || [feature];
}

export function useSchoolContext(): UnifiedSchoolContext {
  const {
    currentSchool,
    availableSchools,
    switchSchool,
    hasPermission,
    user,
    isLoading: authLoading,
  } = useAuth();

  const schoolId = currentSchool?.school_id || user?.current_school_id || user?.primary_school_id;

  const { data: schoolData, isLoading: configLoading } = useQuery({
    queryKey: ['school-context', schoolId],
    queryFn: async (): Promise<SchoolContextApiResponse | null> => {
      if (!schoolId) return null;
      const response = await api.get(`/api/v1/platform/schools/${schoolId}/context`);
      return response.data as SchoolContextApiResponse;
    },
    enabled: !!schoolId,
    staleTime: 5 * 60 * 1000,
  });

  return useMemo(() => {
    const config: SchoolConfiguration = {
      ...DEFAULT_CONFIG,
      ...(schoolData?.config || {}),
      school_id: schoolId || schoolData?.config?.school_id || '',
      features_enabled: {
        ...DEFAULT_CONFIG.features_enabled,
        ...(schoolData?.features_enabled || {}),
        ...(schoolData?.config?.features_enabled || {}),
      },
      grading_system: schoolData?.config?.grading_system || DEFAULT_CONFIG.grading_system,
      notification_settings:
        schoolData?.config?.notification_settings || DEFAULT_CONFIG.notification_settings,
    };

    const enabledModules =
      schoolData?.enabled_modules ||
      schoolData?.schoolContext?.enabled_modules ||
      Object.keys(config.features_enabled).filter((feature) => config.features_enabled[feature]);

    const school =
      schoolId || schoolData
        ? {
            id: schoolData?.id || schoolId || '',
            name: schoolData?.name || currentSchool?.school_name || 'OneClass School',
            subdomain:
              schoolData?.subdomain || currentSchool?.school_subdomain || '',
            type: schoolData?.type || 'school',
            subscription_tier:
              schoolData?.subscription_tier || config.subscription_tier || 'basic',
            config,
          }
        : null;

    const schoolContext: ActiveSchoolSummary | null = currentSchool
      ? {
          school_id: currentSchool.school_id,
          school_name: currentSchool.school_name,
          school_subdomain: currentSchool.school_subdomain,
          role: currentSchool.role,
          subscription_tier:
            schoolData?.subscription_tier || config.subscription_tier || 'basic',
          enabled_modules: enabledModules,
        }
      : schoolData?.schoolContext
        ? {
            school_id: schoolData.schoolContext.school_id,
            school_name: schoolData.schoolContext.school_name,
            school_subdomain: schoolData.schoolContext.school_subdomain,
            subscription_tier: schoolData.schoolContext.subscription_tier,
            enabled_modules: schoolData.schoolContext.enabled_modules || enabledModules,
          }
        : null;

    const hasFeature = (feature: string): boolean => {
      const aliases = resolveFeatureAliases(feature);
      return aliases.some((alias) => {
        return config.features_enabled[alias] === true || enabledModules.includes(alias);
      });
    };

    return {
      school,
      branding: {
        logo_url: config.logo_url,
        primary_color: config.primary_color || DEFAULT_CONFIG.primary_color,
        secondary_color: config.secondary_color || DEFAULT_CONFIG.secondary_color,
        accent_color: config.accent_color || DEFAULT_CONFIG.accent_color,
        font_family: config.font_family || DEFAULT_CONFIG.font_family,
      },
      features: config.features_enabled,
      subscription: {
        tier: school?.subscription_tier || config.subscription_tier || 'basic',
        limits: {
          max_students: config.max_students || DEFAULT_CONFIG.max_students,
          max_staff: 50,
          storage_limit_gb: 10,
        },
      },
      academic: {
        year_start_month:
          config.academic_year_start_month ||
          DEFAULT_CONFIG.academic_year_start_month,
        terms_per_year: config.terms_per_year || DEFAULT_CONFIG.terms_per_year,
        grading_system: config.grading_system || DEFAULT_CONFIG.grading_system,
      },
      regional: {
        timezone: config.timezone || DEFAULT_CONFIG.timezone,
        currency: config.currency || DEFAULT_CONFIG.currency,
        date_format: config.date_format || DEFAULT_CONFIG.date_format,
        primary_language:
          config.language_primary || DEFAULT_CONFIG.language_primary,
        secondary_language: config.language_secondary,
      },
      currentSchool,
      availableSchools,
      schoolContext,
      isLoading: authLoading || configLoading,
      hasMultipleSchools: availableSchools.length > 1,
      switchSchool,
      hasFeature,
      canAccess: (permission: string) => hasPermission(permission),
      formatCurrency: (amount: number) => {
        return new Intl.NumberFormat('en-ZW', {
          style: 'currency',
          currency: config.currency || DEFAULT_CONFIG.currency,
          minimumFractionDigits: 2,
        }).format(amount);
      },
      formatDate: (date: Date) => {
        const locale =
          (config.language_primary || DEFAULT_CONFIG.language_primary) === 'en'
            ? 'en-ZW'
            : 'en-US';
        return date.toLocaleDateString(locale);
      },
      getGradeDisplay: (grade: number) => {
        if (grade <= 7) return `Grade ${grade}`;
        if (grade === 12) return 'Form 5 (Lower 6)';
        if (grade === 13) return 'Form 6 (Upper 6)';
        return `Form ${grade - 6}`;
      },
      getCurrentSchoolId: () => currentSchool?.school_id,
      getCurrentSchoolName: () => currentSchool?.school_name,
      getUserRoleInCurrentSchool: () => currentSchool?.role,
      getUserPermissionsInCurrentSchool: () => currentSchool?.permissions || [],
    };
  }, [
    authLoading,
    availableSchools,
    configLoading,
    currentSchool,
    hasPermission,
    schoolData,
    schoolId,
    switchSchool,
    user?.current_school_id,
    user?.primary_school_id,
  ]);
}

export function useSchoolConfig(): {
  school: UnifiedSchoolContext['school'];
  isLoading: boolean;
} {
  const schoolContext = useSchoolContext();
  return {
    school: schoolContext.school,
    isLoading: schoolContext.isLoading,
  };
}

export function useFeatureAccess(feature: string) {
  const school = useSchoolContext();
  return {
    hasAccess: school.hasFeature(feature),
    tier: school.subscription.tier,
    upgradeRequired: !school.hasFeature(feature),
  };
}

export function usePermissionAccess(permission: string) {
  const school = useSchoolContext();
  return {
    hasAccess: school.canAccess(permission),
  };
}

export function useSubscriptionLimits() {
  const school = useSchoolContext();
  return {
    maxStudents: school.subscription.limits.max_students,
    maxStaff: school.subscription.limits.max_staff,
    storageLimit: school.subscription.limits.storage_limit_gb,
    tier: school.subscription.tier,
    canUpgrade: school.subscription.tier !== 'enterprise',
  };
}
