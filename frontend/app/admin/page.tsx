/**
 * School Admin Dashboard
 * Main dashboard for school administrators with comprehensive overview and management tools
 */

import React from 'react';
import { Suspense } from 'react';
import { Users, GraduationCap, DollarSign, TrendingUp, Calendar, AlertCircle, Settings, BookOpen, Activity, FileText } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { AdminMetrics } from '@/components/admin/AdminMetrics';
import { QuickActions } from '@/components/admin/QuickActions';
import { RecentActivity } from '@/components/admin/RecentActivity';
import { SchoolOverview } from '@/components/admin/SchoolOverview';
import { StudentMetrics } from '@/components/admin/StudentMetrics';
import { FinancialSummary } from '@/components/admin/FinancialSummary';
import { StaffOverview } from '@/components/admin/StaffOverview';
import { AcademicProgress } from '@/components/admin/AcademicProgress';
import { SystemAlerts } from '@/components/admin/SystemAlerts';
import { useAuth } from '@/hooks/useAuth';
import { useSchoolContext } from '@/hooks/useSchoolContext';

const AdminDashboard = () => {
  const { user } = useAuth();
  const { school, hasFeature } = useSchoolContext();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">School Administration</h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name}! Here's what's happening at {school?.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm">
            {school?.subscription_tier?.charAt(0).toUpperCase() + school?.subscription_tier?.slice(1)}
          </Badge>
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* System Alerts */}
      <Suspense fallback={<Card className="h-32 animate-pulse" />}>
        <SystemAlerts />
      </Suspense>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Suspense fallback={<Card className="h-32 animate-pulse" />}>
          <AdminMetrics />
        </Suspense>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Primary Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* School Overview */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <SchoolOverview />
          </Suspense>

          {/* Student Metrics */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <StudentMetrics />
          </Suspense>

          {/* Academic Progress */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <AcademicProgress />
          </Suspense>

          {/* Financial Summary - if enabled */}
          {hasFeature('finance_module') && (
            <Suspense fallback={<Card className="h-64 animate-pulse" />}>
              <FinancialSummary />
            </Suspense>
          )}
        </div>

        {/* Right Column - Secondary Content */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <QuickActions />
          </Suspense>

          {/* Staff Overview */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <StaffOverview />
          </Suspense>

          {/* Recent Activity */}
          <Suspense fallback={<Card className="h-64 animate-pulse" />}>
            <RecentActivity />
          </Suspense>

          {/* Module Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Active Modules
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Student Management</span>
                  <Badge variant="default">Active</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Academic Management</span>
                  <Badge variant="default">Active</Badge>
                </div>
                {hasFeature('finance_module') && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Finance Module</span>
                    <Badge variant="default">Active</Badge>
                  </div>
                )}
                {hasFeature('ai_assistance') && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">AI Assistance</span>
                    <Badge variant="default">Active</Badge>
                  </div>
                )}
                {hasFeature('ministry_reporting') && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Ministry Reporting</span>
                    <Badge variant="default">Active</Badge>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Performance Indicators */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Key Performance Indicators
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Student Enrollment</span>
                  <span>85%</span>
                </div>
                <Progress value={85} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Staff Utilization</span>
                  <span>92%</span>
                </div>
                <Progress value={92} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Academic Performance</span>
                  <span>78%</span>
                </div>
                <Progress value={78} className="h-2" />
              </div>
              {hasFeature('finance_module') && (
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Fee Collection</span>
                    <span>67%</span>
                  </div>
                  <Progress value={67} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Section - Additional Management Tools */}
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
                  <p className="font-medium text-sm">Parent-Teacher Conference</p>
                  <p className="text-xs text-gray-500">March 15, 2024</p>
                </div>
                <Badge variant="outline">2 days</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Term Examinations</p>
                  <p className="text-xs text-gray-500">March 20-25, 2024</p>
                </div>
                <Badge variant="outline">1 week</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Sports Day</p>
                  <p className="text-xs text-gray-500">April 5, 2024</p>
                </div>
                <Badge variant="outline">3 weeks</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Health */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Database Status</span>
                <Badge variant="default">Healthy</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">API Response Time</span>
                <Badge variant="default">Good</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Backup Status</span>
                <Badge variant="default">Up to date</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Security Scan</span>
                <Badge variant="default">Passed</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Reports */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Quick Reports
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Users className="h-4 w-4 mr-2" />
                Student Report
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <GraduationCap className="h-4 w-4 mr-2" />
                Academic Report
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <BookOpen className="h-4 w-4 mr-2" />
                Attendance Report
              </Button>
              {hasFeature('finance_module') && (
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Financial Report
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;