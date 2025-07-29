/**
 * Clerk Authentication Provider with Multi-Tenant Support
 * Integrates Clerk auth with school-based multi-tenancy
 */

'use client'

import React from 'react'
import { ClerkProvider as BaseClerkProvider } from '@clerk/nextjs'
import { useSearchParams } from 'next/navigation'
import { dark } from '@clerk/themes'
import { useSchoolContext } from '@/hooks/useSchoolContext'

interface ClerkProviderProps {
  children: React.ReactNode
}

export function ClerkProvider({ children }: ClerkProviderProps) {
  // TODO: Re-enable school context integration when dependencies are resolved
  // const { school, isLoading } = useSchoolContext()
  const school = null // Temporary default
  const isLoading = false // Temporary default
  const searchParams = useSearchParams()
  
  // Get subdomain from URL or headers
  const getSubdomain = () => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname
      const parts = hostname.split('.')
      if (parts.length >= 3 && parts[0] !== 'www') {
        return parts[0]
      }
    }
    return null
  }
  
  const subdomain = getSubdomain()
  
  // Clerk configuration with school context
  const clerkConfig = {
    // Use subdomain as organization context
    publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!,
    
    // Custom appearance based on school branding
    appearance: {
      baseTheme: school?.configuration?.branding?.theme === 'dark' ? dark : undefined,
      variables: {
        colorPrimary: school?.configuration?.branding?.primary_color || '#2563eb',
        colorBackground: school?.configuration?.branding?.background_color || '#ffffff',
        fontFamily: school?.configuration?.branding?.font_family || 'Inter, sans-serif',
      },
      elements: {
        formButtonPrimary: {
          backgroundColor: school?.configuration?.branding?.primary_color || '#2563eb',
        },
        card: {
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
        },
        headerTitle: {
          color: school?.configuration?.branding?.primary_color || '#1f2937',
        },
        formFieldInput: {
          borderColor: school?.configuration?.branding?.secondary_color || '#d1d5db',
        },
        footerActionLink: {
          color: school?.configuration?.branding?.accent_color || '#2563eb',
        },
      },
      layout: {
        logoImageUrl: school?.configuration?.branding?.logo_url,
        socialButtonsVariant: 'iconButton',
        socialButtonsPlacement: 'bottom',
      },
    },
    
    // Custom localization for Zimbabwe
    localization: {
      signIn: {
        start: {
          title: `Welcome back to ${school?.name || 'your school'}`,
          subtitle: 'Please sign in to access your account',
        },
      },
      signUp: {
        start: {
          title: `Join ${school?.name || 'the school'}`,
          subtitle: 'Create your account to get started',
        },
      },
    },
    
    // Routing configuration
    signInUrl: '/sign-in',
    signUpUrl: '/sign-up',
    fallbackRedirectUrl: '/dashboard',
    afterSignUpUrl: '/onboarding/user',
    
    // Multi-tenant configuration
    ...(subdomain && {
      // Pass subdomain as organization context
      organizationSlug: subdomain,
    }),
  }
  
  // Show loading state while school context is loading
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }
  
  // Temporarily disable Clerk authentication while we set up proper keys
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  
  // If no valid Clerk key, return children without Clerk wrapper
  if (!publishableKey || publishableKey.includes('your-publishable-key-here')) {
    return (
      <div>
        {/* Temporary: No Clerk authentication */}
        <SchoolContextInjector subdomain={subdomain}>
          {children}
        </SchoolContextInjector>
      </div>
    )
  }

  return (
    <BaseClerkProvider {...clerkConfig}>
      <SchoolContextInjector subdomain={subdomain}>
        {children}
      </SchoolContextInjector>
    </BaseClerkProvider>
  )
}

/**
 * Component to inject school context into Clerk user metadata
 */
function SchoolContextInjector({ 
  children, 
  subdomain 
}: { 
  children: React.ReactNode
  subdomain: string | null 
}) {
  // TODO: Re-enable when useSchoolContext is properly configured
  // const { school } = useSchoolContext()
  const school = null // Temporary default
  
  React.useEffect(() => {
    // Inject school context into global window for Clerk webhooks
    if (typeof window !== 'undefined' && school) {
      (window as any).__SCHOOL_CONTEXT__ = {
        school_id: school.id,
        school_name: school.name,
        subdomain: subdomain,
        subscription_tier: school.subscription_tier,
        enabled_modules: school.configuration?.features?.enabled_modules || [],
      }
    }
  }, [school, subdomain])
  
  return <>{children}</>
}

export default ClerkProvider
