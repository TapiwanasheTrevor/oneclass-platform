/**
 * Staff Dashboard
 * Main dashboard for teachers, registrars, and other staff members
 */

import React from 'react';
import { Suspense } from 'react';
import { Users, BookOpen, ClipboardCheck, Calendar, Bell, TrendingUp, Award, MessageSquare } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { StaffMetrics } from '@/components/staff/StaffMetrics';
import { MyClasses } from '@/components/staff/MyClasses';
import { TodaySchedule } from '@/components/staff/TodaySchedule';
import { StudentProgress } from '@/components/staff/StudentProgress';
import { AttendanceQuickEntry } from '@/components/staff/AttendanceQuickEntry';
import { GradeBookSummary } from '@/components/staff/GradeBookSummary';
import { StaffNotifications } from '@/components/staff/StaffNotifications';
import { QuickActions } from '@/components/staff/QuickActions';
import { useAuth } from '@/hooks/useAuth';
import { useSchoolContext } from '@/hooks/useSchoolContext';

const StaffDashboard = () => {
  const { user } = useAuth();
  const { school, hasFeature, canAccess } = useSchoolContext();

  const isTeacher = user?.role === 'teacher';
  const isRegistrar = user?.role === 'registrar';
  const isStaff = user?.role === 'staff';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isTeacher ? 'Teacher Dashboard' : isRegistrar ? 'Registrar Dashboard' : 'Staff Dashboard'}
          </h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name}! Here's your daily overview
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm">
            {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
          </Badge>
        </div>
      </div>

      {/* Staff Notifications */}
      <Suspense fallback={<Card className="h-32 animate-pulse" />}>
        <StaffNotifications />
      </Suspense>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Suspense fallback={<Card className="h-32 animate-pulse" />}>
          <StaffMetrics />
        </Suspense>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Primary Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Schedule */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <TodaySchedule />
          </Suspense>

          {/* My Classes - For Teachers */}
          {isTeacher && (
            <Suspense fallback={<Card className="h-64 animate-pulse" />}>
              <MyClasses />
            </Suspense>
          )}

          {/* Student Progress - For Teachers */}
          {isTeacher && (
            <Suspense fallback={<Card className="h-64 animate-pulse" />}>
              <StudentProgress />
            </Suspense>
          )}

          {/* Grade Book Summary - For Teachers */}
          {isTeacher && (
            <Suspense fallback={<Card className="h-64 animate-pulse" />}>
              <GradeBookSummary />
            </Suspense>
          )}

          {/* Quick Student Management - For Registrars */}
          {isRegistrar && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Student Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium">Recent Enrollments</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm">John Doe - Grade 10</span>
                        <Badge variant="outline">Pending</Badge>
                      </div>
                      <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm">Jane Smith - Grade 9</span>
                        <Badge variant="default">Active</Badge>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Document Verification</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm">Birth Certificates</span>
                        <Badge variant="destructive">5 Pending</Badge>
                      </div>
                      <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm">Transfer Certificates</span>
                        <Badge variant="secondary">2 Pending</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Secondary Content */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <QuickActions />
          </Suspense>

          {/* Attendance Quick Entry - For Teachers */}
          {isTeacher && canAccess('attendance.mark') && (
            <Suspense fallback={<Card className="h-64 animate-pulse" />}>
              <AttendanceQuickEntry />
            </Suspense>
          )}

          {/* Today's Tasks */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5" />
                Today's Tasks
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">Review homework submissions</span>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">Prepare lesson plans</span>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">Update gradebook</span>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">Parent communication</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Class Performance - For Teachers */}
          {isTeacher && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Class Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Grade 10A - Mathematics</span>
                    <span>87%</span>
                  </div>
                  <Progress value={87} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Grade 10B - Mathematics</span>
                    <span>79%</span>
                  </div>
                  <Progress value={79} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Grade 9A - Mathematics</span>
                    <span>92%</span>
                  </div>
                  <Progress value={92} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Messages */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Recent Messages
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm font-medium">Parent Inquiry</p>
                  <p className="text-xs text-gray-600">Mrs. Johnson asking about homework</p>
                  <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm font-medium">Staff Meeting</p>
                  <p className="text-xs text-gray-600">Tomorrow at 3:00 PM</p>
                  <p className="text-xs text-gray-500">1 day ago</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm font-medium">Grade Submission</p>
                  <p className="text-xs text-gray-600">Deadline: End of week</p>
                  <p className="text-xs text-gray-500">2 days ago</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Section - Additional Tools */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Upcoming Events */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Upcoming Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Staff Meeting</p>
                  <p className="text-xs text-gray-500">Tomorrow, 3:00 PM</p>
                </div>
                <Badge variant="outline">Required</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Grade Submission</p>
                  <p className="text-xs text-gray-500">Friday, 5:00 PM</p>
                </div>
                <Badge variant="destructive">Deadline</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Parent Conference</p>
                  <p className="text-xs text-gray-500">March 15, 2024</p>
                </div>
                <Badge variant="secondary">Optional</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Student Achievements */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Student Achievements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <Award className="h-4 w-4 text-yellow-600" />
                </div>
                <div>
                  <p className="font-medium text-sm">Sarah Wilson</p>
                  <p className="text-xs text-gray-500">Perfect Attendance</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Award className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-sm">Mike Chen</p>
                  <p className="text-xs text-gray-500">Math Competition Winner</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <Award className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-sm">Emma Davis</p>
                  <p className="text-xs text-gray-500">Science Fair Winner</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Professional Development */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Professional Development
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="p-3 bg-blue-50 rounded">
                <p className="font-medium text-sm">Teaching Techniques Workshop</p>
                <p className="text-xs text-gray-600">March 20, 2024 - Online</p>
                <Button size="sm" className="mt-2">Register</Button>
              </div>
              <div className="p-3 bg-green-50 rounded">
                <p className="font-medium text-sm">Technology in Education</p>
                <p className="text-xs text-gray-600">April 5, 2024 - In-person</p>
                <Button size="sm" variant="outline" className="mt-2">Learn More</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StaffDashboard;