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
  }

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    // Navigate to dashboard after completion
    router.push("/dashboard")
  }

  const progress = (currentStep / steps.length) * 100

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <nav className="border-b bg-background/95 backdrop-blur">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold">OneClass</span>
            </Link>
            <div className="text-sm text-muted-foreground">
              Step {currentStep} of {steps.length}
            </div>
          </div>
        </div>
      </nav>

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
                    />
                  </div>
                  <div>
                    <Label htmlFor="schoolType">School Type *</Label>
                    <Select
                      value={formData.schoolType}
                      onValueChange={(value) => handleInputChange("schoolType", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select school type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="primary">Primary School</SelectItem>
                        <SelectItem value="secondary">Secondary School</SelectItem>
                        <SelectItem value="combined">Combined School</SelectItem>
                        <SelectItem value="college">College</SelectItem>
                      </SelectContent>
                    </Select>
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
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="city">City *</Label>
                    <Input
                      id="city"
                      value={formData.city}
                      onChange={(e) => handleInputChange("city", e.target.value)}
                      placeholder="e.g. Harare"
                    />
                  </div>
                  <div>
                    <Label htmlFor="province">Province *</Label>
                    <Select value={formData.province} onValueChange={(value) => handleInputChange("province", value)}>
                      <SelectTrigger>
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
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="phone">Phone Number *</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => handleInputChange("phone", e.target.value)}
                      placeholder="+263 77 123 4567"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      placeholder="admin@yourschool.co.zw"
                    />
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
                    />
                  </div>
                  <div>
                    <Label htmlFor="adminLastName">Last Name *</Label>
                    <Input
                      id="adminLastName"
                      value={formData.adminLastName}
                      onChange={(e) => handleInputChange("adminLastName", e.target.value)}
                      placeholder="Mukamuri"
                    />
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
                  />
                  <p className="text-xs text-muted-foreground mt-1">This will be your login email address</p>
                </div>

                <div>
                  <Label htmlFor="adminPhone">Phone Number *</Label>
                  <Input
                    id="adminPhone"
                    value={formData.adminPhone}
                    onChange={(e) => handleInputChange("adminPhone", e.target.value)}
                    placeholder="+263 77 123 4567"
                  />
                </div>

                <div>
                  <Label htmlFor="adminPassword">Password *</Label>
                  <Input
                    id="adminPassword"
                    type="password"
                    value={formData.adminPassword}
                    onChange={(e) => handleInputChange("adminPassword", e.target.value)}
                    placeholder="Create a strong password"
                  />
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
                  />
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
                    <SelectTrigger>
                      <SelectValue placeholder="Select academic year" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2024">2024</SelectItem>
                      <SelectItem value="2025">2025</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="termStructure">Term Structure *</Label>
                  <Select
                    value={formData.termStructure}
                    onValueChange={(value) => handleInputChange("termStructure", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select term structure" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3-terms">3 Terms per Year</SelectItem>
                      <SelectItem value="4-terms">4 Terms per Year</SelectItem>
                      <SelectItem value="2-semesters">2 Semesters per Year</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="gradeStructure">Grade Structure *</Label>
                  <Select
                    value={formData.gradeStructure}
                    onValueChange={(value) => handleInputChange("gradeStructure", value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select grade structure" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="primary">Primary (ECD A - Grade 7)</SelectItem>
                      <SelectItem value="secondary">Secondary (Form 1 - Form 6)</SelectItem>
                      <SelectItem value="combined">Combined (ECD A - Form 6)</SelectItem>
                    </SelectContent>
                  </Select>
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
                <div className="grid gap-4">
                  {[
                    {
                      id: "starter",
                      name: "Starter",
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
