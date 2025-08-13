"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { 
  UserCheck,
  Users,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Calendar,
  BarChart3,
  Save,
  RefreshCw,
  Download,
  Filter,
  TrendingUp,
  TrendingDown,
  FileText,
  Search,
  Info
} from "lucide-react"
import { toast } from "sonner"
import { format } from "date-fns"

import { 
  useAcademicHooks,
  type AttendanceSession,
  type AttendanceRecord,
  zimbabweTerms,
  formatTerm
} from "@/lib/academic-api"

interface AttendanceTrackerProps {
  classId: string
  subjectId: string
  academicYearId: string
  className?: string
}

const ATTENDANCE_STATUSES = [
  { value: 'present', label: 'Present', icon: CheckCircle2, color: 'text-green-600' },
  { value: 'absent', label: 'Absent', icon: XCircle, color: 'text-red-600' },
  { value: 'late', label: 'Late', icon: Clock, color: 'text-yellow-600' },
  { value: 'excused', label: 'Excused', icon: AlertTriangle, color: 'text-blue-600' }
]

const SESSION_TYPES = [
  { value: 'regular', label: 'Regular Class' },
  { value: 'makeup', label: 'Makeup Class' },
  { value: 'extra', label: 'Extra Class' },
  { value: 'exam', label: 'Examination' }
]

// Mock student data - in production, this would come from SIS module
const mockStudents = [
  { id: '1', name: 'Tinashe Mukamuri', student_number: 'ST2024001', class: 'Form 4A' },
  { id: '2', name: 'Chipo Nyathi', student_number: 'ST2024002', class: 'Form 4A' },
  { id: '3', name: 'Tatenda Moyo', student_number: 'ST2024003', class: 'Form 4A' },
  { id: '4', name: 'Blessing Ndlovu', student_number: 'ST2024004', class: 'Form 4A' },
  { id: '5', name: 'Rudo Chigumba', student_number: 'ST2024005', class: 'Form 4A' },
]

export default function AttendanceTracker({ 
  classId, 
  subjectId, 
  academicYearId,
  className 
}: AttendanceTrackerProps) {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [selectedTerm, setSelectedTerm] = useState(1)
  const [selectedSessionType, setSelectedSessionType] = useState<'regular' | 'makeup' | 'extra' | 'exam'>('regular')
  const [attendanceRecords, setAttendanceRecords] = useState<Record<string, string>>({})
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [sessionNotes, setSessionNotes] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [isSessionDialogOpen, setIsSessionDialogOpen] = useState(false)

  const { 
    useCreateAttendanceSession,
    useMarkBulkAttendance,
    useAttendanceStats
  } = useAcademicHooks()

  const createSessionMutation = useCreateAttendanceSession()
  const markAttendanceMutation = useMarkBulkAttendance()
  
  const { data: attendanceStats, isLoading: statsLoading } = useAttendanceStats({
    class_id: classId,
    subject_id: subjectId,
    start_date: selectedDate,
    end_date: selectedDate
  })

  // Filter students based on search
  const filteredStudents = mockStudents.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.student_number.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Initialize attendance records with all present
  const initializeAttendance = () => {
    const records: Record<string, string> = {}
    mockStudents.forEach(student => {
      records[student.id] = 'present'
    })
    setAttendanceRecords(records)
  }

  // Quick actions for bulk marking
  const markAllAs = (status: string) => {
    const records: Record<string, string> = {}
    filteredStudents.forEach(student => {
      records[student.id] = status
    })
    setAttendanceRecords(prev => ({ ...prev, ...records }))
    toast.success(`Marked all visible students as ${status}`)
  }

  const handleCreateSession = async () => {
    try {
      const session = await createSessionMutation.mutateAsync({
        timetable_id: `${classId}-${subjectId}`, // Mock timetable ID
        session_date: selectedDate,
        session_type: selectedSessionType
      })
      
      setIsSessionDialogOpen(false)
      toast.success('Attendance session created successfully')
      
      // Now mark attendance
      await handleSubmitAttendance(session.id)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleSubmitAttendance = async (sessionId: string) => {
    const records = Object.entries(attendanceRecords).map(([studentId, status]) => ({
      student_id: studentId,
      attendance_status: status as any,
      notes: notes[studentId] || undefined
    }))

    try {
      await markAttendanceMutation.mutateAsync({
        attendance_session_id: sessionId,
        attendance_records: records
      })
      
      toast.success('Attendance marked successfully')
    } catch (error) {
      // Error handled by mutation
    }
  }

  const getAttendanceStats = () => {
    const total = filteredStudents.length
    const statuses = Object.values(attendanceRecords)
    
    return {
      total,
      present: statuses.filter(s => s === 'present').length,
      absent: statuses.filter(s => s === 'absent').length,
      late: statuses.filter(s => s === 'late').length,
      excused: statuses.filter(s => s === 'excused').length,
      rate: total > 0 ? ((statuses.filter(s => s === 'present' || s === 'late').length / total) * 100).toFixed(1) : '0'
    }
  }

  const stats = getAttendanceStats()

  const renderAttendanceTable = () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">
            <Checkbox 
              checked={filteredStudents.every(s => attendanceRecords[s.id] === 'present')}
              onCheckedChange={(checked) => {
                if (checked) markAllAs('present')
              }}
            />
          </TableHead>
          <TableHead>Student Number</TableHead>
          <TableHead>Student Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Notes</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filteredStudents.map((student) => {
          const status = attendanceRecords[student.id] || 'present'
          const statusInfo = ATTENDANCE_STATUSES.find(s => s.value === status)
          const Icon = statusInfo?.icon || CheckCircle2
          
          return (
            <TableRow key={student.id}>
              <TableCell>
                <Checkbox 
                  checked={status === 'present'}
                  onCheckedChange={(checked) => {
                    setAttendanceRecords(prev => ({
                      ...prev,
                      [student.id]: checked ? 'present' : 'absent'
                    }))
                  }}
                />
              </TableCell>
              <TableCell className="font-medium">{student.student_number}</TableCell>
              <TableCell>{student.name}</TableCell>
              <TableCell>
                <Select 
                  value={status}
                  onValueChange={(value) => {
                    setAttendanceRecords(prev => ({
                      ...prev,
                      [student.id]: value
                    }))
                  }}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue>
                      <div className="flex items-center">
                        <Icon className={`mr-2 h-4 w-4 ${statusInfo?.color}`} />
                        {statusInfo?.label}
                      </div>
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {ATTENDANCE_STATUSES.map((statusOption) => {
                      const StatusIcon = statusOption.icon
                      return (
                        <SelectItem key={statusOption.value} value={statusOption.value}>
                          <div className="flex items-center">
                            <StatusIcon className={`mr-2 h-4 w-4 ${statusOption.color}`} />
                            {statusOption.label}
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </TableCell>
              <TableCell>
                <Input
                  placeholder="Add note..."
                  value={notes[student.id] || ''}
                  onChange={(e) => {
                    setNotes(prev => ({
                      ...prev,
                      [student.id]: e.target.value
                    }))
                  }}
                  className="w-48"
                />
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )

  const renderStatCards = () => (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Students
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
            <CheckCircle2 className="mr-1 h-4 w-4 text-green-600" />
            Present
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.present}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
            <XCircle className="mr-1 h-4 w-4 text-red-600" />
            Absent
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">{stats.absent}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
            <Clock className="mr-1 h-4 w-4 text-yellow-600" />
            Late
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-yellow-600">{stats.late}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Attendance Rate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.rate}%</div>
          <Progress value={parseFloat(stats.rate)} className="mt-2 h-2" />
        </CardContent>
      </Card>
    </div>
  )

  const renderAttendanceTrends = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <BarChart3 className="mr-2 h-5 w-5" />
          Attendance Trends
        </CardTitle>
        <CardDescription>
          Weekly attendance patterns and statistics
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Weekly Stats */}
          <div className="grid grid-cols-5 gap-4">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].map((day, index) => (
              <div key={day} className="text-center">
                <div className="text-sm font-medium text-muted-foreground mb-2">{day}</div>
                <div className="relative">
                  <Progress 
                    value={95 - index * 2} 
                    className="h-24 w-8 mx-auto [&>div]:bg-gradient-to-t [&>div]:from-primary [&>div]:to-primary/60"
                    style={{ transform: 'rotate(180deg)' }}
                  />
                  <div className="text-xs font-medium mt-2">{95 - index * 2}%</div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                <span className="text-sm font-medium">Best Day</span>
              </div>
              <div className="text-lg font-bold">Monday</div>
              <div className="text-xs text-muted-foreground">95% attendance</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                <span className="text-sm font-medium">Worst Day</span>
              </div>
              <div className="text-lg font-bold">Friday</div>
              <div className="text-xs text-muted-foreground">87% attendance</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center mb-1">
                <BarChart3 className="h-4 w-4 text-blue-600 mr-1" />
                <span className="text-sm font-medium">Weekly Avg</span>
              </div>
              <div className="text-lg font-bold">91%</div>
              <div className="text-xs text-muted-foreground">This week</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const renderAbsenteeList = () => {
    const absentStudents = filteredStudents.filter(s => 
      attendanceRecords[s.id] === 'absent' || attendanceRecords[s.id] === 'excused'
    )

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center">
              <AlertTriangle className="mr-2 h-5 w-5" />
              Absentee List
            </span>
            <Badge variant="destructive">
              {absentStudents.length} student{absentStudents.length !== 1 ? 's' : ''}
            </Badge>
          </CardTitle>
          <CardDescription>
            Students marked as absent or excused today
          </CardDescription>
        </CardHeader>
        <CardContent>
          {absentStudents.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle2 className="mx-auto h-12 w-12 text-green-600 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Perfect Attendance!</h3>
              <p className="text-muted-foreground">
                All students are present today
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {absentStudents.map((student) => {
                const status = attendanceRecords[student.id]
                const isExcused = status === 'excused'
                
                return (
                  <div key={student.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {isExcused ? (
                        <AlertTriangle className="h-5 w-5 text-blue-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      <div>
                        <p className="font-medium">{student.name}</p>
                        <p className="text-sm text-muted-foreground">{student.student_number}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={isExcused ? "secondary" : "destructive"}>
                        {isExcused ? 'Excused' : 'Absent'}
                      </Badge>
                      {notes[student.id] && (
                        <p className="text-xs text-muted-foreground mt-1">{notes[student.id]}</p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  // Initialize attendance on mount
  useState(() => {
    initializeAttendance()
  })

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Attendance Tracker</h1>
          <p className="text-muted-foreground">
            Mark and manage class attendance
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
          <Dialog open={isSessionDialogOpen} onOpenChange={setIsSessionDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Save className="mr-2 h-4 w-4" />
                Submit Attendance
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Submit Attendance</DialogTitle>
                <DialogDescription>
                  Create attendance session and submit records
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div>
                  <Label>Session Type</Label>
                  <Select value={selectedSessionType} onValueChange={(value: any) => setSelectedSessionType(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SESSION_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Session Notes (Optional)</Label>
                  <Textarea
                    placeholder="Add any notes about this session..."
                    value={sessionNotes}
                    onChange={(e) => setSessionNotes(e.target.value)}
                  />
                </div>

                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    You are about to submit attendance for {stats.total} students:
                    <ul className="mt-2 text-sm">
                      <li>• {stats.present} Present</li>
                      <li>• {stats.absent} Absent</li>
                      <li>• {stats.late} Late</li>
                      <li>• {stats.excused} Excused</li>
                    </ul>
                  </AlertDescription>
                </Alert>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsSessionDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateSession} disabled={createSessionMutation.isPending}>
                    {createSessionMutation.isPending ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Submit Attendance
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Attendance Session</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label>Date</Label>
              <Input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
              />
            </div>
            <div>
              <Label>Term</Label>
              <Select value={selectedTerm.toString()} onValueChange={(value) => setSelectedTerm(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {zimbabweTerms.map((term) => (
                    <SelectItem key={term.value} value={term.value.toString()}>
                      {formatTerm(term.value)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Class</Label>
              <Input value="Form 4A" disabled />
            </div>
            <div>
              <Label>Subject</Label>
              <Input value="Mathematics" disabled />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      {renderStatCards()}

      {/* Main Content */}
      <Tabs defaultValue="mark" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="mark">Mark Attendance</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="absentees">Absentees</TabsTrigger>
        </TabsList>
        
        <TabsContent value="mark" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Student Attendance</CardTitle>
              <CardDescription>
                Mark attendance for each student in the class
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Search and Quick Actions */}
              <div className="flex items-center justify-between mb-4">
                <div className="relative w-64">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search students..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm" onClick={() => markAllAs('present')}>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Mark All Present
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => markAllAs('absent')}>
                    <XCircle className="mr-2 h-4 w-4" />
                    Mark All Absent
                  </Button>
                </div>
              </div>

              {/* Attendance Table */}
              {renderAttendanceTable()}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="trends" className="space-y-6">
          {renderAttendanceTrends()}
        </TabsContent>
        
        <TabsContent value="absentees" className="space-y-6">
          {renderAbsenteeList()}
        </TabsContent>
      </Tabs>
    </div>
  )
}