"use client"

/**
 * Unauthorized Access Page
 * Handles various authorization and tenant access errors
 */

import React from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { AlertCircle, Lock, Home, ArrowLeft, Shield, Building2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

interface ErrorInfo {
  icon: React.ReactNode
  title: string
  description: string
  suggestion: string
  actions: Array<{
    label: string
    action: () => void
    variant?: 'default' | 'outline' | 'destructive'
  }>
}

export default function UnauthorizedPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const error = searchParams.get('error') || 'access_denied'
  const requiredFor = searchParams.get('required_for')
  const schoolName = searchParams.get('school_name')
  
  const getErrorInfo = (): ErrorInfo => {
    switch (error) {
      case 'wrong_school':
        return {
          icon: <Building2 className="h-12 w-12 text-orange-500" />,
          title: 'Wrong School Access',
          description: `You are trying to access ${schoolName || 'a different school'}'s platform, but your account belongs to a different school.`,
          suggestion: 'Please log in using your school\'s subdomain or contact your school administrator.',
          actions: [
            {
              label: 'Go to My School',
              action: () => {
                // This would redirect to their actual school's subdomain
                // For now, redirect to root domain
                window.location.href = '/'
              }
            },
            {
              label: 'Contact Support',
              action: () => router.push('/support'),
              variant: 'outline'
            }
          ]
        }
      
      case 'insufficient_permissions':
        return {
          icon: <Shield className="h-12 w-12 text-red-500" />,
          title: 'Insufficient Permissions',
          description: `You don't have the required permissions to access ${requiredFor || 'this page'}.`,
          suggestion: 'Contact your school administrator to request access to this feature.',
          actions: [
            {
              label: 'Go to Dashboard',
              action: () => router.push('/dashboard')
            },
            {
              label: 'Request Access',
              action: () => router.push('/request-access'),
              variant: 'outline'
            }
          ]
        }
      
      case 'module_not_available':
        return {
          icon: <Lock className="h-12 w-12 text-purple-500" />,
          title: 'Module Not Available',
          description: 'This module is not included in your school\'s current subscription plan.',
          suggestion: 'Contact your school administrator to upgrade your subscription plan.',
          actions: [
            {
              label: 'View Available Features',
              action: () => router.push('/features')
            },
            {
              label: 'Contact Administrator',
              action: () => router.push('/contact-admin'),
              variant: 'outline'
            }
          ]
        }
      
      case 'session_expired':
        return {
          icon: <AlertCircle className="h-12 w-12 text-yellow-500" />,
          title: 'Session Expired',
          description: 'Your session has expired for security reasons.',
          suggestion: 'Please log in again to continue using the platform.',
          actions: [
            {
              label: 'Log In Again',
              action: () => router.push('/login')
            }
          ]
        }
      
      case 'account_suspended':
        return {
          icon: <Lock className="h-12 w-12 text-red-600" />,
          title: 'Account Suspended',
          description: 'Your account has been temporarily suspended.',
          suggestion: 'Please contact your school administrator for assistance.',
          actions: [
            {
              label: 'Contact Administrator',
              action: () => router.push('/contact-admin')
            }
          ]
        }
      
      default:
        return {
          icon: <AlertCircle className="h-12 w-12 text-gray-500" />,
          title: 'Access Denied',
          description: 'You are not authorized to access this resource.',
          suggestion: 'Please check your permissions or contact support.',
          actions: [
            {
              label: 'Go Back',
              action: () => router.back(),
              variant: 'outline'
            },
            {
              label: 'Go to Dashboard',
              action: () => router.push('/dashboard')
            }
          ]
        }
    }
  }
  
  const errorInfo = getErrorInfo()
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Error Card */}
        <Card className="border-2">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-4">
              {errorInfo.icon}
            </div>
            <CardTitle className="text-xl text-gray-900">
              {errorInfo.title}
            </CardTitle>
            <CardDescription className="text-gray-600">
              {errorInfo.description}
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Error Details */}
            {error && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Error Code:</span>
                <Badge variant="secondary" className="font-mono text-xs">
                  {error.toUpperCase()}
                </Badge>
              </div>
            )}
            
            {/* Suggestion Alert */}
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {errorInfo.suggestion}
              </AlertDescription>
            </Alert>
            
            {/* Action Buttons */}
            <div className="space-y-3">
              {errorInfo.actions.map((action, index) => (
                <Button
                  key={index}
                  onClick={action.action}
                  variant={action.variant || 'default'}
                  className="w-full"
                >
                  {action.label}
                </Button>
              ))}
            </div>
            
            {/* Additional Info */}
            {requiredFor && (
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Requested Resource:</strong> {requiredFor}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Help Section */}
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="p-4">
            <div className="text-center space-y-2">
              <h3 className="font-semibold text-blue-900">Need Help?</h3>
              <p className="text-sm text-blue-800">
                If you continue to experience issues, please contact support.
              </p>
              <div className="flex gap-2 justify-center">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => router.push('/help')}
                  className="border-blue-300 text-blue-700 hover:bg-blue-100"
                >
                  Help Center
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => router.push('/support')}
                  className="border-blue-300 text-blue-700 hover:bg-blue-100"
                >
                  Contact Support
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Navigation Helper */}
        <div className="text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/')}
            className="text-gray-500 hover:text-gray-700"
          >
            <Home className="h-4 w-4 mr-2" />
            Back to Home
          </Button>
        </div>
        
        {/* Footer */}
        <div className="text-center text-xs text-gray-400">
          <p>
            OneClass Platform • Secure Multi-Tenant Access
          </p>
        </div>
      </div>
    </div>
  )
}
