"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Checkbox } from "@/components/ui/checkbox"
import { 
  Plus, 
  Clock, 
  Calendar, 
  Users, 
  BookOpen,
  MapPin,
  AlertTriangle,
  Edit,
  Trash2,
  Copy,
  Save,
  RefreshCw,
  Coffee,
  Utensils,
  GraduationCap
} from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"

import { 
  useAcademicHooks,
  type Period,
  type PeriodCreate,
  type Timetable,
  type TimetableCreate,
  zimbabweTerms,
  formatTerm
} from "@/lib/academic-api"

const periodSchema = z.object({
  period_number: z.number().min(1, "Period number must be at least 1"),
  name: z.string().min(1, "Period name is required").max(50),
  start_time: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/, "Invalid time format"),
  end_time: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/, "Invalid time format"),
  is_break: z.boolean().default(false),
  break_type: z.enum(["tea", "lunch", "assembly"]).optional(),
})

const timetableSchema = z.object({
  academic_year_id: z.string().min(1, "Academic year is required"),
  term_number: z.number().min(1).max(3),
  class_id: z.string().min(1, "Class is required"),
  subject_id: z.string().min(1, "Subject is required"),
  teacher_id: z.string().min(1, "Teacher is required"),
  period_id: z.string().min(1, "Period is required"),
  day_of_week: z.number().min(1).max(6),
  room_number: z.string().optional(),
  is_double_period: z.boolean().default(false),
  is_practical: z.boolean().default(false),
  week_pattern: z.enum(["all", "odd", "even"]).default("all"),
  effective_from: z.string(),
  effective_to: z.string().optional(),
  notes: z.string().optional(),
})

type PeriodFormData = z.infer<typeof periodSchema>
type TimetableFormData = z.infer<typeof timetableSchema>

interface TimetableManagementProps {
  academicYearId: string
  className?: string
}

const DAYS_OF_WEEK = [
  { value: 1, label: 'Monday', short: 'Mon' },
  { value: 2, label: 'Tuesday', short: 'Tue' },
  { value: 3, label: 'Wednesday', short: 'Wed' },
  { value: 4, label: 'Thursday', short: 'Thu' },
  { value: 5, label: 'Friday', short: 'Fri' },
  { value: 6, label: 'Saturday', short: 'Sat' }
]

const WEEK_PATTERNS = [
  { value: 'all', label: 'Every Week' },
  { value: 'odd', label: 'Odd Weeks' },
  { value: 'even', label: 'Even Weeks' }
]

export default function TimetableManagement({ academicYearId, className }: TimetableManagementProps) {
  const [selectedTerm, setSelectedTerm] = useState(1)
  const [selectedView, setSelectedView] = useState<'week' | 'teacher' | 'room'>('week')
  const [isPeriodDialogOpen, setIsPeriodDialogOpen] = useState(false)
  const [isTimetableDialogOpen, setIsTimetableDialogOpen] = useState(false)

  const { 
    usePeriods, 
    useCreatePeriod,
    useCreateTimetable,
    useSubjects
  } = useAcademicHooks()

  const { data: periods, isLoading: periodsLoading } = usePeriods()
  const { data: subjects } = useSubjects()
  const createPeriodMutation = useCreatePeriod()
  const createTimetableMutation = useCreateTimetable()

  const {
    register: registerPeriod,
    handleSubmit: handlePeriodSubmit,
    formState: { errors: periodErrors },
    reset: resetPeriod,
    setValue: setPeriodValue,
    watch: watchPeriod
  } = useForm<PeriodFormData>({
    resolver: zodResolver(periodSchema),
    defaultValues: {
      is_break: false,
      period_number: 1
    }
  })

  const {
    register: registerTimetable,
    handleSubmit: handleTimetableSubmit,
    formState: { errors: timetableErrors },
    reset: resetTimetable,
    setValue: setTimetableValue,
    watch: watchTimetable
  } = useForm<TimetableFormData>({
    resolver: zodResolver(timetableSchema),
    defaultValues: {
      academic_year_id: academicYearId,
      term_number: selectedTerm,
      is_double_period: false,
      is_practical: false,
      week_pattern: "all",
      effective_from: new Date().toISOString().split('T')[0]
    }
  })

  const watchIsBreak = watchPeriod("is_break")
  const watchIsPractical = watchTimetable("is_practical")

  const handleCreatePeriod = async (data: PeriodFormData) => {
    try {
      await createPeriodMutation.mutateAsync(data)
      setIsPeriodDialogOpen(false)
      resetPeriod()
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleCreateTimetableEntry = async (data: TimetableFormData) => {
    try {
      await createTimetableMutation.mutateAsync(data)
      setIsTimetableDialogOpen(false)
      resetTimetable()
    } catch (error) {
      // Error handled by mutation
    }
  }

  const getBreakIcon = (breakType?: string) => {
    switch (breakType) {
      case 'tea': return <Coffee className="h-4 w-4" />
      case 'lunch': return <Utensils className="h-4 w-4" />
      case 'assembly': return <Users className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const renderPeriodsTable = () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Period</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Time</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {periods?.items?.map((period: Period) => (
          <TableRow key={period.id}>
            <TableCell className="font-medium">
              {period.period_number}
            </TableCell>
            <TableCell className="flex items-center space-x-2">
              {getBreakIcon(period.break_type)}
              <span>{period.name}</span>
            </TableCell>
            <TableCell>
              {period.start_time} - {period.end_time}
            </TableCell>
            <TableCell>
              {(() => {
                const start = new Date(`2024-01-01T${period.start_time}:00`)
                const end = new Date(`2024-01-01T${period.end_time}:00`)
                const duration = (end.getTime() - start.getTime()) / (1000 * 60)
                return `${duration} min`
              })()}
            </TableCell>
            <TableCell>
              {period.is_break ? (
                <Badge variant="secondary" className="capitalize">
                  {period.break_type || 'Break'}
                </Badge>
              ) : (
                <Badge variant="outline">
                  Class
                </Badge>
              )}
            </TableCell>
            <TableCell>
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm">
                  <Edit className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )

  const renderWeeklyTimetable = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-7 gap-4">
        <div className="font-semibold p-2">Time</div>
        {DAYS_OF_WEEK.map((day) => (
          <div key={day.value} className="font-semibold p-2 text-center">
            {day.short}
          </div>
        ))}
      </div>
      
      {periods?.items?.filter((p: Period) => !p.is_break).map((period: Period) => (
        <div key={period.id} className="grid grid-cols-7 gap-4 border rounded-lg p-2">
          <div className="flex flex-col justify-center">
            <div className="font-medium text-sm">{period.name}</div>
            <div className="text-xs text-muted-foreground">
              {period.start_time} - {period.end_time}
            </div>
          </div>
          
          {DAYS_OF_WEEK.map((day) => (
            <div key={day.value} className="min-h-[60px] border rounded p-2 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors">
              <div className="text-xs text-center text-muted-foreground">
                No class scheduled
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Timetable Management</h1>
          <p className="text-muted-foreground">
            Manage school timetables, periods, and class schedules
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Dialog open={isPeriodDialogOpen} onOpenChange={setIsPeriodDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Clock className="mr-2 h-4 w-4" />
                Add Period
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Period</DialogTitle>
                <DialogDescription>
                  Add a new time period to the school schedule
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handlePeriodSubmit(handleCreatePeriod)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="period_number">Period Number*</Label>
                    <Input
                      id="period_number"
                      type="number"
                      min="1"
                      {...registerPeriod("period_number", { valueAsNumber: true })}
                    />
                    {periodErrors.period_number && (
                      <p className="text-sm text-red-600 mt-1">{periodErrors.period_number.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="name">Period Name*</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Period 1, Tea Break"
                      {...registerPeriod("name")}
                    />
                    {periodErrors.name && (
                      <p className="text-sm text-red-600 mt-1">{periodErrors.name.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="start_time">Start Time*</Label>
                    <Input
                      id="start_time"
                      type="time"
                      {...registerPeriod("start_time")}
                    />
                    {periodErrors.start_time && (
                      <p className="text-sm text-red-600 mt-1">{periodErrors.start_time.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="end_time">End Time*</Label>
                    <Input
                      id="end_time"
                      type="time"
                      {...registerPeriod("end_time")}
                    />
                    {periodErrors.end_time && (
                      <p className="text-sm text-red-600 mt-1">{periodErrors.end_time.message}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="is_break"
                    checked={watchIsBreak}
                    onCheckedChange={(checked) => setPeriodValue("is_break", checked as boolean)}
                  />
                  <Label htmlFor="is_break">This is a break period</Label>
                </div>

                {watchIsBreak && (
                  <div>
                    <Label htmlFor="break_type">Break Type</Label>
                    <Select onValueChange={(value) => setPeriodValue("break_type", value as any)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select break type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tea">
                          <div className="flex items-center">
                            <Coffee className="mr-2 h-4 w-4" />
                            Tea Break
                          </div>
                        </SelectItem>
                        <SelectItem value="lunch">
                          <div className="flex items-center">
                            <Utensils className="mr-2 h-4 w-4" />
                            Lunch Break
                          </div>
                        </SelectItem>
                        <SelectItem value="assembly">
                          <div className="flex items-center">
                            <Users className="mr-2 h-4 w-4" />
                            Assembly
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsPeriodDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createPeriodMutation.isPending}>
                    {createPeriodMutation.isPending ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Create Period
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
          
          <Dialog open={isTimetableDialogOpen} onOpenChange={setIsTimetableDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Timetable Entry
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Timetable Entry</DialogTitle>
                <DialogDescription>
                  Schedule a class for a specific period and day
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleTimetableSubmit(handleCreateTimetableEntry)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="term_number">Term</Label>
                    <Select 
                      value={selectedTerm.toString()}
                      onValueChange={(value) => {
                        const termNumber = parseInt(value)
                        setSelectedTerm(termNumber)
                        setTimetableValue("term_number", termNumber)
                      }}
                    >
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
                    <Label htmlFor="day_of_week">Day of Week*</Label>
                    <Select onValueChange={(value) => setTimetableValue("day_of_week", parseInt(value))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select day" />
                      </SelectTrigger>
                      <SelectContent>
                        {DAYS_OF_WEEK.map((day) => (
                          <SelectItem key={day.value} value={day.value.toString()}>
                            {day.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {timetableErrors.day_of_week && (
                      <p className="text-sm text-red-600 mt-1">{timetableErrors.day_of_week.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="period_id">Period*</Label>
                    <Select onValueChange={(value) => setTimetableValue("period_id", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select period" />
                      </SelectTrigger>
                      <SelectContent>
                        {periods?.items?.filter((p: Period) => !p.is_break).map((period: Period) => (
                          <SelectItem key={period.id} value={period.id}>
                            {period.name} ({period.start_time} - {period.end_time})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {timetableErrors.period_id && (
                      <p className="text-sm text-red-600 mt-1">{timetableErrors.period_id.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="subject_id">Subject*</Label>
                    <Select onValueChange={(value) => setTimetableValue("subject_id", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select subject" />
                      </SelectTrigger>
                      <SelectContent>
                        {subjects?.items?.map((subject: any) => (
                          <SelectItem key={subject.id} value={subject.id}>
                            {subject.name} ({subject.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {timetableErrors.subject_id && (
                      <p className="text-sm text-red-600 mt-1">{timetableErrors.subject_id.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="class_id">Class*</Label>
                    <Input
                      placeholder="Class ID (from SIS module)"
                      {...registerTimetable("class_id")}
                    />
                    {timetableErrors.class_id && (
                      <p className="text-sm text-red-600 mt-1">{timetableErrors.class_id.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="teacher_id">Teacher*</Label>
                    <Input
                      placeholder="Teacher ID (from user management)"
                      {...registerTimetable("teacher_id")}
                    />
                    {timetableErrors.teacher_id && (
                      <p className="text-sm text-red-600 mt-1">{timetableErrors.teacher_id.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="room_number">Room Number</Label>
                    <Input
                      placeholder="e.g., Room 101, Lab A"
                      {...registerTimetable("room_number")}
                    />
                  </div>
                  <div>
                    <Label htmlFor="week_pattern">Week Pattern</Label>
                    <Select 
                      defaultValue="all"
                      onValueChange={(value) => setTimetableValue("week_pattern", value as any)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {WEEK_PATTERNS.map((pattern) => (
                          <SelectItem key={pattern.value} value={pattern.value}>
                            {pattern.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="is_double_period"
                      onCheckedChange={(checked) => setTimetableValue("is_double_period", checked as boolean)}
                    />
                    <Label htmlFor="is_double_period">Double Period</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="is_practical"
                      checked={watchIsPractical}
                      onCheckedChange={(checked) => setTimetableValue("is_practical", checked as boolean)}
                    />
                    <Label htmlFor="is_practical">Practical Class</Label>
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsTimetableDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createTimetableMutation.isPending}>
                    {createTimetableMutation.isPending ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Create Entry
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Term and View Controls */}
      <Card>
        <CardHeader>
          <CardTitle>View Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div>
              <Label>Academic Term</Label>
              <Select 
                value={selectedTerm.toString()}
                onValueChange={(value) => setSelectedTerm(parseInt(value))}
              >
                <SelectTrigger className="w-48">
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
              <Label>View Type</Label>
              <Select value={selectedView} onValueChange={(value) => setSelectedView(value as any)}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">Weekly Timetable</SelectItem>
                  <SelectItem value="teacher">Teacher View</SelectItem>
                  <SelectItem value="room">Room View</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs defaultValue="timetable" className="space-y-6">
        <TabsList>
          <TabsTrigger value="timetable">Timetable</TabsTrigger>
          <TabsTrigger value="periods">Periods</TabsTrigger>
        </TabsList>
        
        <TabsContent value="timetable" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calendar className="mr-2 h-5 w-5" />
                {formatTerm(selectedTerm)} Timetable
              </CardTitle>
              <CardDescription>
                Weekly class schedule for the selected term
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedView === 'week' && renderWeeklyTimetable()}
              {selectedView === 'teacher' && (
                <div className="text-center py-8">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Teacher View</h3>
                  <p className="text-muted-foreground">
                    Teacher-specific timetable view coming soon
                  </p>
                </div>
              )}
              {selectedView === 'room' && (
                <div className="text-center py-8">
                  <MapPin className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Room View</h3>
                  <p className="text-muted-foreground">
                    Room utilization view coming soon
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="periods" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Clock className="mr-2 h-5 w-5" />
                School Periods
              </CardTitle>
              <CardDescription>
                Manage time periods for the school day
              </CardDescription>
            </CardHeader>
            <CardContent>
              {periodsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex items-center space-x-4">
                      <Skeleton className="h-4 w-16" />
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                  ))}
                </div>
              ) : periods?.items?.length > 0 ? (
                renderPeriodsTable()
              ) : (
                <div className="text-center py-8">
                  <Clock className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No periods configured</h3>
                  <p className="text-muted-foreground mb-4">
                    Create your first school period to get started with timetabling
                  </p>
                  <Button onClick={() => setIsPeriodDialogOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Period
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}