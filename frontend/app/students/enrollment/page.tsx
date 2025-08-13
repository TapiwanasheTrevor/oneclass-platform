"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ChevronLeft } from "lucide-react"
import Link from "next/link"
import StudentRegistrationForm from "@/components/sis/StudentRegistrationForm"

export default function StudentEnrollmentPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/students">
            <Button variant="outline" size="sm">
              <ChevronLeft className="mr-2 h-4 w-4" />
              Back to Students
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Student Registration</h1>
            <p className="text-muted-foreground">Register a new student in the system</p>
          </div>
        </div>
      </div>

      {/* Registration Form */}
      <StudentRegistrationForm 
        onSuccess={() => {
          // Redirect to students list after successful registration
          window.location.href = '/students'
        }}
        onCancel={() => {
          // Go back to students list
          window.location.href = '/students'
        }}
      />
    </div>
  )
}