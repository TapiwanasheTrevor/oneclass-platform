"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { GraduationCap, Mail, Lock, User, School, Users, BookOpen } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const router = useRouter()
  const [loginData, setLoginData] = useState({
    email: "",
    password: "",
    userType: "admin",
    schoolCode: "",
    rememberMe: false,
  })

  const handleInputChange = (field: string, value: string | boolean) => {
    setLoginData((prev) => ({ ...prev, [field]: value }))
  }

  const handleLogin = (userType: string) => {
    // Simulate login and redirect to appropriate dashboard
    switch (userType) {
      case "admin":
        router.push("/dashboard")
        break
      case "teacher":
        router.push("/teacher-dashboard")
        break
      case "parent":
        router.push("/parent-dashboard")
        break
      case "student":
        router.push("/student-dashboard")
        break
      default:
        router.push("/dashboard")
    }
  }

  const userTypes = [
    {
      id: "admin",
      title: "School Administrator",
      description: "Full access to school management",
      icon: School,
      color: "text-blue-600",
    },
    {
      id: "teacher",
      title: "Teacher",
      description: "Manage classes and students",
      icon: BookOpen,
      color: "text-green-600",
    },
    {
      id: "parent",
      title: "Parent/Guardian",
      description: "View child progress and communicate",
      icon: Users,
      color: "text-purple-600",
    },
    {
      id: "student",
      title: "Student",
      description: "Access learning materials and assignments",
      icon: User,
      color: "text-orange-600",
    },
  ]

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2 mb-4">
            <GraduationCap className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold">OneClass</span>
          </Link>
          <h1 className="text-2xl font-bold">Welcome Back</h1>
          <p className="text-muted-foreground">Sign in to your account</p>
        </div>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Sign In</TabsTrigger>
            <TabsTrigger value="user-type">Choose Role</TabsTrigger>
          </TabsList>

          <TabsContent value="login">
            <Card>
              <CardHeader>
                <CardTitle>Sign In</CardTitle>
                <CardDescription>Enter your credentials to access your account</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="your.email@school.co.zw"
                      value={loginData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter your password"
                      value={loginData.password}
                      onChange={(e) => handleInputChange("password", e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="schoolCode">School Code (Optional)</Label>
                  <Input
                    id="schoolCode"
                    placeholder="e.g. HPS001"
                    value={loginData.schoolCode}
                    onChange={(e) => handleInputChange("schoolCode", e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-1">Leave blank if you're a school administrator</p>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="remember"
                      checked={loginData.rememberMe}
                      onCheckedChange={(checked) => handleInputChange("rememberMe", checked as boolean)}
                    />
                    <Label htmlFor="remember" className="text-sm">
                      Remember me
                    </Label>
                  </div>
                  <Link href="/forgot-password" className="text-sm text-primary hover:underline">
                    Forgot password?
                  </Link>
                </div>

                <Button className="w-full" onClick={() => handleLogin("admin")}>
                  Sign In
                </Button>

                <div className="text-center">
                  <p className="text-sm text-muted-foreground">
                    Don't have an account?{" "}
                    <Link href="/onboarding" className="text-primary hover:underline">
                      Start free trial
                    </Link>
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="user-type">
            <Card>
              <CardHeader>
                <CardTitle>Choose Your Role</CardTitle>
                <CardDescription>Select how you'll be using OneClass</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {userTypes.map((type) => (
                  <div
                    key={type.id}
                    className="border rounded-lg p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => handleLogin(type.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <type.icon className={`h-6 w-6 ${type.color}`} />
                      <div className="flex-1">
                        <h3 className="font-medium">{type.title}</h3>
                        <p className="text-sm text-muted-foreground">{type.description}</p>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="text-center pt-4">
                  <p className="text-sm text-muted-foreground">
                    Need help?{" "}
                    <Link href="/support" className="text-primary hover:underline">
                      Contact support
                    </Link>
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Demo Accounts */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-sm">Demo Accounts</CardTitle>
            <CardDescription className="text-xs">Try OneClass with sample data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" size="sm" onClick={() => handleLogin("admin")} className="text-xs">
                Admin Demo
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleLogin("teacher")} className="text-xs">
                Teacher Demo
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleLogin("parent")} className="text-xs">
                Parent Demo
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleLogin("student")} className="text-xs">
                Student Demo
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
