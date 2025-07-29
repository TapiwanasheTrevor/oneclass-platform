'use client'

import type React from "react"
import { usePathname } from "next/navigation"
import { PlatformNavigation } from "@/components/navigation/PlatformNavigation"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/ui/error-boundary"

export function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  // Don't show navigation on auth pages
  const isAuthPage = pathname?.startsWith('/login') || 
                    pathname?.startsWith('/signup') || 
                    pathname?.startsWith('/auth');

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {!isAuthPage && (
          <ErrorBoundary fallback={<div className="p-4 bg-red-50 text-red-800">Navigation error</div>}>
            <PlatformNavigation />
          </ErrorBoundary>
        )}
        <main className={isAuthPage ? '' : 'min-h-[calc(100vh-64px)]'}>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
        <Toaster />
      </div>
    </ErrorBoundary>
  );
}