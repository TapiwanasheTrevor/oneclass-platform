"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { User, BookOpen, DollarSign, Calendar, MessageSquare, TrendingUp } from "lucide-react"

export default function ParentDashboard() {
  const children = [
    {
      name: "Tendai Mukamuri",
      grade: "Form 4A",
      overallGrade: "B+",
      attendance: 95,
      fees: "Paid",
      nextPayment: "Term 2 - Due March 15",
    },
    {
      name: "Chipo Mukamuri",
      grade: "Form 2B",
      overallGrade: "A-",
      attendance: 98,
      fees: "Outstanding",
      nextPayment: "Term 1 Balance - $150",
    },
  ]

  const recentGrades = [
    { subject: "Mathematics", grade: "B+", date: "Jan 15", student: "Tendai" },
    { subject: "English", grade: "A", date: "Jan 14", student: "Chipo" },
    { subject: "Science", grade: "B", date: "Jan 12", student: "Tendai" },
    { subject: "Shona", grade: "A+", date: "Jan 10", student: "Chipo" },
  ]

  const upcomingEvents = [
    { event: "Parent-Teacher Conference", date: "Jan 25", time: "2:00 PM" },
    { event: "Sports Day", date: "Feb 2", time: "9:00 AM" },
    { event: "Science Fair", date: "Feb 15", time: "10:00 AM" },
  ]

  const messages = [
    {
      from: "Mrs. Chikwanha (Math Teacher)",
      subject: "Tendai's Progress Update",
      time: "2 hours ago",
      unread: true,
    },
    {
      from: "School Administration",
      subject: "Sports Day Permission Form",
      time: "1 day ago",
      unread: false,
    },
    {
      from: "Mr. Moyo (Form Teacher)",
      subject: "Chipo's Excellent Performance",
      time: "3 days ago",
      unread: false,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Parent Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, Mr. Mukamuri! Track your children's progress.</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <MessageSquare className="mr-2 h-4 w-4" />
            Messages
          </Button>
          <Button>
            <DollarSign className="mr-2 h-4 w-4" />
            Pay Fees
          </Button>
        </div>
      </div>

      {/* Children Overview */}
      <div className="grid gap-6 md:grid-cols-2">
        {children.map((child, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <User className="mr-2 h-5 w-5" />
                  {child.name}
                </div>
                <Badge variant="outline">{child.grade}</Badge>
              </CardTitle>
              <CardDescription>Academic overview and status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Overall Grade</p>
                  <p className="text-2xl font-bold text-green-600">{child.overallGrade}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Attendance</p>
                  <p className="text-2xl font-bold">{child.attendance}%</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Attendance Rate</span>
                  <span className="text-sm font-medium">{child.attendance}%</span>
                </div>
                <Progress value={child.attendance} className="h-2" />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div>
                  <p className="text-sm font-medium">Fee Status</p>
                  <p className="text-xs text-muted-foreground">{child.nextPayment}</p>
                </div>
                <Badge variant={child.fees === "Paid" ? "default" : "destructive"} className="text-xs">
                  {child.fees}
                </Badge>
              </div>

              <div className="flex space-x-2">
                <Button variant="outline" size="sm" className="flex-1 bg-transparent">
                  View Details
                </Button>
                <Button size="sm" className="flex-1">
                  Contact Teacher
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Recent Grades */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="mr-2 h-5 w-5" />
              Recent Grades
            </CardTitle>
            <CardDescription>Latest academic performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentGrades.map((grade, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <p className="font-medium">{grade.subject}</p>
                    <p className="text-xs text-muted-foreground">
                      {grade.student} • {grade.date}
                    </p>
                  </div>
                  <Badge
                    variant={
                      grade.grade.startsWith("A") ? "default" : grade.grade.startsWith("B") ? "secondary" : "outline"
                    }
                  >
                    {grade.grade}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Events */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="mr-2 h-5 w-5" />
              Upcoming Events
            </CardTitle>
            <CardDescription>School events and important dates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingEvents.map((event, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <p className="font-medium">{event.event}</p>
                    <p className="text-xs text-muted-foreground">{event.time}</p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {event.date}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Messages */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <MessageSquare className="mr-2 h-5 w-5" />
                Messages
              </div>
              <Badge variant="destructive" className="text-xs">
                1 New
              </Badge>
            </CardTitle>
            <CardDescription>Communications from school</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {messages.map((message, index) => (
                <div key={index} className={`p-2 border rounded ${message.unread ? "bg-blue-50 border-blue-200" : ""}`}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium">{message.from}</p>
                    <span className="text-xs text-muted-foreground">{message.time}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{message.subject}</p>
                  {message.unread && (
                    <Badge variant="destructive" className="text-xs mt-1">
                      New
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common parent tasks and communications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <DollarSign className="h-6 w-6 mb-2" />
              <span className="text-sm">Pay School Fees</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <MessageSquare className="h-6 w-6 mb-2" />
              <span className="text-sm">Message Teacher</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <Calendar className="h-6 w-6 mb-2" />
              <span className="text-sm">Book Meeting</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <BookOpen className="h-6 w-6 mb-2" />
              <span className="text-sm">View Reports</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
