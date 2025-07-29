/**
 * Timetable Management Component
 * Comprehensive timetable scheduling with conflict detection
 */

'use client'

import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import {
  Plus,
  Clock,
  Calendar,
  Users,
  BookOpen,
  MapPin,
  AlertTriangle,
  Save,
  Edit,
  Trash2,
  Copy,
  Download,
  RefreshCw
} from 'lucide-react'

import { 
  academicApi, 
  Period,
  PeriodCreate,
  Timetable,
  TimetableCreate,
  TimetableWithDetails,
  TermNumber 
} from '@/lib/academic-api'
import { useAuth } from '@/hooks/useAuth'
import { formatTime } from '@/lib/utils'

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

export function TimetableManagement({ academicYearId, className }: TimetableManagementProps) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [selectedTerm, setSelectedTerm] = useState<TermNumber>(TermNumber.TERM_1)
  const [selectedClass, setSelectedClass] = useState<string>('')
  const [isCreatePeriodOpen, setIsCreatePeriodOpen] = useState(false)
  const [isCreateTimetableOpen, setIsCreateTimetableOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'week' | 'teacher' | 'room'>('week')

  // Mock data - in real app, this would come from APIs
  const mockPeriods: Period[] = [
    {
      id: '1',
      school_id: user?.school_id || '',
      period_number: 1,
      name: 'Period 1',
      start_time: '08:00',
      end_time: '08:40',
      is_break: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '2',
      school_id: user?.school_id || '',
      period_number: 2,
      name: 'Period 2',
      start_time: '08:40',
      end_time: '09:20',
      is_break: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '3',
      school_id: user?.school_id || '',
      period_number: 3,
      name: 'Tea Break',
      start_time: '09:20',
      end_time: '09:40',
      is_break: true,
      break_type: 'tea',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '4',
      school_id: user?.school_id || '',
      period_number: 4,
      name: 'Period 3',
      start_time: '09:40',
      end_time: '10:20',
      is_break: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '5',
      school_id: user?.school_id || '',
      period_number: 5,
      name: 'Period 4',
      start_time: '10:20',
      end_time: '11:00',
      is_break: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '6',
      school_id: user?.school_id || '',
      period_number: 6,
      name: 'Lunch Break',
      start_time: '11:00',
      end_time: '12:00',
      is_break: true,
      break_type: 'lunch',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '7',
      school_id: user?.school_id || '',
      period_number: 7,
      name: 'Period 5',
      start_time: '12:00',
      end_time: '12:40',
      is_break: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    },
    {
      id: '8',
      school_id: user?.school_id || '',
      period_number: 8,
      name: 'Period 6',
      start_time: '12:40',
      end_time: '13:20',
      is_break: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || ''
    }
  ]

  const mockTimetableEntries: TimetableWithDetails[] = [
    {
      id: '1',
      school_id: user?.school_id || '',
      academic_year_id: academicYearId,
      term_number: 1,
      class_id: 'class1',
      subject_id: 'math',
      teacher_id: 'teacher1',
      period_id: '1',
      day_of_week: 1,
      room_number: 'Room 101',
      is_double_period: false,
      is_practical: false,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || '',
      subject_name: 'Mathematics',
      teacher_name: 'Mr. Mukamuri',
      period_name: 'Period 1',
      class_name: 'Form 4A',
      start_time: '08:00',
      end_time: '08:40'
    },
    {
      id: '2',
      school_id: user?.school_id || '',
      academic_year_id: academicYearId,
      term_number: 1,
      class_id: 'class1',
      subject_id: 'english',
      teacher_id: 'teacher2',
      period_id: '2',
      day_of_week: 1,
      room_number: 'Room 102',
      is_double_period: false,
      is_practical: false,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: user?.id || '',
      subject_name: 'English',
      teacher_name: 'Mrs. Chigumba',
      period_name: 'Period 2',
      class_name: 'Form 4A',
      start_time: '08:40',
      end_time: '09:20'
    }
  ]

  const mockClasses = [
    { id: 'class1', name: 'Form 4A', grade_level: 11 },
    { id: 'class2', name: 'Form 4B', grade_level: 11 },
    { id: 'class3', name: 'Form 5A', grade_level: 12 }
  ]

  const mockSubjects = [
    { id: 'math', name: 'Mathematics', code: 'MATH' },
    { id: 'english', name: 'English', code: 'ENG' },
    { id: 'science', name: 'Science', code: 'SCI' },
    { id: 'history', name: 'History', code: 'HIST' }
  ]

  const mockTeachers = [
    { id: 'teacher1', name: 'Mr. Mukamuri', subjects: ['math'] },
    { id: 'teacher2', name: 'Mrs. Chigumba', subjects: ['english'] },
    { id: 'teacher3', name: 'Dr. Moyo', subjects: ['science'] }
  ]

  // Create period mutation
  const createPeriodMutation = useMutation({
    mutationFn: (data: PeriodCreate) => academicApi.createPeriod(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] })
      setIsCreatePeriodOpen(false)
      toast.success('Period created successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create period')
    }
  })

  // Create timetable entry mutation
  const createTimetableMutation = useMutation({
    mutationFn: (data: TimetableCreate) => academicApi.createTimetableEntry(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable'] })
      setIsCreateTimetableOpen(false)
      toast.success('Timetable entry created successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create timetable entry')
    }
  })

  const getFilteredTimetableEntries = () => {
    return mockTimetableEntries.filter(entry => 
      entry.term_number === selectedTerm &&
      (!selectedClass || entry.class_id === selectedClass)
    )
  }

  const getTimetableGrid = () => {
    const entries = getFilteredTimetableEntries()
    const grid: { [key: string]: TimetableWithDetails | null } = {}
    
    DAYS_OF_WEEK.forEach(day => {
      mockPeriods.filter(p => !p.is_break).forEach(period => {
        const key = `${day.value}-${period.id}`
        const entry = entries.find(e => e.day_of_week === day.value && e.period_id === period.id)
        grid[key] = entry || null
      })
    })
    
    return grid
  }

  const PeriodForm = ({ onSubmit, isLoading }: { onSubmit: (data: PeriodCreate) => void; isLoading: boolean }) => {
    const [formData, setFormData] = useState<PeriodCreate>({
      period_number: mockPeriods.length + 1,
      name: '',
      start_time: '',
      end_time: '',
      is_break: false
    })

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      onSubmit(formData)
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="period_number">Period Number *</Label>
            <Input
              id="period_number"
              type="number"
              value={formData.period_number}
              onChange={(e) => setFormData(prev => ({ ...prev, period_number: Number(e.target.value) }))}
              min={1}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="name">Period Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Period 1, Tea Break"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start_time">Start Time *</Label>
            <Input
              id="start_time"
              type="time"
              value={formData.start_time}
              onChange={(e) => setFormData(prev => ({ ...prev, start_time: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end_time">End Time *</Label>
            <Input
              id="end_time"
              type="time"
              value={formData.end_time}
              onChange={(e) => setFormData(prev => ({ ...prev, end_time: e.target.value }))}
              required
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="is_break"
            checked={formData.is_break}
            onChange={(e) => setFormData(prev => ({ ...prev, is_break: e.target.checked }))}
            className="rounded"
          />
          <Label htmlFor="is_break">This is a break period</Label>
        </div>

        {formData.is_break && (
          <div className="space-y-2">
            <Label htmlFor="break_type">Break Type</Label>
            <Select 
              value={formData.break_type || ''}
              onValueChange={(value) => setFormData(prev => ({ ...prev, break_type: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select break type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="tea">Tea Break</SelectItem>
                <SelectItem value="lunch">Lunch Break</SelectItem>
                <SelectItem value="assembly">Assembly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}

        <DialogFooter>
          <Button type="submit" disabled={isLoading}>
            {isLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />}
            <Save className="h-4 w-4 mr-2" />
            Create Period
          </Button>
        </DialogFooter>
      </form>
    )
  }

  const TimetableForm = ({ onSubmit, isLoading }: { onSubmit: (data: TimetableCreate) => void; isLoading: boolean }) => {
    const [formData, setFormData] = useState<TimetableCreate>({
      academic_year_id: academicYearId,
      term_number: selectedTerm,
      class_id: '',
      subject_id: '',
      teacher_id: '',
      period_id: '',
      day_of_week: 1,
      room_number: '',
      is_double_period: false,
      is_practical: false,
      week_pattern: 'all',
      effective_from: new Date().toISOString().split('T')[0]
    })

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      onSubmit(formData)
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="class_id">Class *</Label>
            <Select 
              value={formData.class_id}
              onValueChange={(value) => setFormData(prev => ({ ...prev, class_id: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select class" />
              </SelectTrigger>
              <SelectContent>
                {mockClasses.map(cls => (
                  <SelectItem key={cls.id} value={cls.id}>{cls.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="subject_id">Subject *</Label>
            <Select 
              value={formData.subject_id}
              onValueChange={(value) => setFormData(prev => ({ ...prev, subject_id: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select subject" />
              </SelectTrigger>
              <SelectContent>
                {mockSubjects.map(subject => (
                  <SelectItem key={subject.id} value={subject.id}>{subject.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="teacher_id">Teacher *</Label>
            <Select 
              value={formData.teacher_id}
              onValueChange={(value) => setFormData(prev => ({ ...prev, teacher_id: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select teacher" />
              </SelectTrigger>
              <SelectContent>
                {mockTeachers.map(teacher => (
                  <SelectItem key={teacher.id} value={teacher.id}>{teacher.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="room_number">Room</Label>
            <Input
              id="room_number"
              value={formData.room_number}
              onChange={(e) => setFormData(prev => ({ ...prev, room_number: e.target.value }))}
              placeholder="e.g., Room 101, Lab A"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="day_of_week">Day *</Label>
            <Select 
              value={formData.day_of_week.toString()}
              onValueChange={(value) => setFormData(prev => ({ ...prev, day_of_week: Number(value) }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DAYS_OF_WEEK.map(day => (
                  <SelectItem key={day.value} value={day.value.toString()}>{day.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="period_id">Period *</Label>
            <Select 
              value={formData.period_id}
              onValueChange={(value) => setFormData(prev => ({ ...prev, period_id: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select period" />
              </SelectTrigger>
              <SelectContent>
                {mockPeriods.filter(p => !p.is_break).map(period => (
                  <SelectItem key={period.id} value={period.id}>
                    {period.name} ({formatTime(period.start_time)} - {formatTime(period.end_time)})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="week_pattern">Week Pattern</Label>
            <Select 
              value={formData.week_pattern}
              onValueChange={(value) => setFormData(prev => ({ ...prev, week_pattern: value }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {WEEK_PATTERNS.map(pattern => (
                  <SelectItem key={pattern.value} value={pattern.value}>{pattern.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_double_period"
              checked={formData.is_double_period}
              onChange={(e) => setFormData(prev => ({ ...prev, is_double_period: e.target.checked }))}
              className="rounded"
            />
            <Label htmlFor="is_double_period">Double Period</Label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_practical"
              checked={formData.is_practical}
              onChange={(e) => setFormData(prev => ({ ...prev, is_practical: e.target.checked }))}
              className="rounded"
            />
            <Label htmlFor="is_practical">Practical Session</Label>
          </div>
        </div>

        <DialogFooter>
          <Button type="submit" disabled={isLoading}>
            {isLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />}
            <Save className="h-4 w-4 mr-2" />
            Add to Timetable
          </Button>
        </DialogFooter>
      </form>
    )
  }

  const renderTimetableGrid = () => {
    const grid = getTimetableGrid()
    const teachingPeriods = mockPeriods.filter(p => !p.is_break)

    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr>
              <th className="border border-gray-300 p-2 bg-gray-50 w-24">Time</th>
              {DAYS_OF_WEEK.map(day => (
                <th key={day.value} className="border border-gray-300 p-2 bg-gray-50 min-w-32">
                  {day.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {teachingPeriods.map(period => (
              <tr key={period.id}>
                <td className="border border-gray-300 p-2 bg-gray-50 text-sm">
                  <div className="font-medium">{period.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatTime(period.start_time)} - {formatTime(period.end_time)}
                  </div>
                </td>
                {DAYS_OF_WEEK.map(day => {
                  const entry = grid[`${day.value}-${period.id}`]
                  return (
                    <td key={`${day.value}-${period.id}`} className="border border-gray-300 p-1 h-20 relative">
                      {entry ? (
                        <div className="bg-blue-50 border border-blue-200 rounded p-2 h-full">
                          <div className="text-xs font-medium text-blue-900 truncate">
                            {entry.subject_name}
                          </div>
                          <div className="text-xs text-blue-700 truncate">
                            {entry.teacher_name}
                          </div>
                          {entry.room_number && (
                            <div className="text-xs text-blue-600 truncate">
                              {entry.room_number}
                            </div>
                          )}
                          {entry.is_practical && (
                            <Badge variant="outline" className="text-xs mt-1">
                              Practical
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <div className="h-full flex items-center justify-center text-gray-400">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsCreateTimetableOpen(true)}
                            className="text-xs"
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Timetable Management</h1>
          <p className="text-muted-foreground">
            Manage class schedules and periods for {user?.school_name}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Dialog open={isCreatePeriodOpen} onOpenChange={setIsCreatePeriodOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Clock className="h-4 w-4 mr-2" />
                Add Period
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Period</DialogTitle>
                <DialogDescription>
                  Add a new period to the school timetable
                </DialogDescription>
              </DialogHeader>
              <PeriodForm
                onSubmit={(data) => createPeriodMutation.mutate(data)}
                isLoading={createPeriodMutation.isPending}
              />
            </DialogContent>
          </Dialog>
          
          <Dialog open={isCreateTimetableOpen} onOpenChange={setIsCreateTimetableOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Class
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Timetable Entry</DialogTitle>
                <DialogDescription>
                  Schedule a class for a specific period and day
                </DialogDescription>
              </DialogHeader>
              <TimetableForm
                onSubmit={(data) => createTimetableMutation.mutate(data)}
                isLoading={createTimetableMutation.isPending}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <div className="space-y-1">
              <Label className="text-sm">Term</Label>
              <Select value={selectedTerm.toString()} onValueChange={(value) => setSelectedTerm(Number(value) as TermNumber)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Term 1</SelectItem>
                  <SelectItem value="2">Term 2</SelectItem>
                  <SelectItem value="3">Term 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-1">
              <Label className="text-sm">Class</Label>
              <Select value={selectedClass} onValueChange={setSelectedClass}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="All classes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All classes</SelectItem>
                  {mockClasses.map(cls => (
                    <SelectItem key={cls.id} value={cls.id}>{cls.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-1">
              <Label className="text-sm">View</Label>
              <Select value={viewMode} onValueChange={(value) => setViewMode(value as 'week' | 'teacher' | 'room')}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">Weekly</SelectItem>
                  <SelectItem value="teacher">By Teacher</SelectItem>
                  <SelectItem value="room">By Room</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Button variant="outline" className="mt-5">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs defaultValue="timetable" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timetable">Timetable</TabsTrigger>
          <TabsTrigger value="periods">Periods</TabsTrigger>
          <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
        </TabsList>

        <TabsContent value="timetable">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2" />
                  Weekly Timetable - Term {selectedTerm}
                </div>
                <div className="flex items-center space-x-2">
                  {selectedClass && (
                    <Badge variant="outline">
                      {mockClasses.find(c => c.id === selectedClass)?.name}
                    </Badge>
                  )}
                  <Button variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {renderTimetableGrid()}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="periods">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Clock className="h-5 w-5 mr-2" />
                School Periods
              </CardTitle>
              <CardDescription>
                Manage daily periods and break times
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockPeriods.map((period) => (
                  <div key={period.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="text-lg font-medium">
                        {period.period_number}
                      </div>
                      <div>
                        <div className="font-medium">{period.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatTime(period.start_time)} - {formatTime(period.end_time)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {period.is_break && (
                        <Badge variant="secondary" className="capitalize">
                          {period.break_type || 'Break'}
                        </Badge>
                      )}
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conflicts">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertTriangle className="h-5 w-5 mr-2" />
                Schedule Conflicts
              </CardTitle>
              <CardDescription>
                Identify and resolve timetable conflicts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No conflicts detected</p>
                <p className="text-sm">All timetable entries are properly scheduled</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default TimetableManagement