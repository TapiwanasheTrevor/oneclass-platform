/**
 * Clerk Authentication Provider with Multi-Tenant Support
 * Integrates Clerk auth with school-based multi-tenancy
 * Bypasses Clerk when no valid publishable key is configured
 */

'use client'

import React, { lazy, Suspense } from 'react'

interface ClerkProviderProps {
  children: React.ReactNode
}

/**
 * Check if Clerk is properly configured
 */
function isClerkConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  return !!key && !key.includes('your-') && key.startsWith('pk_')
}

// Lazy-load the actual Clerk provider only when configured
const ClerkProviderWithAuth = lazy(() => import('./ClerkProviderInner'))

export function ClerkProvider({ children }: ClerkProviderProps) {
  if (!isClerkConfigured()) {
    // Dev mode: no Clerk auth, just render children
    return <>{children}</>
  }

  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    }>
      <ClerkProviderWithAuth>{children}</ClerkProviderWithAuth>
    </Suspense>
  )
}

export default ClerkProvider
