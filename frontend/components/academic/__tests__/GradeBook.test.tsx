/**
 * Grade Book Component Tests
 * Tests for assessment creation and grade management
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import GradeBook from '../GradeBook'
import { academicApi } from '@/lib/academic-api'

// Mock the academic API
vi.mock('@/lib/academic-api', () => ({
  academicApi: {
    getAssessments: vi.fn(),
    createAssessment: vi.fn(),
    getGrades: vi.fn(),
    submitBulkGrades: vi.fn(),
  }
}))

// Mock integration API for student data
vi.mock('@/lib/integration-api', () => ({
  integrationApi: {
    getClassStudentsForAcademic: vi.fn(),
  }
)))

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  }
}))

const mockStudents = [
  {
    id: 'student-1',
    student_number: 'STU001',
    first_name: 'John',
    last_name: 'Doe',
    grade_level: 10
  },
  {
    id: 'student-2',
    student_number: 'STU002',
    first_name: 'Jane',
    last_name: 'Smith',
    grade_level: 10
  },
  {
    id: 'student-3',
    student_number: 'STU003',
    first_name: 'Bob',
    last_name: 'Johnson',
    grade_level: 10
  }
]

const mockAssessments = {
  items: [
    {
      id: 'assess-1',
      name: 'Mid-Term Mathematics Test',
      description: 'Comprehensive mathematics assessment',
      subject_id: 'subject-1',
      class_id: 'class-1',
      teacher_id: 'teacher-1',
      term_number: 1,
      assessment_type: 'test',
      assessment_category: 'continuous',
      total_marks: 100.0,
      pass_mark: 50.0,
      weight_percentage: 25.0,
      assessment_date: '2024-03-15',
      duration_minutes: 90,
      is_published: false,
      created_at: '2024-03-10T08:00:00Z'
    },
    {
      id: 'assess-2',
      name: 'English Essay Assignment',
      description: 'Creative writing assignment',
      subject_id: 'subject-2',
      class_id: 'class-1',
      teacher_id: 'teacher-1',
      term_number: 1,
      assessment_type: 'assignment',
      assessment_category: 'continuous',
      total_marks: 50.0,
      pass_mark: 25.0,
      weight_percentage: 15.0,
      assessment_date: '2024-03-20',
      duration_minutes: null,
      is_published: true,
      created_at: '2024-03-12T08:00:00Z'
    }
  ],
  total_count: 2
}

const mockGrades = {
  items: [
    {
      id: 'grade-1',
      assessment_id: 'assess-1',
      student_id: 'student-1',
      raw_score: 85.0,
      percentage_score: 85.0,
      letter_grade: 'A',
      is_absent: false,
      feedback: 'Excellent work',
      created_at: '2024-03-16T08:00:00Z'
    },
    {
      id: 'grade-2',
      assessment_id: 'assess-1',
      student_id: 'student-2',
      raw_score: 72.0,
      percentage_score: 72.0,
      letter_grade: 'B',
      is_absent: false,
      feedback: 'Good effort',
      created_at: '2024-03-16T08:00:00Z'
    },
    {
      id: 'grade-3',
      assessment_id: 'assess-1',
      student_id: 'student-3',
      raw_score: null,
      percentage_score: null,
      letter_grade: null,
      is_absent: true,
      is_excused: true,
      feedback: null,
      created_at: '2024-03-16T08:00:00Z'
    }
  ],
  total_count: 3
}

const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
}

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('GradeBook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders grade book with assessments list', async () => {
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Grade Book')).toBeInTheDocument()
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
      expect(screen.getByText('English Essay Assignment')).toBeInTheDocument()
    })

    // Check assessment details
    expect(screen.getByText('100 marks')).toBeInTheDocument()
    expect(screen.getByText('50 marks')).toBeInTheDocument()
    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('Assignment')).toBeInTheDocument()
  })

  it('creates new assessment successfully', async () => {
    const newAssessment = {
      id: 'assess-3',
      name: 'Physics Lab Report',
      description: 'Laboratory experiment report',
      subject_id: 'subject-3',
      class_id: 'class-1',
      teacher_id: 'teacher-1',
      term_number: 1,
      assessment_type: 'practical',
      assessment_category: 'continuous',
      total_marks: 75.0,
      pass_mark: 37.5,
      weight_percentage: 20.0,
      assessment_date: '2024-03-25',
      duration_minutes: 120,
      is_published: false,
      created_at: '2024-03-20T08:00:00Z'
    }

    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.createAssessment).mockResolvedValue(newAssessment)

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Grade Book')).toBeInTheDocument()
    })

    // Click create assessment button
    const createButton = screen.getByRole('button', { name: /create assessment/i })
    await userEvent.click(createButton)

    expect(screen.getByText('Create New Assessment')).toBeInTheDocument()

    // Fill assessment form
    await userEvent.type(screen.getByLabelText('Assessment Name'), 'Physics Lab Report')
    await userEvent.type(screen.getByLabelText('Description'), 'Laboratory experiment report')
    
    // Select assessment type
    const typeSelect = screen.getByRole('combobox', { name: /assessment type/i })
    await userEvent.click(typeSelect)
    await userEvent.click(screen.getByText('Practical'))

    // Set marks
    await userEvent.type(screen.getByLabelText('Total Marks'), '75')
    await userEvent.type(screen.getByLabelText('Pass Mark'), '37.5')
    await userEvent.type(screen.getByLabelText('Weight Percentage'), '20')

    // Set date
    await userEvent.type(screen.getByLabelText('Assessment Date'), '2024-03-25')

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create assessment/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.createAssessment).toHaveBeenCalledWith({
        name: 'Physics Lab Report',
        description: 'Laboratory experiment report',
        subject_id: 'subject-1',
        class_id: 'class-1',
        teacher_id: 'teacher-1',
        term_number: 1,
        assessment_type: 'practical',
        assessment_category: 'continuous',
        total_marks: 75.0,
        pass_mark: 37.5,
        weight_percentage: 20.0,
        assessment_date: '2024-03-25',
        duration_minutes: 120,
        instructions: '',
        resources_allowed: [],
        is_group_assessment: false
      })
    })
  })

  it('displays and edits grades for an assessment', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.getGrades).mockResolvedValue(mockGrades)

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
    })

    // Click "View Grades" button for first assessment
    const viewGradesButtons = screen.getAllByRole('button', { name: /view grades/i })
    await userEvent.click(viewGradesButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Grades: Mid-Term Mathematics Test')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument()
    })

    // Check existing grades
    expect(screen.getByDisplayValue('85')).toBeInTheDocument() // John's score
    expect(screen.getByDisplayValue('72')).toBeInTheDocument() // Jane's score
    expect(screen.getByText('Absent')).toBeInTheDocument() // Bob is absent

    // Check letter grades (Zimbabwe A-U system)
    expect(screen.getByText('A')).toBeInTheDocument() // John's grade
    expect(screen.getByText('B')).toBeInTheDocument() // Jane's grade
  })

  it('submits bulk grades successfully', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.getGrades).mockResolvedValue({ items: [], total_count: 0 }) // No existing grades
    vi.mocked(academicApi.submitBulkGrades).mockResolvedValue({
      total_processed: 3,
      successful: 3,
      failed: 0,
      created_ids: ['grade-1', 'grade-2', 'grade-3']
    })

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
    })

    // Click "View Grades" button
    const viewGradesButtons = screen.getAllByRole('button', { name: /view grades/i })
    await userEvent.click(viewGradesButtons[0])

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Enter grades for students
    const scoreInputs = screen.getAllByLabelText(/score/i)
    await userEvent.type(scoreInputs[0], '88') // John
    await userEvent.type(scoreInputs[1], '76') // Jane
    
    // Mark third student as absent
    const absentCheckboxes = screen.getAllByLabelText(/absent/i)
    await userEvent.click(absentCheckboxes[2]) // Bob

    // Add feedback
    const feedbackInputs = screen.getAllByLabelText(/feedback/i)
    await userEvent.type(feedbackInputs[0], 'Great improvement')
    await userEvent.type(feedbackInputs[1], 'Keep it up')

    // Submit grades
    const submitButton = screen.getByRole('button', { name: /submit grades/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.submitBulkGrades).toHaveBeenCalledWith({
        assessment_id: 'assess-1',
        grades: [
          {
            student_id: 'student-1',
            raw_score: 88.0,
            is_absent: false,
            feedback: 'Great improvement'
          },
          {
            student_id: 'student-2',
            raw_score: 76.0,
            is_absent: false,
            feedback: 'Keep it up'
          },
          {
            student_id: 'student-3',
            is_absent: true,
            is_excused: false
          }
        ]
      })
    })
  })

  it('displays Zimbabwe grading scale (A-U)', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.getGrades).mockResolvedValue(mockGrades)

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
    })

    // View grades to see grading scale
    const viewGradesButtons = screen.getAllByRole('button', { name: /view grades/i })
    await userEvent.click(viewGradesButtons[0])

    await waitFor(() => {
      // Should show Zimbabwe grading scale reference
      expect(screen.getByText('Grading Scale:')).toBeInTheDocument()
      expect(screen.getByText('A: 80-100%')).toBeInTheDocument()
      expect(screen.getByText('B: 70-79%')).toBeInTheDocument()
      expect(screen.getByText('C: 60-69%')).toBeInTheDocument()
      expect(screen.getByText('D: 50-59%')).toBeInTheDocument()
      expect(screen.getByText('E: 40-49%')).toBeInTheDocument()
      expect(screen.getByText('U: 0-39%')).toBeInTheDocument()
    })
  })

  it('handles grade validation and auto-calculation', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.getGrades).mockResolvedValue({ items: [], total_count: 0 })

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
    })

    // View grades
    const viewGradesButtons = screen.getAllByRole('button', { name: /view grades/i })
    await userEvent.click(viewGradesButtons[0])

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Enter a score that should auto-calculate letter grade
    const scoreInputs = screen.getAllByLabelText(/score/i)
    await userEvent.type(scoreInputs[0], '85')

    // Should automatically show letter grade 'A'
    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
    })

    // Test invalid score (over total marks)
    await userEvent.clear(scoreInputs[0])
    await userEvent.type(scoreInputs[0], '150') // Over 100 total marks

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Score cannot exceed total marks (100)')).toBeInTheDocument()
    })
  })

  it('filters assessments by type and status', async () => {
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Grade Book')).toBeInTheDocument()
    })

    // Filter by assessment type
    const typeFilter = screen.getByRole('combobox', { name: /filter by type/i })
    await userEvent.click(typeFilter)
    await userEvent.click(screen.getByText('Test'))

    await waitFor(() => {
      expect(academicApi.getAssessments).toHaveBeenCalledWith(expect.objectContaining({
        assessment_type: 'test'
      }))
    })

    // Filter by published status
    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i })
    await userEvent.click(statusFilter)
    await userEvent.click(screen.getByText('Published'))

    await waitFor(() => {
      expect(academicApi.getAssessments).toHaveBeenCalledWith(expect.objectContaining({
        is_published: true
      }))
    })
  })

  it('exports grades to CSV', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.getGrades).mockResolvedValue(mockGrades)

    // Mock URL.createObjectURL
    global.URL.createObjectURL = vi.fn(() => 'mock-url')
    global.URL.revokeObjectURL = vi.fn()

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
    })

    // View grades
    const viewGradesButtons = screen.getAllByRole('button', { name: /view grades/i })
    await userEvent.click(viewGradesButtons[0])

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Click export button
    const exportButton = screen.getByRole('button', { name: /export to csv/i })
    await userEvent.click(exportButton)

    // Should trigger CSV download
    expect(global.URL.createObjectURL).toHaveBeenCalled()
  })

  it('handles assessment statistics and analytics', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAssessments).mockResolvedValue(mockAssessments)
    vi.mocked(academicApi.getGrades).mockResolvedValue(mockGrades)

    renderWithQueryClient(
      <GradeBook 
        classId="class-1" 
        subjectId="subject-1"
        academicYearId="year-2024"
        teacherId="teacher-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mid-Term Mathematics Test')).toBeInTheDocument()
    })

    // View grades to see statistics
    const viewGradesButtons = screen.getAllByRole('button', { name: /view grades/i })
    await userEvent.click(viewGradesButtons[0])

    await waitFor(() => {
      // Should show assessment statistics
      expect(screen.getByText('Class Average:')).toBeInTheDocument()
      expect(screen.getByText('78.5%')).toBeInTheDocument() // (85+72)/2
      expect(screen.getByText('Pass Rate:')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument() // Both above 50%
      expect(screen.getByText('Highest Score:')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()
    })
  })
})
