/**
 * Invitation Handler Component
 * Processes different types of invitations and routes to appropriate onboarding flows
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Users, UserPlus, School, GraduationCap, Heart, 
  Mail, CheckCircle, AlertTriangle, Info, Clock, 
  Star, Shield, Building, Link
} from 'lucide-react';
import { toast } from 'sonner';

import { useAuth, PlatformRole, SchoolRole } from '@/hooks/useAuth';
import { OnboardingWizard } from './OnboardingWizard';

interface InvitationData {
  id: string;
  email: string;
  school_id: string;
  school_name: string;
  school_subdomain: string;
  invited_role: PlatformRole;
  school_role: SchoolRole;
  inviter_name: string;
  inviter_role: string;
  created_at: string;
  expires_at: string;
  status: 'pending' | 'accepted' | 'expired' | 'declined';
  invitation_type: 'new_user' | 'existing_user' | 'school_membership' | 'bulk_import';
  existing_user_id?: string;
  additional_context?: {
    department?: string;
    employee_id?: string;
    student_id?: string;
    classes?: string[];
    subjects?: string[];
    children_info?: Array<{
      name: string;
      student_id: string;
      grade: string;
    }>;
  };
}

interface InvitationHandlerProps {
  invitationToken: string;
  onAccepted?: () => void;
  onDeclined?: () => void;
}

export const InvitationHandler: React.FC<InvitationHandlerProps> = ({
  invitationToken,
  onAccepted,
  onDeclined
}) => {
  const { user, token } = useAuth();
  
  const [invitation, setInvitation] = useState<InvitationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchInvitationDetails();
  }, [invitationToken]);

  const fetchInvitationDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/invitations/${invitationToken}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const invitationData = await response.json();
        setInvitation(invitationData);
        
        // Check if invitation is expired
        if (new Date(invitationData.expires_at) < new Date()) {
          setError('This invitation has expired. Please contact the school administrator for a new invitation.');
          return;
        }
        
        // Check if already accepted
        if (invitationData.status === 'accepted') {
          setError('This invitation has already been accepted.');
          return;
        }
        
      } else if (response.status === 404) {
        setError('Invalid invitation link. Please check the URL or contact the school administrator.');
      } else {
        throw new Error('Failed to load invitation details');
      }
    } catch (error) {
      setError('Failed to load invitation. Please try again or contact support.');
      console.error('Error fetching invitation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvitation = async () => {
    if (!invitation) return;

    setProcessing(true);
    try {
      if (invitation.invitation_type === 'existing_user' && user) {
        // Add school membership to existing user
        const response = await fetch(`/api/v1/invitations/${invitationToken}/accept`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          toast.success(`Successfully joined ${invitation.school_name}!`);
          onAccepted?.();
        } else {
          throw new Error('Failed to accept invitation');
        }
      } else {
        // New user - start onboarding process
        setShowOnboarding(true);
      }
    } catch (error) {
      toast.error('Failed to accept invitation. Please try again.');
      console.error('Error accepting invitation:', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleDeclineInvitation = async () => {
    if (!invitation) return;

    setProcessing(true);
    try {
      const response = await fetch(`/api/v1/invitations/${invitationToken}/decline`, {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        toast.success('Invitation declined');
        onDeclined?.();
      } else {
        throw new Error('Failed to decline invitation');
      }
    } catch (error) {
      toast.error('Failed to decline invitation. Please try again.');
      console.error('Error declining invitation:', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleOnboardingComplete = (userData: any) => {
    toast.success(`Welcome to ${invitation?.school_name}!`);
    onAccepted?.();
  };

  const getRoleIcon = (role: PlatformRole) => {
    switch (role) {
      case PlatformRole.TEACHER:
        return <GraduationCap className="h-6 w-6 text-green-600" />;
      case PlatformRole.PARENT:
        return <Heart className="h-6 w-6 text-pink-600" />;
      case PlatformRole.STUDENT:
        return <Users className="h-6 w-6 text-blue-600" />;
      case PlatformRole.STAFF:
        return <Users className="h-6 w-6 text-purple-600" />;
      default:
        return <Users className="h-6 w-6 text-gray-600" />;
    }
  };

  const getInvitationTypeDescription = (invitation: InvitationData): string => {
    switch (invitation.invitation_type) {
      case 'new_user':
        return 'Create a new OneClass account and join the school';
      case 'existing_user':
        return 'Add this school to your existing OneClass account';
      case 'school_membership':
        return 'Gain additional access to this school';
      case 'bulk_import':
        return 'Your account was created as part of a bulk import';
      default:
        return 'Join this school on OneClass';
    }
  };

  if (showOnboarding) {
    return (
      <OnboardingWizard
        invitationToken={invitationToken}
        onComplete={handleOnboardingComplete}
        onCancel={() => setShowOnboarding(false)}
      />
    );
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card>
          <CardContent className="p-8 text-center">
            <Clock className="h-12 w-12 mx-auto text-blue-600 mb-4 animate-spin" />
            <h3 className="text-lg font-medium mb-2">Loading Invitation</h3>
            <p className="text-gray-600">Please wait while we verify your invitation...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Invitation Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!invitation) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>No Invitation Found</AlertTitle>
          <AlertDescription>
            We couldn't find the invitation you're looking for. Please check the link or contact the school administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <Building className="h-16 w-16 mx-auto text-blue-600 mb-4" />
        <h1 className="text-3xl font-bold mb-2">You're Invited!</h1>
        <p className="text-xl text-gray-600">
          Join <strong>{invitation.school_name}</strong> on OneClass
        </p>
      </div>

      {/* Invitation Details */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <School className="h-8 w-8 text-blue-600" />
              <div>
                <CardTitle className="text-xl">{invitation.school_name}</CardTitle>
                <CardDescription>{invitation.school_subdomain}.oneclass.ac.zw</CardDescription>
              </div>
            </div>
            <Badge variant="outline" className="text-sm">
              {invitation.invitation_type.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Role Information */}
            <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              {getRoleIcon(invitation.invited_role)}
              <div>
                <h4 className="font-semibold">Your Role</h4>
                <p className="text-sm text-gray-600 capitalize">
                  {invitation.invited_role.replace('_', ' ')} - {invitation.school_role.replace('_', ' ')}
                </p>
              </div>
            </div>

            {/* Invitation Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-gray-500">Invited By</Label>
                <p className="font-medium">{invitation.inviter_name}</p>
                <p className="text-sm text-gray-600 capitalize">{invitation.inviter_role.replace('_', ' ')}</p>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-gray-500">Invitation Date</Label>
                <p className="font-medium">{new Date(invitation.created_at).toLocaleDateString()}</p>
                <p className="text-sm text-gray-600">
                  Expires: {new Date(invitation.expires_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Additional Context */}
            {invitation.additional_context && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h4 className="font-medium">Additional Information</h4>
                  
                  {invitation.additional_context.department && (
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Department</Label>
                      <p className="font-medium">{invitation.additional_context.department}</p>
                    </div>
                  )}
                  
                  {invitation.additional_context.employee_id && (
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Employee ID</Label>
                      <p className="font-medium">{invitation.additional_context.employee_id}</p>
                    </div>
                  )}
                  
                  {invitation.additional_context.student_id && (
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Student ID</Label>
                      <p className="font-medium">{invitation.additional_context.student_id}</p>
                    </div>
                  )}
                  
                  {invitation.additional_context.subjects && invitation.additional_context.subjects.length > 0 && (
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Teaching Subjects</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {invitation.additional_context.subjects.map((subject) => (
                          <Badge key={subject} variant="secondary" className="text-xs">
                            {subject}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {invitation.additional_context.classes && invitation.additional_context.classes.length > 0 && (
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Assigned Classes</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {invitation.additional_context.classes.map((class_name) => (
                          <Badge key={class_name} variant="secondary" className="text-xs">
                            {class_name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {invitation.additional_context.children_info && invitation.additional_context.children_info.length > 0 && (
                    <div>
                      <Label className="text-sm font-medium text-gray-500">Your Children</Label>
                      <div className="space-y-2 mt-1">
                        {invitation.additional_context.children_info.map((child, index) => (
                          <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <span className="font-medium">{child.name}</span>
                            <div className="text-right">
                              <div className="text-sm">{child.grade}</div>
                              <div className="text-xs text-gray-500">ID: {child.student_id}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* What Happens Next */}
      <Card className="mb-6 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-600" />
            What Happens When You Accept?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700 mb-3">{getInvitationTypeDescription(invitation)}</p>
          
          <div className="space-y-2">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
              <div className="text-sm">
                <span className="font-medium">Access school systems:</span> Grade books, calendars, communication tools
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
              <div className="text-sm">
                <span className="font-medium">Role-based permissions:</span> Appropriate access for your role
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
              <div className="text-sm">
                <span className="font-medium">Mobile app access:</span> Stay connected on the go
              </div>
            </div>
            
            {invitation.invitation_type === 'existing_user' && (
              <div className="flex items-start gap-3">
                <Link className="h-4 w-4 text-blue-600 mt-0.5" />
                <div className="text-sm">
                  <span className="font-medium">Multi-school access:</span> Switch between your schools seamlessly
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* User Status Alert */}
      {invitation.invitation_type === 'existing_user' && user && (
        <Alert className="mb-6">
          <Info className="h-4 w-4" />
          <AlertTitle>Existing Account Detected</AlertTitle>
          <AlertDescription>
            We'll add {invitation.school_name} to your existing OneClass account. 
            You'll be able to switch between schools using the school selector.
          </AlertDescription>
        </Alert>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={handleAcceptInvitation}
          disabled={processing}
          className="flex-1"
          size="lg"
        >
          {processing ? 'Processing...' : 'Accept Invitation'}
        </Button>
        
        <Button
          variant="outline"
          onClick={handleDeclineInvitation}
          disabled={processing}
          size="lg"
        >
          Decline
        </Button>
      </div>

      {/* Help Text */}
      <div className="text-center mt-6">
        <p className="text-sm text-gray-600">
          Need help? Contact{' '}
          <a href={`mailto:support@${invitation.school_subdomain}.oneclass.ac.zw`} className="text-blue-600 hover:underline">
            {invitation.school_name} support
          </a>{' '}
          or{' '}
          <a href="mailto:support@oneclass.ac.zw" className="text-blue-600 hover:underline">
            OneClass support
          </a>
        </p>
      </div>
    </div>
  );
};