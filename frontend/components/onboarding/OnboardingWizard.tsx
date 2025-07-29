/**
 * Comprehensive User Onboarding Wizard
 * Handles complex multi-school, multi-role onboarding scenarios
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Users, UserPlus, School, GraduationCap, Heart, 
  ArrowRight, ArrowLeft, CheckCircle, Mail, 
  Smartphone, Calendar, BookOpen, MapPin, Link,
  AlertTriangle, Info, Clock, Star, Shield, Building
} from 'lucide-react';
import { toast } from 'sonner';

import { useAuth, PlatformRole, SchoolRole, UserStatus } from '@/hooks/useAuth';

interface OnboardingData {
  // User basic info
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  dateOfBirth?: string;
  gender?: string;
  address?: string;
  
  // Onboarding context
  invitationType: 'new_user' | 'existing_user' | 'bulk_import' | 'self_signup';
  sourceSchoolId?: string;
  sourceSchoolName?: string;
  invitationToken?: string;
  
  // Role and school info
  primaryRole: PlatformRole;
  schoolMemberships: {
    schoolId: string;
    schoolName: string;
    role: SchoolRole;
    department?: string;
    employeeId?: string;
    studentId?: string;
    currentGrade?: string;
    childrenIds?: string[];
  }[];
  
  // Role-specific data
  teachingSubjects?: string[];
  qualifications?: string[];
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  
  // Parent-specific
  childrenInfo?: {
    name: string;
    schoolId: string;
    studentId?: string;
    grade?: string;
  }[];
  
  // Student-specific
  previousSchool?: string;
  transferReason?: string;
  medicalInfo?: string;
  
  // Preferences
  preferredLanguage: string;
  timezone: string;
  notificationPreferences: {
    emailNotifications: boolean;
    smsNotifications: boolean;
    pushNotifications: boolean;
    marketingEmails: boolean;
  };
}

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  component: React.ComponentType<any>;
  shouldShow: (data: OnboardingData) => boolean;
}

interface OnboardingWizardProps {
  invitationToken?: string;
  onComplete?: (userData: OnboardingData) => void;
  onCancel?: () => void;
}

// Step Components
const WelcomeStep: React.FC<{ data: OnboardingData; updateData: (data: Partial<OnboardingData>) => void; }> = ({
  data, updateData
}) => {
  const [detectedContext, setDetectedContext] = useState<any>(null);
  
  useEffect(() => {
    // Detect context from invitation token or subdomain
    const detectOnboardingContext = async () => {
      if (data.invitationToken) {
        try {
          const response = await fetch(`/api/v1/invitations/${data.invitationToken}`);
          if (response.ok) {
            const context = await response.json();
            setDetectedContext(context);
            updateData({
              sourceSchoolId: context.school_id,
              sourceSchoolName: context.school_name,
              primaryRole: context.suggested_role,
              invitationType: context.existing_user ? 'existing_user' : 'new_user'
            });
          }
        } catch (error) {
          console.error('Error detecting context:', error);
        }
      }
    };
    
    detectOnboardingContext();
  }, [data.invitationToken]);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Building className="h-16 w-16 mx-auto text-blue-600 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Welcome to OneClass</h2>
        <p className="text-gray-600 mb-6">
          Zimbabwe's most advanced school management platform
        </p>
      </div>

      {detectedContext && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Invitation Detected</AlertTitle>
          <AlertDescription>
            You've been invited to join <strong>{detectedContext.school_name}</strong> as a{' '}
            <Badge variant="outline">{detectedContext.suggested_role}</Badge>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-600" />
            What makes OneClass special?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <Users className="h-5 w-5 text-blue-600 mt-1" />
              <div>
                <h4 className="font-medium">One Account, Multiple Schools</h4>
                <p className="text-sm text-gray-600">Access all your schools with a single login</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-green-600 mt-1" />
              <div>
                <h4 className="font-medium">Role-Based Access</h4>
                <p className="text-sm text-gray-600">Appropriate permissions for each role</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <Link className="h-5 w-5 text-purple-600 mt-1" />
              <div>
                <h4 className="font-medium">Smart Context Switching</h4>
                <p className="text-sm text-gray-600">Seamlessly switch between schools and roles</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-orange-600 mt-1" />
              <div>
                <h4 className="font-medium">Unified Notifications</h4>
                <p className="text-sm text-gray-600">All your updates in one place</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {data.invitationType === 'existing_user' && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertTitle>Existing Account Detected</AlertTitle>
          <AlertDescription>
            We found an existing OneClass account for this email. We'll add the new school membership to your existing account.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

const BasicInfoStep: React.FC<{ data: OnboardingData; updateData: (data: Partial<OnboardingData>) => void; }> = ({
  data, updateData
}) => {
  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <UserPlus className="h-12 w-12 mx-auto text-blue-600 mb-4" />
        <h2 className="text-xl font-bold">Basic Information</h2>
        <p className="text-gray-600">Let's get to know you better</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="firstName">First Name *</Label>
          <Input
            id="firstName"
            value={data.firstName}
            onChange={(e) => updateData({ firstName: e.target.value })}
            placeholder="Enter your first name"
            required
          />
        </div>
        
        <div>
          <Label htmlFor="lastName">Last Name *</Label>
          <Input
            id="lastName"
            value={data.lastName}
            onChange={(e) => updateData({ lastName: e.target.value })}
            placeholder="Enter your last name"
            required
          />
        </div>
        
        <div>
          <Label htmlFor="email">Email Address *</Label>
          <Input
            id="email"
            type="email"
            value={data.email}
            onChange={(e) => updateData({ email: e.target.value })}
            placeholder="your.email@example.com"
            required
            disabled={!!data.invitationToken} // Pre-filled from invitation
          />
        </div>
        
        <div>
          <Label htmlFor="phone">Phone Number</Label>
          <Input
            id="phone"
            value={data.phone || ''}
            onChange={(e) => updateData({ phone: e.target.value })}
            placeholder="+263 XXX XXX XXX"
          />
        </div>
        
        <div>
          <Label htmlFor="dateOfBirth">Date of Birth</Label>
          <Input
            id="dateOfBirth"
            type="date"
            value={data.dateOfBirth || ''}
            onChange={(e) => updateData({ dateOfBirth: e.target.value })}
          />
        </div>
        
        <div>
          <Label htmlFor="gender">Gender</Label>
          <Select value={data.gender || ''} onValueChange={(value) => updateData({ gender: value })}>
            <SelectTrigger>
              <SelectValue placeholder="Select gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="other">Other</SelectItem>
              <SelectItem value="prefer_not_to_say">Prefer not to say</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="address">Address</Label>
        <Textarea
          id="address"
          value={data.address || ''}
          onChange={(e) => updateData({ address: e.target.value })}
          placeholder="Enter your address"
          rows={3}
        />
      </div>
    </div>
  );
};

const RoleSelectionStep: React.FC<{ data: OnboardingData; updateData: (data: Partial<OnboardingData>) => void; }> = ({
  data, updateData
}) => {
  const [availableRoles, setAvailableRoles] = useState<{ role: PlatformRole; description: string; icon: React.ReactNode }[]>([]);

  useEffect(() => {
    // Get available roles based on invitation or school context
    const roles = [
      {
        role: PlatformRole.TEACHER,
        description: 'Teach classes, manage grades, and communicate with students and parents',
        icon: <GraduationCap className="h-6 w-6 text-green-600" />
      },
      {
        role: PlatformRole.PARENT,
        description: 'Track your children\'s academic progress and communicate with teachers',
        icon: <Heart className="h-6 w-6 text-pink-600" />
      },
      {
        role: PlatformRole.STUDENT,
        description: 'Access assignments, grades, and school resources',
        icon: <BookOpen className="h-6 w-6 text-blue-600" />
      },
      {
        role: PlatformRole.STAFF,
        description: 'Support school operations and student services',
        icon: <Users className="h-6 w-6 text-purple-600" />
      }
    ];
    
    setAvailableRoles(roles);
  }, []);

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <Shield className="h-12 w-12 mx-auto text-blue-600 mb-4" />
        <h2 className="text-xl font-bold">Select Your Primary Role</h2>
        <p className="text-gray-600">Choose your main role at {data.sourceSchoolName || 'the school'}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {availableRoles.map((roleOption) => (
          <Card
            key={roleOption.role}
            className={`cursor-pointer transition-all ${
              data.primaryRole === roleOption.role
                ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                : 'hover:border-gray-300'
            }`}
            onClick={() => updateData({ primaryRole: roleOption.role })}
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                {roleOption.icon}
                <div>
                  <h3 className="font-semibold capitalize">
                    {roleOption.role.replace('_', ' ')}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {roleOption.description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {data.primaryRole && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Role Selected</AlertTitle>
          <AlertDescription>
            You've selected <strong>{data.primaryRole.replace('_', ' ')}</strong> as your primary role. 
            You can have additional roles at other schools later.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

const SchoolSpecificStep: React.FC<{ data: OnboardingData; updateData: (data: Partial<OnboardingData>) => void; }> = ({
  data, updateData
}) => {
  const [schoolRoles, setSchoolRoles] = useState<SchoolRole[]>([]);

  useEffect(() => {
    // Get appropriate school roles based on primary role
    const getRolesForPrimaryRole = (primaryRole: PlatformRole): SchoolRole[] => {
      switch (primaryRole) {
        case PlatformRole.TEACHER:
          return [SchoolRole.TEACHER, SchoolRole.FORM_TEACHER, SchoolRole.DEPARTMENT_HEAD, SchoolRole.ACADEMIC_HEAD];
        case PlatformRole.PARENT:
          return [SchoolRole.PARENT];
        case PlatformRole.STUDENT:
          return [SchoolRole.STUDENT];
        case PlatformRole.STAFF:
          return [SchoolRole.REGISTRAR, SchoolRole.BURSAR, SchoolRole.LIBRARIAN, SchoolRole.IT_SUPPORT, SchoolRole.SECURITY];
        default:
          return [SchoolRole.TEACHER];
      }
    };
    
    setSchoolRoles(getRolesForPrimaryRole(data.primaryRole));
  }, [data.primaryRole]);

  const updateSchoolMembership = (field: string, value: any) => {
    const membership = data.schoolMemberships[0] || {
      schoolId: data.sourceSchoolId || '',
      schoolName: data.sourceSchoolName || '',
      role: SchoolRole.TEACHER
    };
    
    const updatedMembership = { ...membership, [field]: value };
    updateData({ schoolMemberships: [updatedMembership] });
  };

  const membership = data.schoolMemberships[0];

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <School className="h-12 w-12 mx-auto text-blue-600 mb-4" />
        <h2 className="text-xl font-bold">School-Specific Information</h2>
        <p className="text-gray-600">Configure your role at {data.sourceSchoolName}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">School Membership Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>School</Label>
            <Input value={data.sourceSchoolName || ''} disabled />
          </div>

          <div>
            <Label htmlFor="schoolRole">Specific Role at School</Label>
            <Select 
              value={membership?.role || ''} 
              onValueChange={(value) => updateSchoolMembership('role', value as SchoolRole)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select your role" />
              </SelectTrigger>
              <SelectContent>
                {schoolRoles.map((role) => (
                  <SelectItem key={role} value={role}>
                    {role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {data.primaryRole === PlatformRole.TEACHER && (
            <>
              <div>
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  value={membership?.department || ''}
                  onChange={(e) => updateSchoolMembership('department', e.target.value)}
                  placeholder="e.g., Mathematics, English, Science"
                />
              </div>
              
              <div>
                <Label htmlFor="employeeId">Employee ID</Label>
                <Input
                  id="employeeId"
                  value={membership?.employeeId || ''}
                  onChange={(e) => updateSchoolMembership('employeeId', e.target.value)}
                  placeholder="Your staff ID number"
                />
              </div>
              
              <div>
                <Label htmlFor="teachingSubjects">Teaching Subjects</Label>
                <Textarea
                  id="teachingSubjects"
                  value={data.teachingSubjects?.join(', ') || ''}
                  onChange={(e) => updateData({ teachingSubjects: e.target.value.split(',').map(s => s.trim()) })}
                  placeholder="Mathematics, Physics, Chemistry"
                  rows={2}
                />
              </div>
            </>
          )}

          {data.primaryRole === PlatformRole.STUDENT && (
            <>
              <div>
                <Label htmlFor="studentId">Student ID</Label>
                <Input
                  id="studentId"
                  value={membership?.studentId || ''}
                  onChange={(e) => updateSchoolMembership('studentId', e.target.value)}
                  placeholder="Your student ID number"
                />
              </div>
              
              <div>
                <Label htmlFor="currentGrade">Current Grade/Form</Label>
                <Input
                  id="currentGrade"
                  value={membership?.currentGrade || ''}
                  onChange={(e) => updateSchoolMembership('currentGrade', e.target.value)}
                  placeholder="e.g., Form 4A, Grade 7"
                />
              </div>
            </>
          )}

          {data.primaryRole === PlatformRole.STAFF && (
            <>
              <div>
                <Label htmlFor="employeeId">Employee ID</Label>
                <Input
                  id="employeeId"
                  value={membership?.employeeId || ''}
                  onChange={(e) => updateSchoolMembership('employeeId', e.target.value)}
                  placeholder="Your staff ID number"
                />
              </div>
              
              <div>
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  value={membership?.department || ''}
                  onChange={(e) => updateSchoolMembership('department', e.target.value)}
                  placeholder="e.g., Administration, Finance, Library"
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const PreferencesStep: React.FC<{ data: OnboardingData; updateData: (data: Partial<OnboardingData>) => void; }> = ({
  data, updateData
}) => {
  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <Smartphone className="h-12 w-12 mx-auto text-blue-600 mb-4" />
        <h2 className="text-xl font-bold">Preferences & Settings</h2>
        <p className="text-gray-600">Customize your OneClass experience</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Regional Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="preferredLanguage">Preferred Language</Label>
            <Select 
              value={data.preferredLanguage} 
              onValueChange={(value) => updateData({ preferredLanguage: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="sn">Shona</SelectItem>
                <SelectItem value="nd">Ndebele</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="timezone">Timezone</Label>
            <Select 
              value={data.timezone} 
              onValueChange={(value) => updateData({ timezone: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Africa/Harare">Africa/Harare (CAT)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notification Preferences</CardTitle>
          <CardDescription>
            Choose how you'd like to receive updates and communications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Email Notifications</Label>
              <p className="text-sm text-gray-600">Grades, assignments, and school announcements</p>
            </div>
            <input
              type="checkbox"
              checked={data.notificationPreferences.emailNotifications}
              onChange={(e) => updateData({
                notificationPreferences: {
                  ...data.notificationPreferences,
                  emailNotifications: e.target.checked
                }
              })}
              className="h-4 w-4"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <Label>SMS Notifications</Label>
              <p className="text-sm text-gray-600">Urgent updates and reminders</p>
            </div>
            <input
              type="checkbox"
              checked={data.notificationPreferences.smsNotifications}
              onChange={(e) => updateData({
                notificationPreferences: {
                  ...data.notificationPreferences,
                  smsNotifications: e.target.checked
                }
              })}
              className="h-4 w-4"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <Label>Push Notifications</Label>
              <p className="text-sm text-gray-600">Real-time alerts on mobile app</p>
            </div>
            <input
              type="checkbox"
              checked={data.notificationPreferences.pushNotifications}
              onChange={(e) => updateData({
                notificationPreferences: {
                  ...data.notificationPreferences,
                  pushNotifications: e.target.checked
                }
              })}
              className="h-4 w-4"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <Label>Marketing Emails</Label>
              <p className="text-sm text-gray-600">Product updates and educational content</p>
            </div>
            <input
              type="checkbox"
              checked={data.notificationPreferences.marketingEmails}
              onChange={(e) => updateData({
                notificationPreferences: {
                  ...data.notificationPreferences,
                  marketingEmails: e.target.checked
                }
              })}
              className="h-4 w-4"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const CompletionStep: React.FC<{ data: OnboardingData; onComplete: () => void; }> = ({
  data, onComplete
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleComplete = async () => {
    setIsSubmitting(true);
    try {
      await onComplete();
    } catch (error) {
      toast.error('Failed to complete onboarding');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <CheckCircle className="h-16 w-16 mx-auto text-green-600 mb-4" />
        <h2 className="text-2xl font-bold">Welcome to OneClass!</h2>
        <p className="text-gray-600">You're all set up and ready to go</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Account Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium text-gray-500">Name</Label>
              <p className="font-medium">{data.firstName} {data.lastName}</p>
            </div>
            
            <div>
              <Label className="text-sm font-medium text-gray-500">Email</Label>
              <p className="font-medium">{data.email}</p>
            </div>
            
            <div>
              <Label className="text-sm font-medium text-gray-500">Primary Role</Label>
              <Badge variant="outline" className="capitalize">
                {data.primaryRole?.replace('_', ' ')}
              </Badge>
            </div>
            
            <div>
              <Label className="text-sm font-medium text-gray-500">School</Label>
              <p className="font-medium">{data.sourceSchoolName}</p>
            </div>
          </div>

          {data.schoolMemberships[0] && (
            <div>
              <Label className="text-sm font-medium text-gray-500">School Role</Label>
              <Badge className="capitalize">
                {data.schoolMemberships[0].role?.replace('_', ' ')}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-r from-blue-50 to-green-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-600" />
            What's Next?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium">Complete your profile</p>
              <p className="text-sm text-gray-600">Add a profile photo and additional details</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium">Explore your dashboard</p>
              <p className="text-sm text-gray-600">Get familiar with your school's features</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium">Download the mobile app</p>
              <p className="text-sm text-gray-600">Stay connected with push notifications</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button 
        onClick={handleComplete} 
        disabled={isSubmitting}
        className="w-full"
        size="lg"
      >
        {isSubmitting ? 'Setting up your account...' : 'Complete Setup'}
      </Button>
    </div>
  );
};

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  invitationToken,
  onComplete,
  onCancel
}) => {
  const { token } = useAuth();
  
  const [currentStep, setCurrentStep] = useState(0);
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    firstName: '',
    lastName: '',
    email: '',
    invitationType: 'new_user',
    invitationToken,
    primaryRole: PlatformRole.TEACHER,
    schoolMemberships: [],
    preferredLanguage: 'en',
    timezone: 'Africa/Harare',
    notificationPreferences: {
      emailNotifications: true,
      smsNotifications: true,
      pushNotifications: true,
      marketingEmails: false,
    },
  });

  const steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome',
      description: 'Welcome to OneClass',
      icon: <Building className="h-5 w-5" />,
      component: WelcomeStep,
      shouldShow: () => true,
    },
    {
      id: 'basic_info',
      title: 'Basic Info',
      description: 'Your personal information',
      icon: <UserPlus className="h-5 w-5" />,
      component: BasicInfoStep,
      shouldShow: () => true,
    },
    {
      id: 'role_selection',
      title: 'Role Selection',
      description: 'Choose your primary role',
      icon: <Shield className="h-5 w-5" />,
      component: RoleSelectionStep,
      shouldShow: () => true,
    },
    {
      id: 'school_specific',
      title: 'School Details',
      description: 'School-specific information',
      icon: <School className="h-5 w-5" />,
      component: SchoolSpecificStep,
      shouldShow: () => true,
    },
    {
      id: 'preferences',
      title: 'Preferences',
      description: 'Customize your experience',
      icon: <Smartphone className="h-5 w-5" />,
      component: PreferencesStep,
      shouldShow: () => true,
    },
    {
      id: 'completion',
      title: 'Complete',
      description: 'Finish setup',
      icon: <CheckCircle className="h-5 w-5" />,
      component: CompletionStep,
      shouldShow: () => true,
    },
  ];

  const visibleSteps = steps.filter(step => step.shouldShow(onboardingData));
  const currentStepData = visibleSteps[currentStep];
  const CurrentStepComponent = currentStepData?.component;

  const updateData = (updates: Partial<OnboardingData>) => {
    setOnboardingData(prev => ({ ...prev, ...updates }));
  };

  const canProceed = () => {
    switch (currentStepData?.id) {
      case 'basic_info':
        return onboardingData.firstName && onboardingData.lastName && onboardingData.email;
      case 'role_selection':
        return onboardingData.primaryRole;
      case 'school_specific':
        return onboardingData.schoolMemberships.length > 0;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (currentStep < visibleSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    try {
      const response = await fetch('/api/v1/auth/complete-onboarding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(onboardingData),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('Welcome to OneClass! Your account is ready.');
        onComplete?.(result);
      } else {
        throw new Error('Failed to complete onboarding');
      }
    } catch (error) {
      toast.error('Failed to complete onboarding. Please try again.');
      throw error;
    }
  };

  const progress = ((currentStep + 1) / visibleSteps.length) * 100;

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-600">
            Step {currentStep + 1} of {visibleSteps.length}
          </span>
          <span className="text-sm text-gray-500">{Math.round(progress)}% Complete</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Step Navigation */}
      <div className="flex justify-center mb-8">
        <div className="flex items-center space-x-2">
          {visibleSteps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index < currentStep
                    ? 'bg-green-600 text-white'
                    : index === currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {index < currentStep ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  index + 1
                )}
              </div>
              {index < visibleSteps.length - 1 && (
                <div className={`w-8 h-0.5 ${index < currentStep ? 'bg-green-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <Card className="mb-8">
        <CardContent className="p-6">
          {CurrentStepComponent && (
            <CurrentStepComponent
              data={onboardingData}
              updateData={updateData}
              onComplete={handleComplete}
            />
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={currentStep === 0 ? onCancel : handlePrevious}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          {currentStep === 0 ? 'Cancel' : 'Previous'}
        </Button>

        {currentStep < visibleSteps.length - 1 ? (
          <Button
            onClick={handleNext}
            disabled={!canProceed()}
            className="flex items-center gap-2"
          >
            Next
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
};