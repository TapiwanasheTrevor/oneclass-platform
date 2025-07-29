import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Users, UserPlus, School, GraduationCap, Heart, 
  ArrowRight, ArrowDown, CheckCircle, Mail, 
  Smartphone, Calendar, BookOpen, MapPin, Link,
  AlertTriangle, Info, Clock, Star
} from 'lucide-react';

const JourneyStep = ({ step, title, description, icon, status = "pending", details = [], substeps = [] }) => {
  const statusColors = {
    completed: "bg-green-100 border-green-300 text-green-800",
    current: "bg-blue-100 border-blue-300 text-blue-800", 
    pending: "bg-gray-100 border-gray-300 text-gray-600"
  };

  const statusIcons = {
    completed: <CheckCircle className="h-5 w-5 text-green-600" />,
    current: <Clock className="h-5 w-5 text-blue-600" />,
    pending: <div className="h-5 w-5 rounded-full border-2 border-gray-400" />
  };

  return (
    <div className={`border-l-4 pl-6 pb-8 relative ${status === 'current' ? 'border-blue-500' : status === 'completed' ? 'border-green-500' : 'border-gray-300'}`}>
      <div className="absolute -left-3 top-0 bg-white">
        {statusIcons[status]}
      </div>
      
      <Card className={`${statusColors[status]} border-2`}>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg">
              {icon}
            </div>
            <div>
              <CardTitle className="text-lg">{step}. {title}</CardTitle>
              <CardDescription className="text-sm mt-1">{description}</CardDescription>
            </div>
          </div>
        </CardHeader>
        
        {(details.length > 0 || substeps.length > 0) && (
          <CardContent className="pt-0">
            {details.length > 0 && (
              <div className="space-y-2 mb-4">
                {details.map((detail, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <ArrowRight className="h-4 w-4 mt-0.5 text-gray-500" />
                    <span>{detail}</span>
                  </div>
                ))}
              </div>
            )}
            
            {substeps.length > 0 && (
              <div className="space-y-2">
                <div className="font-medium text-sm">Substeps:</div>
                {substeps.map((substep, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm ml-4">
                    <div className="h-2 w-2 bg-gray-400 rounded-full mt-2"></div>
                    <span>{substep}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
};

const ScenarioCard = ({ title, description, complexity, icon, children }) => {
  const complexityColors = {
    simple: "bg-green-100 text-green-800",
    moderate: "bg-yellow-100 text-yellow-800",
    complex: "bg-red-100 text-red-800"
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              {icon}
            </div>
            <div>
              <CardTitle className="text-xl">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </div>
          </div>
          <Badge className={complexityColors[complexity]}>
            {complexity.charAt(0).toUpperCase() + complexity.slice(1)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {children}
      </CardContent>
    </Card>
  );
};

export default function UserOnboardingJourneys() {
  const [activeTab, setActiveTab] = useState("staff");

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-4">1Class User Onboarding Journeys</h1>
        <p className="text-xl text-gray-600 max-w-4xl mx-auto">
          Comprehensive user onboarding flows for Zimbabwe's most advanced school management platform.
          Handling complex multi-school, multi-role scenarios with elegance.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="staff">School Staff</TabsTrigger>
          <TabsTrigger value="parents">Parents</TabsTrigger>
          <TabsTrigger value="students">Students</TabsTrigger>
          <TabsTrigger value="complex">Complex Scenarios</TabsTrigger>
        </TabsList>

        {/* SCHOOL STAFF ONBOARDING */}
        <TabsContent value="staff" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Simple Staff Onboarding */}
            <ScenarioCard
              title="Single School Teacher"
              description="New teacher joining St. Mary's High School"
              complexity="simple"
              icon={<GraduationCap className="h-6 w-6 text-blue-600" />}
            >
              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Admin Invitation"
                  description="School admin invites teacher via 1Class dashboard"
                  icon={<UserPlus className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "Admin goes to stmarys.oneclass.ac.zw/staff/invite",
                    "Enters teacher's email: john.doe@gmail.com",
                    "Selects role: Teacher",
                    "Assigns subjects: Mathematics, Physics",
                    "Sets classes: Form 4A, Form 4B"
                  ]}
                />
                
                <JourneyStep
                  step={2}
                  title="Email Invitation"
                  description="Teacher receives personalized invitation email"
                  icon={<Mail className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "Email from: noreply@stmarys.oneclass.ac.zw",
                    "Subject: 'Welcome to St. Mary's High School on 1Class'",
                    "Contains school branding and welcome message",
                    "Secure invitation link with 7-day expiry"
                  ]}
                />
                
                <JourneyStep
                  step={3}
                  title="Account Creation"
                  description="Teacher creates account via Clerk authentication"
                  icon={<CheckCircle className="h-5 w-5 text-purple-600" />}
                  status="current"
                  substeps={[
                    "Clicks invitation link → redirected to stmarys.oneclass.ac.zw/signup",
                    "Clerk signup form pre-filled with email",
                    "Creates password and verifies email",
                    "Automatically assigned to St. Mary's with Teacher role"
                  ]}
                />
                
                <JourneyStep
                  step={4}
                  title="Profile Setup"
                  description="Complete profile with teaching credentials"
                  icon={<BookOpen className="h-5 w-5 text-orange-600" />}
                  status="pending"
                  details={[
                    "Upload profile photo",
                    "Add qualifications and experience",
                    "Set emergency contact information",
                    "Configure notification preferences"
                  ]}
                />
                
                <JourneyStep
                  step={5}
                  title="Dashboard Access"
                  description="Full access to school-specific features"
                  icon={<School className="h-5 w-5 text-indigo-600" />}
                  status="pending"
                  details={[
                    "Access assigned classes and students",
                    "View school calendar and events",
                    "Access grade book and attendance tools",
                    "Join staff communication channels"
                  ]}
                />
              </div>
            </ScenarioCard>

            {/* Multi-School Staff */}
            <ScenarioCard
              title="Multi-School Teacher"
              description="Teacher working at both St. Mary's and Harare International"
              complexity="moderate"
              icon={<Users className="h-6 w-6 text-orange-600" />}
            >
              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Existing Account"
                  description="Teacher already has account at St. Mary's"
                  icon={<CheckCircle className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "Active account: john.doe@gmail.com",
                    "Current role: Teacher at St. Mary's",
                    "Teaches Mathematics and Physics"
                  ]}
                />
                
                <JourneyStep
                  step={2}
                  title="Second School Invitation"
                  description="Harare International admin invites existing user"
                  icon={<Mail className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "Harare International admin searches for john.doe@gmail.com",
                    "System detects existing 1Class account",
                    "Sends invitation to add school membership",
                    "Email: 'You've been invited to join Harare International'"
                  ]}
                />
                
                <JourneyStep
                  step={3}
                  title="School Membership Addition"
                  description="User accepts invitation and gains access"
                  icon={<Link className="h-5 w-5 text-purple-600" />}
                  status="current"
                  substeps={[
                    "Clicks link → logs into existing account",
                    "Sees: 'Accept invitation to Harare International?'",
                    "Reviews new role and permissions",
                    "Accepts → gains membership to second school"
                  ]}
                />
                
                <JourneyStep
                  step={4}
                  title="School Context Switching"
                  description="Seamlessly switch between schools"
                  icon={<ArrowRight className="h-5 w-5 text-indigo-600" />}
                  status="pending"
                  details={[
                    "School selector in top navigation",
                    "URL automatically changes: stmarys.oneclass.ac.zw ↔ harare-international.oneclass.ac.zw",
                    "Different classes, students, and permissions per school",
                    "Unified notification center across all schools"
                  ]}
                />
              </div>
            </ScenarioCard>
          </div>
        </TabsContent>

        {/* PARENT ONBOARDING */}
        <TabsContent value="parents" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Single School Parent */}
            <ScenarioCard
              title="New Parent Registration"
              description="Parent with one child at Chitungwiza Primary"
              complexity="simple"
              icon={<Heart className="h-6 w-6 text-pink-600" />}
            >
              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Student Enrollment"
                  description="School enrolls student and captures parent info"
                  icon={<School className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "School admin adds student: Tinashe Mukamuri",
                    "Parent contact: mary.mukamuri@gmail.com",
                    "Relationship: Mother",
                    "Emergency contact and medical info collected"
                  ]}
                />
                
                <JourneyStep
                  step={2}
                  title="Automatic Parent Invitation"
                  description="System automatically invites parent"
                  icon={<Mail className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "Triggered when student is enrolled",
                    "Email from: chitungwiza-primary.oneclass.ac.zw",
                    "Subject: 'Track Tinashe's progress on 1Class'",
                    "Personalized with child's name and class"
                  ]}
                />
                
                <JourneyStep
                  step={3}
                  title="Parent Account Setup"
                  description="Parent creates account linked to child"
                  icon={<UserPlus className="h-5 w-5 text-purple-600" />}
                  status="current"
                  substeps={[
                    "Clicks invitation link",
                    "Pre-filled signup form with child information",
                    "Creates account with Clerk authentication",
                    "Automatically linked as Tinashe's parent"
                  ]}
                />
                
                <JourneyStep
                  step={4}
                  title="Parent Dashboard Access"
                  description="Full access to child's school information"
                  icon={<BookOpen className="h-5 w-5 text-orange-600" />}
                  status="pending"
                  details={[
                    "View Tinashe's grades and attendance",
                    "Receive real-time notifications",
                    "Communicate with teachers",
                    "Access school calendar and events",
                    "Make fee payments online"
                  ]}
                />
              </div>
            </ScenarioCard>

            {/* Multi-Child Parent */}
            <ScenarioCard
              title="Multi-Child Parent"
              description="Parent with children at different schools"
              complexity="complex"
              icon={<Users className="h-6 w-6 text-red-600" />}
            >
              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Existing Parent Account"
                  description="Parent already tracking first child"
                  icon={<CheckCircle className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "Account: mary.mukamuri@gmail.com",
                    "Tracking: Tinashe (Grade 2, Chitungwiza Primary)",
                    "Active parent role since January 2025"
                  ]}
                />
                
                <JourneyStep
                  step={2}
                  title="Second Child Enrollment"
                  description="Older child enrolls at St. Mary's High School"
                  icon={<School className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "Child: Chipo Mukamuri enrolls at St. Mary's",
                    "Admin enters same parent email: mary.mukamuri@gmail.com",
                    "System detects existing 1Class parent account",
                    "Links Chipo to existing parent account"
                  ]}
                />
                
                <JourneyStep
                  step={3}
                  title="Multi-School Access Notification"
                  description="Parent gains access to second school"
                  icon={<Mail className="h-5 w-5 text-purple-600" />}
                  status="current"
                  details={[
                    "Email: 'Chipo has been added to your 1Class account'",
                    "Notification in parent dashboard",
                    "Automatic access to St. Mary's parent portal",
                    "Can now switch between school contexts"
                  ]}
                />
                
                <JourneyStep
                  step={4}
                  title="Unified Parent Experience"
                  description="Manage all children from one account"
                  icon={<Star className="h-5 w-5 text-yellow-600" />}
                  status="pending"
                  substeps={[
                    "Dashboard shows both children's progress",
                    "Unified notification center for both schools",
                    "Can switch between school contexts when needed",
                    "Combined fee payments and communication"
                  ]}
                />
              </div>
            </ScenarioCard>
          </div>
        </TabsContent>

        {/* STUDENT ONBOARDING */}
        <TabsContent value="students" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* High School Student */}
            <ScenarioCard
              title="High School Student"
              description="Form 4 student at St. Mary's getting their own account"
              complexity="simple"
              icon={<GraduationCap className="h-6 w-6 text-blue-600" />}
            >
              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Eligibility Check"
                  description="School enables student accounts for Form 4+"
                  icon={<CheckCircle className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "St. Mary's policy: Form 4+ students get accounts",
                    "Student: Chipo Mukamuri (Form 4A)",
                    "Parent permission already on file",
                    "School generates student email: chipo.mukamuri@stmarys.student"
                  ]}
                />
                
                <JourneyStep
                  step={2}
                  title="Bulk Student Account Creation"
                  description="School admin creates accounts for eligible students"
                  icon={<Users className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "Admin selects Form 4A, 4B classes",
                    "Bulk generates student accounts",
                    "Assigns student role with restricted permissions",
                    "Links to existing student records"
                  ]}
                />
                
                <JourneyStep
                  step={3}
                  title="Student Invitation"
                  description="Student receives account activation email"
                  icon={<Mail className="h-5 w-5 text-purple-600" />}
                  status="current"
                  details={[
                    "Email to: chipo.mukamuri@stmarys.student",
                    "CC: Parent (mary.mukamuri@gmail.com)",
                    "Subject: 'Your St. Mary's student account is ready'",
                    "Secure activation link with instructions"
                  ]}
                />
                
                <JourneyStep
                  step={4}
                  title="Student Account Activation"
                  description="Student sets up their own account"
                  icon={<Smartphone className="h-5 w-5 text-orange-600" />}
                  status="pending"
                  substeps={[
                    "Clicks activation link on mobile device",
                    "Creates password for student account",
                    "Sets up profile with interests and goals",
                    "Downloads 1Class mobile app"
                  ]}
                />
                
                <JourneyStep
                  step={5}
                  title="Student Dashboard Access"
                  description="Age-appropriate features and restrictions"
                  icon={<BookOpen className="h-5 w-5 text-indigo-600" />}
                  status="pending"
                  details={[
                    "View own grades and assignments",
                    "Submit homework digitally",
                    "Access class materials and resources",
                    "Limited communication with teachers",
                    "Cannot view other students' information"
                  ]}
                />
              </div>
            </ScenarioCard>

            {/* Transfer Student */}
            <ScenarioCard
              title="Transfer Student"
              description="Student moving from one 1Class school to another"
              complexity="moderate"
              icon={<MapPin className="h-6 w-6 text-green-600" />}
            >
              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Existing Student Account"
                  description="Student has active account at previous school"
                  icon={<CheckCircle className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "Student: Tendai Chigamba",
                    "Current school: Chitungwiza Primary",
                    "Has student account with grades and history",
                    "Parent account linked: grace.chigamba@gmail.com"
                  ]}
                />
                
                <JourneyStep
                  step={2}
                  title="Transfer Process Initiation"
                  description="Parent initiates transfer to new school"
                  icon={<ArrowRight className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "Parent requests transfer to Harare International",
                    "Provides transfer letter and new school details",
                    "Chitungwiza admin marks student as 'transferring'",
                    "Academic records exported for transfer"
                  ]}
                />
                
                <JourneyStep
                  step={3}
                  title="New School Enrollment"
                  description="New school enrolls transfer student"
                  icon={<School className="h-5 w-5 text-purple-600" />}
                  status="current"
                  substeps={[
                    "Harare International admin creates enrollment",
                    "Enters existing student email and parent details",
                    "System detects existing 1Class account",
                    "Prompts for transfer confirmation"
                  ]}
                />
                
                <JourneyStep
                  step={4}
                  title="Account Migration"
                  description="Seamless account transfer between schools"
                  icon={<Link className="h-5 w-5 text-orange-600" />}
                  status="pending"
                  details={[
                    "Student maintains same login credentials",
                    "Academic history preserved and transferred",
                    "New school membership added to account",
                    "Previous school access archived (not deleted)",
                    "Parent automatically gains access to new school"
                  ]}
                />
                
                <JourneyStep
                  step={5}
                  title="Continued Education"
                  description="Student continues with full academic history"
                  icon={<Star className="h-5 w-5 text-yellow-600" />}
                  status="pending"
                  details={[
                    "Access to new school's systems and resources",
                    "Historical grades visible to new teachers",
                    "Continuous academic progression tracking",
                    "Parent can view both schools if needed"
                  ]}
                />
              </div>
            </ScenarioCard>
          </div>
        </TabsContent>

        {/* COMPLEX SCENARIOS */}
        <TabsContent value="complex" className="space-y-6">
          
          <ScenarioCard
            title="The Ultimate Multi-School Family"
            description="Complex family with multiple children across different schools and a parent who also teaches"
            complexity="complex"
            icon={<Star className="h-6 w-6 text-purple-600" />}
          >
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-yellow-800">Scenario: The Moyo Family</h4>
                  <p className="text-yellow-700 text-sm mt-1">
                    Sarah Moyo is a Mathematics teacher at St. Mary's High School. She has three children:
                    Emma (Grade 1, Chitungwiza Primary), Michael (Form 2, St. Mary's), and Lisa (Form 5, Harare International).
                    Her husband David is a school governor at Chitungwiza Primary.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="bg-blue-50 border-blue-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <GraduationCap className="h-5 w-5 text-blue-600" />
                      Sarah's Teacher Account
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm space-y-2">
                    <div><strong>Primary Role:</strong> Teacher at St. Mary's</div>
                    <div><strong>Subjects:</strong> Mathematics (Forms 1-4)</div>
                    <div><strong>Classes:</strong> 1A, 2B, 3A, 4A</div>
                    <div><strong>Access:</strong> stmarys.oneclass.ac.zw</div>
                  </CardContent>
                </Card>

                <Card className="bg-pink-50 border-pink-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Heart className="h-5 w-5 text-pink-600" />
                      Sarah's Parent Account
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm space-y-2">
                    <div><strong>Children:</strong> Emma, Michael, Lisa</div>
                    <div><strong>Schools:</strong> 3 different schools</div>
                    <div><strong>Primary Contact:</strong> For all three children</div>
                    <div><strong>Special:</strong> Can see Michael as both teacher & parent</div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <JourneyStep
                  step={1}
                  title="Initial Teacher Setup"
                  description="Sarah starts as a teacher at St. Mary's"
                  icon={<School className="h-5 w-5 text-blue-600" />}
                  status="completed"
                  details={[
                    "Hired as Mathematics teacher",
                    "Account created: sarah.moyo@stmarys.staff",
                    "Assigned to teach Forms 1-4 Mathematics",
                    "Full teacher permissions and access"
                  ]}
                />

                <JourneyStep
                  step={2}
                  title="First Child Enrollment"
                  description="Emma enrolls at Chitungwiza Primary"
                  icon={<UserPlus className="h-5 w-5 text-green-600" />}
                  status="completed"
                  details={[
                    "Emma enrolled at Chitungwiza Primary (Grade 1)",
                    "Parent contact: sarah.moyo@gmail.com (personal email)",
                    "System creates parent membership for Sarah",
                    "Now has BOTH teacher and parent roles"
                  ]}
                />

                <JourneyStep
                  step={3}
                  title="Second Child - Same School Conflict"
                  description="Michael enrolls at St. Mary's where Sarah teaches"
                  icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
                  status="completed"
                  details={[
                    "Michael enrolls at St. Mary's (Form 2)",
                    "System detects Sarah is BOTH teacher AND parent",
                    "Creates dual context management",
                    "Separate teacher/parent views for Michael's data",
                    "Special permissions to prevent grade manipulation"
                  ]}
                />

                <JourneyStep
                  step={4}
                  title="Third Child - Different School"
                  description="Lisa enrolls at Harare International"
                  icon={<Link className="h-5 w-5 text-purple-600" />}
                  status="current"
                  substeps={[
                    "Lisa enrolls at Harare International (Form 5)",
                    "Same parent email used: sarah.moyo@gmail.com",
                    "System adds third school membership",
                    "Now parent at THREE different schools"
                  ]}
                />

                <JourneyStep
                  step={5}
                  title="David's Governor Role"
                  description="Husband gains school governor access"
                  icon={<Users className="h-5 w-5 text-indigo-600" />}
                  status="current"
                  details={[
                    "David appointed as school governor at Chitungwiza Primary",
                    "Given governance-level access and reporting",
                    "Can view school-wide data and analytics",
                    "Linked as Emma's father and governor"
                  ]}
                />

                <JourneyStep
                  step={6}
                  title="Complex Dashboard Management"
                  description="Sarah's unified but role-separated experience"
                  icon={<Star className="h-5 w-5 text-yellow-600" />}
                  status="pending"
                  substeps={[
                    "Single login with role selector",
                    "Teacher mode: Access St. Mary's teaching tools",
                    "Parent mode: Switch between 3 school contexts",
                    "Smart notifications: Separated by role and school",
                    "Can see Michael's grades but not edit them"
                  ]}
                />
              </div>

              <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
                <CardHeader>
                  <CardTitle className="text-lg">Sarah's Daily Experience</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="bg-white p-3 rounded border">
                      <div className="font-semibold text-blue-600">8:00 AM - Teacher Mode</div>
                      <div>Teaching Form 2B at stmarys.oneclass.ac.zw</div>
                      <div className="text-gray-600">Can see Michael in class but as teacher, not parent</div>
                    </div>
                    <div className="bg-white p-3 rounded border">
                      <div className="font-semibold text-green-600">2:00 PM - Parent Mode</div>
                      <div>Checking Emma's progress at chitungwiza-primary.oneclass.ac.zw</div>
                      <div className="text-gray-600">Full parent access and communication</div>
                    </div>
                    <div className="bg-white p-3 rounded border">
                      <div className="font-semibold text-purple-600">6:00 PM - Multi-Parent</div>
                      <div>Reviewing Lisa's assignments at harare-international.oneclass.ac.zw</div>
                      <div className="text-gray-600">Seamless school switching</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScenarioCard>

          <ScenarioCard
            title="School Merger Scenario"
            description="Two schools merge and need to consolidate user accounts"
            complexity="complex"
            icon={<Link className="h-6 w-6 text-blue-600" />}
          >
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-blue-800">Scenario: School Merger</h4>
                  <p className="text-blue-700 text-sm mt-1">
                    Westgate Primary merges with Eastgate Primary to form United Primary School. 
                    Both schools are already using 1Class with existing students, staff, and parent accounts.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <JourneyStep
                step={1}
                title="Pre-Merger Analysis"
                description="System analyzes both schools' user bases"
                icon={<Users className="h-5 w-5 text-blue-600" />}
                status="completed"
                details={[
                  "Westgate Primary: 300 students, 20 staff, 450 parents",
                  "Eastgate Primary: 250 students, 18 staff, 380 parents", 
                  "Duplicate detection: 23 families with children at both schools",
                  "Staff overlap: 3 teachers worked at both schools"
                ]}
              />

              <JourneyStep
                step={2}
                title="Merger Configuration"
                description="Admin configures the school merger process"
                icon={<Link className="h-5 w-5 text-green-600" />}
                status="completed"
                details={[
                  "Create new school: United Primary School",
                  "New subdomain: united-primary.oneclass.ac.zw",
                  "Map class structures and grade levels",
                  "Configure merged academic calendar"
                ]}
              />

              <JourneyStep
                step={3}
                title="User Account Consolidation"
                description="Intelligent merging of duplicate accounts"
                icon={<CheckCircle className="h-5 w-5 text-purple-600" />}
                status="current"
                substeps={[
                  "Automatic detection of duplicate parent accounts",
                  "Staff accounts with multiple memberships retained",
                  "Student accounts transferred to new school",
                  "Academic histories preserved and merged"
                ]}
              />

              <JourneyStep
                step={4}
                title="Transition Communication"
                description="Notify all users about the merger"
                icon={<Mail className="h-5 w-5 text-orange-600" />}
                status="pending"
                details={[
                  "Email campaign to all affected users",
                  "New login instructions and URL changes",
                  "Timeline for old subdomain deprecation",
                  "Support contact for merger questions"
                ]}
              />

              <JourneyStep
                step={5}
                title="Go-Live & Legacy Access"
                description="Seamless transition with fallback options"
                icon={<Star className="h-5 w-5 text-yellow-600" />}
                status="pending"
                details={[
                  "New school portal goes live",
                  "Old subdomains redirect to new portal",
                  "6-month grace period for old URLs",
                  "Combined academic records and reporting"
                ]}
              />
            </div>
          </ScenarioCard>
        </TabsContent>
      </Tabs>

      {/* Key Benefits Section */}
      <Card className="mt-8 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-3">
            <CheckCircle className="h-8 w-8 text-green-600" />
            1Class Multi-Tenant Advantages
          </CardTitle>
          <CardDescription className="text-lg">
            How our sophisticated user management handles Zimbabwe's complex educational landscape
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white p-4 rounded-lg border border-green-200">
              <div className="flex items-center gap-3 mb-3">
                <Users className="h-6 w-6 text-blue-600" />
                <h4 className="font-semibold">Single Account, Multiple Schools</h4>
              </div>
              <p className="text-sm text-gray-600">
                One login for teachers working at multiple schools, parents with children at different schools, 
                or students transferring between institutions.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <div className="flex items-center gap-3 mb-3">
                <Link className="h-6 w-6 text-green-600" />
                <h4 className="font-semibold">Seamless School Switching</h4>
              </div>
              <p className="text-sm text-gray-600">
                Automatic context switching based on subdomain. Users see only relevant data 
                for the current school while maintaining access to all their schools.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <div className="flex items-center gap-3 mb-3">
                <Shield className="h-6 w-6 text-purple-600" />
                <h4 className="font-semibold">Role-Based Security</h4>
              </div>
              <p className="text-sm text-gray-600">
                Different permissions per school. A teacher at one school can be a parent at another 
                with appropriate access controls for each role.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-orange-200">
              <div className="flex items-center gap-3 mb-3">
                <Calendar className="h-6 w-6 text-orange-600" />
                <h4 className="font-semibold">Unified Notifications</h4>
              </div>
              <p className="text-sm text-gray-600">
                Smart notification system that aggregates updates from all schools while 
                maintaining clear separation and context for each institution.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-red-200">
              <div className="flex items-center gap-3 mb-3">
                <BookOpen className="h-6 w-6 text-red-600" />
                <h4 className="font-semibold">Academic Continuity</h4>
              </div>
              <p className="text-sm text-gray-600">
                Student academic records follow them between schools. Teachers can access 
                historical performance data for better educational outcomes.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-indigo-200">
              <div className="flex items-center gap-3 mb-3">
                <Star className="h-6 w-6 text-indigo-600" />
                <h4 className="font-semibold">Future-Proof Architecture</h4>
              </div>
              <p className="text-sm text-gray-600">
                Handles complex scenarios like school mergers, district management, 
                and franchise education models with sophisticated user relationship management.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}