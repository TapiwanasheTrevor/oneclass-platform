"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar, 
  GraduationCap, 
  Heart, 
  Users, 
  FileText, 
  Edit, 
  Download,
  AlertCircle,
  Clock,
  BookOpen,
  Activity,
  Shield
} from "lucide-react"
import { useSISHooks, type Student, validateZimbabweData } from "@/lib/sis-api"
import { formatDistanceToNow, format } from "date-fns"

interface StudentProfileProps {
  studentId: string
  onEdit?: (student: Student) => void
  className?: string
}

export default function StudentProfile({ studentId, onEdit, className }: StudentProfileProps) {
  const [activeTab, setActiveTab] = useState("overview")
  const { useStudent } = useSISHooks()
  const { data: student, isLoading, error } = useStudent(studentId)

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100"
      case "suspended":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100"
      case "transferred":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100"
      case "graduated":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100"
      case "expelled":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100"
    }
  }

  const getGradeName = (gradeLevel: number) => {
    return gradeLevel <= 7 ? `Grade ${gradeLevel}` : `Form ${gradeLevel - 6}`
  }

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
  }

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Skeleton className="h-20 w-20 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-20" />
          </div>
        </div>
        
        <Card>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-6 w-32" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load student profile. Please try again or contact support if the problem persists.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!student) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Student not found. They may have been removed or you may not have permission to view this profile.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="mr-2 h-5 w-5" />
            Personal Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Full Name</h4>
              <p className="text-lg font-medium">{student.full_name}</p>
            </div>
            {student.preferred_name && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Preferred Name</h4>
                <p className="text-lg font-medium">{student.preferred_name}</p>
              </div>
            )}
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Date of Birth</h4>
              <p className="text-lg font-medium">
                {format(new Date(student.date_of_birth), 'dd MMM yyyy')} 
                <span className="text-sm text-muted-foreground ml-2">(Age {student.age})</span>
              </p>
            </div>
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Gender</h4>
              <p className="text-lg font-medium">{student.gender}</p>
            </div>
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Nationality</h4>
              <p className="text-lg font-medium">{student.nationality}</p>
            </div>
            {student.home_language && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Home Language</h4>
                <p className="text-lg font-medium">{student.home_language}</p>
              </div>
            )}
            {student.religion && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Religion</h4>
                <p className="text-lg font-medium">{student.religion}</p>
              </div>
            )}
            {student.tribe && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Tribe</h4>
                <p className="text-lg font-medium">{student.tribe}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Mail className="mr-2 h-5 w-5" />
            Contact Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {student.mobile_number && (
                <div className="flex items-center space-x-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{student.mobile_number}</p>
                    <p className="text-sm text-muted-foreground">Mobile</p>
                  </div>
                </div>
              )}
              {student.email && (
                <div className="flex items-center space-x-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{student.email}</p>
                    <p className="text-sm text-muted-foreground">Email</p>
                  </div>
                </div>
              )}
            </div>
            
            {student.residential_address && (
              <div className="flex items-start space-x-3">
                <MapPin className="h-4 w-4 text-muted-foreground mt-1" />
                <div>
                  <p className="font-medium">Residential Address</p>
                  <div className="text-sm text-muted-foreground">
                    <p>{student.residential_address.street}</p>
                    <p>{student.residential_address.suburb}, {student.residential_address.city}</p>
                    <p>{student.residential_address.province}</p>
                    {student.residential_address.postal_code && (
                      <p>{student.residential_address.postal_code}</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Academic Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <GraduationCap className="mr-2 h-5 w-5" />
            Academic Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Student Number</h4>
              <p className="text-lg font-medium">{student.student_number}</p>
            </div>
            {student.current_grade_level && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Current Grade</h4>
                <p className="text-lg font-medium">{getGradeName(student.current_grade_level)}</p>
              </div>
            )}
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Enrollment Date</h4>
              <p className="text-lg font-medium">
                {format(new Date(student.enrollment_date), 'dd MMM yyyy')}
                <span className="text-sm text-muted-foreground ml-2">
                  ({formatDistanceToNow(new Date(student.enrollment_date), { addSuffix: true })})
                </span>
              </p>
            </div>
            {student.zimsec_number && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">ZIMSEC Number</h4>
                <p className="text-lg font-medium">{student.zimsec_number}</p>
              </div>
            )}
            {student.expected_graduation_date && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Expected Graduation</h4>
                <p className="text-lg font-medium">{format(new Date(student.expected_graduation_date), 'dd MMM yyyy')}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Student Behavior */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="mr-2 h-5 w-5" />
            Student Behavior
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <h4 className="font-medium">Merit Points</h4>
                <p className="text-sm text-muted-foreground">Positive behavior recognition</p>
              </div>
              <div className="text-2xl font-bold text-green-600">{student.merit_points}</div>
            </div>
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <h4 className="font-medium">Disciplinary Points</h4>
                <p className="text-sm text-muted-foreground">Negative behavior points</p>
              </div>
              <div className="text-2xl font-bold text-red-600">{student.disciplinary_points}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderMedicalInfo = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Heart className="mr-2 h-5 w-5" />
            Medical Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {student.blood_type && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Blood Type</h4>
                <p className="text-lg font-medium">{student.blood_type}</p>
              </div>
            )}
            {student.medical_aid_provider && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Medical Aid Provider</h4>
                <p className="text-lg font-medium">{student.medical_aid_provider}</p>
              </div>
            )}
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Medical Conditions</h4>
              <p className="text-lg font-medium">
                {student.has_medical_conditions ? (
                  <Badge variant="outline" className="text-orange-600 border-orange-200">
                    Yes - See details
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-green-600 border-green-200">
                    None recorded
                  </Badge>
                )}
              </p>
            </div>
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-1">Allergies</h4>
              <p className="text-lg font-medium">
                {student.has_allergies ? (
                  <Badge variant="outline" className="text-red-600 border-red-200">
                    Yes - See details
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-green-600 border-green-200">
                    None recorded
                  </Badge>
                )}
              </p>
            </div>
            {student.special_needs && Object.keys(student.special_needs).length > 0 && (
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Special Needs</h4>
                <p className="text-lg font-medium">
                  <Badge variant="outline" className="text-blue-600 border-blue-200">
                    Yes - See details
                  </Badge>
                </p>
              </div>
            )}
            {student.dietary_requirements && (
              <div className="md:col-span-2">
                <h4 className="font-medium text-sm text-muted-foreground mb-1">Dietary Requirements</h4>
                <p className="text-lg font-medium">{student.dietary_requirements}</p>
              </div>
            )}
          </div>
          
          {(student.has_medical_conditions || student.has_allergies) && (
            <Alert className="mt-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                This student has medical conditions or allergies. Detailed information is available to authorized staff members.
                In case of emergency, contact the school nurse or administration immediately.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )

  const renderEmergencyContacts = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="mr-2 h-5 w-5" />
            Emergency Contacts
          </CardTitle>
          <CardDescription>
            Contact information for emergencies and pickup authorization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Contact Details Protected</h3>
            <p className="text-muted-foreground">
              Emergency contact information is available to authorized staff members only.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderRecentActivity = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="mr-2 h-5 w-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Clock className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Activity Timeline</h3>
            <p className="text-muted-foreground">
              Recent attendance, academic, and behavioral activities will be displayed here.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Avatar className="h-20 w-20">
            <AvatarImage src={student.profile_photo_url} alt={student.full_name} />
            <AvatarFallback className="text-lg font-semibold">
              {getInitials(student.first_name, student.last_name)}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {student.preferred_name || student.full_name}
            </h1>
            {student.preferred_name && (
              <p className="text-lg text-muted-foreground">{student.full_name}</p>
            )}
            <div className="flex items-center space-x-4 mt-2">
              <Badge className={getStatusColor(student.status)}>
                {student.status.charAt(0).toUpperCase() + student.status.slice(1)}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Student #{student.student_number}
              </span>
              {student.current_grade_level && (
                <span className="text-sm text-muted-foreground">
                  {getGradeName(student.current_grade_level)}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          {onEdit && (
            <Button onClick={() => onEdit(student)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="medical">Medical</TabsTrigger>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6">
          {renderOverview()}
        </TabsContent>
        
        <TabsContent value="medical" className="space-y-6">
          {renderMedicalInfo()}
        </TabsContent>
        
        <TabsContent value="contacts" className="space-y-6">
          {renderEmergencyContacts()}
        </TabsContent>
        
        <TabsContent value="activity" className="space-y-6">
          {renderRecentActivity()}
        </TabsContent>
      </Tabs>
    </div>
  )
}