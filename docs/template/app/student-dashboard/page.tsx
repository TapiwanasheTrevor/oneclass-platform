"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { BookOpen, Calendar, Trophy, Clock, CheckCircle, AlertCircle, Play, Download, Star } from "lucide-react"

export default function StudentDashboard() {
  const subjects = [
    { name: "Mathematics", grade: "B+", progress: 78, nextAssignment: "Quadratic Equations Test" },
    { name: "English", grade: "A-", progress: 85, nextAssignment: "Essay on Climate Change" },
    { name: "Science", grade: "B", progress: 72, nextAssignment: "Chemistry Lab Report" },
    { name: "Shona", grade: "A", progress: 88, nextAssignment: "Literature Analysis" },
  ]

  const upcomingAssignments = [
    { subject: "Mathematics", title: "Quadratic Equations Test", dueDate: "Tomorrow", priority: "high" },
    { subject: "English", title: "Essay Submission", dueDate: "Jan 20", priority: "medium" },
    { subject: "Science", title: "Lab Report", dueDate: "Jan 22", priority: "low" },
  ]

  const recentGrades = [
    { subject: "Mathematics", assignment: "Algebra Quiz", grade: "B+", date: "Jan 15" },
    { subject: "English", assignment: "Reading Comprehension", grade: "A", date: "Jan 14" },
    { subject: "Science", assignment: "Physics Test", grade: "B", date: "Jan 12" },
  ]

  const achievements = [
    { title: "Perfect Attendance", description: "No absences this term", icon: Trophy, color: "text-yellow-600" },
    { title: "Top Performer", description: "Mathematics class leader", icon: Star, color: "text-blue-600" },
    { title: "Early Submitter", description: "Always on time", icon: Clock, color: "text-green-600" },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Learning Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, Tendai! Ready to learn something new today?</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            My Schedule
          </Button>
          <Button>
            <BookOpen className="mr-2 h-4 w-4" />
            Study Now
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Grade</CardTitle>
            <Trophy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">B+</div>
            <p className="text-xs text-muted-foreground">Above class average</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Attendance</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">95%</div>
            <p className="text-xs text-muted-foreground">This term</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Assignments Due</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">1 due tomorrow</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Study Streak</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">7</div>
            <p className="text-xs text-muted-foreground">Days in a row</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Subject Progress */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Subject Progress</CardTitle>
            <CardDescription>Your performance across all subjects</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {subjects.map((subject, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{subject.name}</span>
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant={
                          subject.grade.startsWith("A")
                            ? "default"
                            : subject.grade.startsWith("B")
                              ? "secondary"
                              : "outline"
                        }
                      >
                        {subject.grade}
                      </Badge>
                      <Button variant="ghost" size="sm">
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>Next: {subject.nextAssignment}</span>
                    <span>{subject.progress}% complete</span>
                  </div>
                  <Progress value={subject.progress} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Achievements */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Trophy className="mr-2 h-5 w-5" />
              Achievements
            </CardTitle>
            <CardDescription>Your recent accomplishments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {achievements.map((achievement, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <achievement.icon className={`h-5 w-5 mt-1 ${achievement.color}`} />
                  <div>
                    <p className="font-medium">{achievement.title}</p>
                    <p className="text-sm text-muted-foreground">{achievement.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Upcoming Assignments */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="mr-2 h-5 w-5" />
              Upcoming Assignments
            </CardTitle>
            <CardDescription>Don't forget these deadlines</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingAssignments.map((assignment, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{assignment.title}</p>
                    <p className="text-sm text-muted-foreground">{assignment.subject}</p>
                  </div>
                  <div className="text-right">
                    <Badge
                      variant={
                        assignment.priority === "high"
                          ? "destructive"
                          : assignment.priority === "medium"
                            ? "default"
                            : "secondary"
                      }
                      className="text-xs mb-1"
                    >
                      {assignment.dueDate}
                    </Badge>
                    <p className="text-xs text-muted-foreground">{assignment.priority} priority</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Grades */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Grades</CardTitle>
            <CardDescription>Your latest assessment results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentGrades.map((grade, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{grade.assignment}</p>
                    <p className="text-sm text-muted-foreground">
                      {grade.subject} • {grade.date}
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
      </div>

      {/* Study Resources */}
      <Card>
        <CardHeader>
          <CardTitle>Study Resources</CardTitle>
          <CardDescription>Materials and tools to help you learn</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <BookOpen className="h-6 w-6 mb-2" />
              <span className="text-sm">Digital Library</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <Play className="h-6 w-6 mb-2" />
              <span className="text-sm">Video Lessons</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <Download className="h-6 w-6 mb-2" />
              <span className="text-sm">Study Guides</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col bg-transparent">
              <Trophy className="h-6 w-6 mb-2" />
              <span className="text-sm">Practice Tests</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
