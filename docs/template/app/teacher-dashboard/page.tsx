"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { BookOpen, Users, Calendar, CheckCircle, Clock, Plus, Eye, Edit, MessageSquare } from "lucide-react"

export default function TeacherDashboard() {
  const classes = [
    { name: "Form 4A Mathematics", students: 32, attendance: 94 },
    { name: "Form 3B Mathematics", students: 28, attendance: 89 },
    { name: "Form 2A Mathematics", students: 35, attendance: 96 },
  ]

  const upcomingLessons = [
    { subject: "Mathematics", class: "Form 4A", time: "08:00 - 08:40", topic: "Quadratic Equations" },
    { subject: "Mathematics", class: "Form 3B", time: "09:00 - 09:40", topic: "Trigonometry" },
    { subject: "Mathematics", class: "Form 2A", time: "10:00 - 10:40", topic: "Algebra Basics" },
  ]

  const recentAssignments = [
    { title: "Quadratic Equations Test", class: "Form 4A", submitted: 28, total: 32, dueDate: "Today" },
    { title: "Trigonometry Homework", class: "Form 3B", submitted: 25, total: 28, dueDate: "Yesterday" },
    { title: "Algebra Practice", class: "Form 2A", submitted: 35, total: 35, dueDate: "2 days ago" },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Teacher Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, Mrs. Chikwanha! Here's your teaching overview.</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <MessageSquare className="mr-2 h-4 w-4" />
            Messages
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Lesson
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">My Classes</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">95 total students</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Lessons</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">2 completed, 1 upcoming</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Grading</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">Assignments to grade</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Attendance</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">93%</div>
            <p className="text-xs text-muted-foreground">This week</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Today's Schedule */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="mr-2 h-5 w-5" />
              Today's Schedule
            </CardTitle>
            <CardDescription>Your lessons for today</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {upcomingLessons.map((lesson, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{lesson.class}</p>
                    <p className="text-sm text-muted-foreground">{lesson.topic}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{lesson.time}</p>
                    <Badge variant="outline" className="text-xs">
                      {index === 0 ? "Next" : index === 1 ? "Later" : "Completed"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* My Classes */}
        <Card>
          <CardHeader>
            <CardTitle>My Classes</CardTitle>
            <CardDescription>Overview of your assigned classes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {classes.map((classItem, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{classItem.name}</span>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{classItem.students} students</span>
                    <span>{classItem.attendance}% attendance</span>
                  </div>
                  <Progress value={classItem.attendance} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Assignments */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Assignments</CardTitle>
            <CardDescription>Submission status overview</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentAssignments.map((assignment, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{assignment.title}</span>
                    <Badge
                      variant={assignment.submitted === assignment.total ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {assignment.dueDate}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{assignment.class}</span>
                    <span>
                      {assignment.submitted}/{assignment.total} submitted
                    </span>
                  </div>
                  <Progress value={(assignment.submitted / assignment.total) * 100} className="h-2" />
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
          <CardDescription>Common teaching tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <BookOpen className="h-6 w-6 mb-2" />
              <span className="text-sm">Create Lesson</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <Users className="h-6 w-6 mb-2" />
              <span className="text-sm">Take Attendance</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <CheckCircle className="h-6 w-6 mb-2" />
              <span className="text-sm">Grade Assignments</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <MessageSquare className="h-6 w-6 mb-2" />
              <span className="text-sm">Message Parents</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
