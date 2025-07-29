/**
 * Attendance Tracker Component Tests
 * Tests for bulk attendance marking and tracking
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import AttendanceTracker from '../AttendanceTracker'
import { academicApi } from '@/lib/academic-api'

// Mock the academic API
vi.mock('@/lib/academic-api', () => ({
  academicApi: {
    getAttendanceSessions: vi.fn(),
    createAttendanceSession: vi.fn(),
    markBulkAttendance: vi.fn(),
    getAttendanceStats: vi.fn(),
  }
}))

// Mock integration API for student data
vi.mock('@/lib/integration-api', () => ({
  integrationApi: {
    getClassStudentsForAcademic: vi.fn(),
  }
}))

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

const mockAttendanceSessions = {
  items: [
    {
      id: 'session-1',
      timetable_id: 'timetable-1',
      session_date: '2024-03-15',
      session_type: 'regular',
      attendance_marked: true,
      created_at: '2024-03-15T08:00:00Z'
    },
    {
      id: 'session-2',
      timetable_id: 'timetable-1',
      session_date: '2024-03-16',
      session_type: 'regular',
      attendance_marked: false,
      created_at: '2024-03-16T08:00:00Z'
    }
  ],
  total_count: 2
}

const mockAttendanceStats = {
  total_students: 3,
  present_students: 2,
  absent_students: 1,
  late_students: 0,
  attendance_rate: 66.7
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

describe('AttendanceTracker', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders attendance tracker with student list', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Attendance Tracker')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument()
    })

    // Check student numbers
    expect(screen.getByText('STU001')).toBeInTheDocument()
    expect(screen.getByText('STU002')).toBeInTheDocument()
    expect(screen.getByText('STU003')).toBeInTheDocument()
  })

  it('displays attendance statistics', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument() // Total students
      expect(screen.getByText('2')).toBeInTheDocument() // Present students
      expect(screen.getByText('1')).toBeInTheDocument() // Absent students
      expect(screen.getByText('66.7%')).toBeInTheDocument() // Attendance rate
    })
  })

  it('creates new attendance session', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    const newSession = {
      id: 'session-3',
      timetable_id: 'timetable-1',
      session_date: '2024-03-17',
      session_type: 'regular',
      attendance_marked: false,
      created_at: '2024-03-17T08:00:00Z'
    }

    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)
    vi.mocked(academicApi.createAttendanceSession).mockResolvedValue(newSession)

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Attendance Tracker')).toBeInTheDocument()
    })

    // Click "Start New Session" button
    const startSessionButton = screen.getByRole('button', { name: /start new session/i })
    await userEvent.click(startSessionButton)

    expect(screen.getByText('Create Attendance Session')).toBeInTheDocument()

    // Fill in session details
    const dateInput = screen.getByLabelText('Session Date')
    await userEvent.clear(dateInput)
    await userEvent.type(dateInput, '2024-03-17')

    // Submit form
    const createButton = screen.getByRole('button', { name: /create session/i })
    await userEvent.click(createButton)

    await waitFor(() => {
      expect(academicApi.createAttendanceSession).toHaveBeenCalledWith({
        timetable_id: 'timetable-1',
        session_date: '2024-03-17',
        session_type: 'regular',
        notes: ''
      })
    })
  })

  it('marks bulk attendance with different statuses', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)
    vi.mocked(academicApi.markBulkAttendance).mockResolvedValue({
      total_processed: 3,
      successful: 3,
      failed: 0,
      created_ids: ['att-1', 'att-2', 'att-3']
    })

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Select active session (the one that's not marked)
    const sessionSelect = screen.getByRole('combobox', { name: /select session/i })
    await userEvent.click(sessionSelect)
    await userEvent.click(screen.getByText('2024-03-16'))

    await waitFor(() => {
      // Should show attendance marking interface
      expect(screen.getAllByText('Present').length).toBeGreaterThan(0)
    })

    // Mark first student as present
    const presentButtons = screen.getAllByRole('button', { name: /present/i })
    await userEvent.click(presentButtons[0])

    // Mark second student as late
    const lateButtons = screen.getAllByRole('button', { name: /late/i })
    await userEvent.click(lateButtons[1])

    // Mark third student as absent
    const absentButtons = screen.getAllByRole('button', { name: /absent/i })
    await userEvent.click(absentButtons[2])

    // Submit attendance
    const submitButton = screen.getByRole('button', { name: /submit attendance/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.markBulkAttendance).toHaveBeenCalledWith({
        attendance_session_id: 'session-2',
        attendance_records: expect.arrayContaining([
          expect.objectContaining({
            student_id: 'student-1',
            attendance_status: 'present'
          }),
          expect.objectContaining({
            student_id: 'student-2',
            attendance_status: 'late'
          }),
          expect.objectContaining({
            student_id: 'student-3',
            attendance_status: 'absent'
          })
        ])
      })
    })
  })

  it('handles quick attendance actions (mark all present/absent)', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)
    vi.mocked(academicApi.markBulkAttendance).mockResolvedValue({
      total_processed: 3,
      successful: 3,
      failed: 0,
      created_ids: ['att-1', 'att-2', 'att-3']
    })

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Select active session
    const sessionSelect = screen.getByRole('combobox', { name: /select session/i })
    await userEvent.click(sessionSelect)
    await userEvent.click(screen.getByText('2024-03-16'))

    await waitFor(() => {
      // Should show quick actions
      expect(screen.getByRole('button', { name: /mark all present/i })).toBeInTheDocument()
    })

    // Click "Mark All Present"
    const markAllPresentButton = screen.getByRole('button', { name: /mark all present/i })
    await userEvent.click(markAllPresentButton)

    // Submit attendance
    const submitButton = screen.getByRole('button', { name: /submit attendance/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.markBulkAttendance).toHaveBeenCalledWith({
        attendance_session_id: 'session-2',
        attendance_records: expect.arrayContaining([
          expect.objectContaining({ attendance_status: 'present' }),
          expect.objectContaining({ attendance_status: 'present' }),
          expect.objectContaining({ attendance_status: 'present' })
        ])
      })
    })
  })

  it('allows adding arrival time for late students', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)
    vi.mocked(academicApi.markBulkAttendance).mockResolvedValue({
      total_processed: 1,
      successful: 1,
      failed: 0,
      created_ids: ['att-1']
    })

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Select active session
    const sessionSelect = screen.getByRole('combobox', { name: /select session/i })
    await userEvent.click(sessionSelect)
    await userEvent.click(screen.getByText('2024-03-16'))

    await waitFor(() => {
      expect(screen.getAllByText('Late').length).toBeGreaterThan(0)
    })

    // Mark first student as late
    const lateButtons = screen.getAllByRole('button', { name: /late/i })
    await userEvent.click(lateButtons[0])

    // Should show arrival time input
    await waitFor(() => {
      expect(screen.getByLabelText('Arrival Time')).toBeInTheDocument()
    })

    // Enter arrival time
    const arrivalTimeInput = screen.getByLabelText('Arrival Time')
    await userEvent.type(arrivalTimeInput, '08:15')

    // Submit attendance
    const submitButton = screen.getByRole('button', { name: /submit attendance/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.markBulkAttendance).toHaveBeenCalledWith({
        attendance_session_id: 'session-2',
        attendance_records: expect.arrayContaining([
          expect.objectContaining({
            student_id: 'student-1',
            attendance_status: 'late',
            arrival_time: '08:15'
          })
        ])
      })
    })
  })

  it('allows adding excuse reason for absent students', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)
    vi.mocked(academicApi.markBulkAttendance).mockResolvedValue({
      total_processed: 1,
      successful: 1,
      failed: 0,
      created_ids: ['att-1']
    })

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Select active session
    const sessionSelect = screen.getByRole('combobox', { name: /select session/i })
    await userEvent.click(sessionSelect)
    await userEvent.click(screen.getByText('2024-03-16'))

    await waitFor(() => {
      expect(screen.getAllByText('Absent').length).toBeGreaterThan(0)
    })

    // Mark first student as absent
    const absentButtons = screen.getAllByRole('button', { name: /absent/i })
    await userEvent.click(absentButtons[0])

    // Should show excuse options
    await waitFor(() => {
      expect(screen.getByLabelText('Excused')).toBeInTheDocument()
    })

    // Mark as excused and add reason
    const excusedCheckbox = screen.getByLabelText('Excused')
    await userEvent.click(excusedCheckbox)

    const reasonInput = screen.getByLabelText('Excuse Reason')
    await userEvent.type(reasonInput, 'Sick')

    // Submit attendance
    const submitButton = screen.getByRole('button', { name: /submit attendance/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.markBulkAttendance).toHaveBeenCalledWith({
        attendance_session_id: 'session-2',
        attendance_records: expect.arrayContaining([
          expect.objectContaining({
            student_id: 'student-1',
            attendance_status: 'absent',
            is_excused: true,
            excuse_reason: 'Sick'
          })
        ])
      })
    })
  })

  it('handles loading and error states', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    
    // Test loading state
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    expect(screen.getByText('Loading students...')).toBeInTheDocument()

    // Test error state
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockRejectedValue(
      new Error('Failed to fetch students')
    )

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Failed to load students')).toBeInTheDocument()
    })
  })

  it('shows real-time attendance rate updates', async () => {
    const { integrationApi } = await import('@/lib/integration-api')
    vi.mocked(integrationApi.getClassStudentsForAcademic).mockResolvedValue(mockStudents)
    vi.mocked(academicApi.getAttendanceSessions).mockResolvedValue(mockAttendanceSessions)
    vi.mocked(academicApi.getAttendanceStats).mockResolvedValue(mockAttendanceStats)

    renderWithQueryClient(
      <AttendanceTracker 
        classId="class-1" 
        academicYearId="year-2024" 
        timetableId="timetable-1"
      />
    )

    await waitFor(() => {
      expect(screen.getByText('66.7%')).toBeInTheDocument() // Initial attendance rate
    })

    // Select active session and mark attendance
    const sessionSelect = screen.getByRole('combobox', { name: /select session/i })
    await userEvent.click(sessionSelect)
    await userEvent.click(screen.getByText('2024-03-16'))

    await waitFor(() => {
      // Should show live preview of attendance changes
      expect(screen.getByText('Preview:')).toBeInTheDocument()
    })

    // Mark students as present
    const presentButtons = screen.getAllByRole('button', { name: /present/i })
    await userEvent.click(presentButtons[0])
    await userEvent.click(presentButtons[1])

    // Should show updated preview rate
    await waitFor(() => {
      expect(screen.getByText(/100%/)).toBeInTheDocument() // All marked as present
    })
  })
})
