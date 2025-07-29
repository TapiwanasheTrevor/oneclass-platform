// =====================================================
// Feature Gate Component for Multitenancy
// File: frontend/components/FeatureGate.tsx
// =====================================================

'use client';

import React from 'react';
import { useFeatureAccess, usePermissionAccess } from '@/hooks/useSchoolContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Lock, Crown, Zap } from 'lucide-react';

interface FeatureGateProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

export function FeatureGate({ 
  feature, 
  children, 
  fallback, 
  showUpgradePrompt = true 
}: FeatureGateProps) {
  const { hasAccess, tier, upgradeRequired } = useFeatureAccess(feature);

  if (hasAccess) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  if (showUpgradePrompt) {
    return <UpgradePrompt feature={feature} currentTier={tier} />;
  }

  return null;
}

interface PermissionGateProps {
  permission: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGate({ 
  permission, 
  children, 
  fallback 
}: PermissionGateProps) {
  const { hasAccess } = usePermissionAccess(permission);

  if (hasAccess) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  return (
    <Card className="border-orange-200 bg-orange-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-orange-800">
          <Lock className="h-5 w-5" />
          Access Restricted
        </CardTitle>
        <CardDescription className="text-orange-700">
          You don't have permission to access this feature. Contact your administrator.
        </CardDescription>
      </CardHeader>
    </Card>
  );
}

interface UpgradePromptProps {
  feature: string;
  currentTier: string;
}

function UpgradePrompt({ feature, currentTier }: UpgradePromptProps) {
  const getRequiredTier = (feature: string) => {
    const featureMap: Record<string, string> = {
      'finance_module': 'premium',
      'ai_assistance': 'enterprise',
      'ministry_reporting': 'enterprise',
      'bulk_communication': 'premium',
      'custom_integrations': 'enterprise',
      'advanced_reports': 'premium',
      'whatsapp_integration': 'premium',
      'bulk_sms': 'premium',
    };
    return featureMap[feature] || 'basic';
  };

  const requiredTier = getRequiredTier(feature);
  
  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'premium': return <Crown className="h-5 w-5 text-yellow-500" />;
      case 'enterprise': return <Zap className="h-5 w-5 text-purple-500" />;
      default: return <Lock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'premium': return 'border-yellow-200 bg-yellow-50';
      case 'enterprise': return 'border-purple-200 bg-purple-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <Card className={`${getTierColor(requiredTier)}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getTierIcon(requiredTier)}
          Upgrade Required
        </CardTitle>
        <CardDescription>
          This feature requires a {requiredTier} subscription.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Badge variant="outline">Current: {currentTier}</Badge>
          <Badge variant="secondary">Required: {requiredTier}</Badge>
        </div>
        
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Unlock powerful features to enhance your school management:
          </p>
          <ul className="text-sm space-y-1 ml-4">
            {feature === 'finance_module' && (
              <>
                <li>• Complete financial management</li>
                <li>• Automated billing and invoicing</li>
                <li>• Financial reporting and analytics</li>
              </>
            )}
            {feature === 'ai_assistance' && (
              <>
                <li>• AI-powered insights</li>
                <li>• Automated lesson planning</li>
                <li>• Predictive analytics</li>
              </>
            )}
            {feature === 'bulk_communication' && (
              <>
                <li>• Mass SMS and email campaigns</li>
                <li>• WhatsApp integration</li>
                <li>• Automated notifications</li>
              </>
            )}
          </ul>
        </div>
        
        <div className="flex gap-2">
          <Button size="sm" className="w-full">
            Upgrade to {requiredTier}
          </Button>
          <Button variant="outline" size="sm">
            Learn More
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Higher-order component for feature gating
export function withFeatureGate<T extends Record<string, any>>(
  Component: React.ComponentType<T>,
  feature: string
) {
  return function FeatureGatedComponent(props: T) {
    return (
      <FeatureGate feature={feature}>
        <Component {...props} />
      </FeatureGate>
    );
  };
}

// Higher-order component for permission gating
export function withPermissionGate<T extends Record<string, any>>(
  Component: React.ComponentType<T>,
  permission: string
) {
  return function PermissionGatedComponent(props: T) {
    return (
      <PermissionGate permission={permission}>
        <Component {...props} />
      </PermissionGate>
    );
  };
}