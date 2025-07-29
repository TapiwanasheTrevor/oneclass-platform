/**
 * Parent Dashboard
 * Main dashboard for parents to monitor their children's academic progress
 */

import React from 'react';
import { Suspense } from 'react';
import { Users, BookOpen, Calendar, CreditCard, MessageSquare, TrendingUp, Bell, Award, Clock, FileText } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ParentMetrics } from '@/components/parent/ParentMetrics';
import { ChildrenOverview } from '@/components/parent/ChildrenOverview';
import { AcademicProgress } from '@/components/parent/AcademicProgress';
import { AttendanceTracking } from '@/components/parent/AttendanceTracking';
import { UpcomingEvents } from '@/components/parent/UpcomingEvents';
import { FinancialOverview } from '@/components/parent/FinancialOverview';
import { CommunicationCenter } from '@/components/parent/CommunicationCenter';
import { ParentNotifications } from '@/components/parent/ParentNotifications';
import { QuickActions } from '@/components/parent/QuickActions';
import { useAuth } from '@/hooks/useAuth';
import { useSchoolContext } from '@/hooks/useSchoolContext';

const ParentDashboard = () => {
  const { user } = useAuth();
  const { school, hasFeature } = useSchoolContext();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Parent Dashboard</h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name}! Here's how your children are doing
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm">
            Parent
          </Badge>
          <Button variant="outline" size="sm">
            <MessageSquare className="h-4 w-4 mr-2" />
            Contact School
          </Button>
        </div>
      </div>

      {/* Parent Notifications */}
      <Suspense fallback={<Card className="h-32 animate-pulse" />}>
        <ParentNotifications />
      </Suspense>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Suspense fallback={<Card className="h-32 animate-pulse" />}>
          <ParentMetrics />
        </Suspense>
      </div>

      {/* Children Overview */}
      <Suspense fallback={<Card className="h-64 animate-pulse" />}>
        <ChildrenOverview />
      </Suspense>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Primary Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Academic Progress */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <AcademicProgress />
          </Suspense>

          {/* Attendance Tracking */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <AttendanceTracking />
          </Suspense>

          {/* Financial Overview - if enabled */}
          {hasFeature('finance_module') && (
            <Suspense fallback={<Card className="h-64 animate-pulse" />}>
              <FinancialOverview />
            </Suspense>
          )}

          {/* Communication Center */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <CommunicationCenter />
          </Suspense>
        </div>

        {/* Right Column - Secondary Content */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <QuickActions />
          </Suspense>

          {/* Upcoming Events */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <UpcomingEvents />
          </Suspense>

          {/* Recent Achievements */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5" />
                Recent Achievements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <Award className="h-4 w-4 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Sarah - Perfect Attendance</p>
                    <p className="text-xs text-gray-500">This month</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Award className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">John - Math Competition</p>
                    <p className="text-xs text-gray-500">Second place</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <BookOpen className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Sarah - Reading Challenge</p>
                    <p className="text-xs text-gray-500">5 books this week</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Teacher Communications */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Teacher Messages
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded">
                  <p className="text-sm font-medium">Ms. Johnson (Math)</p>
                  <p className="text-xs text-gray-600">Sarah is doing excellent work in algebra</p>
                  <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
                <div className="p-3 bg-green-50 rounded">
                  <p className="text-sm font-medium">Mr. Davis (Science)</p>
                  <p className="text-xs text-gray-600">John's project was outstanding</p>
                  <p className="text-xs text-gray-500">1 day ago</p>
                </div>
                <div className="p-3 bg-yellow-50 rounded">
                  <p className="text-sm font-medium">Mrs. Wilson (English)</p>
                  <p className="text-xs text-gray-600">Please review homework guidelines</p>
                  <p className="text-xs text-gray-500">2 days ago</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Section - Detailed Information */}
      <div className="grid grid-cols-1 gap-6">
        {/* Detailed Academic Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Detailed Academic Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="sarah" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="sarah">Sarah (Grade 10)</TabsTrigger>
                <TabsTrigger value="john">John (Grade 8)</TabsTrigger>
              </TabsList>
              <TabsContent value="sarah" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Mathematics</span>
                      <span>92%</span>
                    </div>
                    <Progress value={92} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Excellent progress</p>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>English</span>
                      <span>88%</span>
                    </div>
                    <Progress value={88} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Good work</p>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Science</span>
                      <span>85%</span>
                    </div>
                    <Progress value={85} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Steady improvement</p>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>History</span>
                      <span>78%</span>
                    </div>
                    <Progress value={78} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Needs attention</p>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="john" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Mathematics</span>
                      <span>95%</span>
                    </div>
                    <Progress value={95} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Outstanding</p>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>English</span>
                      <span>82%</span>
                    </div>
                    <Progress value={82} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Good progress</p>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Science</span>
                      <span>90%</span>
                    </div>
                    <Progress value={90} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Excellent</p>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>History</span>
                      <span>86%</span>
                    </div>
                    <Progress value={86} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">Very good</p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Payment Information - if enabled */}
        {hasFeature('finance_module') && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Payment Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-3">
                  <h4 className="font-medium">Outstanding Fees</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Tuition - Q1</span>
                      <span className="font-medium">$500</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Activity Fee</span>
                      <span className="font-medium">$50</span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="font-medium">Total</span>
                      <span className="font-bold">$550</span>
                    </div>
                  </div>
                  <Button className="w-full">Pay Now</Button>
                </div>
                <div className="space-y-3">
                  <h4 className="font-medium">Recent Payments</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Dec 2023 - Tuition</span>
                      <Badge variant="default">Paid</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Nov 2023 - Activity</span>
                      <Badge variant="default">Paid</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Oct 2023 - Tuition</span>
                      <Badge variant="default">Paid</Badge>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-medium">Payment Methods</h4>
                  <div className="space-y-2">
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-sm font-medium">Visa **** 4532</p>
                      <p className="text-xs text-gray-500">Expires 12/25</p>
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      Add Payment Method
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ParentDashboard;