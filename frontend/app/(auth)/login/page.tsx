"use client"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/useAuth"
import { AlertCircle, CheckCircle, Eye, EyeOff, GraduationCap, Loader2 } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { redirectToSchoolSubdomain } from '@/utils/subdomain'

export default function LoginPage() {
  const router = useRouter()
  const { user, login, isLoading } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [schools, setSchools] = useState<any[]>([])
  const [selectedSchool, setSelectedSchool] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })

  // Redirect if already authenticated
  useEffect(() => {
    console.log("API URL:", process.env.NEXT_PUBLIC_API_URL);
    if (user && !isLoading) {
      router.push("/dashboard")
    }
  }, [user, isLoading, router])

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear errors when user starts typing
    if (error) setError("")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      // Use the login function from useAuth hook
      const loginResult = await login(formData.email.trim(), formData.password)

      setSuccess("Login successful! Redirecting to your school...")

      // Redirect to school subdomain after successful login
      setTimeout(() => {
        if (loginResult?.user) {
          redirectToSchoolSubdomain(loginResult.user)
        } else {
          // Fallback to dashboard if no user data
          router.push("/dashboard")
        }
      }, 1000)
    } catch (err: any) {
      console.error('Login error:', err)

      if (err.response?.data?.detail) {
        // Handle validation errors (422) which might be an array of error objects
        if (Array.isArray(err.response.data.detail)) {
          const validationErrors = err.response.data.detail
            .map((error: any) => error.msg || error.message || String(error))
            .join(', ')
          setError(`Validation error: ${validationErrors}`)
        } else if (typeof err.response.data.detail === 'object') {
          // Handle case where detail is an object
          setError(err.response.data.detail.message || JSON.stringify(err.response.data.detail))
        } else {
          setError(err.response.data.detail)
        }

        // If error indicates user has multiple schools, show school selection
        if (err.response.data.schools && err.response.data.schools.length > 1) {
          setSchools(err.response.data.schools)
          setError("Please select a school to continue:")
        }
      } else if (err.response?.status === 401) {
        setError("Invalid email or password. Please check your credentials.")
      } else if (err.response?.status === 422) {
        setError("Please check your input and try again.")
      } else if (err.response?.status === 423) {
        setError("Account is suspended. Please contact your administrator.")
      } else if (err.response?.status === 429) {
        setError("Too many login attempts. Please try again later.")
      } else {
        setError("Login failed. Please check your connection and try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md space-y-6 p-4">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center">
          <GraduationCap className="h-12 w-12 text-primary" />
        </div>
        <h1 className="text-3xl font-bold">Welcome Back</h1>
        <p className="text-muted-foreground">Sign in to your school account</p>
      </div>

      {/* Login Form */}
      <Card>
        <CardHeader>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>Enter your credentials to access your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription className="text-green-700">{success}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
                required
                disabled={loading || success}
                className="transition-colors"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => handleInputChange("password", e.target.value)}
                  required
                  disabled={loading || success}
                  className="pr-10 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  disabled={loading || success}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* School Selection */}
            {schools.length > 0 && (
              <div className="space-y-3">
                <Label>Select School</Label>
                <div className="grid gap-2">
                  {schools.map((school) => (
                    <div
                      key={school.school_id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedSchool === school.school_id
                          ? 'border-primary bg-primary/5'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedSchool(school.school_id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{school.school_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {school.role.replace('_', ' ').toLowerCase()}
                          </p>
                        </div>
                        <div className="space-y-1">
                          <Badge variant="outline" className="text-xs">
                            {school.role}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 text-sm">
                <input 
                  type="checkbox" 
                  className="rounded border-gray-300" 
                  disabled={loading || success}
                />
                <span>Remember me</span>
              </label>
              <Link href="/forgot-password" className="text-sm text-primary hover:underline">
                Forgot password?
              </Link>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading || success || (schools.length > 0 && !selectedSchool)}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : success ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Success! Redirecting...
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link href="/signup" className="text-primary hover:underline font-medium">
                Contact your school administrator
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center">
        <Link href="/" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to homepage
        </Link>
      </div>
    </div>
  )
}
