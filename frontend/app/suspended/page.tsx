"use client"

/**
 * School Suspended Page
 * Displayed when a school's account is suspended or deactivated
 */

import React from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { AlertTriangle, Clock, Mail, Phone, ExternalLink } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

export default function SuspendedPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const reason = searchParams.get('reason') || 'account_suspended'
  const schoolName = searchParams.get('school_name')
  const contactEmail = searchParams.get('contact_email')
  const subdomain = searchParams.get('subdomain')
  
  const getSuspensionInfo = () => {
    switch (reason) {
      case 'payment_overdue':
        return {
          title: 'Account Suspended - Payment Required',
          description: 'Your school account has been temporarily suspended due to overdue payment.',
          icon: <Clock className="h-12 w-12 text-orange-500" />,
          badgeColor: 'bg-orange-100 text-orange-800',
          actions: [
            'Contact your school administrator to update payment information',
            'Ensure all outstanding invoices are settled',
            'Your account will be reactivated once payment is received'
          ]
        }
      
      case 'policy_violation':
        return {
          title: 'Account Suspended - Policy Violation',
          description: 'Your school account has been suspended due to a violation of our terms of service.',
          icon: <AlertTriangle className="h-12 w-12 text-red-500" />,
          badgeColor: 'bg-red-100 text-red-800',
          actions: [
            'Review the OneClass Platform Terms of Service',
            'Contact support to discuss the suspension',
            'Submit an appeal if you believe this is an error'
          ]
        }
      
      case 'maintenance':
        return {
          title: 'Temporarily Unavailable - Maintenance',
          description: 'Your school platform is temporarily unavailable due to scheduled maintenance.',
          icon: <Clock className="h-12 w-12 text-blue-500" />,
          badgeColor: 'bg-blue-100 text-blue-800',
          actions: [
            'Maintenance is typically completed within 2-4 hours',
            'No action is required from your side',
            'Check our status page for updates'
          ]
        }
      
      default:
        return {
          title: 'Account Suspended',
          description: 'Your school account is currently suspended.',
          icon: <AlertTriangle className="h-12 w-12 text-gray-500" />,
          badgeColor: 'bg-gray-100 text-gray-800',
          actions: [
            'Contact your school administrator for more information',
            'Check with OneClass support if needed'
          ]
        }
    }
  }
  
  const suspensionInfo = getSuspensionInfo()
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-100 p-4">
      <div className="w-full max-w-lg space-y-6">
        {/* School Header */}
        {schoolName && (
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900">{schoolName}</h1>
            {subdomain && (
              <p className="text-sm text-gray-600">
                {subdomain}.oneclass.ac.zw
              </p>
            )}
          </div>
        )}
        
        {/* Suspension Notice */}
        <Card className="border-2 border-red-200">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-4">
              {suspensionInfo.icon}
            </div>
            <div className="space-y-2">
              <Badge className={suspensionInfo.badgeColor}>
                SUSPENDED
              </Badge>
              <CardTitle className="text-xl text-gray-900">
                {suspensionInfo.title}
              </CardTitle>
              <CardDescription className="text-gray-600">
                {suspensionInfo.description}
              </CardDescription>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Suspension Details */}
            <Alert className="border-orange-200 bg-orange-50">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-800">
                Your access to the OneClass Platform has been temporarily restricted.
                Please follow the steps below to resolve this issue.
              </AlertDescription>
            </Alert>
            
            {/* Action Steps */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900">What you can do:</h3>
              <ul className="space-y-2">
                {suspensionInfo.actions.map((action, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-xs flex items-center justify-center font-semibold mt-0.5">
                      {index + 1}
                    </span>
                    <span className="text-sm text-gray-700">{action}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Contact Information */}
            <div className="border-t pt-4">
              <h3 className="font-semibold text-gray-900 mb-3">Need Help?</h3>
              <div className="space-y-3">
                {contactEmail && (
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <Mail className="h-5 w-5 text-gray-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">School Administrator</p>
                      <a href={`mailto:${contactEmail}`} className="text-sm text-blue-600 hover:underline">
                        {contactEmail}
                      </a>
                    </div>
                  </div>
                )}
                
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Phone className="h-5 w-5 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">OneClass Support</p>
                    <p className="text-sm text-gray-600">+263 4 123 456</p>
                    <a href="mailto:support@oneclass.ac.zw" className="text-sm text-blue-600 hover:underline">
                      support@oneclass.ac.zw
                    </a>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="space-y-3">
              {reason === 'maintenance' && (
                <Button
                  onClick={() => window.location.reload()}
                  className="w-full"
                >
                  Check Again
                </Button>
              )}
              
              <Button
                variant="outline"
                onClick={() => window.open('https://status.oneclass.ac.zw', '_blank')}
                className="w-full"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Check System Status
              </Button>
              
              <Button
                variant="outline"
                onClick={() => window.open('mailto:support@oneclass.ac.zw', '_blank')}
                className="w-full"
              >
                <Mail className="h-4 w-4 mr-2" />
                Contact Support
              </Button>
            </div>
          </CardContent>
        </Card>
        
        {/* Additional Information */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="text-center space-y-2">
              <h3 className="font-semibold text-blue-900">Important Information</h3>
              <div className="text-sm text-blue-800 space-y-1">
                <p>• Your school data is secure and will not be lost</p>
                <p>• Account suspension is typically temporary</p>
                <p>• Contact support for immediate assistance</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Footer */}
        <div className="text-center text-xs text-gray-400">
          <p>
            Powered by{' '}
            <a href="https://oneclass.ac.zw" className="text-blue-600 hover:underline">
              OneClass Platform
            </a>
          </p>
          <p className="mt-1">
            Secure School Management for Zimbabwe
          </p>
        </div>
      </div>
    </div>
  )
}
