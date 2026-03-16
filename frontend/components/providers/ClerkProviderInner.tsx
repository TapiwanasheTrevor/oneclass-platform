'use client'

import React from 'react'
import { ClerkProvider as BaseClerkProvider } from '@clerk/nextjs'
import { dark } from '@clerk/themes'

interface ClerkProviderInnerProps {
  children: React.ReactNode
}

export default function ClerkProviderInner({ children }: ClerkProviderInnerProps) {
  const school = null as any // TODO: Re-enable school context

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

  const clerkConfig = {
    publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!,
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
      },
    },
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
    signInUrl: '/sign-in',
    signUpUrl: '/sign-up',
    fallbackRedirectUrl: '/dashboard',
    afterSignUpUrl: '/onboarding/user',
    ...(subdomain && { organizationSlug: subdomain }),
  }

  return (
    <BaseClerkProvider {...clerkConfig}>
      {children}
    </BaseClerkProvider>
  )
}
