// =====================================================
// Comprehensive Loading Components
// File: frontend/components/ui/loading.tsx
// =====================================================

import React from 'react';
import { Loader2, Building2, GraduationCap, Users, BookOpen } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <Loader2 className={`animate-spin ${sizeClasses[size]} ${className}`} />
  );
}

interface PageLoadingProps {
  message?: string;
  type?: 'dashboard' | 'auth' | 'onboarding' | 'school' | 'generic';
}

export function PageLoading({ message, type = 'generic' }: PageLoadingProps) {
  const getIcon = () => {
    switch (type) {
      case 'dashboard':
        return <Building2 className="w-12 h-12 text-blue-600" />;
      case 'auth':
        return <GraduationCap className="w-12 h-12 text-blue-600" />;
      case 'onboarding':
        return <Users className="w-12 h-12 text-blue-600" />;
      case 'school':
        return <BookOpen className="w-12 h-12 text-blue-600" />;
      default:
        return <Building2 className="w-12 h-12 text-blue-600" />;
    }
  };

  const getDefaultMessage = () => {
    switch (type) {
      case 'dashboard':
        return 'Loading your dashboard...';
      case 'auth':
        return 'Authenticating...';
      case 'onboarding':
        return 'Setting up your school...';
      case 'school':
        return 'Loading school data...';
      default:
        return 'Loading...';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          {getIcon()}
        </div>
        <div className="space-y-2">
          <LoadingSpinner size="lg" className="mx-auto" />
          <p className="text-lg font-medium text-gray-900">
            {message || getDefaultMessage()}
          </p>
          <p className="text-sm text-gray-500">
            Please wait while we prepare everything for you
          </p>
        </div>
      </div>
    </div>
  );
}

interface CardLoadingProps {
  title?: string;
  rows?: number;
  className?: string;
}

export function CardLoading({ title, rows = 3, className = '' }: CardLoadingProps) {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        {title && (
          <div className="mb-4">
            <div className="h-6 bg-gray-200 rounded animate-pulse" style={{ width: '60%' }} />
          </div>
        )}
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: '80%' }} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface TableLoadingProps {
  columns?: number;
  rows?: number;
  className?: string;
}

export function TableLoading({ columns = 4, rows = 5, className = '' }: TableLoadingProps) {
  return (
    <div className={`overflow-hidden ${className}`}>
      <div className="animate-pulse">
        {/* Header */}
        <div className="grid gap-4 mb-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded" />
          ))}
        </div>
        {/* Rows */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="grid gap-4 mb-3" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div key={colIndex} className="h-4 bg-gray-100 rounded" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

interface DashboardLoadingProps {
  userRole?: 'admin' | 'teacher' | 'parent' | 'student';
}

export function DashboardLoading({ userRole = 'admin' }: DashboardLoadingProps) {
  const getStatsCount = () => {
    switch (userRole) {
      case 'admin':
        return 4;
      case 'teacher':
        return 4;
      case 'parent':
        return 2;
      case 'student':
        return 2;
      default:
        return 4;
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header Loading */}
      <div className="space-y-2">
        <div className="h-8 bg-gray-200 rounded animate-pulse" style={{ width: '40%' }} />
        <div className="h-4 bg-gray-100 rounded animate-pulse" style={{ width: '60%' }} />
      </div>

      {/* Stats Cards Loading */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: getStatsCount() }).map((_, i) => (
          <CardLoading key={i} rows={2} />
        ))}
      </div>

      {/* Main Content Loading */}
      <div className="grid gap-6 md:grid-cols-2">
        <CardLoading title="Quick Actions" rows={4} />
        <CardLoading title="Recent Activity" rows={4} />
      </div>

      {/* Additional Content for Admin */}
      {userRole === 'admin' && (
        <div className="grid gap-6 md:grid-cols-3">
          <CardLoading title="Analytics" rows={3} />
          <CardLoading title="System Health" rows={3} />
          <CardLoading title="Notifications" rows={3} />
        </div>
      )}
    </div>
  );
}

export function InlineLoading({ message = 'Loading...', className = '' }: { message?: string; className?: string }) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <LoadingSpinner size="sm" />
      <span className="text-sm text-gray-600">{message}</span>
    </div>
  );
}

export function ButtonLoading({ message = 'Loading...', className = '' }: { message?: string; className?: string }) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <LoadingSpinner size="sm" />
      <span>{message}</span>
    </div>
  );
}