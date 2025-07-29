// =====================================================
// School Theme Provider for Dynamic Branding
// Implements multitenancy enhancement plan requirements
// File: frontend/components/providers/SchoolThemeProvider.tsx
// =====================================================

'use client';

import React, { createContext, useContext, useEffect } from 'react';
import { useSchoolContext } from '@/hooks/useSchoolContext';

interface ThemeContextValue {
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  fontFamily: string;
  logoUrl?: string;
  applyTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

interface SchoolThemeProviderProps {
  children: React.ReactNode;
}

export function SchoolThemeProvider({ children }: SchoolThemeProviderProps) {
  const schoolContext = useSchoolContext();

  const themeValue: ThemeContextValue = {
    primaryColor: schoolContext?.branding.primary_color ?? '#1e40af',
    secondaryColor: schoolContext?.branding.secondary_color ?? '#10b981',
    accentColor: schoolContext?.branding.accent_color ?? '#f59e0b',
    fontFamily: schoolContext?.branding.font_family ?? 'Inter',
    logoUrl: schoolContext?.branding.logo_url,
    applyTheme: () => {
      if (!schoolContext) return;

      const root = document.documentElement;
      
      // Apply CSS custom properties for dynamic theming
      root.style.setProperty('--color-primary', schoolContext.branding.primary_color);
      root.style.setProperty('--color-secondary', schoolContext.branding.secondary_color);
      root.style.setProperty('--color-accent', schoolContext.branding.accent_color);
      root.style.setProperty('--font-primary', schoolContext.branding.font_family);
      
      // Convert hex to hsl for shadcn/ui compatibility
      const hexToHsl = (hex: string) => {
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h, s, l = (max + min) / 2;

        if (max === min) {
          h = s = 0;
        } else {
          const d = max - min;
          s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
          switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
          }
          h! /= 6;
        }
        
        return `${Math.round(h! * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
      };

      // Apply theme colors to CSS variables
      root.style.setProperty('--primary', hexToHsl(schoolContext.branding.primary_color));
      root.style.setProperty('--secondary', hexToHsl(schoolContext.branding.secondary_color));
      root.style.setProperty('--accent', hexToHsl(schoolContext.branding.accent_color));
      
      // Update favicon if available
      if (schoolContext.branding.logo_url) {
        const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
        if (favicon) {
          favicon.href = schoolContext.branding.logo_url;
        }
      }
      
      // Update page title with school name
      document.title = `OneClass - ${schoolContext.school.name}`;
    }
  };

  // Apply theme on mount and when school context changes
  useEffect(() => {
    themeValue.applyTheme();
  }, [schoolContext?.school.id]);

  return (
    <ThemeContext.Provider value={themeValue}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useSchoolTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useSchoolTheme must be used within SchoolThemeProvider');
  }
  return context;
}

// Component for displaying school logo
export function SchoolLogo({ className, fallback }: { className?: string; fallback?: React.ReactNode }) {
  const { logoUrl } = useSchoolTheme();
  const schoolContext = useSchoolContext();
  
  if (logoUrl) {
    return (
      <img
        src={logoUrl}
        alt={`${schoolContext?.school.name} logo`}
        className={className}
        onError={(e) => {
          // Hide image on error and show fallback
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
    );
  }
  
  if (fallback) {
    return <>{fallback}</>;
  }
  
  // Default fallback - school initials
  const initials = schoolContext?.school.name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 3) ?? '1C';
  
  return (
    <div className={`flex items-center justify-center bg-primary text-primary-foreground font-bold ${className}`}>
      {initials}
    </div>
  );
}