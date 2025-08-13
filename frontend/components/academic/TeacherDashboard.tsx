"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { 
  BookOpen,
  Users,
  Calendar,
  Clock,
  Target,
  TrendingUp,
  TrendingDown,
  Award,
  AlertTriangle,
  CheckCircle2,
  FileText,
  BarChart3,
  PieChart,
  MessageSquare,
  Bell,
  Settings,
  Plus,
  Edit,
  Eye,
  Download,
  Upload,
  RefreshCw,
  ChevronRight,
  GraduationCap,
  Calculator,
  Zap,
  Activity,
  Star,
  ThumbsUp,
  ThumbsDown,
  Coffee,
  MapPin,
  PhoneCall,
  Mail
} from "lucide-react"
import { toast } from "sonner"
import { format, isToday, isTomorrow, addDays } from "date-fns"

import { 
  useAcademicHooks,
  zimbabweTerms,
  formatTerm,
  zimbabweGradeScale,
  getZimbabweGrade
} from "@/lib/academic-api"

interface TeacherDashboardProps {
  teacherId?: string
  academicYearId: string
  className?: string
}

interface ClassOverview {
  id: string
  name: string
  subject: string
  students_count: number
  upcoming_sessions: number
  pending_grades: number
  attendance_rate: number
  average_performance: number
}

interface UpcomingSession {
  id: string
  class_name: string
  subject: string
  time: string
  date: string
  room: string
  type: "regular" | "makeup" | "extra" | "exam"
}

interface RecentActivity {
  id: string
  type: "grade_submitted" | "attendance_marked" | "assessment_created" | "announcement"
  title: string
  description: string
  timestamp: string
  class_name?: string
}

interface StudentAlert {
  id: string
  student_name: string
  student_id: string
  class_name: string
  alert_type: "poor_attendance" | "low_grades" | "missing_assignment" | "improvement"
  severity: "low" | "medium" | "high"
  description: string
  created_at: string
}

// Mock data - in production, this would come from API
const mockClasses: ClassOverview[] = [
  {
    id: "1",
    name: "Form 4A",
    subject: "Mathematics",
    students_count: 32,
    upcoming_sessions: 4,
    pending_grades: 8,
    attendance_rate: 95.2,
    average_performance: 78.5
  },
  {
    id: "2", 
    name: "Form 4B",
    subject: "Mathematics",
    students_count: 28,
    upcoming_sessions: 3,
    pending_grades: 12,
    attendance_rate: 87.8,
    average_performance: 71.2
  },
  {
    id: "3",
    name: "Form 3A",
    subject: "Physics",
    students_count: 25,
    upcoming_sessions: 2,
    pending_grades: 0,
    attendance_rate: 92.1,
    average_performance: 82.3
  }
]

const mockUpcomingSessions: UpcomingSession[] = [
  {
    id: "1",
    class_name: "Form 4A",
    subject: "Mathematics",
    time: "08:00",
    date: new Date().toISOString().split('T')[0],
    room: "Room 101",
    type: "regular"
  },
  {
    id: "2",
    class_name: "Form 4B", 
    subject: "Mathematics",
    time: "10:30",
    date: new Date().toISOString().split('T')[0],
    room: "Room 101",
    type: "regular"
  },
  {
    id: "3",
    class_name: "Form 3A",
    subject: "Physics",
    time: "14:00",
    date: addDays(new Date(), 1).toISOString().split('T')[0],
    room: "Lab A",
    type: "regular"
  }
]

const mockRecentActivities: RecentActivity[] = [
  {
    id: "1",
    type: "grade_submitted",
    title: "Grades submitted for Mid-Term Test",
    description: "32 students graded for Form 4A Mathematics",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    class_name: "Form 4A"
  },
  {
    id: "2",
    type: "attendance_marked",
    title: "Attendance marked",
    description: "Morning session attendance recorded",
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    class_name: "Form 4B"
  },
  {
    id: "3",
    type: "assessment_created",
    title: "New assignment created",
    description: "Algebra problem set due next week",
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    class_name: "Form 4A"
  }
]

const mockStudentAlerts: StudentAlert[] = [
  {
    id: "1",
    student_name: "Tendai Mukamuri",
    student_id: "ST2024001",
    class_name: "Form 4A",
    alert_type: "poor_attendance",
    severity: "high",
    description: "Attendance rate below 80% (currently 65%)",
    created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
  },
  {
    id: "2",
    student_name: "Chipo Nyathi",
    student_id: "ST2024002", 
    class_name: "Form 4B",
    alert_type: "low_grades",
    severity: "medium",
    description: "Average performance dropped to 45% this term",
    created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString()
  },
  {
    id: "3",
    student_name: "Blessing Ndlovu",
    student_id: "ST2024004",
    class_name: "Form 3A",
    alert_type: "improvement",
    severity: "low",
    description: "Significant improvement: 68% to 85% this month",
    created_at: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString()
  }
]

export default function TeacherDashboard({ 
  teacherId, 
  academicYearId, 
  className 
}: TeacherDashboardProps) {
  const [selectedTerm, setSelectedTerm] = useState(1)
  const [selectedTimeframe, setSelectedTimeframe] = useState("week")

  const { useTeacherDashboard } = useAcademicHooks()
  
  // Mock teacher data
  const teacherData = {
    name: "Mrs. Sarah Moyo",
    employee_id: "T2024001",
    department: "Mathematics",
    subjects: ["Mathematics", "Physics"],
    email: "s.moyo@school.co.zw",
    phone: "+263 77 123 4567"
  }

  // Calculate dashboard statistics
  const dashboardStats = useMemo(() => {
    const totalStudents = mockClasses.reduce((sum, cls) => sum + cls.students_count, 0)
    const totalPendingGrades = mockClasses.reduce((sum, cls) => sum + cls.pending_grades, 0)
    const averageAttendance = mockClasses.reduce((sum, cls) => sum + cls.attendance_rate, 0) / mockClasses.length
    const averagePerformance = mockClasses.reduce((sum, cls) => sum + cls.average_performance, 0) / mockClasses.length
    const totalUpcomingSessions = mockUpcomingSessions.length
    const todaySessions = mockUpcomingSessions.filter(session => isToday(new Date(session.date))).length

    return {
      totalStudents,
      totalClasses: mockClasses.length,
      totalPendingGrades,
      averageAttendance,
      averagePerformance,
      totalUpcomingSessions,
      todaySessions,
      highPriorityAlerts: mockStudentAlerts.filter(alert => alert.severity === "high").length
    }
  }, [])

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case "regular": return <BookOpen className="h-4 w-4" />
      case "makeup": return <RefreshCw className="h-4 w-4" />
      case "extra": return <Plus className="h-4 w-4" />
      case "exam": return <FileText className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case "poor_attendance": return <Users className="h-4 w-4" />
      case "low_grades": return <TrendingDown className="h-4 w-4" />
      case "missing_assignment": return <FileText className="h-4 w-4" />
      case "improvement": return <TrendingUp className="h-4 w-4" />
      default: return <AlertTriangle className="h-4 w-4" />
    }
  }

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case "high": return "text-red-600"
      case "medium": return "text-yellow-600"
      case "low": return "text-green-600"
      default: return "text-muted-foreground"
    }
  }

  const renderQuickStats = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Students</p>
              <p className="text-2xl font-bold">{dashboardStats.totalStudents}</p>
            </div>
            <Users className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Classes</p>
              <p className="text-2xl font-bold">{dashboardStats.totalClasses}</p>
            </div>
            <GraduationCap className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Today's Sessions</p>
              <p className="text-2xl font-bold">{dashboardStats.todaySessions}</p>
            </div>
            <Calendar className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Pending Grades</p>
              <p className="text-2xl font-bold">{dashboardStats.totalPendingGrades}</p>
            </div>
            <Calculator className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderPerformanceOverview = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="mr-2 h-5 w-5" />
            Attendance Overview
          </CardTitle>
          <CardDescription>
            Average attendance rate across all classes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{dashboardStats.averageAttendance.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">Overall Attendance Rate</div>
            </div>
            <Progress value={dashboardStats.averageAttendance} className="h-3" />
            <div className="space-y-2">
              {mockClasses.map((cls) => (
                <div key={cls.id} className="flex items-center justify-between text-sm">
                  <span>{cls.name} - {cls.subject}</span>
                  <div className="flex items-center space-x-2">
                    <Progress value={cls.attendance_rate} className="w-16 h-2" />
                    <span className="w-12">{cls.attendance_rate.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Award className="mr-2 h-5 w-5" />
            Academic Performance
          </CardTitle>
          <CardDescription>
            Average performance across all classes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{dashboardStats.averagePerformance.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">
                Overall Grade: {getZimbabweGrade(dashboardStats.averagePerformance)}
              </div>
            </div>
            <Progress value={dashboardStats.averagePerformance} className="h-3" />
            <div className="space-y-2">
              {mockClasses.map((cls) => (
                <div key={cls.id} className="flex items-center justify-between text-sm">
                  <span>{cls.name} - {cls.subject}</span>
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant={
                        cls.average_performance >= 80 ? "default" :
                        cls.average_performance >= 60 ? "secondary" : "destructive"
                      }
                    >
                      {getZimbabweGrade(cls.average_performance)}
                    </Badge>
                    <span className="w-12">{cls.average_performance.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderUpcomingSessions = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <Clock className="mr-2 h-5 w-5" />
            Upcoming Sessions
          </div>
          <Badge variant="outline">
            {dashboardStats.todaySessions} today
          </Badge>
        </CardTitle>
        <CardDescription>
          Your scheduled classes and sessions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {mockUpcomingSessions.slice(0, 5).map((session) => {
            const sessionDate = new Date(session.date)
            const isToday = isToday(sessionDate)
            const isTomorrow = isTomorrow(sessionDate)
            
            return (
              <div key={session.id} className={`flex items-center justify-between p-3 border rounded-lg ${
                isToday ? 'bg-blue-50 border-blue-200' : ''
              }`}>
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full ${
                    isToday ? 'bg-blue-100' : 'bg-muted'
                  }`}>
                    {getSessionTypeIcon(session.type)}
                  </div>
                  <div>
                    <div className="font-medium">{session.class_name} - {session.subject}</div>
                    <div className="text-sm text-muted-foreground flex items-center space-x-4">
                      <span className="flex items-center">
                        <Clock className="mr-1 h-3 w-3" />
                        {session.time}
                      </span>
                      <span className="flex items-center">
                        <MapPin className="mr-1 h-3 w-3" />
                        {session.room}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant={isToday ? "default" : "outline"}>
                    {isToday ? "Today" : isTomorrow ? "Tomorrow" : format(sessionDate, 'MMM dd')}
                  </Badge>
                  <div className="text-xs text-muted-foreground mt-1 capitalize">
                    {session.type} session
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )

  const renderClassOverview = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <BookOpen className="mr-2 h-5 w-5" />
          Class Overview
        </CardTitle>
        <CardDescription>
          Summary of your classes and student progress
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockClasses.map((cls) => (
            <div key={cls.id} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold">{cls.name} - {cls.subject}</h3>
                  <p className="text-sm text-muted-foreground">{cls.students_count} students</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Eye className="mr-2 h-4 w-4" />
                    View
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="font-medium">{cls.upcoming_sessions}</div>
                  <div className="text-muted-foreground">Upcoming Sessions</div>
                </div>
                <div className="text-center">
                  <div className="font-medium">{cls.pending_grades}</div>
                  <div className="text-muted-foreground">Pending Grades</div>
                </div>
                <div className="text-center">
                  <div className="font-medium">{cls.attendance_rate.toFixed(1)}%</div>
                  <div className="text-muted-foreground">Attendance</div>
                </div>
                <div className="text-center">
                  <div className="font-medium">
                    {cls.average_performance.toFixed(1)}% ({getZimbabweGrade(cls.average_performance)})
                  </div>
                  <div className="text-muted-foreground">Performance</div>
                </div>
              </div>
              
              {cls.pending_grades > 0 && (
                <Alert className="mt-3">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    {cls.pending_grades} assessments need grading
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  const renderStudentAlerts = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <Bell className="mr-2 h-5 w-5" />
            Student Alerts
          </div>
          <Badge variant="destructive">
            {dashboardStats.highPriorityAlerts} high priority
          </Badge>
        </CardTitle>
        <CardDescription>
          Students requiring attention or showing improvement
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {mockStudentAlerts.slice(0, 5).map((alert) => (
            <div key={alert.id} className="flex items-start space-x-3 p-3 border rounded-lg">
              <div className={`p-1 rounded-full ${getAlertColor(alert.severity)}`}>
                {getAlertIcon(alert.alert_type)}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{alert.student_name}</div>
                  <Badge variant={
                    alert.severity === "high" ? "destructive" :
                    alert.severity === "medium" ? "secondary" : "default"
                  }>
                    {alert.severity}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  {alert.class_name} • {alert.student_id}
                </div>
                <div className="text-sm mt-1">{alert.description}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {format(new Date(alert.created_at), 'MMM dd, HH:mm')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  const renderRecentActivity = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Activity className="mr-2 h-5 w-5" />
          Recent Activity
        </CardTitle>
        <CardDescription>
          Your recent actions and system updates
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {mockRecentActivities.map((activity) => (
            <div key={activity.id} className="flex items-start space-x-3 p-3 border rounded-lg">
              <div className="p-1 rounded-full bg-muted">
                {activity.type === "grade_submitted" && <Calculator className="h-4 w-4" />}
                {activity.type === "attendance_marked" && <Users className="h-4 w-4" />}
                {activity.type === "assessment_created" && <FileText className="h-4 w-4" />}
                {activity.type === "announcement" && <MessageSquare className="h-4 w-4" />}
              </div>
              <div className="flex-1">
                <div className="font-medium">{activity.title}</div>
                <div className="text-sm text-muted-foreground">{activity.description}</div>
                {activity.class_name && (
                  <Badge variant="outline" className="mt-1 text-xs">
                    {activity.class_name}
                  </Badge>
                )}
                <div className="text-xs text-muted-foreground mt-1">
                  {format(new Date(activity.timestamp), 'MMM dd, HH:mm')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  const renderQuickActions = () => (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
        <CardDescription>
          Common tasks and shortcuts
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          <Button variant="outline" className="h-auto p-4 flex-col">
            <Users className="h-6 w-6 mb-2" />
            <span className="text-sm">Mark Attendance</span>
          </Button>
          <Button variant="outline" className="h-auto p-4 flex-col">
            <Calculator className="h-6 w-6 mb-2" />
            <span className="text-sm">Enter Grades</span>
          </Button>
          <Button variant="outline" className="h-auto p-4 flex-col">
            <Plus className="h-6 w-6 mb-2" />
            <span className="text-sm">Create Assessment</span>
          </Button>
          <Button variant="outline" className="h-auto p-4 flex-col">
            <FileText className="h-6 w-6 mb-2" />
            <span className="text-sm">Generate Report</span>
          </Button>
          <Button variant="outline" className="h-auto p-4 flex-col">
            <MessageSquare className="h-6 w-6 mb-2" />
            <span className="text-sm">Send Message</span>
          </Button>
          <Button variant="outline" className="h-auto p-4 flex-col">
            <Calendar className="h-6 w-6 mb-2" />
            <span className="text-sm">View Timetable</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Teacher Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {teacherData.name}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={selectedTerm.toString()} onValueChange={(value) => setSelectedTerm(parseInt(value))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {zimbabweTerms.map((term) => (
                <SelectItem key={term.value} value={term.value.toString()}>
                  {formatTerm(term.value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      {renderQuickStats()}

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="classes">Classes</TabsTrigger>
          <TabsTrigger value="students">Students</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {renderPerformanceOverview()}
              {renderUpcomingSessions()}
            </div>
            <div className="space-y-6">
              {renderQuickActions()}
              {renderRecentActivity()}
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="classes" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {renderClassOverview()}
            {renderStudentAlerts()}
          </div>
        </TabsContent>
        
        <TabsContent value="students" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {renderStudentAlerts()}
            <Card>
              <CardHeader>
                <CardTitle>Student Performance Trends</CardTitle>
                <CardDescription>
                  Performance tracking and analytics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                  <h3 className="text-lg font-semibold mb-2">Performance Analytics</h3>
                  <p className="text-muted-foreground">
                    Detailed student performance tracking coming soon
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="schedule" className="space-y-6">
          {renderUpcomingSessions()}
          <Card>
            <CardHeader>
              <CardTitle>Weekly Schedule</CardTitle>
              <CardDescription>
                Your complete teaching schedule
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Calendar className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-semibold mb-2">Weekly Timetable</h3>
                <p className="text-muted-foreground">
                  Interactive timetable view coming soon
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}