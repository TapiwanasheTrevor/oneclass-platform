"use client"

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import the dashboard with no SSR to prevent hydration issues
const DashboardContent = dynamic(() => import('./DashboardContent'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="text-lg font-medium text-gray-900">Loading Dashboard...</p>
        <p className="text-sm text-gray-500">Please wait while we prepare everything for you</p>
      </div>
    </div>
  )
});

export default function DashboardWrapper() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-lg font-medium text-gray-900">Loading Dashboard...</p>
          <p className="text-sm text-gray-500">Please wait while we prepare everything for you</p>
        </div>
      </div>
    );
  }

  return <DashboardContent />;
}
