/**
 * Academic Dashboard Component Tests
 * Tests for the main academic management dashboard
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import AcademicDashboard from '../AcademicDashboard'
import { academicApi } from '@/lib/academic-api'

// Mock the academic API
vi.mock('@/lib/academic-api', () => ({
  academicApi: {
    getAcademicDashboard: vi.fn(),
    getTeacherDashboard: vi.fn(),
    getAssessmentCalendar: vi.fn(),
    getSubjects: vi.fn(),
    getClasses: vi.fn(),
  }
}))

// Mock the Chart component to avoid canvas rendering issues in tests
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
}))

const mockDashboardData = {
  school_id: 'school-123',
  academic_year_id: 'year-2024',
  total_subjects: 12,
  total_classes: 8,
  total_teachers: 15,
  total_students: 240,
  average_attendance_rate: 87.5,
  total_assessments: 45,
  completed_assessments: 32,
  pending_assessments: 13,
  recent_activities: [
    {
      id: '1',
      type: 'assessment',
      title: 'Mathematics Test Created',
      description: 'Grade 10 Mathematics test scheduled for next week',
      timestamp: new Date().toISOString(),
      user_name: 'Mr. Smith'
    },
    {
      id: '2', 
      type: 'attendance',
      title: 'Attendance Marked',
      description: 'Form 2A attendance recorded',
      timestamp: new Date().toISOString(),
      user_name: 'Mrs. Jones'
    }
  ],
  attendance_trends: [
    { week: 'Week 1', rate: 85 },
    { week: 'Week 2', rate: 88 },
    { week: 'Week 3', rate: 87 },
    { week: 'Week 4', rate: 90 }
  ],
  upcoming_assessments: [
    {
      id: 'assess-1',
      name: 'Mathematics Mid-Term',
      subject_name: 'Mathematics',
      class_name: 'Form 4A',
      assessment_date: '2024-04-15',
      total_marks: 100
    },
    {
      id: 'assess-2',
      name: 'English Essay',
      subject_name: 'English',
      class_name: 'Form 3B',
      assessment_date: '2024-04-18',
      total_marks: 50
    }
  ],
  generated_at: new Date().toISOString()
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

describe('AcademicDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard loading state', () => {
    vi.mocked(academicApi.getAcademicDashboard).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument()
  })

  it('renders dashboard with data successfully', async () => {
    vi.mocked(academicApi.getAcademicDashboard).mockResolvedValue(mockDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(screen.getByText('Academic Management')).toBeInTheDocument()
    })

    // Check metrics cards
    expect(screen.getByText('12')).toBeInTheDocument() // Total subjects
    expect(screen.getByText('8')).toBeInTheDocument() // Total classes
    expect(screen.getByText('15')).toBeInTheDocument() // Total teachers
    expect(screen.getByText('240')).toBeInTheDocument() // Total students
    expect(screen.getByText('87.5%')).toBeInTheDocument() // Attendance rate
    expect(screen.getByText('45')).toBeInTheDocument() // Total assessments

    // Check recent activities
    expect(screen.getByText('Mathematics Test Created')).toBeInTheDocument()
    expect(screen.getByText('Attendance Marked')).toBeInTheDocument()

    // Check upcoming assessments
    expect(screen.getByText('Mathematics Mid-Term')).toBeInTheDocument()
    expect(screen.getByText('English Essay')).toBeInTheDocument()
  })

  it('handles API error gracefully', async () => {
    vi.mocked(academicApi.getAcademicDashboard).mockRejectedValue(
      new Error('Failed to fetch dashboard data')
    )

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard')).toBeInTheDocument()
    })
  })

  it('auto-refreshes data every 30 seconds', async () => {
    const mockGetDashboard = vi.mocked(academicApi.getAcademicDashboard)
    mockGetDashboard.mockResolvedValue(mockDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(1)
    })

    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000)

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(2)
    })
  })

  it('displays attendance trends chart', async () => {
    vi.mocked(academicApi.getAcademicDashboard).mockResolvedValue(mockDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    })
  })

  it('filters dashboard by academic year', async () => {
    const mockGetDashboard = vi.mocked(academicApi.getAcademicDashboard)
    mockGetDashboard.mockResolvedValue(mockDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledWith('year-2024')
    })
  })

  it('handles teacher dashboard mode', async () => {
    const mockTeacherData = {
      teacher_id: 'teacher-123',
      school_id: 'school-123',
      academic_year_id: 'year-2024',
      total_classes: 3,
      total_subjects: 2,
      total_students: 75,
      my_attendance_rate: 92.0,
      pending_assessments: 5,
      recent_activities: [],
      upcoming_assessments: [],
      generated_at: new Date().toISOString()
    }

    vi.mocked(academicApi.getTeacherDashboard).mockResolvedValue(mockTeacherData)

    renderWithQueryClient(
      <AcademicDashboard 
        academicYearId="year-2024" 
        teacherId="teacher-123"
        mode="teacher"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('My Classes')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // Teacher's classes
      expect(screen.getByText('75')).toBeInTheDocument() // Teacher's students
    })
  })

  it('handles empty data gracefully', async () => {
    const emptyDashboardData = {
      ...mockDashboardData,
      total_subjects: 0,
      total_classes: 0,
      total_teachers: 0,
      total_students: 0,
      recent_activities: [],
      upcoming_assessments: []
    }

    vi.mocked(academicApi.getAcademicDashboard).mockResolvedValue(emptyDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument() // Should show zeros
      expect(screen.getByText('No recent activities')).toBeInTheDocument()
      expect(screen.getByText('No upcoming assessments')).toBeInTheDocument()
    })
  })

  it('displays proper Zimbabwe grading context', async () => {
    vi.mocked(academicApi.getAcademicDashboard).mockResolvedValue(mockDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      // Should show Zimbabwe-specific terminology
      expect(screen.getByText('Form')).toBeInTheDocument() // Zimbabwe term for grade levels
    })
  })

  it('refreshes data on manual refresh', async () => {
    const mockGetDashboard = vi.mocked(academicApi.getAcademicDashboard)
    mockGetDashboard.mockResolvedValue(mockDashboardData)

    renderWithQueryClient(
      <AcademicDashboard academicYearId="year-2024" />
    )

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(1)
    })

    // Find and click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    await userEvent.click(refreshButton)

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(2)
    })
  })
})
