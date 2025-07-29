"use client"

import { useState } from "react"
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
} from "lucide-react"

export default function Dashboard() {
  const [selectedTerm] = useState("Term 1 2024")

  const stats = [
    {
      title: "Total Students",
      value: "1,247",
      change: "+12 this term",
      icon: Users,
      color: "text-blue-600",
    },
    {
      title: "Active Teachers",
      value: "89",
      change: "+3 new hires",
      icon: GraduationCap,
      color: "text-green-600",
    },
    {
      title: "Fee Collection",
      value: "$45,230",
      change: "78% collected",
      icon: DollarSign,
      color: "text-yellow-600",
    },
    {
      title: "Attendance Rate",
      value: "94.2%",
      change: "+2.1% vs last term",
      icon: CheckCircle,
      color: "text-emerald-600",
    },
  ]

  const recentActivities = [
    {
      type: "enrollment",
      message: "15 new students enrolled in Grade 1",
      time: "2 hours ago",
      icon: Users,
    },
    {
      type: "payment",
      message: "Fee payment received from John Mukamuri",
      time: "4 hours ago",
      icon: DollarSign,
    },
    {
      type: "assessment",
      message: "Mathematics test results published for Form 2A",
      time: "6 hours ago",
      icon: FileText,
    },
    {
      type: "event",
      message: "Inter-house sports day scheduled for next Friday",
      time: "1 day ago",
      icon: Trophy,
    },
  ]

  const upcomingTasks = [
    {
      task: "Review Grade 7 exam papers",
      due: "Tomorrow",
      priority: "high",
      module: "Assessment",
    },
    {
      task: "Send fee reminder notices",
      due: "This week",
      priority: "medium",
      module: "Finance",
    },
    {
      task: "Update student medical records",
      due: "Next week",
      priority: "low",
      module: "SIS",
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">School Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here's what's happening at your school today.</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">{selectedTerm}</Badge>
          <Button>Generate Report</Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start bg-transparent">
              <Users className="mr-2 h-4 w-4" />
              Enroll New Student
            </Button>
            <Button variant="outline" className="w-full justify-start bg-transparent">
              <FileText className="mr-2 h-4 w-4" />
              Create Assessment
            </Button>
            <Button variant="outline" className="w-full justify-start bg-transparent">
              <MessageSquare className="mr-2 h-4 w-4" />
              Send Announcement
            </Button>
            <Button variant="outline" className="w-full justify-start bg-transparent">
              <Calendar className="mr-2 h-4 w-4" />
              Schedule Event
            </Button>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest updates across all modules</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.map((activity, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <activity.icon className="h-4 w-4 mt-1 text-muted-foreground" />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm">{activity.message}</p>
                    <p className="text-xs text-muted-foreground">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Tasks */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Tasks</CardTitle>
            <CardDescription>Items requiring your attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingTasks.map((task, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{task.task}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge
                        variant={
                          task.priority === "high"
                            ? "destructive"
                            : task.priority === "medium"
                              ? "default"
                              : "secondary"
                        }
                        className="text-xs"
                      >
                        {task.priority}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{task.module}</span>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">{task.due}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Overview */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Academic Performance</CardTitle>
            <CardDescription>Overall school performance metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Mathematics</span>
                <span className="text-sm font-medium">78%</span>
              </div>
              <Progress value={78} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">English</span>
                <span className="text-sm font-medium">82%</span>
              </div>
              <Progress value={82} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Science</span>
                <span className="text-sm font-medium">75%</span>
              </div>
              <Progress value={75} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Shona</span>
                <span className="text-sm font-medium">85%</span>
              </div>
              <Progress value={85} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Platform status and alerts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-sm">All systems operational</span>
            </div>
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              <span className="text-sm">3 pending data syncs</span>
            </div>
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <span className="text-sm">Database usage: 67%</span>
            </div>
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Last backup: Today at 3:00 AM</p>
              <p className="text-xs text-muted-foreground">Next scheduled maintenance: Sunday 2:00 AM</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
