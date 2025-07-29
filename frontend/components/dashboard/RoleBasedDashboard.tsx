"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Users,
  GraduationCap,
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
} from "lucide-react"

interface DashboardProps {
  userRole: 'admin' | 'teacher' | 'parent' | 'student'
  schoolContext?: any
  analytics?: any
}

export default function RoleBasedDashboard({ userRole, schoolContext, analytics: providedAnalytics }: DashboardProps) {
  const [analytics, setAnalytics] = useState<any>(providedAnalytics || null)
  const [loading, setLoading] = useState(!providedAnalytics)

  useEffect(() => {
    if (providedAnalytics) {
      setAnalytics(providedAnalytics)
      setLoading(false)
    }
  }, [providedAnalytics])

  // Render different dashboards based on user role
  switch (userRole) {
    case 'admin':
      return <AdminDashboard analytics={analytics} loading={loading} schoolContext={schoolContext} />
    case 'teacher':
      return <TeacherDashboard analytics={analytics} loading={loading} schoolContext={schoolContext} />
    case 'parent':
      return <ParentDashboard analytics={analytics} loading={loading} schoolContext={schoolContext} />
    case 'student':
      return <StudentDashboard analytics={analytics} loading={loading} schoolContext={schoolContext} />
    default:
      return <AdminDashboard analytics={analytics} loading={loading} schoolContext={schoolContext} />
  }
}

// Admin Dashboard - Full school overview
function AdminDashboard({ analytics, loading, schoolContext }: { analytics: any; loading: boolean; schoolContext?: any }) {
  const stats = [
    {
      title: "Total Students",
      value: analytics?.student_stats?.total || "1,247",
      change: analytics?.student_stats?.change || "+12 this term",
      icon: Users,
      color: "text-blue-600",
    },
    {
      title: "Active Teachers",
      value: analytics?.teacher_stats?.total || "89",
      change: analytics?.teacher_stats?.change || "+3 new hires",
      icon: GraduationCap,
      color: "text-green-600",
    },
    {
      title: "Fee Collection",
      value: analytics?.financial_stats?.collected || "$45,230",
      change: analytics?.financial_stats?.collection_rate || "78% collected",
      icon: DollarSign,
      color: "text-yellow-600",
    },
    {
      title: "Attendance Rate",
      value: analytics?.attendance_stats?.rate || "94.2%",
      change: analytics?.attendance_stats?.change || "+2.1% vs last term",
      icon: CheckCircle,
      color: "text-emerald-600",
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {schoolContext ? `${schoolContext.school_name} Dashboard` : 'School Dashboard'}
          </h1>
          <p className="text-muted-foreground">
            {schoolContext ? `Complete overview of ${schoolContext.school_name} operations` : 'Complete overview of your school operations'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            {schoolContext?.user_role || 'Administrator'}
          </Badge>
          <Button>Generate Report</Button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-2">Loading dashboard...</span>
        </div>
      )}

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Administrative tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start">
              <Users className="mr-2 h-4 w-4" />
              Manage Users
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Settings className="mr-2 h-4 w-4" />
              School Settings
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <FileText className="mr-2 h-4 w-4" />
              Generate Reports
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <CreditCard className="mr-2 h-4 w-4" />
              Billing & Subscription
            </Button>
          </CardContent>
        </Card>

        {/* Recent Activity and System Health cards... */}
      </div>
    </div>
  )
}

// Teacher Dashboard - Class and student focused
function TeacherDashboard({ analytics, loading, schoolContext }: { analytics: any; loading: boolean; schoolContext?: any }) {
  const stats = [
    {
      title: "My Classes",
      value: analytics?.teacher_stats?.classes || "5",
      change: analytics?.teacher_stats?.total_students || "127 students",
      icon: BookOpen,
      color: "text-blue-600",
    },
    {
      title: "Pending Assessments",
      value: analytics?.assessment_stats?.pending || "8",
      change: "Due this week",
      icon: ClipboardCheck,
      color: "text-orange-600",
    },
    {
      title: "Class Attendance",
      value: analytics?.attendance_stats?.my_classes || "92.5%",
      change: "+1.2% vs last week",
      icon: CheckCircle,
      color: "text-green-600",
    },
    {
      title: "Messages",
      value: analytics?.message_stats?.unread || "12",
      change: "From parents & admin",
      icon: MessageSquare,
      color: "text-purple-600",
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Teacher Dashboard</h1>
          <p className="text-muted-foreground">Manage your classes and track student progress</p>
        </div>
        <Badge variant="outline">Teacher</Badge>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common teaching tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start">
              <ClipboardCheck className="mr-2 h-4 w-4" />
              Take Attendance
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <FileText className="mr-2 h-4 w-4" />
              Create Assessment
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <BookOpen className="mr-2 h-4 w-4" />
              View Lesson Plans
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <MessageSquare className="mr-2 h-4 w-4" />
              Message Parents
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>My Classes</CardTitle>
            <CardDescription>Today's schedule</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics?.schedule?.today?.map((class_session: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <p className="font-medium">{class_session.subject}</p>
                    <p className="text-sm text-muted-foreground">{class_session.class_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{class_session.time}</p>
                    <p className="text-xs text-muted-foreground">{class_session.room}</p>
                  </div>
                </div>
              )) || (
                <p className="text-sm text-muted-foreground">No classes scheduled for today</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Parent Dashboard - Child-focused
function ParentDashboard({ analytics, loading, schoolContext }: { analytics: any; loading: boolean; schoolContext?: any }) {
  const children = analytics?.children || [
    { id: 1, name: "John Doe", class: "Grade 5A", attendance: 95, average_grade: 87 }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Parent Portal</h1>
          <p className="text-muted-foreground">Track your children's academic progress</p>
        </div>
        <Badge variant="outline">Parent</Badge>
      </div>

      <div className="grid gap-6">
        {children.map((child: any) => (
          <Card key={child.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{child.name}</span>
                <Badge variant="secondary">{child.class}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
                <div className="space-y-2">
                  <p className="text-sm font-medium">Attendance</p>
                  <div className="text-2xl font-bold text-green-600">{child.attendance}%</div>
                  <Progress value={child.attendance} className="h-2" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">Average Grade</p>
                  <div className="text-2xl font-bold text-blue-600">{child.average_grade}%</div>
                  <Progress value={child.average_grade} className="h-2" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">Quick Actions</p>
                  <div className="space-y-1">
                    <Button variant="outline" size="sm" className="w-full">
                      View Report Card
                    </Button>
                    <Button variant="outline" size="sm" className="w-full">
                      Contact Teacher
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

// Student Dashboard - Personal academic focus
function StudentDashboard({ analytics, loading, schoolContext }: { analytics: any; loading: boolean; schoolContext?: any }) {
  const student = analytics?.student_info || {
    name: "Student",
    class: "Grade 10A",
    attendance: 94,
    average_grade: 82
  }

  const subjects = analytics?.subjects || [
    { name: "Mathematics", grade: 85, trend: "up" },
    { name: "English", grade: 78, trend: "stable" },
    { name: "Science", grade: 91, trend: "up" },
    { name: "History", grade: 73, trend: "down" }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, {student.name}!</p>
        </div>
        <Badge variant="outline">{student.class}</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>My Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Attendance</span>
                <span className="text-sm font-medium">{student.attendance}%</span>
              </div>
              <Progress value={student.attendance} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Overall Average</span>
                <span className="text-sm font-medium">{student.average_grade}%</span>
              </div>
              <Progress value={student.average_grade} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Subject Grades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {subjects.map((subject: any, index: number) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{subject.name}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">{subject.grade}%</span>
                    {subject.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-600" />}
                    {subject.trend === 'down' && <TrendingUp className="h-4 w-4 text-red-600 rotate-180" />}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 grid-cols-1 sm:grid-cols-2">
            <Button variant="outline" className="justify-start">
              <FileText className="mr-2 h-4 w-4" />
              View Assignments
            </Button>
            <Button variant="outline" className="justify-start">
              <Calendar className="mr-2 h-4 w-4" />
              Check Timetable
            </Button>
            <Button variant="outline" className="justify-start">
              <BookOpen className="mr-2 h-4 w-4" />
              Access Library
            </Button>
            <Button variant="outline" className="justify-start">
              <MessageSquare className="mr-2 h-4 w-4" />
              Message Teacher
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}