"use client"

import { useState, useEffect } from 'react';
import { useAuth, useSchoolContext, SchoolRole } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import RoleBasedDashboard from '@/components/dashboard/RoleBasedDashboard';
import SuperAdminDashboard from '@/components/admin/SuperAdminDashboard';
import { ProgressTracker } from '@/components/progress/ProgressTracker';
import { DashboardLoading, PageLoading } from '@/components/ui/loading';
import { ErrorMessage, NetworkError } from '@/components/ui/error-boundary';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useMigrationCarePackage } from '@/hooks/useMigrationCarePackage';
import MigrationCarePackageModal from '@/components/migration/MigrationCarePackageModal';

export default function DashboardContent() {
  const { user, isLoading: authLoading, isPlatformAdmin } = useAuth();
  const { currentSchool } = useSchoolContext();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Migration Care Package state
  const {
    shouldShowModal: showMigrationModal,
    shouldBlockDashboard,
    setDecision,
    dismissModal,
    state: migrationState
  } = useMigrationCarePackage();

  // Debug logging
  console.log('Migration Care Package Debug:', {
    showMigrationModal,
    shouldBlockDashboard,
    migrationState,
    user: user?.email,
    authLoading,
    loading
  });

  // Map our platform roles to the dashboard component's expected format
  const mapUserRole = (): 'admin' | 'teacher' | 'parent' | 'student' => {
    // School admin sees admin dashboard
    if (isPlatformAdmin) {
      return 'admin';
    }
    
    // Map based on school role if available
    if (currentSchool?.role) {
      switch (currentSchool.role) {
        case 'admin':
        case 'principal':
        case 'registrar':
          return 'admin';
        case 'teacher':
          return 'teacher';
        case 'parent':
          return 'parent';
        default:
          return 'student';
      }
    }
    
    // Fallback to platform role
    switch (user?.platform_role) {
      case 'school_admin':
      case 'registrar':
        return 'admin';
      case 'teacher':
        return 'teacher';
      case 'parent':
        return 'parent';
      default:
        return 'student';
    }
  };

  const userRole = mapUserRole();

  const fetchDashboardData = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Fetch analytics data - use the correct endpoint without role parameter
      const analyticsEndpoint = `/api/v1/analytics/dashboard`;
        
      const response = await api.get(analyticsEndpoint);
      setDashboardData(response.data);
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err);
      setError(err.response?.data?.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && !authLoading) {
      fetchDashboardData();
    }
  }, [user, currentSchool, userRole, authLoading, isPlatformAdmin]);

  // Loading state
  if (authLoading) {
    return <PageLoading type="auth" message="Authenticating..." />;
  }

  if (loading) {
    return <DashboardLoading userRole={userRole} />;
  }

  // Check if user is super admin - render super admin dashboard
  if (isPlatformAdmin && user?.platform_role === 'super_admin') {
    // Super admins still need to see migration care package modal for their school
    if (showMigrationModal && shouldBlockDashboard) {
      return (
        <>
          <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center space-y-4">
              <h1 className="text-2xl font-bold text-gray-900">Welcome to OneClass!</h1>
              <p className="text-gray-600">Let's get your school set up for success.</p>
            </div>
          </div>
          <MigrationCarePackageModal
            isOpen={showMigrationModal}
            onClose={(decision) => {
              if (decision === 'selected') {
                // Handle package selection - could redirect to payment
                console.log('Package selected, redirect to payment');
              }
              setDecision(decision);
              dismissModal();
            }}
            onSelectPackage={(packageType) => {
              console.log('Selected package:', packageType);
            }}
          />
        </>
      );
    }

    return (
      <SuperAdminDashboard
        analytics={dashboardData}
        loading={loading}
      />
    );
  }

  // Migration Care Package Modal - blocks dashboard access for regular users
  if (showMigrationModal && shouldBlockDashboard) {
    return (
      <>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold text-gray-900">Welcome to OneClass!</h1>
            <p className="text-gray-600">Let's get your school set up for success.</p>
          </div>
        </div>
        <MigrationCarePackageModal
          isOpen={showMigrationModal}
          onClose={(decision) => {
            if (decision === 'selected') {
              // Handle package selection - could redirect to payment
              console.log('Package selected, redirect to payment');
            }
            setDecision(decision);
            dismissModal();
          }}
          onSelectPackage={(packageType) => {
            console.log('Selected package:', packageType);
          }}
        />
      </>
    );
  }

  // Not authenticated
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto" />
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">Authentication Required</h1>
            <p className="text-gray-600">Please log in to access your dashboard.</p>
          </div>
          <button
            onClick={() => window.location.href = '/sign-in'}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Go to Sign In
          </button>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4 max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto" />
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard Error</h1>
            <p className="text-gray-600">{error}</p>
          </div>
          <button
            onClick={() => {
              setError(null);
              fetchDashboardData();
            }}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // No school context for school-specific roles
  if (!currentSchool && ['admin', 'teacher'].includes(userRole)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <AlertTriangle className="w-16 h-16 text-yellow-500 mx-auto" />
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">School Selection Required</h1>
            <p className="text-gray-600">
              Please select a school to access your {userRole} dashboard.
            </p>
          </div>
          <button
            onClick={() => window.location.href = '/schools'}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Select School
          </button>
        </div>
      </div>
    );
  }

  // Render role-based dashboard
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <RoleBasedDashboard
          userRole={userRole}
          schoolContext={currentSchool}
          analytics={dashboardData}
        />
        
        {/* Progress Tracker for ongoing operations */}
        <ProgressTracker />
      </div>
    </div>
  );
}
