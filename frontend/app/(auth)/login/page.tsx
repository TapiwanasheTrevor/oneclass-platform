"use client"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/useAuth"
import { api } from "@/lib/api"
import { AlertCircle, CheckCircle, Eye, EyeOff, GraduationCap, Loader2 } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { redirectToSchoolSubdomain } from '@/utils/subdomain'

function isClerkConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  return !!key && !key.includes('your-') && key.startsWith('pk_')
}

/**
 * When Clerk is configured, this page redirects to Clerk's sign-in.
 * Clerk handles the full sign-in flow (social, email, MFA) and redirects
 * to /dashboard on success — the useAuth hook then fetches /auth/me.
 *
 * When Clerk is NOT configured (dev mode), it shows a custom email/password
 * form that calls POST /auth/login for local development.
 */
export default function LoginPage() {
  const router = useRouter()
  const { user, isLoading, isAuthenticated } = useAuth()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/dashboard")
    }
  }, [isAuthenticated, isLoading, router])

  // When Clerk is configured, redirect to Clerk's sign-in page
  useEffect(() => {
    if (isClerkConfigured()) {
      router.replace("/sign-in")
    }
  }, [router])

  // If Clerk is configured, show loading while redirecting
  if (isClerkConfigured()) {
    return (
      <div className="w-full max-w-md flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  // Dev mode: custom login form
  return <DevLoginForm />
}

/**
 * Development-only login form using email/password via POST /auth/login.
 * This bypasses Clerk for local development without Clerk keys.
 */
function DevLoginForm() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
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

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      router.push("/dashboard")
    }
  }, [isAuthenticated, authLoading, router])

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (error) setError("")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const response = await api.post('/api/v1/auth/login', {
        email: formData.email.trim(),
        password: formData.password,
      })
      const data = response.data

      // Store token for dev mode
      if (data.access_token) {
        localStorage.setItem('auth_token', data.access_token)
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
      }
      if (data.user?.primary_school_id) {
        localStorage.setItem('current_school_id', data.user.primary_school_id)
      } else if (data.user?.school_memberships?.length > 0) {
        localStorage.setItem('current_school_id', data.user.school_memberships[0].school_id)
      }

      setSuccess("Login successful! Redirecting to your school...")

      setTimeout(() => {
        if (data.user) {
          redirectToSchoolSubdomain(data.user)
        } else {
          router.push("/dashboard")
        }
      }, 1000)
    } catch (err: any) {
      console.error('Login error:', err)

      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          const validationErrors = err.response.data.detail
            .map((error: any) => error.msg || error.message || String(error))
            .join(', ')
          setError(`Validation error: ${validationErrors}`)
        } else if (typeof err.response.data.detail === 'object') {
          setError(err.response.data.detail.message || JSON.stringify(err.response.data.detail))
        } else {
          setError(err.response.data.detail)
        }

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
        <Badge variant="outline" className="text-xs">Dev Mode</Badge>
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
                disabled={loading || !!success}
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
                  disabled={loading || !!success}
                  className="pr-10 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  disabled={loading || !!success}
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
                  disabled={loading || !!success}
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
              disabled={loading || !!success || (schools.length > 0 && !selectedSchool)}
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
          &larr; Back to homepage
        </Link>
      </div>
    </div>
  )
}
