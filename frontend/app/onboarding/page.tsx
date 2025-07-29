"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Progress } from "@/components/ui/progress"
import { GraduationCap, ArrowLeft, ArrowRight, CheckCircle, Users, MapPin } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

const steps = [
  { id: 1, title: "School Information", description: "Basic details about your school" },
  { id: 2, title: "Administrator Account", description: "Create your admin account" },
  { id: 3, title: "School Configuration", description: "Set up your school structure" },
  { id: 4, title: "Payment Plan", description: "Choose your subscription plan" },
  { id: 5, title: "Confirmation", description: "Review and confirm setup" },
]

export default function OnboardingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [errors, setErrors] = useState({})
  const [formData, setFormData] = useState({
    // School Information
    schoolName: "",
    schoolType: "",
    address: "",
    city: "",
    province: "",
    phone: "",
    email: "",
    website: "",
    establishedYear: "",
    studentCount: "",

    // Administrator Account
    adminFirstName: "",
    adminLastName: "",
    adminEmail: "",
    adminPhone: "",
    adminPassword: "",
    adminConfirmPassword: "",

    // School Configuration
    academicYear: "",
    termStructure: "",
    gradeStructure: "",
    subjects: [],

    // Payment Plan
    selectedPlan: "",
    billingCycle: "monthly",
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  const validateStep = (step: number) => {
    const stepErrors = {}
    
    switch (step) {
      case 1: // School Information
        if (!formData.schoolName?.trim()) stepErrors.schoolName = 'School name is required'
        else if (formData.schoolName.trim().length < 3) stepErrors.schoolName = 'School name must be at least 3 characters'
        
        if (!formData.schoolType) stepErrors.schoolType = 'School type is required'
        
        if (!formData.address?.trim()) stepErrors.address = 'Address is required'
        
        if (!formData.city?.trim()) stepErrors.city = 'City is required'
        
        if (!formData.province) stepErrors.province = 'Province is required'
        
        if (!formData.phone?.trim()) {
          stepErrors.phone = 'Phone number is required'
        } else if (!/^[\+]?[0-9\s\-\(\)]{10,15}$/.test(formData.phone.replace(/\s+/g, ''))) {
          stepErrors.phone = 'Please enter a valid phone number (10-15 digits)'
        }
        
        if (!formData.email?.trim()) stepErrors.email = 'Email is required'
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
          stepErrors.email = 'Please enter a valid email address'
        }
        
        if (formData.establishedYear && (parseInt(formData.establishedYear) < 1900 || parseInt(formData.establishedYear) > new Date().getFullYear())) {
          stepErrors.establishedYear = 'Please enter a valid year'
        }
        
        if (!formData.studentCount) stepErrors.studentCount = 'Student count range is required'
        break
        
      case 2: // Administrator Account
        if (!formData.adminFirstName?.trim()) stepErrors.adminFirstName = 'First name is required'
        else if (formData.adminFirstName.trim().length < 2) stepErrors.adminFirstName = 'First name must be at least 2 characters'
        
        if (!formData.adminLastName?.trim()) stepErrors.adminLastName = 'Last name is required'
        else if (formData.adminLastName.trim().length < 2) stepErrors.adminLastName = 'Last name must be at least 2 characters'
        
        if (!formData.adminEmail?.trim()) stepErrors.adminEmail = 'Email is required'
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.adminEmail)) {
          stepErrors.adminEmail = 'Please enter a valid email address'
        }
        
        if (!formData.adminPhone?.trim()) {
          stepErrors.adminPhone = 'Phone number is required'
        } else if (!/^[\+]?[0-9\s\-\(\)]{10,15}$/.test(formData.adminPhone.replace(/\s+/g, ''))) {
          stepErrors.adminPhone = 'Please enter a valid phone number (10-15 digits)'
        }
        
        if (!formData.adminPassword) stepErrors.adminPassword = 'Password is required'
        else if (formData.adminPassword.length < 8) stepErrors.adminPassword = 'Password must be at least 8 characters'
        else if (!/(?=.*[0-9])(?=.*[!@#$%^&*])/.test(formData.adminPassword)) {
          stepErrors.adminPassword = 'Password must contain at least one number and one special character'
        }
        
        if (!formData.adminConfirmPassword) stepErrors.adminConfirmPassword = 'Please confirm your password'
        else if (formData.adminPassword !== formData.adminConfirmPassword) {
          stepErrors.adminConfirmPassword = 'Passwords do not match'
        }
        break
        
      case 3: // School Configuration
        if (!formData.academicYear) stepErrors.academicYear = 'Academic year is required'
        if (!formData.termStructure) stepErrors.termStructure = 'Term structure is required'
        if (!formData.gradeStructure) stepErrors.gradeStructure = 'Grade structure is required'
        break
        
      case 4: // Payment Plan
        if (!formData.selectedPlan) stepErrors.selectedPlan = 'Please select a subscription plan'
        break
    }
    
    setErrors(stepErrors)
    return Object.keys(stepErrors).length === 0
  }

  const nextStep = () => {
    if (validateStep(currentStep) && currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = async () => {
    try {
      // Validate all steps before submission
      const allStepsValid = [1, 2, 3, 4].every(step => validateStep(step))
      
      if (!allStepsValid) {
        alert('Please complete all required fields before submitting.')
        return
      }

      const requestBody = {
        name: formData.schoolName,
        type: formData.schoolType,
        contact: {
          email: formData.email,
          phone: formData.phone,
          website: formData.website,
        },
        address: {
          line1: formData.address,
          city: formData.city,
          province: formData.province,
        },
        established_year: parseInt(formData.establishedYear) || new Date().getFullYear(),
        student_count_range: formData.studentCount,
        subscription_tier: formData.selectedPlan || 'basic',
        configuration: {
          academic_year: formData.academicYear,
          term_structure: formData.termStructure,
          grade_structure: formData.gradeStructure,
          timezone: "Africa/Harare",
          language: "en",
          currency: "USD"
        },
        admin_user: {
          first_name: formData.adminFirstName,
          last_name: formData.adminLastName,
          email: formData.adminEmail,
          phone: formData.adminPhone,
        },
      };

      console.log("Request Body:", JSON.stringify(requestBody, null, 2));

      // Create school using our API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/platform/schools`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      
      if (response.ok) {
        const result = await response.json()
        console.log('School created successfully:', result)

        // Show success message
        alert(`School "${result.name}" created successfully! Please log in at your school's dedicated portal.`)

        // Redirect to school's subdomain login page
        const schoolUrl = `http://localhost:3001/sign-in?school=${result.subdomain}&message=school_created`
        window.location.href = schoolUrl
      } else {
        const error = await response.json()
        console.error('Failed to create school:', error)
        alert(`Failed to create school: ${error.detail || 'Please try again.'}`)
      }
    } catch (error) {
      console.error('Onboarding failed:', error)
      alert('Something went wrong. Please check your connection and try again.')
    }
  }

  const progress = (currentStep / steps.length) * 100

  return (
    <div className="min-h-screen bg-background">
      {/* Simple Header - No navigation menu */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold">OneClass</span>
            </Link>
            <div className="text-sm text-muted-foreground">
              Step {currentStep} of {steps.length}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-2xl font-bold">School Setup</h1>
            <span className="text-sm text-muted-foreground">{Math.round(progress)}% Complete</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Steps Navigation */}
        <div className="flex items-center justify-center mb-8 overflow-x-auto">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
                  currentStep === step.id
                    ? "bg-primary text-primary-foreground"
                    : currentStep > step.id
                      ? "bg-green-100 text-green-800"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {currentStep > step.id ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <span className="h-4 w-4 rounded-full bg-current opacity-20" />
                )}
                <span className="text-sm font-medium hidden sm:block">{step.title}</span>
              </div>
              {index < steps.length - 1 && <div className="w-8 h-px bg-border mx-2" />}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="max-w-2xl mx-auto">
          {currentStep === 1 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MapPin className="mr-2 h-5 w-5" />
                  School Information
                </CardTitle>
                <CardDescription>Tell us about your school so we can customize your experience</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="schoolName">School Name *</Label>
                    <Input
                      id="schoolName"
                      value={formData.schoolName}
                      onChange={(e) => handleInputChange("schoolName", e.target.value)}
                      placeholder="e.g. Harare Primary School"
                      className={errors.schoolName ? "border-red-500" : ""}
                    />
                    {errors.schoolName && <p className="text-red-500 text-xs mt-1">{errors.schoolName}</p>}
                  </div>
                  <div>
                    <Label htmlFor="schoolType">School Type *</Label>
                    <Select
                      value={formData.schoolType}
                      onValueChange={(value) => handleInputChange("schoolType", value)}
                    >
                      <SelectTrigger className={errors.schoolType ? "border-red-500" : ""}>
                        <SelectValue placeholder="Select school type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="primary">Primary School</SelectItem>
                        <SelectItem value="secondary">Secondary School</SelectItem>
                        <SelectItem value="combined">Combined School</SelectItem>
                        <SelectItem value="college">College</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.schoolType && <p className="text-red-500 text-xs mt-1">{errors.schoolType}</p>}
                  </div>
                </div>

                <div>
                  <Label htmlFor="address">Physical Address *</Label>
                  <Textarea
                    id="address"
                    value={formData.address}
                    onChange={(e) => handleInputChange("address", e.target.value)}
                    placeholder="Enter your school's physical address"
                    rows={3}
                    className={errors.address ? "border-red-500" : ""}
                  />
                  {errors.address && <p className="text-red-500 text-xs mt-1">{errors.address}</p>}
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="city">City *</Label>
                    <Input
                      id="city"
                      value={formData.city}
                      onChange={(e) => handleInputChange("city", e.target.value)}
                      placeholder="e.g. Harare"
                      className={errors.city ? "border-red-500" : ""}
                    />
                    {errors.city && <p className="text-red-500 text-xs mt-1">{errors.city}</p>}
                  </div>
                  <div>
                    <Label htmlFor="province">Province *</Label>
                    <Select value={formData.province} onValueChange={(value) => handleInputChange("province", value)}>
                      <SelectTrigger className={errors.province ? "border-red-500" : ""}>
                        <SelectValue placeholder="Select province" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="harare">Harare</SelectItem>
                        <SelectItem value="bulawayo">Bulawayo</SelectItem>
                        <SelectItem value="manicaland">Manicaland</SelectItem>
                        <SelectItem value="mashonaland-central">Mashonaland Central</SelectItem>
                        <SelectItem value="mashonaland-east">Mashonaland East</SelectItem>
                        <SelectItem value="mashonaland-west">Mashonaland West</SelectItem>
                        <SelectItem value="masvingo">Masvingo</SelectItem>
                        <SelectItem value="matabeleland-north">Matabeleland North</SelectItem>
                        <SelectItem value="matabeleland-south">Matabeleland South</SelectItem>
                        <SelectItem value="midlands">Midlands</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.province && <p className="text-red-500 text-xs mt-1">{errors.province}</p>}
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="phone">Phone Number *</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleInputChange("phone", e.target.value)}
                      placeholder="+263 77 123 4567"
                      className={errors.phone ? "border-red-500" : ""}
                    />
                    {errors.phone && <p className="text-red-500 text-xs mt-1">{errors.phone}</p>}
                    <p className="text-xs text-muted-foreground mt-1">Include country code (e.g., +263 for Zimbabwe)</p>
                  </div>
                  <div>
                    <Label htmlFor="email">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      placeholder="admin@yourschool.co.zw"
                      className={errors.email ? "border-red-500" : ""}
                    />
                    {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="website">Website (Optional)</Label>
                    <Input
                      id="website"
                      value={formData.website}
                      onChange={(e) => handleInputChange("website", e.target.value)}
                      placeholder="www.yourschool.co.zw"
                    />
                  </div>
                  <div>
                    <Label htmlFor="establishedYear">Established Year</Label>
                    <Input
                      id="establishedYear"
                      value={formData.establishedYear}
                      onChange={(e) => handleInputChange("establishedYear", e.target.value)}
                      placeholder="e.g. 1995"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="studentCount">Approximate Student Count *</Label>
                  <Select
                    value={formData.studentCount}
                    onValueChange={(value) => handleInputChange("studentCount", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select student count range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1-50">1-50 students</SelectItem>
                      <SelectItem value="51-200">51-200 students</SelectItem>
                      <SelectItem value="201-500">201-500 students</SelectItem>
                      <SelectItem value="501-1000">501-1000 students</SelectItem>
                      <SelectItem value="1000+">1000+ students</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.studentCount && <p className="text-red-500 text-xs mt-1">{errors.studentCount}</p>}
                </div>
              </CardContent>
            </Card>
          )}

          {currentStep === 2 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Users className="mr-2 h-5 w-5" />
                  Administrator Account
                </CardTitle>
                <CardDescription>Create your administrator account to manage the school system</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="adminFirstName">First Name *</Label>
                    <Input
                      id="adminFirstName"
                      value={formData.adminFirstName}
                      onChange={(e) => handleInputChange("adminFirstName", e.target.value)}
                      placeholder="John"
                      className={errors.adminFirstName ? "border-red-500" : ""}
                    />
                    {errors.adminFirstName && <p className="text-red-500 text-xs mt-1">{errors.adminFirstName}</p>}
                  </div>
                  <div>
                    <Label htmlFor="adminLastName">Last Name *</Label>
                    <Input
                      id="adminLastName"
                      value={formData.adminLastName}
                      onChange={(e) => handleInputChange("adminLastName", e.target.value)}
                      placeholder="Mukamuri"
                      className={errors.adminLastName ? "border-red-500" : ""}
                    />
                    {errors.adminLastName && <p className="text-red-500 text-xs mt-1">{errors.adminLastName}</p>}
                  </div>
                </div>

                <div>
                  <Label htmlFor="adminEmail">Email Address *</Label>
                  <Input
                    id="adminEmail"
                    type="email"
                    value={formData.adminEmail}
                    onChange={(e) => handleInputChange("adminEmail", e.target.value)}
                    placeholder="john.mukamuri@yourschool.co.zw"
                    className={errors.adminEmail ? "border-red-500" : ""}
                  />
                  {errors.adminEmail && <p className="text-red-500 text-xs mt-1">{errors.adminEmail}</p>}
                  <p className="text-xs text-muted-foreground mt-1">This will be your login email address</p>
                </div>

                <div>
                  <Label htmlFor="adminPhone">Phone Number *</Label>
                  <Input
                    id="adminPhone"
                    type="tel"
                    value={formData.adminPhone}
                    onChange={(e) => handleInputChange("adminPhone", e.target.value)}
                    placeholder="+263 77 123 4567"
                    className={errors.adminPhone ? "border-red-500" : ""}
                  />
                  {errors.adminPhone && <p className="text-red-500 text-xs mt-1">{errors.adminPhone}</p>}
                  <p className="text-xs text-muted-foreground mt-1">Include country code (e.g., +263 for Zimbabwe)</p>
                </div>

                <div>
                  <Label htmlFor="adminPassword">Password *</Label>
                  <Input
                    id="adminPassword"
                    type="password"
                    value={formData.adminPassword}
                    onChange={(e) => handleInputChange("adminPassword", e.target.value)}
                    placeholder="Create a strong password"
                    className={errors.adminPassword ? "border-red-500" : ""}
                  />
                  {errors.adminPassword && <p className="text-red-500 text-xs mt-1">{errors.adminPassword}</p>}
                  <p className="text-xs text-muted-foreground mt-1">
                    Must be at least 8 characters with numbers and special characters
                  </p>
                </div>

                <div>
                  <Label htmlFor="adminConfirmPassword">Confirm Password *</Label>
                  <Input
                    id="adminConfirmPassword"
                    type="password"
                    value={formData.adminConfirmPassword}
                    onChange={(e) => handleInputChange("adminConfirmPassword", e.target.value)}
                    placeholder="Confirm your password"
                    className={errors.adminConfirmPassword ? "border-red-500" : ""}
                  />
                  {errors.adminConfirmPassword && <p className="text-red-500 text-xs mt-1">{errors.adminConfirmPassword}</p>}
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox id="terms" />
                  <Label htmlFor="terms" className="text-sm">
                    I agree to the{" "}
                    <a href="#" className="text-primary hover:underline">
                      Terms of Service
                    </a>{" "}
                    and{" "}
                    <a href="#" className="text-primary hover:underline">
                      Privacy Policy
                    </a>
                  </Label>
                </div>
              </CardContent>
            </Card>
          )}

          {currentStep === 3 && (
            <Card>
              <CardHeader>
                <CardTitle>School Configuration</CardTitle>
                <CardDescription>Set up your school's academic structure and preferences</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="academicYear">Current Academic Year *</Label>
                  <Select
                    value={formData.academicYear}
                    onValueChange={(value) => handleInputChange("academicYear", value)}
                  >
                    <SelectTrigger className={errors.academicYear ? "border-red-500" : ""}>
                      <SelectValue placeholder="Select academic year" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2024">2024</SelectItem>
                      <SelectItem value="2025">2025</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.academicYear && <p className="text-red-500 text-xs mt-1">{errors.academicYear}</p>}
                </div>

                <div>
                  <Label htmlFor="termStructure">Term Structure *</Label>
                  <Select
                    value={formData.termStructure}
                    onValueChange={(value) => handleInputChange("termStructure", value)}
                  >
                    <SelectTrigger className={errors.termStructure ? "border-red-500" : ""}>
                      <SelectValue placeholder="Select term structure" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3-terms">3 Terms per Year</SelectItem>
                      <SelectItem value="4-terms">4 Terms per Year</SelectItem>
                      <SelectItem value="2-semesters">2 Semesters per Year</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.termStructure && <p className="text-red-500 text-xs mt-1">{errors.termStructure}</p>}
                </div>

                <div>
                  <Label htmlFor="gradeStructure">Grade Structure *</Label>
                  <Select
                    value={formData.gradeStructure}
                    onValueChange={(value) => handleInputChange("gradeStructure", value)}
                  >
                    <SelectTrigger className={errors.gradeStructure ? "border-red-500" : ""}>
                      <SelectValue placeholder="Select grade structure" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="primary">Primary (ECD A - Grade 7)</SelectItem>
                      <SelectItem value="secondary">Secondary (Form 1 - Form 6)</SelectItem>
                      <SelectItem value="combined">Combined (ECD A - Form 6)</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.gradeStructure && <p className="text-red-500 text-xs mt-1">{errors.gradeStructure}</p>}
                </div>

                <div>
                  <Label>Core Subjects (Select all that apply)</Label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {[
                      "Mathematics",
                      "English",
                      "Shona",
                      "Science",
                      "Social Studies",
                      "Physical Education",
                      "Art",
                      "Music",
                      "Religious Studies",
                      "Computer Studies",
                    ].map((subject) => (
                      <div key={subject} className="flex items-center space-x-2">
                        <Checkbox id={subject} />
                        <Label htmlFor={subject} className="text-sm">
                          {subject}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-muted p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Additional Configuration</h4>
                  <p className="text-sm text-muted-foreground">
                    You can add more subjects, classes, and configure detailed settings after completing the setup.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {currentStep === 4 && (
            <Card>
              <CardHeader>
                <CardTitle>Choose Your Plan</CardTitle>
                <CardDescription>
                  Select the plan that best fits your school's needs. You can change this later.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {errors.selectedPlan && <p className="text-red-500 text-sm mb-4">{errors.selectedPlan}</p>}
                <div className="grid gap-4">
                  {[
                    {
                      id: "basic",
                      name: "Basic",
                      price: "$29",
                      period: "month",
                      description: "Perfect for small schools up to 200 students",
                      features: ["Up to 200 students", "Basic SIS features", "Parent portal", "Email support"],
                    },
                    {
                      id: "professional",
                      name: "Professional",
                      price: "$79",
                      period: "month",
                      description: "Ideal for medium schools up to 800 students",
                      features: [
                        "Up to 800 students",
                        "Full SIS & academic management",
                        "Finance & billing",
                        "AI learning tools",
                      ],
                      popular: true,
                    },
                    {
                      id: "enterprise",
                      name: "Enterprise",
                      price: "$199",
                      period: "month",
                      description: "For large schools and school groups",
                      features: [
                        "Unlimited students",
                        "All features included",
                        "Multi-school management",
                        "Dedicated support",
                      ],
                    },
                  ].map((plan) => (
                    <div
                      key={plan.id}
                      className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                        formData.selectedPlan === plan.id ? "border-primary bg-primary/5" : "border-border"
                      }`}
                      onClick={() => handleInputChange("selectedPlan", plan.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="font-semibold">{plan.name}</h3>
                            {plan.popular && (
                              <span className="bg-primary text-primary-foreground text-xs px-2 py-1 rounded">
                                Popular
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{plan.description}</p>
                          <ul className="text-xs text-muted-foreground mt-2 space-y-1">
                            {plan.features.map((feature, index) => (
                              <li key={index}>• {feature}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold">{plan.price}</div>
                          <div className="text-sm text-muted-foreground">per {plan.period}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <span className="font-medium text-green-800">30-Day Free Trial</span>
                  </div>
                  <p className="text-sm text-green-700 mt-1">
                    Start with a free trial. No credit card required. Cancel anytime.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {currentStep === 5 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="mr-2 h-5 w-5 text-green-600" />
                  Setup Complete!
                </CardTitle>
                <CardDescription>Review your information and complete the setup</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-2">School Information</h4>
                    <div className="text-sm space-y-1">
                      <p>
                        <strong>Name:</strong> {formData.schoolName}
                      </p>
                      <p>
                        <strong>Type:</strong> {formData.schoolType}
                      </p>
                      <p>
                        <strong>Location:</strong> {formData.city}, {formData.province}
                      </p>
                      <p>
                        <strong>Students:</strong> {formData.studentCount}
                      </p>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Administrator</h4>
                    <div className="text-sm space-y-1">
                      <p>
                        <strong>Name:</strong> {formData.adminFirstName} {formData.adminLastName}
                      </p>
                      <p>
                        <strong>Email:</strong> {formData.adminEmail}
                      </p>
                      <p>
                        <strong>Phone:</strong> {formData.adminPhone}
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Selected Plan</h4>
                  <div className="bg-muted p-4 rounded-lg">
                    <p className="font-medium capitalize">{formData.selectedPlan} Plan</p>
                    <p className="text-sm text-muted-foreground">30-day free trial included</p>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 mb-2">What happens next?</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Your school account will be created</li>
                    <li>• You'll receive login credentials via email</li>
                    <li>• Our team will help you import your existing data</li>
                    <li>• You can start using OneClass immediately</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <Button variant="outline" onClick={prevStep} disabled={currentStep === 1}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Previous
            </Button>

            {currentStep < steps.length ? (
              <Button onClick={nextStep}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={handleComplete} className="bg-green-600 hover:bg-green-700">
                Complete Setup
                <CheckCircle className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}