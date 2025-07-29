/**
 * Grade Book Component
 * Comprehensive grade management with Zimbabwe grading scale
 */

'use client'

import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { toast } from 'sonner'
import {
  Plus,
  Save,
  Edit,
  Eye,
  Download,
  BarChart3,
  Award,
  TrendingUp,
  Users,
  BookOpen,
  Calculator,
  FileText,
  AlertCircle
} from 'lucide-react'

import { 
  academicApi, 
  Assessment,
  AssessmentCreate,
  Grade,
  GradeCreate,
  BulkGradeCreate,
  GradingScale,
  AssessmentType,
  AssessmentCategory,
  TermNumber 
} from '@/lib/academic-api'
import { useAuth } from '@/hooks/useAuth'
import { formatDate, formatPercentage } from '@/lib/utils'

interface GradeBookProps {
  classId?: string
  subjectId?: string
  academicYearId: string
  className?: string
}

interface StudentGrade {
  student_id: string
  student_name: string
  raw_score?: number
  percentage_score?: number
  letter_grade?: GradingScale
  is_absent: boolean
  feedback?: string
}

export function GradeBook({ classId, subjectId, academicYearId, className }: GradeBookProps) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [selectedAssessment, setSelectedAssessment] = useState<Assessment | null>(null)
  const [isCreateAssessmentOpen, setIsCreateAssessmentOpen] = useState(false)
  const [isGradingOpen, setIsGradingOpen] = useState(false)
  const [studentGrades, setStudentGrades] = useState<StudentGrade[]>([])
  const [selectedTerm, setSelectedTerm] = useState<TermNumber>(TermNumber.TERM_1)

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

  // Mock assessments data
  const mockAssessments: Assessment[] = [
    {
      id: '1',
      school_id: user?.school_id || '',
      academic_year_id: academicYearId,
      name: 'Mid-Term Test',
      description: 'Mathematics mid-term assessment',
      subject_id: subjectId || '',
      class_id: classId || '',
      teacher_id: user?.id || '',
      term_number: TermNumber.TERM_1,
      assessment_type: AssessmentType.TEST,
      assessment_category: AssessmentCategory.CONTINUOUS,
      total_marks: 100,
      pass_mark: 50,
      weight_percentage: 25,
      assessment_date: '2024-03-15',
      duration_minutes: 90,
      instructions: 'Answer all questions',
      resources_allowed: [],
      is_group_assessment: false,
      status: 'published',
      results_published: false,
      is_active: true,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
      created_by: user?.id || '',
    },
    {
      id: '2',
      school_id: user?.school_id || '',
      academic_year_id: academicYearId,
      name: 'Assignment 1',
      description: 'Algebra problem set',
      subject_id: subjectId || '',
      class_id: classId || '',
      teacher_id: user?.id || '',
      term_number: TermNumber.TERM_1,
      assessment_type: AssessmentType.ASSIGNMENT,
      assessment_category: AssessmentCategory.CONTINUOUS,
      total_marks: 50,
      pass_mark: 25,
      weight_percentage: 15,
      assessment_date: '2024-02-20',
      due_date: '2024-02-27',
      instructions: 'Submit handwritten solutions',
      resources_allowed: ['Calculator', 'Formula sheet'],
      is_group_assessment: false,
      status: 'completed',
      results_published: true,
      is_active: true,
      created_at: '2024-02-01T00:00:00Z',
      updated_at: '2024-02-01T00:00:00Z',
      created_by: user?.id || '',
    }
  ]

  // Initialize student grades when assessment changes
  useEffect(() => {
    if (selectedAssessment) {
      setStudentGrades(mockStudents.map(student => ({
        student_id: student.id,
        student_name: student.name,
        is_absent: false
      })))
    }
  }, [selectedAssessment])

  // Create assessment mutation
  const createAssessmentMutation = useMutation({
    mutationFn: (data: AssessmentCreate) => academicApi.createAssessment(data),
    onSuccess: (assessment) => {
      queryClient.invalidateQueries({ queryKey: ['assessments'] })
      setIsCreateAssessmentOpen(false)
      toast.success('Assessment created successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create assessment')
    }
  })

  // Submit grades mutation
  const submitGradesMutation = useMutation({
    mutationFn: (data: BulkGradeCreate) => academicApi.submitBulkGrades(data.assessment_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grades'] })
      setIsGradingOpen(false)
      toast.success('Grades submitted successfully')
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to submit grades')
    }
  })

  const getZimbabweGrade = (percentage: number): GradingScale => {
    if (percentage >= 80) return GradingScale.A
    if (percentage >= 70) return GradingScale.B
    if (percentage >= 60) return GradingScale.C
    if (percentage >= 50) return GradingScale.D
    if (percentage >= 40) return GradingScale.E
    return GradingScale.U
  }

  const handleGradeChange = (studentId: string, field: string, value: any) => {
    setStudentGrades(prev => 
      prev.map(grade => {
        if (grade.student_id === studentId) {
          const updated = { ...grade, [field]: value }
          
          // Auto-calculate percentage and letter grade when raw score changes
          if (field === 'raw_score' && selectedAssessment && value !== undefined) {
            const percentage = (value / selectedAssessment.total_marks) * 100
            updated.percentage_score = Math.round(percentage * 100) / 100
            updated.letter_grade = getZimbabweGrade(percentage)
          }
          
          return updated
        }
        return grade
      })
    )
  }

  const handleSubmitGrades = () => {
    if (!selectedAssessment) return

    const gradeData: GradeCreate[] = studentGrades.map(grade => ({
      assessment_id: selectedAssessment.id,
      student_id: grade.student_id,
      raw_score: grade.raw_score,
      percentage_score: grade.percentage_score,
      letter_grade: grade.letter_grade,
      is_absent: grade.is_absent,
      feedback: grade.feedback
    }))

    submitGradesMutation.mutate({
      assessment_id: selectedAssessment.id,
      grades: gradeData
    })
  }

  const calculateClassStats = () => {
    const validGrades = studentGrades.filter(g => g.percentage_score !== undefined && !g.is_absent)
    if (validGrades.length === 0) {
      return {
        average: 0,
        highest: 0,
        lowest: 0,
        passRate: 0,
        distribution: { A: 0, B: 0, C: 0, D: 0, E: 0, U: 0 }
      }
    }

    const scores = validGrades.map(g => g.percentage_score!)
    const average = scores.reduce((sum, score) => sum + score, 0) / scores.length
    const highest = Math.max(...scores)
    const lowest = Math.min(...scores)
    const passCount = validGrades.filter(g => (g.percentage_score || 0) >= (selectedAssessment?.pass_mark || 50)).length
    const passRate = (passCount / validGrades.length) * 100

    const distribution = { A: 0, B: 0, C: 0, D: 0, E: 0, U: 0 }
    validGrades.forEach(grade => {
      if (grade.letter_grade) {
        distribution[grade.letter_grade]++
      }
    })

    return { average, highest, lowest, passRate, distribution }
  }

  const stats = calculateClassStats()

  const getGradeBadgeVariant = (grade: GradingScale) => {
    switch (grade) {
      case GradingScale.A: return 'default'
      case GradingScale.B: return 'secondary'
      case GradingScale.C: return 'outline'
      case GradingScale.D: return 'outline'
      case GradingScale.E: return 'destructive'
      case GradingScale.U: return 'destructive'
      default: return 'outline'
    }
  }

  const AssessmentForm = ({ onSubmit, isLoading }: { onSubmit: (data: AssessmentCreate) => void; isLoading: boolean }) => {
    const [formData, setFormData] = useState<AssessmentCreate>({
      academic_year_id: academicYearId,
      name: '',
      description: '',
      subject_id: subjectId || '',
      class_id: classId || '',
      teacher_id: user?.id || '',
      term_number: selectedTerm,
      assessment_type: AssessmentType.TEST,
      assessment_category: AssessmentCategory.CONTINUOUS,
      total_marks: 100,
      pass_mark: 50,
      weight_percentage: 25,
      assessment_date: new Date().toISOString().split('T')[0],
      instructions: '',
      resources_allowed: [],
      is_group_assessment: false
    })

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      onSubmit(formData)
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Assessment Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Mid-Term Test"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="assessment_type">Type *</Label>
            <Select 
              value={formData.assessment_type}
              onValueChange={(value) => setFormData(prev => ({ ...prev, assessment_type: value as AssessmentType }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={AssessmentType.TEST}>Test</SelectItem>
                <SelectItem value={AssessmentType.QUIZ}>Quiz</SelectItem>
                <SelectItem value={AssessmentType.ASSIGNMENT}>Assignment</SelectItem>
                <SelectItem value={AssessmentType.PROJECT}>Project</SelectItem>
                <SelectItem value={AssessmentType.PRACTICAL}>Practical</SelectItem>
                <SelectItem value={AssessmentType.EXAM}>Exam</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Brief description of the assessment"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="total_marks">Total Marks *</Label>
            <Input
              id="total_marks"
              type="number"
              value={formData.total_marks}
              onChange={(e) => setFormData(prev => ({ ...prev, total_marks: Number(e.target.value) }))}
              min={1}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="pass_mark">Pass Mark *</Label>
            <Input
              id="pass_mark"
              type="number"
              value={formData.pass_mark}
              onChange={(e) => setFormData(prev => ({ ...prev, pass_mark: Number(e.target.value) }))}
              min={0}
              max={formData.total_marks}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="weight_percentage">Weight % *</Label>
            <Input
              id="weight_percentage"
              type="number"
              value={formData.weight_percentage}
              onChange={(e) => setFormData(prev => ({ ...prev, weight_percentage: Number(e.target.value) }))}
              min={1}
              max={100}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="assessment_date">Assessment Date *</Label>
            <Input
              id="assessment_date"
              type="date"
              value={formData.assessment_date}
              onChange={(e) => setFormData(prev => ({ ...prev, assessment_date: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="term_number">Term *</Label>
            <Select 
              value={formData.term_number.toString()}
              onValueChange={(value) => setFormData(prev => ({ ...prev, term_number: Number(value) as TermNumber }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Term 1</SelectItem>
                <SelectItem value="2">Term 2</SelectItem>
                <SelectItem value="3">Term 3</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button type="submit" disabled={isLoading}>
            {isLoading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />}
            <Save className="h-4 w-4 mr-2" />
            Create Assessment
          </Button>
        </DialogFooter>
      </form>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Grade Book</h1>
          <p className="text-muted-foreground">
            Manage assessments and grades for {user?.school_name}
          </p>
        </div>
        <div className="flex items-center space-x-2">
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
          <Dialog open={isCreateAssessmentOpen} onOpenChange={setIsCreateAssessmentOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Assessment
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Assessment</DialogTitle>
                <DialogDescription>
                  Create a new assessment for grading
                </DialogDescription>
              </DialogHeader>
              <AssessmentForm
                onSubmit={(data) => createAssessmentMutation.mutate(data)}
                isLoading={createAssessmentMutation.isPending}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Stats */}
      {selectedAssessment && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Calculator className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-2xl font-bold">{stats.average.toFixed(1)}%</div>
                  <div className="text-xs text-muted-foreground">Class Average</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <div>
                  <div className="text-2xl font-bold text-green-600">{stats.highest}%</div>
                  <div className="text-xs text-muted-foreground">Highest Score</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Award className="h-4 w-4 text-blue-600" />
                <div>
                  <div className="text-2xl font-bold text-blue-600">{formatPercentage(stats.passRate)}</div>
                  <div className="text-xs text-muted-foreground">Pass Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="text-2xl font-bold">{studentGrades.length}</div>
                  <div className="text-xs text-muted-foreground">Total Students</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs defaultValue="assessments" className="space-y-4">
        <TabsList>
          <TabsTrigger value="assessments">Assessments</TabsTrigger>
          <TabsTrigger value="grading">Grade Entry</TabsTrigger>
          <TabsTrigger value="analytics">Grade Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="assessments">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BookOpen className="h-5 w-5 mr-2" />
                Assessments ({mockAssessments.length})
              </CardTitle>
              <CardDescription>
                Manage assessments for Term {selectedTerm}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Total Marks</TableHead>
                    <TableHead>Weight</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockAssessments
                    .filter(assessment => assessment.term_number === selectedTerm)
                    .map((assessment) => (
                    <TableRow key={assessment.id}>
                      <TableCell className="font-medium">{assessment.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {assessment.assessment_type}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(assessment.assessment_date)}</TableCell>
                      <TableCell>{assessment.total_marks}</TableCell>
                      <TableCell>{assessment.weight_percentage}%</TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            assessment.status === 'completed' ? 'default' : 
                            assessment.status === 'published' ? 'secondary' : 'outline'
                          }
                          className="capitalize"
                        >
                          {assessment.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedAssessment(assessment)
                              setIsGradingOpen(true)
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="grading">
          {selectedAssessment ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 mr-2" />
                    Grade Entry - {selectedAssessment.name}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">
                      Total: {selectedAssessment.total_marks} marks
                    </Badge>
                    <Badge variant="outline">
                      Pass: {selectedAssessment.pass_mark} marks
                    </Badge>
                  </div>
                </CardTitle>
                <CardDescription>
                  Enter grades for {selectedAssessment.assessment_type} on {formatDate(selectedAssessment.assessment_date)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student Name</TableHead>
                      <TableHead>Raw Score</TableHead>
                      <TableHead>Percentage</TableHead>
                      <TableHead>Letter Grade</TableHead>
                      <TableHead>Absent</TableHead>
                      <TableHead>Feedback</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {studentGrades.map((grade) => (
                      <TableRow key={grade.student_id}>
                        <TableCell className="font-medium">
                          {grade.student_name}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={grade.raw_score || ''}
                            onChange={(e) => handleGradeChange(
                              grade.student_id, 
                              'raw_score', 
                              e.target.value ? Number(e.target.value) : undefined
                            )}
                            min={0}
                            max={selectedAssessment.total_marks}
                            disabled={grade.is_absent}
                            className="w-20"
                            placeholder="0"
                          />
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {grade.percentage_score?.toFixed(1) || '-'}%
                          </div>
                        </TableCell>
                        <TableCell>
                          {grade.letter_grade && (
                            <Badge variant={getGradeBadgeVariant(grade.letter_grade)}>
                              {grade.letter_grade}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={grade.is_absent}
                            onChange={(e) => handleGradeChange(
                              grade.student_id, 
                              'is_absent', 
                              e.target.checked
                            )}
                            className="rounded"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            value={grade.feedback || ''}
                            onChange={(e) => handleGradeChange(
                              grade.student_id, 
                              'feedback', 
                              e.target.value
                            )}
                            placeholder="Optional feedback..."
                            className="w-40"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                
                <div className="flex items-center justify-between pt-6">
                  <div className="text-sm text-muted-foreground">
                    Class Average: {stats.average.toFixed(1)}% • Pass Rate: {formatPercentage(stats.passRate)}
                  </div>
                  <Button
                    onClick={handleSubmitGrades}
                    disabled={submitGradesMutation.isPending}
                    size="lg"
                  >
                    {submitGradesMutation.isPending && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    )}
                    <Save className="h-4 w-4 mr-2" />
                    Submit Grades
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8">
                <div className="text-center text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Select an assessment to start grading</p>
                  <p className="text-sm">Choose an assessment from the Assessments tab</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="analytics">
          {selectedAssessment ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Grade Distribution</CardTitle>
                  <CardDescription>
                    Distribution of letter grades for {selectedAssessment.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(stats.distribution).map(([grade, count]) => (
                      <div key={grade} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge variant={getGradeBadgeVariant(grade as GradingScale)}>
                            {grade}
                          </Badge>
                          <span className="text-sm">{count} students</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Progress 
                            value={studentGrades.length > 0 ? (count / studentGrades.length) * 100 : 0} 
                            className="w-20 h-2" 
                          />
                          <span className="text-sm text-muted-foreground w-10">
                            {studentGrades.length > 0 ? Math.round((count / studentGrades.length) * 100) : 0}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance Statistics</CardTitle>
                  <CardDescription>
                    Key metrics for {selectedAssessment.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Class Average:</span>
                      <span className="font-medium">{stats.average.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Highest Score:</span>
                      <span className="font-medium text-green-600">{stats.highest}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Lowest Score:</span>
                      <span className="font-medium text-red-600">{stats.lowest}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Pass Rate:</span>
                      <span className="font-medium">{formatPercentage(stats.passRate)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Students:</span>
                      <span className="font-medium">{studentGrades.length}</span>
                    </div>
                    <div className="pt-4 border-t">
                      <div className="text-sm text-muted-foreground space-y-1">
                        {stats.average >= 75 && <p>✓ Excellent class performance</p>}
                        {stats.passRate >= 80 && <p>✓ Good pass rate</p>}
                        {stats.passRate < 60 && <p>⚠ Low pass rate - consider review</p>}
                        {stats.average < 50 && <p>⚠ Below average performance</p>}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-8">
                <div className="text-center text-muted-foreground">
                  <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No analytics available</p>
                  <p className="text-sm">Select an assessment to view grade analytics</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default GradeBook