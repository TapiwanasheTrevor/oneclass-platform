"use client"

import { getCurrentSubdomain, getSchoolFromSubdomain, isMainPlatform } from '@/utils/subdomain';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

interface TenantInfo {
  subdomain: string;
  schoolName: string;
  schoolId: string;
  isMainPlatform: boolean;
}

interface TenantContextType {
  tenant: TenantInfo | null;
  isLoading: boolean;
  error: string | null;
  refreshTenant: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export function useTenant() {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}

interface TenantProviderProps {
  children: ReactNode;
}

export function TenantProvider({ children }: TenantProviderProps) {
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTenantInfo = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if we're on the main platform
      if (isMainPlatform()) {
        setTenant({
          subdomain: '',
          schoolName: 'OneClass Platform',
          schoolId: '',
          isMainPlatform: true,
        });
        return;
      }

      // Get current subdomain
      const subdomain = getCurrentSubdomain();
      if (!subdomain) {
        throw new Error('No subdomain detected');
      }

      // Fetch school information from API (authoritative)
      const schoolInfo = await getSchoolFromSubdomain(subdomain);
      if (!schoolInfo) {
        throw new Error('School not found for subdomain');
      }
      setTenant({
        subdomain: schoolInfo.subdomain,
        schoolName: schoolInfo.schoolName,
        schoolId: schoolInfo.schoolId,
        isMainPlatform: false,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tenant information';
      setError(errorMessage);
      console.error('Tenant loading error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshTenant = async () => {
    await loadTenantInfo();
  };

  useEffect(() => {
    loadTenantInfo();
  }, []);

  // Do not inject tenant headers from client; backend derives from Host/JWT

  const value: TenantContextType = {
    tenant,
    isLoading,
    error,
    refreshTenant,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}

// Tenant-aware error boundary
export function TenantErrorBoundary({ children }: { children: ReactNode }) {
  const { tenant, isLoading, error } = useTenant();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-lg font-medium text-gray-900">Loading School...</p>
          <p className="text-sm text-gray-500">Detecting your school environment</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4 max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">School Not Found</h1>
          <p className="text-gray-600">{error}</p>
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              Make sure you're accessing the correct subdomain for your school.
            </p>
            <p className="text-sm text-gray-500">
              Format: <code className="bg-gray-100 px-2 py-1 rounded">school-name.oneclass.local</code>
            </p>
          </div>
          <button
            onClick={() => window.location.href = 'http://oneclass.local:3000'}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Go to Main Platform
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Tenant info display component
export function TenantInfo() {
  const { tenant } = useTenant();

  if (!tenant || tenant.isMainPlatform) {
    return null;
  }

  return (
    <div className="bg-blue-50 border-b border-blue-200 px-4 py-2">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
          <span className="text-sm font-medium text-blue-900">
            {tenant.schoolName}
          </span>
          <span className="text-sm text-blue-700">
            ({tenant.subdomain}.oneclass.local)
          </span>
        </div>
        <div className="text-xs text-blue-600">
          School Environment
        </div>
      </div>
    </div>
  );
}
