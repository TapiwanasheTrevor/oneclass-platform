"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Users,
  School,
  DollarSign,
  Calendar,
  MessageSquare,
  Trophy,
  FileText,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  BookOpen,
  ClipboardCheck,
  CreditCard,
  Settings,
  Package,
  Zap,
  Shield,
  Globe,
} from "lucide-react"
import { useAuth } from "@/hooks/useAuth"
import { api } from "@/lib/api"

interface SuperAdminDashboardProps {
  analytics?: any
  loading?: boolean
}

export default function SuperAdminDashboard({ analytics, loading }: SuperAdminDashboardProps) {
  const { user, isPlatformAdmin } = useAuth()
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [migrationStats, setMigrationStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isPlatformAdmin) {
      fetchSuperAdminData()
    }
  }, [isPlatformAdmin])

  const fetchSuperAdminData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // For now, use mock data for super admin dashboard
      // In production, this would fetch real platform-wide statistics
      const mockDashboardData = {
        total_schools: 0,
        total_users: 1,
        active_users_percentage: 100,
        total_revenue: 0,
        revenue_growth: 0,
        new_schools_this_month: 0
      };

      const mockMigrationStats = {
        total_orders: 0,
        pending_orders: 0,
        completed_orders: 0,
        revenue: 0
      };

      setDashboardData(mockDashboardData);
      setMigrationStats(mockMigrationStats);

    } catch (err: any) {
      console.error('Error fetching super admin data:', err)
      setError('Failed to load dashboard data')
    } finally {
      setIsLoading(false)
    }
  }

  if (!isPlatformAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access the super admin dashboard.</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Super Admin Dashboard</h1>
            <p className="text-muted-foreground">Platform-wide overview and management</p>
          </div>
          <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
            <Shield className="w-4 h-4 mr-1" />
            Super Admin
          </Badge>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Loading...</CardTitle>
                <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded animate-pulse mb-2" />
                <div className="h-4 bg-gray-100 rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Super Admin Dashboard</h1>
          <p className="text-muted-foreground">Platform-wide overview and management</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
            <Shield className="w-4 h-4 mr-1" />
            Super Admin
          </Badge>
          <Badge variant="outline">
            {user?.first_name} {user?.last_name}
          </Badge>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Platform Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Schools</CardTitle>
            <School className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.total_schools || 0}</div>
            <p className="text-xs text-muted-foreground">
              +{dashboardData?.new_schools_this_month || 0} this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.active_users_percentage || 0}% active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Platform Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${dashboardData?.total_revenue?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              +{dashboardData?.revenue_growth || 0}% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Migration Orders</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{migrationStats?.total_orders || 0}</div>
            <p className="text-xs text-muted-foreground">
              {migrationStats?.pending_orders || 0} pending
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Migration Care Package Section */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Package className="w-5 h-5" />
              <span>Migration Care Packages</span>
            </CardTitle>
            <CardDescription>
              Help schools migrate to OneClass Platform with our comprehensive care packages
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <h4 className="font-medium">Basic Migration</h4>
                  <p className="text-sm text-muted-foreground">Data migration + basic setup</p>
                </div>
                <Badge variant="secondary">$2,500</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <h4 className="font-medium">Standard Migration</h4>
                  <p className="text-sm text-muted-foreground">Full migration + training</p>
                </div>
                <Badge variant="secondary">$5,000</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <h4 className="font-medium">Premium Migration</h4>
                  <p className="text-sm text-muted-foreground">Complete migration + ongoing support</p>
                </div>
                <Badge variant="secondary">$10,000</Badge>
              </div>
            </div>
            
            <Button className="w-full" onClick={() => window.location.href = '/admin/migration'}>
              <Package className="w-4 h-4 mr-2" />
              Manage Migration Services
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5" />
              <span>Platform Analytics</span>
            </CardTitle>
            <CardDescription>
              Key performance indicators across the platform
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span>System Uptime</span>
                  <span className="font-medium">99.9%</span>
                </div>
                <Progress value={99.9} className="h-2" />
              </div>
              
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span>User Satisfaction</span>
                  <span className="font-medium">94%</span>
                </div>
                <Progress value={94} className="h-2" />
              </div>
              
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span>Feature Adoption</span>
                  <span className="font-medium">87%</span>
                </div>
                <Progress value={87} className="h-2" />
              </div>
            </div>
            
            <Button variant="outline" className="w-full">
              <Globe className="w-4 h-4 mr-2" />
              View Detailed Analytics
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common administrative tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
            <Button variant="outline" size="sm">
              <Users className="w-4 h-4 mr-2" />
              Manage Schools
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Platform Settings
            </Button>
            <Button variant="outline" size="sm">
              <FileText className="w-4 h-4 mr-2" />
              System Reports
            </Button>
            <Button variant="outline" size="sm">
              <Shield className="w-4 h-4 mr-2" />
              Security Center
            </Button>
            <Button variant="outline" size="sm">
              <Zap className="w-4 h-4 mr-2" />
              API Management
            </Button>
            <Button variant="outline" size="sm">
              <MessageSquare className="w-4 h-4 mr-2" />
              Support Center
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
