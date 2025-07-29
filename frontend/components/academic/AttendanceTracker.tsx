/**
 * Attendance Tracker Component
 * Comprehensive attendance management with bulk operations and analytics
 */

'use client'

import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import {
  UserCheck,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Calendar,
  BarChart3,
  Save,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react'

import { 
  academicApi, 
  AttendanceStatus, 
  AttendanceSession,
  AttendanceRecord,
  AttendanceRecordCreate,
  BulkAttendanceCreate,
  AttendanceStats,
  SessionType 
} from '@/lib/academic-api'
import { useAuth } from '@/hooks/useAuth'
import { formatDate, formatTime, formatPercentage } from '@/lib/utils'

interface AttendanceTrackerProps {
  classId?: string
  subjectId?: string
  className?: string
}

interface StudentAttendance {
  student_id: string
  student_name: string
  status: AttendanceStatus
  arrival_time?: string
  notes?: string
  is_excused: boolean
}

export function AttendanceTracker({ classId, subjectId, className }: AttendanceTrackerProps) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [selectedSession, setSelectedSession] = useState<AttendanceSession | null>(null)
  const [studentsAttendance, setStudentsAttendance] = useState<StudentAttendance[]>([])
  const [isMarkingAttendance, setIsMarkingAttendance] = useState(false)
  const [bulkStatus, setBulkStatus] = useState<AttendanceStatus | ''>('')
  const [showStats, setShowStats] = useState(false)

  // Mock students data - in real app, this would come from SIS
  const mockStudents = [
    { id: '1', name: 'Tendai Mukamuri', class: 'Form 4A' },
    { id: '2', name: 'Chipo Madziva', class: 'Form 4A' },
    { id: '3', name: 'Takudzwa Ndoro', class: 'Form 4A' },
    { id: '4', name: 'Nyasha Chipanga', class: 'Form 4A' },
    { id: '5', name: 'Rudo Makoni', class: 'Form 4A' },
    { id: '6', name: 'Tapiwa Mugabe', class: 'Form 4A' },
    { id: '7', name: 'Privilege Chigumba', class: 'Form 4A' },
    { id: '8', name: 'Tatenda Moyo', class: 'Form 4A' }
  ]

  // Initialize students attendance
  useEffect(() => {
    setStudentsAttendance(mockStudents.map(student => ({
      student_id: student.id,
      student_name: student.name,
      status: AttendanceStatus.PRESENT,
      is_excused: false
    })))
  }, [])

  // Fetch attendance stats
  const { data: attendanceStats, isLoading: statsLoading } = useQuery({
    queryKey: ['attendance-stats', classId, subjectId, selectedDate],
    queryFn: () => academicApi.getAttendanceStats({
      class_id: classId,
      subject_id: subjectId,
      start_date: selectedDate,
      end_date: selectedDate
    }),
    enabled: showStats
  })

  // Create attendance session mutation
  const createSessionMutation = useMutation({
    mutationFn: (data: { timetable_id: string; session_date: string; session_type?: SessionType }) =>
      academicApi.createAttendanceSession(data),
    onSuccess: (session) => {
      setSelectedSession(session)
      toast.success('Attendance session created')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create attendance session')
    }
  })

  // Mark bulk attendance mutation
  const markAttendanceMutation = useMutation({
    mutationFn: (data: BulkAttendanceCreate) => academicApi.markBulkAttendance(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance-stats'] })
      setIsMarkingAttendance(false)
      toast.success('Attendance marked successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to mark attendance')
    }
  })

  const handleStudentStatusChange = (studentId: string, status: AttendanceStatus) => {
    setStudentsAttendance(prev => 
      prev.map(student => 
        student.student_id === studentId 
          ? { ...student, status }
          : student
      )
    )
  }

  const handleStudentExcusedChange = (studentId: string, isExcused: boolean) => {
    setStudentsAttendance(prev => 
      prev.map(student => 
        student.student_id === studentId 
          ? { ...student, is_excused: isExcused }
          : student
      )
    )
  }

  const handleBulkStatusChange = () => {
    if (!bulkStatus) return
    
    setStudentsAttendance(prev => 
      prev.map(student => ({
        ...student,
        status: bulkStatus as AttendanceStatus
      }))
    )
    setBulkStatus('')
  }

  const handleMarkAttendance = () => {
    if (!selectedSession) {
      toast.error('Please create an attendance session first')
      return
    }

    const attendanceRecords: AttendanceRecordCreate[] = studentsAttendance.map(student => ({
      student_id: student.student_id,
      attendance_status: student.status,
      arrival_time: student.arrival_time,
      notes: student.notes,
      is_excused: student.is_excused
    }))

    markAttendanceMutation.mutate({
      attendance_session_id: selectedSession.id,
      attendance_records: attendanceRecords
    })
  }

  const getStatusIcon = (status: AttendanceStatus) => {
    switch (status) {
      case AttendanceStatus.PRESENT:
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case AttendanceStatus.ABSENT:
        return <XCircle className="h-4 w-4 text-red-600" />
      case AttendanceStatus.LATE:
        return <Clock className="h-4 w-4 text-yellow-600" />
      case AttendanceStatus.EXCUSED:
        return <AlertTriangle className="h-4 w-4 text-blue-600" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: AttendanceStatus) => {
    const variants = {
      [AttendanceStatus.PRESENT]: 'default',
      [AttendanceStatus.ABSENT]: 'destructive',
      [AttendanceStatus.LATE]: 'secondary',
      [AttendanceStatus.EXCUSED]: 'outline'
    } as const

    return (
      <Badge variant={variants[status]} className="capitalize">
        {status}
      </Badge>
    )
  }

  const calculateAttendanceStats = () => {
    const total = studentsAttendance.length
    const present = studentsAttendance.filter(s => s.status === AttendanceStatus.PRESENT).length
    const absent = studentsAttendance.filter(s => s.status === AttendanceStatus.ABSENT).length
    const late = studentsAttendance.filter(s => s.status === AttendanceStatus.LATE).length
    const excused = studentsAttendance.filter(s => s.status === AttendanceStatus.EXCUSED).length
    const attendanceRate = total > 0 ? ((present + late) / total) * 100 : 0

    return { total, present, absent, late, excused, attendanceRate }
  }

  const stats = calculateAttendanceStats()

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Attendance Tracker</h1>
          <p className="text-muted-foreground">
            Mark and manage student attendance for {user?.school_name}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={() => setShowStats(!showStats)}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            {showStats ? 'Hide Stats' : 'Show Stats'}
          </Button>
          <Button
            variant="outline"
            onClick={() => window.print()}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Session Setup */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calendar className="h-5 w-5 mr-2" />
            Attendance Session
          </CardTitle>
          <CardDescription>
            Set up attendance session for the selected date and class
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Date</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Session Type</label>
              <Select defaultValue={SessionType.REGULAR}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SessionType.REGULAR}>Regular Class</SelectItem>
                  <SelectItem value={SessionType.MAKEUP}>Makeup Class</SelectItem>
                  <SelectItem value={SessionType.EXTRA}>Extra Class</SelectItem>
                  <SelectItem value={SessionType.EXAM}>Examination</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Class</label>
              <Select value={classId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select class" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="class1">Form 4A</SelectItem>
                  <SelectItem value="class2">Form 4B</SelectItem>
                  <SelectItem value="class3">Form 5A</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                onClick={() => createSessionMutation.mutate({
                  timetable_id: 'mock-timetable-id',
                  session_date: selectedDate,
                  session_type: SessionType.REGULAR
                })}
                disabled={createSessionMutation.isPending}
                className="w-full"
              >
                {createSessionMutation.isPending && (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                )}
                Create Session
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="text-2xl font-bold">{stats.total}</div>
                <div className="text-xs text-muted-foreground">Total Students</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <div>
                <div className="text-2xl font-bold text-green-600">{stats.present}</div>
                <div className="text-xs text-muted-foreground">Present</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-4 w-4 text-red-600" />
              <div>
                <div className="text-2xl font-bold text-red-600">{stats.absent}</div>
                <div className="text-xs text-muted-foreground">Absent</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-yellow-600" />
              <div>
                <div className="text-2xl font-bold text-yellow-600">{stats.late}</div>
                <div className="text-xs text-muted-foreground">Late</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <UserCheck className="h-4 w-4 text-blue-600" />
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {formatPercentage(stats.attendanceRate)}
                </div>
                <div className="text-xs text-muted-foreground">Attendance Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Attendance Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Attendance Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Present & Late Students</span>
              <span className="text-sm text-muted-foreground">
                {stats.present + stats.late} of {stats.total}
              </span>
            </div>
            <Progress value={stats.attendanceRate} className="h-2" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>0%</span>
              <span>{formatPercentage(stats.attendanceRate)} Attendance Rate</span>
              <span>100%</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Attendance Interface */}
      <Tabs defaultValue="mark" className="space-y-4">
        <TabsList>
          <TabsTrigger value="mark">Mark Attendance</TabsTrigger>
          <TabsTrigger value="history">Attendance History</TabsTrigger>
          {showStats && <TabsTrigger value="analytics">Analytics</TabsTrigger>}
        </TabsList>

        <TabsContent value="mark">
          <Card>
            <CardHeader>
              <CardTitle>Student Attendance</CardTitle>
              <CardDescription>
                Mark attendance for each student on {formatDate(selectedDate)}
              </CardDescription>
              
              {/* Bulk Actions */}
              <div className="flex items-center space-x-2 pt-4">
                <Select value={bulkStatus} onValueChange={setBulkStatus}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Bulk mark as..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={AttendanceStatus.PRESENT}>Present</SelectItem>
                    <SelectItem value={AttendanceStatus.ABSENT}>Absent</SelectItem>
                    <SelectItem value={AttendanceStatus.LATE}>Late</SelectItem>
                    <SelectItem value={AttendanceStatus.EXCUSED}>Excused</SelectItem>
                  </SelectContent>
                </Select>
                <Button 
                  variant="outline" 
                  onClick={handleBulkStatusChange}
                  disabled={!bulkStatus}
                >
                  Apply to All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student Name</TableHead>
                    <TableHead>Attendance Status</TableHead>
                    <TableHead>Arrival Time</TableHead>
                    <TableHead>Excused</TableHead>
                    <TableHead>Notes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {studentsAttendance.map((student) => (
                    <TableRow key={student.student_id}>
                      <TableCell className="font-medium">
                        {student.student_name}
                      </TableCell>
                      <TableCell>
                        <Select
                          value={student.status}
                          onValueChange={(value) => 
                            handleStudentStatusChange(student.student_id, value as AttendanceStatus)
                          }
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value={AttendanceStatus.PRESENT}>
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="h-4 w-4 text-green-600" />
                                <span>Present</span>
                              </div>
                            </SelectItem>
                            <SelectItem value={AttendanceStatus.ABSENT}>
                              <div className="flex items-center space-x-2">
                                <XCircle className="h-4 w-4 text-red-600" />
                                <span>Absent</span>
                              </div>
                            </SelectItem>
                            <SelectItem value={AttendanceStatus.LATE}>
                              <div className="flex items-center space-x-2">
                                <Clock className="h-4 w-4 text-yellow-600" />
                                <span>Late</span>
                              </div>
                            </SelectItem>
                            <SelectItem value={AttendanceStatus.EXCUSED}>
                              <div className="flex items-center space-x-2">
                                <AlertTriangle className="h-4 w-4 text-blue-600" />
                                <span>Excused</span>
                              </div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <input
                          type="time"
                          value={student.arrival_time || ''}
                          onChange={(e) => 
                            setStudentsAttendance(prev => 
                              prev.map(s => 
                                s.student_id === student.student_id
                                  ? { ...s, arrival_time: e.target.value }
                                  : s
                              )
                            )
                          }
                          className="px-2 py-1 border rounded text-sm"
                          disabled={student.status === AttendanceStatus.ABSENT}
                        />
                      </TableCell>
                      <TableCell>
                        <Checkbox
                          checked={student.is_excused}
                          onCheckedChange={(checked) => 
                            handleStudentExcusedChange(student.student_id, checked as boolean)
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <input
                          type="text"
                          value={student.notes || ''}
                          onChange={(e) => 
                            setStudentsAttendance(prev => 
                              prev.map(s => 
                                s.student_id === student.student_id
                                  ? { ...s, notes: e.target.value }
                                  : s
                              )
                            )
                          }
                          placeholder="Notes..."
                          className="px-2 py-1 border rounded text-sm w-full"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              <div className="flex items-center justify-between pt-6">
                <div className="text-sm text-muted-foreground">
                  {stats.total} students • {stats.present + stats.late} present • {stats.attendanceRate.toFixed(1)}% attendance rate
                </div>
                <Button
                  onClick={handleMarkAttendance}
                  disabled={markAttendanceMutation.isPending || !selectedSession}
                  size="lg"
                >
                  {markAttendanceMutation.isPending && (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  <Save className="h-4 w-4 mr-2" />
                  Save Attendance
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Attendance History</CardTitle>
              <CardDescription>
                View past attendance records and trends
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No attendance history available</p>
                <p className="text-sm">Start marking attendance to see historical data</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {showStats && (
          <TabsContent value="analytics">
            <Card>
              <CardHeader>
                <CardTitle>Attendance Analytics</CardTitle>
                <CardDescription>
                  Detailed attendance statistics and insights
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statsLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-3/4" />
                    <Skeleton className="h-8 w-1/2" />
                  </div>
                ) : attendanceStats ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-4">
                      <h3 className="font-semibold">Daily Statistics</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Total Students:</span>
                          <span className="font-medium">{attendanceStats.total_students}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Present:</span>
                          <span className="font-medium text-green-600">{attendanceStats.present_students}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Absent:</span>
                          <span className="font-medium text-red-600">{attendanceStats.absent_students}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Late:</span>
                          <span className="font-medium text-yellow-600">{attendanceStats.late_students}</span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                          <span>Attendance Rate:</span>
                          <span className="font-medium">{formatPercentage(attendanceStats.attendance_rate)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="font-semibold">Insights</h3>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        {attendanceStats.attendance_rate >= 90 && (
                          <p>✓ Excellent attendance rate</p>
                        )}
                        {attendanceStats.attendance_rate < 80 && (
                          <p>⚠ Low attendance rate requires attention</p>
                        )}
                        {attendanceStats.late_students > attendanceStats.total_students * 0.1 && (
                          <p>⚠ High number of late arrivals</p>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No analytics data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}

export default AttendanceTracker