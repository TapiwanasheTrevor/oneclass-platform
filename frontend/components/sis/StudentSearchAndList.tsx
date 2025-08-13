"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { 
  Search, 
  Plus, 
  MoreHorizontal, 
  Eye, 
  Edit, 
  FileText, 
  Download, 
  Filter, 
  Users, 
  UserCheck, 
  UserX,
  Calendar,
  Phone,
  Mail,
  MapPin
} from "lucide-react"
import { useSISHooks, type Student, type StudentSearchRequest, ZIMBABWE_PROVINCES } from "@/lib/sis-api"
import { formatDistanceToNow } from "date-fns"
import Link from "next/link"

interface StudentSearchAndListProps {
  onStudentSelect?: (student: Student) => void
  onCreateStudent?: () => void
  onEditStudent?: (student: Student) => void
}

export default function StudentSearchAndList({ 
  onStudentSelect, 
  onCreateStudent, 
  onEditStudent 
}: StudentSearchAndListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedGrade, setSelectedGrade] = useState<string>("all")
  const [selectedStatus, setSelectedStatus] = useState<string>("all")
  const [selectedProvince, setSelectedProvince] = useState<string>("all")
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)

  const { useStudents, useStudentStats } = useSISHooks()

  // Build search parameters
  const searchParams = useMemo((): StudentSearchRequest => {
    const params: StudentSearchRequest = {
      page: currentPage,
      page_size: pageSize,
      sort_by: 'first_name',
      sort_order: 'asc',
    }

    if (searchQuery.trim()) {
      params.search_query = searchQuery.trim()
    }

    if (selectedGrade !== "all") {
      params.filters = {
        ...params.filters,
        grade_level: Number(selectedGrade),
      }
    }

    if (selectedStatus !== "all") {
      params.filters = {
        ...params.filters,
        status: selectedStatus,
      }
    }

    return params
  }, [searchQuery, selectedGrade, selectedStatus, currentPage, pageSize])

  const { data: studentsData, isLoading, error, refetch } = useStudents(searchParams)
  const { data: statsData, isLoading: statsLoading } = useStudentStats()

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

  const handleExport = async () => {
    try {
      // TODO: Implement export functionality
      console.log('Export functionality to be implemented')
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const handleStudentAction = (action: string, student: Student) => {
    switch (action) {
      case 'view':
        if (onStudentSelect) {
          onStudentSelect(student)
        } else {
          // Default navigation to student profile
          window.location.href = `/students/${student.id}`
        }
        break
      case 'edit':
        if (onEditStudent) {
          onEditStudent(student)
        } else {
          // Default navigation to edit page
          window.location.href = `/students/${student.id}/edit`
        }
        break
      case 'academic':
        window.location.href = `/students/${student.id}/academic`
        break
      case 'attendance':
        window.location.href = `/students/${student.id}/attendance`
        break
      case 'health':
        window.location.href = `/students/${student.id}/health`
        break
      default:
        break
    }
  }

  const resetFilters = () => {
    setSearchQuery("")
    setSelectedGrade("all")
    setSelectedStatus("all")
    setSelectedProvince("all")
    setCurrentPage(1)
  }

  const renderStatsCards = () => {
    if (statsLoading) {
      return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-3 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>
      )
    }

    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.total_students?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsData?.new_enrollments_this_term ? `+${statsData.new_enrollments_this_term} this term` : 'No change this term'}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Students</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.active_students?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsData?.total_students 
                ? `${((statsData.active_students / statsData.total_students) * 100).toFixed(1)}% of total`
                : 'No data available'
              }
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New Enrollments</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.new_enrollments_this_term?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">This term</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Attendance</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.average_attendance ? `${statsData.average_attendance.toFixed(1)}%` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsData?.attendance_trend 
                ? `${statsData.attendance_trend > 0 ? '+' : ''}${statsData.attendance_trend.toFixed(1)}% vs last term`
                : 'No comparison data'
              }
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderStudentsTable = () => {
    if (isLoading) {
      return (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Grade</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Enrollment</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-16" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                  <TableCell><Skeleton className="h-8 w-8 ml-auto" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )
    }

    if (error) {
      return (
        <Alert>
          <AlertDescription>
            Failed to load students. Please try again or contact support if the problem persists.
            <Button variant="outline" size="sm" onClick={() => refetch()} className="ml-4">
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )
    }

    if (!studentsData?.students.length) {
      return (
        <div className="text-center py-12">
          <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No students found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery || selectedGrade !== "all" || selectedStatus !== "all"
              ? "Try adjusting your search filters."
              : "Get started by adding your first student."
            }
          </p>
          {(searchQuery || selectedGrade !== "all" || selectedStatus !== "all") && (
            <Button variant="outline" onClick={resetFilters}>
              Clear Filters
            </Button>
          )}
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Grade</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Enrollment</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {studentsData.students.map((student) => (
                <TableRow key={student.id} className="cursor-pointer hover:bg-muted/50">
                  <TableCell className="font-medium">{student.student_number}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">
                        {student.preferred_name || `${student.first_name} ${student.last_name}`}
                      </div>
                      {student.preferred_name && (
                        <div className="text-sm text-muted-foreground">
                          {student.first_name} {student.last_name}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {student.current_grade_level ? getGradeName(student.current_grade_level) : 'Not set'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(student.status)}>
                      {student.status.charAt(0).toUpperCase() + student.status.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      {student.mobile_number && (
                        <div className="flex items-center text-sm">
                          <Phone className="mr-1 h-3 w-3" />
                          {student.mobile_number}
                        </div>
                      )}
                      {student.email && (
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Mail className="mr-1 h-3 w-3" />
                          {student.email}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {formatDistanceToNow(new Date(student.enrollment_date), { addSuffix: true })}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Age: {student.age}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">Open menu</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => handleStudentAction('view', student)}>
                          <Eye className="mr-2 h-4 w-4" />
                          View Profile
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleStudentAction('edit', student)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit Details
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleStudentAction('academic', student)}>
                          <FileText className="mr-2 h-4 w-4" />
                          Academic Record
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleStudentAction('attendance', student)}>
                          <Calendar className="mr-2 h-4 w-4" />
                          Attendance
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleStudentAction('health', student)}>
                          <Users className="mr-2 h-4 w-4" />
                          Health Records
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {studentsData && studentsData.total_pages > 1 && (
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, studentsData.total_count)} of {studentsData.total_count} students
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={!studentsData.has_previous}
              >
                Previous
              </Button>
              <div className="text-sm">
                Page {currentPage} of {studentsData.total_pages}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={!studentsData.has_next}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Student Information System</h1>
          <p className="text-muted-foreground">Manage student profiles, enrollment, and academic records</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          {onCreateStudent ? (
            <Button onClick={onCreateStudent}>
              <Plus className="mr-2 h-4 w-4" />
              Add Student
            </Button>
          ) : (
            <Link href="/students/enrollment">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Student
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {renderStatsCards()}

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Student Directory</CardTitle>
          <CardDescription>Search and manage student records</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Search Input */}
            <div className="flex items-center space-x-2">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search students by name, student number, or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Grade Level</Label>
                <Select value={selectedGrade} onValueChange={setSelectedGrade}>
                  <SelectTrigger>
                    <SelectValue placeholder="All grades" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Grades</SelectItem>
                    {Array.from({ length: 13 }, (_, i) => i + 1).map(grade => (
                      <SelectItem key={grade} value={grade.toString()}>
                        {getGradeName(grade)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                    <SelectItem value="transferred">Transferred</SelectItem>
                    <SelectItem value="graduated">Graduated</SelectItem>
                    <SelectItem value="expelled">Expelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Province</Label>
                <Select value={selectedProvince} onValueChange={setSelectedProvince}>
                  <SelectTrigger>
                    <SelectValue placeholder="All provinces" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Provinces</SelectItem>
                    {ZIMBABWE_PROVINCES.map(province => (
                      <SelectItem key={province} value={province}>{province}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Active Filters */}
            {(searchQuery || selectedGrade !== "all" || selectedStatus !== "all" || selectedProvince !== "all") && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground">Active filters:</span>
                {searchQuery && (
                  <Badge variant="secondary">
                    Search: {searchQuery}
                  </Badge>
                )}
                {selectedGrade !== "all" && (
                  <Badge variant="secondary">
                    Grade: {getGradeName(Number(selectedGrade))}
                  </Badge>
                )}
                {selectedStatus !== "all" && (
                  <Badge variant="secondary">
                    Status: {selectedStatus}
                  </Badge>
                )}
                {selectedProvince !== "all" && (
                  <Badge variant="secondary">
                    Province: {selectedProvince}
                  </Badge>
                )}
                <Button variant="outline" size="sm" onClick={resetFilters}>
                  Clear all
                </Button>
              </div>
            )}
          </div>

          {/* Students Table */}
          <div className="mt-6">
            {renderStudentsTable()}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}