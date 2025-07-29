/**
 * Academic Dashboard Component
 * Real-time academic management overview with Zimbabwe-specific features
 */

'use client'

import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import {
  BookOpen,
  Users,
  UserCheck,
  ClipboardList,
  TrendingUp,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  Target,
  Award,
  BarChart3
} from 'lucide-react'

import { academicApi, AcademicDashboard as AcademicDashboardType, TermNumber } from '@/lib/academic-api'
import { useAuth } from '@/hooks/useAuth'
import { formatNumber, formatPercentage } from '@/lib/utils'

interface AcademicDashboardProps {
  academicYearId: string
  className?: string
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']

export function AcademicDashboard({ academicYearId, className }: AcademicDashboardProps) {
  const { user } = useAuth()
  const [selectedTerm, setSelectedTerm] = useState<TermNumber>(TermNumber.TERM_1)

  // Fetch dashboard data
  const { 
    data: dashboard, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['academic-dashboard', academicYearId],
    queryFn: () => academicApi.getAcademicDashboard(academicYearId),
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: !!academicYearId
  })

  // Fetch terms enum
  const { data: terms } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicApi.getTermsEnum()
  })

  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load academic dashboard. Please try again.
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => refetch()} 
            className="ml-2"
          >
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  const renderStatCard = (
    title: string,
    value: number | string,
    icon: React.ReactNode,
    description?: string,
    trend?: number,
    loading?: boolean
  ) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {loading ? (
          <Skeleton className="h-4 w-4" />
        ) : (
          <div className="h-4 w-4 text-muted-foreground">{icon}</div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {loading ? <Skeleton className="h-8 w-20" /> : value}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground">
            {loading ? <Skeleton className="h-3 w-32" /> : description}
          </p>
        )}
        {trend !== undefined && !loading && (
          <div className="flex items-center text-xs">
            <TrendingUp className={`h-3 w-3 mr-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`} />
            <span className={trend >= 0 ? 'text-green-600' : 'text-red-600'}>
              {trend >= 0 ? '+' : ''}{trend}% from last term
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )

  const renderGradeDistribution = () => {
    if (!dashboard?.grade_distribution || dashboard.grade_distribution.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          <div className="text-center">
            <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No grade data available</p>
          </div>
        </div>
      )
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={dashboard.grade_distribution}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {dashboard.grade_distribution.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  const renderAttendanceTrend = () => {
    if (!dashboard?.attendance_trend || dashboard.attendance_trend.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          <div className="text-center">
            <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No attendance trend data available</p>
          </div>
        </div>
      )
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={dashboard.attendance_trend}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line 
            type="monotone" 
            dataKey="attendance_rate" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={{ fill: '#8884d8' }}
          />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  const renderSubjectPerformance = () => {
    if (!dashboard?.subject_performance || dashboard.subject_performance.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          <div className="text-center">
            <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No subject performance data available</p>
          </div>
        </div>
      )
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={dashboard.subject_performance}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="subject_name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="average_score" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  const renderRecentGrades = () => {
    if (!dashboard?.recent_grades || dashboard.recent_grades.length === 0) {
      return (
        <div className="text-center text-muted-foreground py-8">
          <Award className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No recent grades available</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {dashboard.recent_grades.slice(0, 5).map((grade: any, index: number) => (
          <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex-1">
              <div className="font-medium">{grade.student_name}</div>
              <div className="text-sm text-muted-foreground">
                {grade.subject_name} • {grade.assessment_name}
              </div>
            </div>
            <div className="text-right">
              <Badge 
                variant={grade.letter_grade === 'A' ? 'default' : 
                        grade.letter_grade === 'U' ? 'destructive' : 'secondary'}
              >
                {grade.letter_grade}
              </Badge>
              <div className="text-sm text-muted-foreground mt-1">
                {grade.percentage_score}%
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderUpcomingEvents = () => {
    if (!dashboard?.upcoming_events || dashboard.upcoming_events.length === 0) {
      return (
        <div className="text-center text-muted-foreground py-8">
          <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No upcoming events</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {dashboard.upcoming_events.slice(0, 5).map((event: any, index: number) => (
          <div key={index} className="flex items-center space-x-3 p-3 border rounded-lg">
            <div className="flex-shrink-0">
              <Calendar className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="flex-1">
              <div className="font-medium">{event.title}</div>
              <div className="text-sm text-muted-foreground">
                {event.event_type} • {event.date}
              </div>
            </div>
            <Badge variant="outline">{event.status}</Badge>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Academic Dashboard</h1>
          <p className="text-muted-foreground">
            Academic year overview for {user?.school_name}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {terms && (
            <select
              value={selectedTerm}
              onChange={(e) => setSelectedTerm(Number(e.target.value) as TermNumber)}
              className="px-3 py-2 border rounded-md"
            >
              {terms.map((term) => (
                <option key={term.value} value={term.value}>
                  {term.label}
                </option>
              ))}
            </select>
          )}
          <Button variant="outline" onClick={() => refetch()}>
            <TrendingUp className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {renderStatCard(
          'Total Subjects',
          isLoading ? '...' : formatNumber(dashboard?.total_subjects || 0),
          <BookOpen className="h-4 w-4" />,
          'Active subjects this year',
          undefined,
          isLoading
        )}
        {renderStatCard(
          'Total Students',
          isLoading ? '...' : formatNumber(dashboard?.total_students || 0),
          <Users className="h-4 w-4" />,
          'Enrolled students',
          undefined,
          isLoading
        )}
        {renderStatCard(
          'Attendance Rate',
          isLoading ? '...' : formatPercentage(dashboard?.average_attendance_rate || 0),
          <UserCheck className="h-4 w-4" />,
          'Average attendance',
          undefined,
          isLoading
        )}
        {renderStatCard(
          'Assessments',
          isLoading ? '...' : formatNumber(dashboard?.total_assessments || 0),
          <ClipboardList className="h-4 w-4" />,
          `${dashboard?.completed_assessments || 0} completed`,
          undefined,
          isLoading
        )}
      </div>

      {/* Assessment Progress */}
      {dashboard && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="h-5 w-5 mr-2" />
              Assessment Progress
            </CardTitle>
            <CardDescription>
              Track completion of assessments this academic year
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Completed Assessments</span>
                <span className="text-sm text-muted-foreground">
                  {dashboard.completed_assessments} of {dashboard.total_assessments}
                </span>
              </div>
              <Progress 
                value={dashboard.total_assessments > 0 
                  ? (dashboard.completed_assessments / dashboard.total_assessments) * 100 
                  : 0
                } 
                className="h-2" 
              />
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-1" />
                  <span>{dashboard.completed_assessments} Completed</span>
                </div>
                <div className="flex items-center">
                  <Clock className="h-4 w-4 text-yellow-600 mr-1" />
                  <span>{dashboard.pending_assessments} Pending</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="analytics" className="space-y-4">
        <TabsList>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="grades">Recent Grades</TabsTrigger>
          <TabsTrigger value="events">Upcoming Events</TabsTrigger>
        </TabsList>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Grade Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Grade Distribution</CardTitle>
                <CardDescription>
                  Distribution of grades across all subjects
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                ) : (
                  renderGradeDistribution()
                )}
              </CardContent>
            </Card>

            {/* Attendance Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Attendance Trend</CardTitle>
                <CardDescription>
                  Daily attendance rates over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                ) : (
                  renderAttendanceTrend()
                )}
              </CardContent>
            </Card>
          </div>

          {/* Subject Performance */}
          <Card>
            <CardHeader>
              <CardTitle>Subject Performance</CardTitle>
              <CardDescription>
                Average performance across all subjects
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ) : (
                renderSubjectPerformance()
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="grades">
          <Card>
            <CardHeader>
              <CardTitle>Recent Grades</CardTitle>
              <CardDescription>
                Latest grade entries across all subjects
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center space-x-3">
                      <Skeleton className="h-10 w-10 rounded-full" />
                      <div className="space-y-2 flex-1">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                      <Skeleton className="h-6 w-12" />
                    </div>
                  ))}
                </div>
              ) : (
                renderRecentGrades()
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Events</CardTitle>
              <CardDescription>
                Academic calendar events and important dates
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center space-x-3">
                      <Skeleton className="h-5 w-5" />
                      <div className="space-y-2 flex-1">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                      <Skeleton className="h-6 w-16" />
                    </div>
                  ))}
                </div>
              ) : (
                renderUpcomingEvents()
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AcademicDashboard