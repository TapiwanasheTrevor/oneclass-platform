// =====================================================
// Super Admin Dashboard - Platform Overview
// File: frontend/app/super-admin/page.tsx
// =====================================================

'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import {
  Building2,
  Users,
  GraduationCap,
  TrendingUp,
  AlertCircle,
  Activity,
  DollarSign,
  Globe,
  Server,
  Zap,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  Plus,
  BarChart3,
  FileText,
  Shield
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface PlatformStats {
  total_schools: number;
  active_schools: number;
  total_users: number;
  total_students: number;
  total_teachers: number;
  monthly_growth: number;
  revenue_current_month: number;
  revenue_last_month: number;
  system_health_score: number;
}

interface SchoolOverview {
  id: string;
  name: string;
  subdomain: string;
  subscription_tier: string;
  student_count: number;
  teacher_count: number;
  status: string;
  last_activity: string;
  monthly_revenue: number;
  admin_name: string;
  admin_email: string;
}

interface SystemHealth {
  services: Array<{
    name: string;
    status: 'healthy' | 'warning' | 'error';
    response_time: number;
    uptime: number;
  }>;
  database_performance: {
    connection_pool: number;
    slow_queries: number;
    avg_response_time: number;
  };
  real_time_connections: number;
  active_operations: number;
}

export default function SuperAdminDashboard() {
  const { user, isPlatformAdmin } = useAuth();
  const [selectedTab, setSelectedTab] = useState('overview');

  // Redirect if not super admin
  if (!isPlatformAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access this area.</p>
        </div>
      </div>
    );
  }

  // Fetch platform statistics
  const { data: platformStats, isLoading: statsLoading } = useQuery({
    queryKey: ['platform-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/super-admin/stats');
      return response.data as PlatformStats;
    },
  });

  // Fetch schools overview
  const { data: schools, isLoading: schoolsLoading } = useQuery({
    queryKey: ['schools-overview'],
    queryFn: async () => {
      const response = await api.get('/api/v1/platform/schools');
      return response.data as SchoolOverview[];
    },
  });

  // Fetch system health
  const { data: systemHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      const response = await api.get('/api/v1/super-admin/health');
      return response.data as SystemHealth;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'warning':
      case 'trial':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'suspended':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getServiceIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-ZW', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const calculateGrowthPercentage = () => {
    if (!platformStats) return 0;
    const { revenue_current_month, revenue_last_month } = platformStats;
    if (revenue_last_month === 0) return 100;
    return ((revenue_current_month - revenue_last_month) / revenue_last_month) * 100;
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Platform Overview</h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name}. Here's what's happening across OneClass.
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline">
            <FileText className="w-4 h-4 mr-2" />
            Generate Report
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Add School
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Schools</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : platformStats?.total_schools || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsLoading ? '...' : platformStats?.active_schools || 0} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : platformStats?.total_users?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsLoading ? '...' : platformStats?.total_students || 0} students, {' '}
              {statsLoading ? '...' : platformStats?.total_teachers || 0} teachers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : formatCurrency(platformStats?.revenue_current_month || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {calculateGrowthPercentage() >= 0 ? '+' : ''}
              {calculateGrowthPercentage().toFixed(1)}% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {healthLoading ? '...' : platformStats?.system_health_score || 0}%
            </div>
            <Progress 
              value={platformStats?.system_health_score || 0} 
              className="mt-2"
            />
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="schools">Schools</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent School Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent School Activity</CardTitle>
                <CardDescription>Latest updates from your schools</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {schoolsLoading ? (
                    <div className="text-center py-4">Loading...</div>
                  ) : (
                    schools?.slice(0, 5).map((school) => (
                      <div key={school.id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback>
                              {school.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-sm font-medium">{school.name}</p>
                            <p className="text-xs text-gray-500">{school.last_activity}</p>
                          </div>
                        </div>
                        <Badge className={getStatusColor(school.status)}>
                          {school.status}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
                <CardDescription>Real-time system health monitoring</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {healthLoading ? (
                    <div className="text-center py-4">Loading...</div>
                  ) : (
                    systemHealth?.services.map((service) => (
                      <div key={service.name} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getServiceIcon(service.status)}
                          <div>
                            <p className="text-sm font-medium">{service.name}</p>
                            <p className="text-xs text-gray-500">
                              {service.response_time}ms avg response
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">{service.uptime}%</p>
                          <p className="text-xs text-gray-500">uptime</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Schools Tab */}
        <TabsContent value="schools" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Schools Management</CardTitle>
              <CardDescription>Manage all schools on the platform</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>School</TableHead>
                    <TableHead>Subscription</TableHead>
                    <TableHead>Users</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Admin</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schoolsLoading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-4">
                        Loading schools...
                      </TableCell>
                    </TableRow>
                  ) : (
                    schools?.map((school) => (
                      <TableRow key={school.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{school.name}</p>
                            <p className="text-sm text-gray-500">{school.subdomain}.oneclass.ac.zw</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {school.subscription_tier}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p>{school.student_count} students</p>
                            <p className="text-gray-500">{school.teacher_count} teachers</p>
                          </div>
                        </TableCell>
                        <TableCell>{formatCurrency(school.monthly_revenue)}</TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(school.status)}>
                            {school.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p className="font-medium">{school.admin_name}</p>
                            <p className="text-gray-500">{school.admin_email}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Health Tab */}
        <TabsContent value="system" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Service Status */}
            <Card>
              <CardHeader>
                <CardTitle>Service Status</CardTitle>
                <CardDescription>Current status of all platform services</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {healthLoading ? (
                    <div className="text-center py-4">Loading...</div>
                  ) : (
                    systemHealth?.services.map((service) => (
                      <div key={service.name} className="flex items-center justify-between p-3 rounded-lg border">
                        <div className="flex items-center space-x-3">
                          {getServiceIcon(service.status)}
                          <div>
                            <p className="font-medium">{service.name}</p>
                            <p className="text-sm text-gray-500">
                              Response: {service.response_time}ms | Uptime: {service.uptime}%
                            </p>
                          </div>
                        </div>
                        <Badge className={getStatusColor(service.status)}>
                          {service.status}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Performance Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Real-time performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Database Performance</span>
                    <span className="text-sm font-medium">
                      {systemHealth?.database_performance.avg_response_time}ms avg
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Connection Pool</span>
                    <span className="text-sm font-medium">
                      {systemHealth?.database_performance.connection_pool}% used
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active Real-time Connections</span>
                    <span className="text-sm font-medium">
                      {systemHealth?.real_time_connections}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active Operations</span>
                    <span className="text-sm font-medium">
                      {systemHealth?.active_operations}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Platform Analytics</CardTitle>
              <CardDescription>Comprehensive analytics and insights</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Advanced Analytics</h3>
                <p className="text-gray-600 mb-4">
                  Detailed analytics and reporting will be available here.
                </p>
                <Button>View Full Analytics</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}