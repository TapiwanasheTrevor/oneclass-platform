"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft } from "lucide-react"
import Link from "next/link"
import { useParams } from "next/navigation"
import StudentProfile from "@/components/sis/StudentProfile"

export default function StudentProfilePage() {
  const params = useParams()
  const studentId = params.id as string

  return (
    <div className="space-y-6">
      {/* Back Navigation */}
      <div className="flex items-center space-x-4">
        <Link href="/students">
          <Button variant="outline" size="sm">
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Students
          </Button>
        </Link>
      </div>

      {/* Student Profile */}
      <StudentProfile 
        studentId={studentId}
        onEdit={(student) => {
          // Navigate to edit page
          window.location.href = `/students/${student.id}/edit`
        }}
      />
    </div>
  )
}