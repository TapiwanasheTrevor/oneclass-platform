'use client'

import React from 'react'
import { ClerkProvider as BaseClerkProvider } from '@clerk/nextjs'
import { dark } from '@clerk/themes'

interface ClerkProviderInnerProps {
  children: React.ReactNode
}

export default function ClerkProviderInner({ children }: ClerkProviderInnerProps) {
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
  const schoolDisplayName = subdomain
    ? subdomain
        .split('-')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ')
    : 'your school'

  const branding = (() => {
    if (typeof window === 'undefined') {
      return {
        theme: 'light',
        primaryColor: '#2563eb',
        backgroundColor: '#ffffff',
        fontFamily: 'ui-sans-serif',
      }
    }

    const styles = window.getComputedStyle(document.documentElement)
    return {
      theme: styles.getPropertyValue('--theme-mode').trim() || 'light',
      primaryColor: styles.getPropertyValue('--color-primary').trim() || '#2563eb',
      backgroundColor: styles.getPropertyValue('--color-background').trim() || '#ffffff',
      fontFamily: styles.getPropertyValue('--font-primary').trim() || 'ui-sans-serif',
    }
  })()

  const clerkConfig = {
    publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!,
    appearance: {
      baseTheme: branding.theme === 'dark' ? dark : undefined,
      variables: {
        colorPrimary: branding.primaryColor,
        colorBackground: branding.backgroundColor,
        fontFamily: `${branding.fontFamily}, sans-serif`,
      },
      elements: {
        formButtonPrimary: {
          backgroundColor: branding.primaryColor,
        },
        card: {
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    localization: {
      signIn: {
        start: {
          title: `Welcome back to ${schoolDisplayName}`,
          subtitle: 'Please sign in to access your account',
        },
      },
      signUp: {
        start: {
          title: `Join ${schoolDisplayName}`,
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
