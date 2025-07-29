// =====================================================
// School Context Hook for Frontend Multitenancy
// Implements multitenancy enhancement plan requirements
// File: frontend/hooks/useSchoolContext.ts
// =====================================================

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { api } from '@/lib/api';

interface SchoolConfiguration {
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

interface SchoolDomain {
  domain: string;
  is_primary: boolean;
  is_custom: boolean;
}

interface SchoolContext {
  school: {
    id: string;
    name: string;
    type: string;
    config: SchoolConfiguration;
    domains: SchoolDomain[];
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

export function useSchoolContext(): SchoolContext | null {
  const { user } = useAuth();
  
  const { data: schoolData } = useQuery({
    queryKey: ['school-context', user?.school_id],
    queryFn: async () => {
      if (!user?.school_id) return null;
      
      const response = await api.get(`/schools/${user.school_id}/context`);
      return response.data;
    },
    enabled: !!user?.school_id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });

  if (!schoolData || !user) return null;

  return {
    school: {
      id: schoolData.id,
      name: schoolData.name,
      type: schoolData.type,
      config: schoolData.config,
      domains: schoolData.domains
    },
    branding: {
      logo_url: schoolData.config.logo_url,
      primary_color: schoolData.config.primary_color,
      secondary_color: schoolData.config.secondary_color,
      accent_color: schoolData.config.accent_color,
      font_family: schoolData.config.font_family
    },
    features: schoolData.config.features_enabled,
    subscription: {
      tier: schoolData.config.subscription_tier,
      limits: {
        max_students: schoolData.config.max_students,
        max_staff: 50, // This would come from config
        storage_limit_gb: 10 // This would come from config
      }
    },
    academic: {
      year_start_month: schoolData.config.academic_year_start_month,
      terms_per_year: schoolData.config.terms_per_year,
      grading_system: schoolData.config.grading_system
    },
    regional: {
      timezone: schoolData.config.timezone,
      currency: schoolData.config.currency,
      date_format: schoolData.config.date_format,
      primary_language: schoolData.config.language_primary,
      secondary_language: schoolData.config.language_secondary
    },
    hasFeature: (feature: string) => {
      return schoolData.config.features_enabled[feature] === true &&
             user.available_features.includes(feature);
    },
    canAccess: (permission: string) => {
      return user.permissions.includes('*') || user.permissions.includes(permission);
    },
    formatCurrency: (amount: number) => {
      const currency = schoolData.config.currency;
      return new Intl.NumberFormat('en-ZW', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
      }).format(amount);
    },
    formatDate: (date: Date) => {
      const format = schoolData.config.date_format;
      const locale = schoolData.config.language_primary === 'en' ? 'en-ZW' : 'en-US';
      
      if (format === 'DD/MM/YYYY') {
        return date.toLocaleDateString(locale, {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
        });
      }
      
      return date.toLocaleDateString(locale);
    },
    getGradeDisplay: (grade: number) => {
      if (grade <= 7) return `Grade ${grade}`;
      if (grade === 12) return `Form 5 (Lower 6)`;
      if (grade === 13) return `Form 6 (Upper 6)`;
      return `Form ${grade - 6}`;
    }
  };
}

// Hook for feature-gated components
export function useFeatureAccess(feature: string) {
  const schoolContext = useSchoolContext();
  
  return {
    hasAccess: schoolContext?.hasFeature(feature) ?? false,
    tier: schoolContext?.subscription.tier ?? 'trial',
    upgradeRequired: !schoolContext?.hasFeature(feature)
  };
}

// Hook for permission-gated components
export function usePermissionAccess(permission: string) {
  const schoolContext = useSchoolContext();
  
  return {
    hasAccess: schoolContext?.canAccess(permission) ?? false,
    userRole: schoolContext?.school ? 'unknown' : 'guest'
  };
}

// Hook for subscription limits
export function useSubscriptionLimits() {
  const schoolContext = useSchoolContext();
  
  return {
    maxStudents: schoolContext?.subscription.limits.max_students ?? 0,
    maxStaff: schoolContext?.subscription.limits.max_staff ?? 0,
    storageLimit: schoolContext?.subscription.limits.storage_limit_gb ?? 0,
    tier: schoolContext?.subscription.tier ?? 'trial',
    canUpgrade: schoolContext?.subscription.tier !== 'enterprise'
  };
}