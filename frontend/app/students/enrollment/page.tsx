"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ChevronLeft, ChevronRight, Check, User, MapPin, GraduationCap, Users } from "lucide-react"

// Zimbabwe provinces for dropdown
const ZIMBABWE_PROVINCES = [
  'Bulawayo',
  'Harare',
  'Manicaland',
  'Mashonaland Central',
  'Mashonaland East',
  'Mashonaland West',
  'Masvingo',
  'Matabeleland North',
  'Matabeleland South',
  'Midlands'
]

// Form steps
const FORM_STEPS = [
  { id: 'personal', title: 'Personal Information', icon: User },
  { id: 'contact', title: 'Contact Details', icon: MapPin },
  { id: 'academic', title: 'Academic Information', icon: GraduationCap },
  { id: 'guardian', title: 'Guardian Information', icon: Users },
  { id: 'review', title: 'Review & Submit', icon: Check }
]

interface StudentData {
  firstName: string
  middleName: string
  lastName: string
  dateOfBirth: string
  gender: string
  nationality: string
  homeLanguage: string
  mobileNumber: string
  email: string
  residentialAddress: {
    street: string
    suburb: string
    city: string
    province: string
    postalCode: string
  }
  currentGradeLevel: string
  previousSchool: string
  guardianName: string
  guardianPhone: string
  guardianEmail: string
  relationship: string
}

export default function StudentEnrollmentPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  
  const [formData, setFormData] = useState<StudentData>({
    firstName: '',
    middleName: '',
    lastName: '',
    dateOfBirth: '',
    gender: '',
    nationality: 'Zimbabwean',
    homeLanguage: '',
    mobileNumber: '',
    email: '',
    residentialAddress: {
      street: '',
      suburb: '',
      city: '',
      province: '',
      postalCode: ''
    },
    currentGradeLevel: '',
    previousSchool: '',
    guardianName: '',
    guardianPhone: '',
    guardianEmail: '',
    relationship: ''
  })

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('residentialAddress.')) {
      const addressField = field.split('.')[1]
      setFormData(prev => ({
        ...prev,
        residentialAddress: {
          ...prev.residentialAddress,
          [addressField]: value
        }
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

  const handleNext = () => {
    if (currentStep < FORM_STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      console.log('Student data:', formData)
      setSubmitSuccess(true)
    } catch (error) {
      console.error('Error submitting form:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderPersonalInfo = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="firstName">First Name *</Label>
          <Input
            id="firstName"
            value={formData.firstName}
            onChange={(e) => handleInputChange('firstName', e.target.value)}
            placeholder="Enter first name"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="middleName">Middle Name</Label>
          <Input
            id="middleName"
            value={formData.middleName}
            onChange={(e) => handleInputChange('middleName', e.target.value)}
            placeholder="Enter middle name"
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="lastName">Last Name *</Label>
        <Input
          id="lastName"
          value={formData.lastName}
          onChange={(e) => handleInputChange('lastName', e.target.value)}
          placeholder="Enter last name"
          required
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="dateOfBirth">Date of Birth *</Label>
          <Input
            id="dateOfBirth"
            type="date"
            value={formData.dateOfBirth}
            onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="gender">Gender *</Label>
          <Select value={formData.gender} onValueChange={(value) => handleInputChange('gender', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Male">Male</SelectItem>
              <SelectItem value="Female">Female</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="nationality">Nationality</Label>
          <Input
            id="nationality"
            value={formData.nationality}
            onChange={(e) => handleInputChange('nationality', e.target.value)}
            placeholder="Enter nationality"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="homeLanguage">Home Language *</Label>
          <Select value={formData.homeLanguage} onValueChange={(value) => handleInputChange('homeLanguage', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select home language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="English">English</SelectItem>
              <SelectItem value="Shona">Shona</SelectItem>
              <SelectItem value="Ndebele">Ndebele</SelectItem>
              <SelectItem value="Tonga">Tonga</SelectItem>
              <SelectItem value="Kalanga">Kalanga</SelectItem>
              <SelectItem value="Nambya">Nambya</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )

  const renderContactDetails = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="mobileNumber">Mobile Number</Label>
          <Input
            id="mobileNumber"
            value={formData.mobileNumber}
            onChange={(e) => handleInputChange('mobileNumber', e.target.value)}
            placeholder="+263 xxx xxx xxx"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email Address</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            placeholder="Enter email address"
          />
        </div>
      </div>
      
      <Separator />
      
      <div className="space-y-6">
        <h3 className="text-lg font-semibold">Residential Address</h3>
        
        <div className="space-y-2">
          <Label htmlFor="street">Street Address *</Label>
          <Input
            id="street"
            value={formData.residentialAddress.street}
            onChange={(e) => handleInputChange('residentialAddress.street', e.target.value)}
            placeholder="Enter street address"
            required
          />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="suburb">Suburb/Township</Label>
            <Input
              id="suburb"
              value={formData.residentialAddress.suburb}
              onChange={(e) => handleInputChange('residentialAddress.suburb', e.target.value)}
              placeholder="Enter suburb or township"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="city">City *</Label>
            <Input
              id="city"
              value={formData.residentialAddress.city}
              onChange={(e) => handleInputChange('residentialAddress.city', e.target.value)}
              placeholder="Enter city"
              required
            />
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="province">Province *</Label>
            <Select value={formData.residentialAddress.province} onValueChange={(value) => handleInputChange('residentialAddress.province', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select province" />
              </SelectTrigger>
              <SelectContent>
                {ZIMBABWE_PROVINCES.map(province => (
                  <SelectItem key={province} value={province}>{province}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="postalCode">Postal Code</Label>
            <Input
              id="postalCode"
              value={formData.residentialAddress.postalCode}
              onChange={(e) => handleInputChange('residentialAddress.postalCode', e.target.value)}
              placeholder="Enter postal code"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderAcademicInfo = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="currentGradeLevel">Current Grade Level *</Label>
        <Select value={formData.currentGradeLevel} onValueChange={(value) => handleInputChange('currentGradeLevel', value)}>
          <SelectTrigger>
            <SelectValue placeholder="Select grade level" />
          </SelectTrigger>
          <SelectContent>
            {Array.from({ length: 13 }, (_, i) => i + 1).map(grade => (
              <SelectItem key={grade} value={grade.toString()}>
                {grade <= 7 ? `Grade ${grade}` : `Form ${grade - 6}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="previousSchool">Previous School</Label>
        <Input
          id="previousSchool"
          value={formData.previousSchool}
          onChange={(e) => handleInputChange('previousSchool', e.target.value)}
          placeholder="Name of previous school (if any)"
        />
      </div>
    </div>
  )

  const renderGuardianInfo = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Primary Guardian/Parent</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="guardianName">Guardian Name *</Label>
          <Input
            id="guardianName"
            value={formData.guardianName}
            onChange={(e) => handleInputChange('guardianName', e.target.value)}
            placeholder="Enter guardian's full name"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="relationship">Relationship *</Label>
          <Select value={formData.relationship} onValueChange={(value) => handleInputChange('relationship', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select relationship" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Father">Father</SelectItem>
              <SelectItem value="Mother">Mother</SelectItem>
              <SelectItem value="Guardian">Guardian</SelectItem>
              <SelectItem value="Grandmother">Grandmother</SelectItem>
              <SelectItem value="Grandfather">Grandfather</SelectItem>
              <SelectItem value="Uncle">Uncle</SelectItem>
              <SelectItem value="Aunt">Aunt</SelectItem>
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="guardianPhone">Guardian Phone *</Label>
          <Input
            id="guardianPhone"
            value={formData.guardianPhone}
            onChange={(e) => handleInputChange('guardianPhone', e.target.value)}
            placeholder="+263 xxx xxx xxx"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="guardianEmail">Guardian Email</Label>
          <Input
            id="guardianEmail"
            type="email"
            value={formData.guardianEmail}
            onChange={(e) => handleInputChange('guardianEmail', e.target.value)}
            placeholder="Enter guardian's email"
          />
        </div>
      </div>
    </div>
  )

  const renderReview = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Review Your Information</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Personal Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Name:</span>
              <span className="text-sm font-medium">{formData.firstName} {formData.middleName} {formData.lastName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Date of Birth:</span>
              <span className="text-sm font-medium">{formData.dateOfBirth}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Gender:</span>
              <span className="text-sm font-medium">{formData.gender}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Language:</span>
              <span className="text-sm font-medium">{formData.homeLanguage}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Contact Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Phone:</span>
              <span className="text-sm font-medium">{formData.mobileNumber || 'Not provided'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Email:</span>
              <span className="text-sm font-medium">{formData.email || 'Not provided'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Address:</span>
              <span className="text-sm font-medium">{formData.residentialAddress.street}, {formData.residentialAddress.city}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Province:</span>
              <span className="text-sm font-medium">{formData.residentialAddress.province}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Academic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Grade Level:</span>
              <span className="text-sm font-medium">{formData.currentGradeLevel}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Previous School:</span>
              <span className="text-sm font-medium">{formData.previousSchool || 'None'}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Guardian Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Name:</span>
              <span className="text-sm font-medium">{formData.guardianName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Relationship:</span>
              <span className="text-sm font-medium">{formData.relationship}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Phone:</span>
              <span className="text-sm font-medium">{formData.guardianPhone}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Email:</span>
              <span className="text-sm font-medium">{formData.guardianEmail || 'Not provided'}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderPersonalInfo()
      case 1:
        return renderContactDetails()
      case 2:
        return renderAcademicInfo()
      case 3:
        return renderGuardianInfo()
      case 4:
        return renderReview()
      default:
        return null
    }
  }

  if (submitSuccess) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Student Registration</h1>
            <p className="text-muted-foreground">Registration completed successfully</p>
          </div>
        </div>
        
        <Card className="mx-auto max-w-2xl">
          <CardContent className="p-8 text-center">
            <div className="mb-6">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <Check className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Registration Successful!</h2>
              <p className="text-muted-foreground">
                Student registration has been submitted successfully. You will receive confirmation details shortly.
              </p>
            </div>
            <div className="space-y-2">
              <Button onClick={() => window.location.href = '/students'} className="w-full">
                View Student Directory
              </Button>
              <Button variant="outline" onClick={() => window.location.href = '/'} className="w-full">
                Return to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Student Registration</h1>
          <p className="text-muted-foreground">Register a new student in the system</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            Step {currentStep + 1} of {FORM_STEPS.length}
          </Badge>
        </div>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            {FORM_STEPS.map((step, index) => {
              const Icon = step.icon
              return (
                <div key={step.id} className="flex flex-col items-center">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                    index === currentStep 
                      ? 'border-primary bg-primary text-primary-foreground' 
                      : index < currentStep 
                        ? 'border-primary bg-primary text-primary-foreground' 
                        : 'border-muted-foreground/25 bg-muted text-muted-foreground'
                  }`}>
                    {index < currentStep ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <span className="mt-2 text-xs text-center font-medium max-w-20">
                    {step.title}
                  </span>
                </div>
              )
            })}
          </div>
          <div className="mt-4">
            <Progress value={((currentStep + 1) / FORM_STEPS.length) * 100} className="h-2" />
          </div>
        </CardHeader>
      </Card>

      {/* Form Content */}
      <Card>
        <CardHeader>
          <CardTitle>{FORM_STEPS[currentStep].title}</CardTitle>
          <CardDescription>
            {currentStep === 0 && "Enter the student's personal information"}
            {currentStep === 1 && "Provide contact details and address information"}
            {currentStep === 2 && "Enter academic and school information"}
            {currentStep === 3 && "Add guardian/parent information"}
            {currentStep === 4 && "Review all information before submitting"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderStepContent()}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button 
          variant="outline" 
          onClick={handleBack}
          disabled={currentStep === 0}
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        
        <div className="flex space-x-2">
          {currentStep < FORM_STEPS.length - 1 ? (
            <Button onClick={handleNext}>
              Next
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button 
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Registration'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}