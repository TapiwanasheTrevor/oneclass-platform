/**
 * Subject Management Component
 * Comprehensive subject management with Zimbabwe-specific features
 */

'use client'

import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import {
  Plus,
  Search,
  Edit,
  Trash2,
  BookOpen,
  Filter,
  MoreHorizontal,
  AlertCircle,
  Save,
  X
} from 'lucide-react'

import { 
  useAcademicHooks,
  type Subject, 
  type SubjectCreate,
  zimbabweGradeLevels,
  formatGradeLevel
} from '@/lib/academic-api'
import { useAuth } from '@/hooks/useAuth'

interface SubjectManagementProps {
  className?: string
}

const GRADE_LEVELS = Array.from({ length: 13 }, (_, i) => i + 1)
const LANGUAGES = ['English', 'Shona', 'Ndebele']
const DEPARTMENTS = ['Mathematics', 'Sciences', 'Languages', 'Humanities', 'Arts', 'Sports', 'Technical']

export function SubjectManagement({ className }: SubjectManagementProps) {
  const { user } = useAuth()
  
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterGrade, setFilterGrade] = useState<string>('')
  const [filterDepartment, setFilterDepartment] = useState<string>('')
  const [filterCore, setFilterCore] = useState<string>('')

  const { 
    useSubjects, 
    useCreateSubject, 
    useUpdateSubject, 
    useDeleteSubject 
  } = useAcademicHooks()

  // Build filter params
  const filterParams = {
    ...(filterGrade && { grade_level: parseInt(filterGrade) }),
    ...(filterDepartment && { department: filterDepartment }),
    ...(filterCore !== "" && { is_core: filterCore === "true" }),
  }

  const { data: subjectsResponse, isLoading, error } = useSubjects(filterParams)
  const createSubjectMutation = useCreateSubject()
  const updateSubjectMutation = useUpdateSubject()
  const deleteSubjectMutation = useDeleteSubject()

  const handleEdit = (subject: Subject) => {
    setEditingSubject(subject)
    setIsEditDialogOpen(true)
  }

  const handleDelete = async (subject: Subject) => {
    if (window.confirm(`Are you sure you want to delete ${subject.name}?`)) {
      deleteSubjectMutation.mutate(subject.id)
    }
  }

  const handleCreateSubject = async (data: SubjectCreate) => {
    await createSubjectMutation.mutateAsync(data)
    setIsCreateDialogOpen(false)
  }

  const handleUpdateSubject = async (data: SubjectCreate) => {
    if (!editingSubject) return
    await updateSubjectMutation.mutateAsync({ id: editingSubject.id, data })
    setIsEditDialogOpen(false)
    setEditingSubject(null)
  }

  // Filter subjects based on search term
  const filteredSubjects = subjectsResponse?.items?.filter((subject: Subject) => 
    subject.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    subject.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    subject.department?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const SubjectForm = ({ 
    subject, 
    onSubmit, 
    isLoading: submitting 
  }: {
    subject?: Subject
    onSubmit: (data: SubjectCreate) => void
    isLoading: boolean
  }) => {
    const [formData, setFormData] = useState<SubjectCreate>({
      code: subject?.code || '',
      name: subject?.name || '',
      description: subject?.description || '',
      grade_levels: subject?.grade_levels || [],
      is_core: subject?.is_core || false,
      is_practical: subject?.is_practical || false,
      requires_lab: subject?.requires_lab || false,
      pass_mark: subject?.pass_mark || 50,
      max_mark: subject?.max_mark || 100,
      credit_hours: subject?.credit_hours || 1,
      department: subject?.department || '',
      language_of_instruction: subject?.language_of_instruction || 'English',
      display_order: subject?.display_order || 0
    })

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      onSubmit(formData)
    }

    const handleGradeLevelChange = (gradeLevel: number, checked: boolean) => {
      if (checked) {
        setFormData(prev => ({
          ...prev,
          grade_levels: [...prev.grade_levels, gradeLevel].sort((a, b) => a - b)
        }))
      } else {
        setFormData(prev => ({
          ...prev,
          grade_levels: prev.grade_levels.filter(level => level !== gradeLevel)
        }))
      }
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="code">Subject Code *</Label>
            <Input
              id="code"
              value={formData.code}
              onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
              placeholder="e.g., MATH, ENG, SCI"
              maxLength={10}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="name">Subject Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Mathematics"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Brief description of the subject"
          />
        </div>

        <div className="space-y-2">
          <Label>Grade Levels *</Label>
          <div className="space-y-4">
            {/* Primary School */}
            <div>
              <h4 className="font-medium text-sm mb-2">Primary School (Grades 1-7)</h4>
              <div className="grid grid-cols-4 gap-2">
                {zimbabweGradeLevels.filter(g => g.category === 'Primary').map((grade) => (
                  <div key={grade.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`grade-${grade.value}`}
                      checked={formData.grade_levels.includes(grade.value)}
                      onCheckedChange={(checked) => handleGradeLevelChange(grade.value, checked as boolean)}
                    />
                    <Label htmlFor={`grade-${grade.value}`} className="text-sm">
                      {grade.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Secondary School */}
            <div>
              <h4 className="font-medium text-sm mb-2">Secondary School (Forms 1-6)</h4>
              <div className="grid grid-cols-3 gap-2">
                {zimbabweGradeLevels.filter(g => g.category === 'Secondary').map((grade) => (
                  <div key={grade.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`grade-${grade.value}`}
                      checked={formData.grade_levels.includes(grade.value)}
                      onCheckedChange={(checked) => handleGradeLevelChange(grade.value, checked as boolean)}
                    />
                    <Label htmlFor={`grade-${grade.value}`} className="text-sm">
                      {grade.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="department">Department</Label>
            <Select 
              value={formData.department}
              onValueChange={(value) => setFormData(prev => ({ ...prev, department: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select department" />
              </SelectTrigger>
              <SelectContent>
                {DEPARTMENTS.map(dept => (
                  <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="language">Language of Instruction</Label>
            <Select 
              value={formData.language_of_instruction}
              onValueChange={(value) => setFormData(prev => ({ ...prev, language_of_instruction: value }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map(lang => (
                  <SelectItem key={lang} value={lang}>{lang}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="pass_mark">Pass Mark</Label>
            <Input
              id="pass_mark"
              type="number"
              value={formData.pass_mark}
              onChange={(e) => setFormData(prev => ({ ...prev, pass_mark: Number(e.target.value) }))}
              min={0}
              max={100}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_mark">Maximum Mark</Label>
            <Input
              id="max_mark"
              type="number"
              value={formData.max_mark}
              onChange={(e) => setFormData(prev => ({ ...prev, max_mark: Number(e.target.value) }))}
              min={1}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="credit_hours">Credit Hours</Label>
            <Input
              id="credit_hours"
              type="number"
              value={formData.credit_hours}
              onChange={(e) => setFormData(prev => ({ ...prev, credit_hours: Number(e.target.value) }))}
              min={1}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_core"
              checked={formData.is_core}
              onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_core: checked as boolean }))}
            />
            <Label htmlFor="is_core">Core Subject</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_practical"
              checked={formData.is_practical}
              onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_practical: checked as boolean }))}
            />
            <Label htmlFor="is_practical">Practical Subject</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="requires_lab"
              checked={formData.requires_lab}
              onCheckedChange={(checked) => setFormData(prev => ({ ...prev, requires_lab: checked as boolean }))}
            />
            <Label htmlFor="requires_lab">Requires Laboratory</Label>
          </div>
        </div>

        <DialogFooter>
          <Button type="submit" disabled={submitting || formData.grade_levels.length === 0}>
            {submitting && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />}
            <Save className="h-4 w-4 mr-2" />
            {subject ? 'Update Subject' : 'Create Subject'}
          </Button>
        </DialogFooter>
      </form>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load subjects. Please try again.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Subject Management</h1>
          <p className="text-muted-foreground">
            Manage academic subjects for {user?.school_name}
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Subject
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Subject</DialogTitle>
              <DialogDescription>
                Add a new subject to the academic curriculum
              </DialogDescription>
            </DialogHeader>
            <SubjectForm
              onSubmit={handleCreateSubject}
              isLoading={createSubjectMutation.isPending}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search subjects..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Grade Level</Label>
              <Select value={filterGrade} onValueChange={setFilterGrade}>
                <SelectTrigger>
                  <SelectValue placeholder="All grades" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All grades</SelectItem>
                  {zimbabweGradeLevels.map(grade => (
                    <SelectItem key={grade.value} value={grade.value.toString()}>
                      {grade.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Department</Label>
              <Select value={filterDepartment} onValueChange={setFilterDepartment}>
                <SelectTrigger>
                  <SelectValue placeholder="All departments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All departments</SelectItem>
                  {DEPARTMENTS.map(dept => (
                    <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={filterCore} onValueChange={setFilterCore}>
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All types</SelectItem>
                  <SelectItem value="true">Core subjects</SelectItem>
                  <SelectItem value="false">Elective subjects</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subjects Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BookOpen className="h-5 w-5 mr-2" />
            Subjects ({filteredSubjects.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-20" />
                </div>
              ))}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Grade Levels</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Language</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSubjects.map((subject) => (
                    <TableRow key={subject.id}>
                      <TableCell className="font-medium">{subject.code}</TableCell>
                      <TableCell>{subject.name}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {subject.grade_levels.slice(0, 3).map(level => (
                            <Badge key={level} variant="outline" className="text-xs">
                              {formatGradeLevel(level)}
                            </Badge>
                          ))}
                          {subject.grade_levels.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{subject.grade_levels.length - 3}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{subject.department || '-'}</TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {subject.is_core && (
                            <Badge variant="default" className="text-xs">Core</Badge>
                          )}
                          {subject.is_practical && (
                            <Badge variant="secondary" className="text-xs">Practical</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{subject.language_of_instruction}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(subject)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(subject)}
                            disabled={deleteSubjectMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {filteredSubjects.length === 0 && !isLoading && (
                <div className="text-center py-8">
                  <BookOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No subjects found</h3>
                  <p className="text-muted-foreground mb-4">
                    {searchTerm || filterGrade || filterDepartment || filterCore
                      ? "Try adjusting your filters or search term."
                      : "Get started by creating your first subject."
                    }
                  </p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Subject</DialogTitle>
            <DialogDescription>
              Update subject information
            </DialogDescription>
          </DialogHeader>
          {editingSubject && (
            <SubjectForm
              subject={editingSubject}
              onSubmit={handleUpdateSubject}
              isLoading={updateSubjectMutation.isPending}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default SubjectManagement