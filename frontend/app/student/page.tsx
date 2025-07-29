/**
 * Student Dashboard
 * Main dashboard for students with academic overview and learning tools
 */

import React from 'react';
import { Suspense } from 'react';
import { BookOpen, Calendar, Trophy, Clock, Users, TrendingUp, MessageSquare, FileText, Target, Star } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { StudentMetrics } from '@/components/student/StudentMetrics';
import { ClassSchedule } from '@/components/student/ClassSchedule';
import { RecentGrades } from '@/components/student/RecentGrades';
import { Assignments } from '@/components/student/Assignments';
import { AttendanceOverview } from '@/components/student/AttendanceOverview';
import { AcademicProgress } from '@/components/student/AcademicProgress';
import { StudentNotifications } from '@/components/student/StudentNotifications';
import { QuickActions } from '@/components/student/QuickActions';
import { useAuth } from '@/hooks/useAuth';
import { useSchoolContext } from '@/hooks/useSchoolContext';

const StudentDashboard = () => {
  const { user } = useAuth();
  const { school, hasFeature } = useSchoolContext();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Student Dashboard</h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name}! Ready to learn today?
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm">
            Grade {user?.profile?.grade_level || 'N/A'}
          </Badge>
          <Badge variant="outline" className="text-sm">
            ID: {user?.profile?.student_id || 'N/A'}
          </Badge>
        </div>
      </div>

      {/* Student Notifications */}
      <Suspense fallback={<Card className="h-32 animate-pulse" />}>
        <StudentNotifications />
      </Suspense>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Suspense fallback={<Card className="h-32 animate-pulse" />}>
          <StudentMetrics />
        </Suspense>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Primary Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Schedule */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <ClassSchedule />
          </Suspense>

          {/* Current Assignments */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <Assignments />
          </Suspense>

          {/* Recent Grades */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <RecentGrades />
          </Suspense>

          {/* Academic Progress */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <AcademicProgress />
          </Suspense>
        </div>

        {/* Right Column - Secondary Content */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <QuickActions />
          </Suspense>

          {/* Attendance Overview */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <AttendanceOverview />
          </Suspense>

          {/* Subject Performance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Subject Performance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Mathematics</span>
                  <span>92%</span>
                </div>
                <Progress value={92} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>English</span>
                  <span>88%</span>
                </div>
                <Progress value={88} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Science</span>
                  <span>85%</span>
                </div>
                <Progress value={85} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>History</span>
                  <span>78%</span>
                </div>
                <Progress value={78} className="h-2" />
              </div>
            </CardContent>
          </Card>

          {/* Goals & Targets */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Learning Goals
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-sm line-through text-gray-500">Complete Math Chapter 5</span>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">Improve English essay writing</span>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">Science project presentation</span>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">History timeline assignment</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Achievements */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                Recent Achievements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <Star className="h-4 w-4 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Perfect Attendance</p>
                    <p className="text-xs text-gray-500">This month</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Trophy className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Math Quiz Champion</p>
                    <p className="text-xs text-gray-500">95% average</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <BookOpen className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Reading Milestone</p>
                    <p className="text-xs text-gray-500">10 books this term</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Section - Additional Resources */}
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
                  <p className="font-medium text-sm">Mathematics Test</p>
                  <p className="text-xs text-gray-500">Tomorrow, 10:00 AM</p>
                </div>
                <Badge variant="destructive">Test</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Science Project Due</p>
                  <p className="text-xs text-gray-500">Friday, 3:00 PM</p>
                </div>
                <Badge variant="secondary">Assignment</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Sports Day</p>
                  <p className="text-xs text-gray-500">March 15, 2024</p>
                </div>
                <Badge variant="outline">Event</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Study Resources */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Study Resources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                Lecture Notes
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <BookOpen className="h-4 w-4 mr-2" />
                E-Books
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Users className="h-4 w-4 mr-2" />
                Study Groups
              </Button>
              {hasFeature('ai_assistance') && (
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Target className="h-4 w-4 mr-2" />
                  AI Tutor
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Communication */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Messages
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="p-3 bg-blue-50 rounded">
                <p className="text-sm font-medium">Math Teacher</p>
                <p className="text-xs text-gray-600">Great work on your test!</p>
                <p className="text-xs text-gray-500">2 hours ago</p>
              </div>
              <div className="p-3 bg-gray-50 rounded">
                <p className="text-sm font-medium">Class Announcement</p>
                <p className="text-xs text-gray-600">Science lab tomorrow</p>
                <p className="text-xs text-gray-500">1 day ago</p>
              </div>
              <div className="p-3 bg-green-50 rounded">
                <p className="text-sm font-medium">Library Notice</p>
                <p className="text-xs text-gray-600">Book return reminder</p>
                <p className="text-xs text-gray-500">2 days ago</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Learning Assistant - if enabled */}
      {hasFeature('ai_assistance') && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              AI Learning Assistant
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Personalized Study Plan</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Based on your performance, focus on algebra and geometry this week.
                </p>
                <Button size="sm" variant="outline">View Plan</Button>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Practice Recommendations</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Complete 15 more physics problems to master momentum.
                </p>
                <Button size="sm" variant="outline">Start Practice</Button>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Learning Insights</h4>
                <p className="text-xs text-gray-600 mb-3">
                  You learn best in the morning. Schedule study sessions accordingly.
                </p>
                <Button size="sm" variant="outline">View Insights</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StudentDashboard;