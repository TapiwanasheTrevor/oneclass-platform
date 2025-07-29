/**
 * Timetable Management Component Tests
 * Tests for visual timetable grid and period management
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import TimetableManagement from '../TimetableManagement'
import { academicApi } from '@/lib/academic-api'

// Mock the academic API
vi.mock('@/lib/academic-api', () => ({
  academicApi: {
    getPeriods: vi.fn(),
    createPeriod: vi.fn(),
    updatePeriod: vi.fn(),
    deletePeriod: vi.fn(),
    getTimetables: vi.fn(),
    createTimetableEntry: vi.fn(),
    updateTimetableEntry: vi.fn(),
    deleteTimetableEntry: vi.fn(),
    getSubjects: vi.fn(),
    getTeachers: vi.fn(),
  }
}))

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  }
}))

const mockPeriods = {
  items: [
    {
      id: 'period-1',
      period_number: 1,
      name: 'Period 1',
      start_time: '08:00:00',
      end_time: '08:40:00',
      is_break: false,
      is_active: true
    },
    {
      id: 'period-2',
      period_number: 2,
      name: 'Period 2',
      start_time: '08:45:00',
      end_time: '09:25:00',
      is_break: false,
      is_active: true
    },
    {
      id: 'period-break',
      period_number: 3,
      name: 'Break',
      start_time: '09:25:00',
      end_time: '09:40:00',
      is_break: true,
      is_active: true
    },
    {
      id: 'period-3',
      period_number: 4,
      name: 'Period 3',
      start_time: '09:40:00',
      end_time: '10:20:00',
      is_break: false,
      is_active: true
    }
  ],
  total_count: 4
}

const mockTimetables = {
  items: [
    {
      id: 'timetable-1',
      academic_year_id: 'year-2024',
      term_number: 1,
      class_id: 'class-1',
      subject_id: 'subject-1',
      teacher_id: 'teacher-1',
      period_id: 'period-1',
      day_of_week: 1, // Monday
      room_number: 'Room 101',
      is_double_period: false,
      is_practical: false,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      subject_name: 'Mathematics',
      teacher_name: 'Mr. Smith',
      class_name: 'Form 4A'
    },
    {
      id: 'timetable-2',
      academic_year_id: 'year-2024',
      term_number: 1,
      class_id: 'class-1',
      subject_id: 'subject-2',
      teacher_id: 'teacher-2',
      period_id: 'period-2',
      day_of_week: 1, // Monday
      room_number: 'Room 102',
      is_double_period: false,
      is_practical: false,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      subject_name: 'English',
      teacher_name: 'Mrs. Jones',
      class_name: 'Form 4A'
    },
    {
      id: 'timetable-3',
      academic_year_id: 'year-2024',
      term_number: 1,
      class_id: 'class-1',
      subject_id: 'subject-3',
      teacher_id: 'teacher-3',
      period_id: 'period-3',
      day_of_week: 2, // Tuesday
      room_number: 'Lab 1',
      is_double_period: false,
      is_practical: true,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      subject_name: 'Chemistry',
      teacher_name: 'Dr. Brown',
      class_name: 'Form 4A'
    }
  ],
  total_count: 3
}

const mockSubjects = {
  items: [
    {
      id: 'subject-1',
      code: 'MATH',
      name: 'Mathematics'
    },
    {
      id: 'subject-2',
      code: 'ENG',
      name: 'English'
    },
    {
      id: 'subject-3',
      code: 'CHEM',
      name: 'Chemistry'
    }
  ]
}

const mockTeachers = {
  items: [
    {
      id: 'teacher-1',
      first_name: 'John',
      last_name: 'Smith',
      subject_specializations: ['Mathematics']
    },
    {
      id: 'teacher-2',
      first_name: 'Mary',
      last_name: 'Jones',
      subject_specializations: ['English']
    },
    {
      id: 'teacher-3',
      first_name: 'David',
      last_name: 'Brown',
      subject_specializations: ['Chemistry']
    }
  ]
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

describe('TimetableManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders timetable management with periods and grid', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Timetable Management')).toBeInTheDocument()
      
      // Check periods are displayed
      expect(screen.getByText('Period 1')).toBeInTheDocument()
      expect(screen.getByText('Period 2')).toBeInTheDocument()
      expect(screen.getByText('Break')).toBeInTheDocument()
      expect(screen.getByText('Period 3')).toBeInTheDocument()
      
      // Check time slots
      expect(screen.getByText('08:00 - 08:40')).toBeInTheDocument()
      expect(screen.getByText('08:45 - 09:25')).toBeInTheDocument()
      expect(screen.getByText('09:25 - 09:40')).toBeInTheDocument()
      expect(screen.getByText('09:40 - 10:20')).toBeInTheDocument()
    })

    // Check timetable grid shows days of week
    expect(screen.getByText('Monday')).toBeInTheDocument()
    expect(screen.getByText('Tuesday')).toBeInTheDocument()
    expect(screen.getByText('Wednesday')).toBeInTheDocument()
    expect(screen.getByText('Thursday')).toBeInTheDocument()
    expect(screen.getByText('Friday')).toBeInTheDocument()
  })

  it('displays timetable entries in correct grid positions', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      // Check subjects are displayed in correct positions
      expect(screen.getByText('Mathematics')).toBeInTheDocument() // Monday Period 1
      expect(screen.getByText('English')).toBeInTheDocument() // Monday Period 2
      expect(screen.getByText('Chemistry')).toBeInTheDocument() // Tuesday Period 3
      
      // Check teacher names
      expect(screen.getByText('Mr. Smith')).toBeInTheDocument()
      expect(screen.getByText('Mrs. Jones')).toBeInTheDocument()
      expect(screen.getByText('Dr. Brown')).toBeInTheDocument()
      
      // Check room numbers
      expect(screen.getByText('Room 101')).toBeInTheDocument()
      expect(screen.getByText('Room 102')).toBeInTheDocument()
      expect(screen.getByText('Lab 1')).toBeInTheDocument()
    })
  })

  it('creates new period successfully', async () => {
    const newPeriod = {
      id: 'period-4',
      period_number: 5,
      name: 'Period 4',
      start_time: '10:25:00',
      end_time: '11:05:00',
      is_break: false,
      is_active: true
    }

    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)
    vi.mocked(academicApi.createPeriod).mockResolvedValue(newPeriod)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Timetable Management')).toBeInTheDocument()
    })

    // Click "Add Period" button
    const addPeriodButton = screen.getByRole('button', { name: /add period/i })
    await userEvent.click(addPeriodButton)

    expect(screen.getByText('Create New Period')).toBeInTheDocument()

    // Fill period form
    await userEvent.type(screen.getByLabelText('Period Name'), 'Period 4')
    await userEvent.type(screen.getByLabelText('Start Time'), '10:25')
    await userEvent.type(screen.getByLabelText('End Time'), '11:05')

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create period/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.createPeriod).toHaveBeenCalledWith({
        period_number: expect.any(Number),
        name: 'Period 4',
        start_time: '10:25',
        end_time: '11:05',
        is_break: false
      })
    })
  })

  it('creates new timetable entry by clicking empty slot', async () => {
    const newTimetableEntry = {
      id: 'timetable-4',
      academic_year_id: 'year-2024',
      term_number: 1,
      class_id: 'class-1',
      subject_id: 'subject-1',
      teacher_id: 'teacher-1',
      period_id: 'period-1',
      day_of_week: 3, // Wednesday
      room_number: 'Room 103',
      is_double_period: false,
      is_practical: false,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      subject_name: 'Mathematics',
      teacher_name: 'Mr. Smith',
      class_name: 'Form 4A'
    }

    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)
    vi.mocked(academicApi.createTimetableEntry).mockResolvedValue(newTimetableEntry)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Timetable Management')).toBeInTheDocument()
    })

    // Find and click an empty slot (Wednesday, Period 1)
    const emptySlots = screen.getAllByTestId('empty-slot')
    await userEvent.click(emptySlots[0])

    expect(screen.getByText('Add Timetable Entry')).toBeInTheDocument()

    // Fill timetable entry form
    const subjectSelect = screen.getByRole('combobox', { name: /subject/i })
    await userEvent.click(subjectSelect)
    await userEvent.click(screen.getByText('Mathematics'))

    const teacherSelect = screen.getByRole('combobox', { name: /teacher/i })
    await userEvent.click(teacherSelect)
    await userEvent.click(screen.getByText('Mr. Smith'))

    await userEvent.type(screen.getByLabelText('Room Number'), 'Room 103')

    // Submit form
    const submitButton = screen.getByRole('button', { name: /add entry/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.createTimetableEntry).toHaveBeenCalledWith({
        academic_year_id: 'year-2024',
        term_number: 1,
        class_id: 'class-1',
        subject_id: 'subject-1',
        teacher_id: 'teacher-1',
        period_id: expect.any(String),
        day_of_week: expect.any(Number),
        room_number: 'Room 103',
        is_double_period: false,
        is_practical: false,
        week_pattern: 'all',
        effective_from: expect.any(String)
      })
    })
  })

  it('edits existing timetable entry', async () => {
    const updatedTimetableEntry = {
      ...mockTimetables.items[0],
      room_number: 'Room 105',
      teacher_id: 'teacher-2',
      teacher_name: 'Mrs. Jones'
    }

    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)
    vi.mocked(academicApi.updateTimetableEntry).mockResolvedValue(updatedTimetableEntry)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Click on existing timetable entry (Mathematics)
    const mathEntry = screen.getByText('Mathematics').closest('[data-testid="timetable-entry"]')
    await userEvent.click(mathEntry!)

    expect(screen.getByText('Edit Timetable Entry')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Room 101')).toBeInTheDocument()

    // Change room number
    const roomInput = screen.getByDisplayValue('Room 101')
    await userEvent.clear(roomInput)
    await userEvent.type(roomInput, 'Room 105')

    // Change teacher
    const teacherSelect = screen.getByRole('combobox', { name: /teacher/i })
    await userEvent.click(teacherSelect)
    await userEvent.click(screen.getByText('Mrs. Jones'))

    // Submit changes
    const submitButton = screen.getByRole('button', { name: /update entry/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.updateTimetableEntry).toHaveBeenCalledWith('timetable-1', {
        room_number: 'Room 105',
        teacher_id: 'teacher-2'
      })
    })
  })

  it('deletes timetable entry with confirmation', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)
    vi.mocked(academicApi.deleteTimetableEntry).mockResolvedValue(true)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Right-click on timetable entry to show context menu
    const mathEntry = screen.getByText('Mathematics').closest('[data-testid="timetable-entry"]')
    await userEvent.pointer({
      target: mathEntry!,
      keys: '[MouseRight]'
    })

    // Click delete option
    const deleteOption = screen.getByText('Delete Entry')
    await userEvent.click(deleteOption)

    // Confirm deletion
    expect(screen.getByText('Delete Timetable Entry')).toBeInTheDocument()
    const confirmButton = screen.getByRole('button', { name: /confirm delete/i })
    await userEvent.click(confirmButton)

    await waitFor(() => {
      expect(academicApi.deleteTimetableEntry).toHaveBeenCalledWith('timetable-1')
    })
  })

  it('handles period conflicts when creating entries', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)
    vi.mocked(academicApi.createTimetableEntry).mockRejectedValue(
      new Error('Teacher conflict: Mr. Smith is already scheduled for this period')
    )

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Timetable Management')).toBeInTheDocument()
    })

    // Try to add entry with conflicting teacher
    const emptySlots = screen.getAllByTestId('empty-slot')
    await userEvent.click(emptySlots[0])

    // Fill form with conflicting teacher
    const subjectSelect = screen.getByRole('combobox', { name: /subject/i })
    await userEvent.click(subjectSelect)
    await userEvent.click(screen.getByText('Mathematics'))

    const teacherSelect = screen.getByRole('combobox', { name: /teacher/i })
    await userEvent.click(teacherSelect)
    await userEvent.click(screen.getByText('Mr. Smith')) // Already scheduled

    await userEvent.type(screen.getByLabelText('Room Number'), 'Room 103')

    const submitButton = screen.getByRole('button', { name: /add entry/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Teacher conflict: Mr. Smith is already scheduled for this period')).toBeInTheDocument()
    })
  })

  it('supports double periods', async () => {
    const doublePeriodEntry = {
      id: 'timetable-double',
      academic_year_id: 'year-2024',
      term_number: 1,
      class_id: 'class-1',
      subject_id: 'subject-3',
      teacher_id: 'teacher-3',
      period_id: 'period-1',
      day_of_week: 4, // Thursday
      room_number: 'Lab 1',
      is_double_period: true,
      is_practical: true,
      week_pattern: 'all',
      effective_from: '2024-01-15',
      subject_name: 'Chemistry',
      teacher_name: 'Dr. Brown',
      class_name: 'Form 4A'
    }

    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue({
      ...mockTimetables,
      items: [...mockTimetables.items, doublePeriodEntry]
    })
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      // Double period should span two time slots
      const doublePeriodElements = screen.getAllByText('Chemistry')
      expect(doublePeriodElements.length).toBeGreaterThan(1)
      
      // Should show double period indicator
      expect(screen.getByText('Double Period')).toBeInTheDocument()
      expect(screen.getByText('Practical')).toBeInTheDocument()
    })
  })

  it('handles break periods correctly', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      // Break period should be clearly marked
      expect(screen.getByText('Break')).toBeInTheDocument()
      
      // Break slots should not be clickable for timetable entries
      const breakSlots = screen.getAllByTestId('break-slot')
      expect(breakSlots.length).toBeGreaterThan(0)
    })

    // Try to click on break slot - should not open entry dialog
    const breakSlots = screen.getAllByTestId('break-slot')
    await userEvent.click(breakSlots[0])

    // Should not show timetable entry dialog
    expect(screen.queryByText('Add Timetable Entry')).not.toBeInTheDocument()
  })

  it('filters timetable by week pattern', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Timetable Management')).toBeInTheDocument()
    })

    // Filter by week pattern
    const weekFilter = screen.getByRole('combobox', { name: /week pattern/i })
    await userEvent.click(weekFilter)
    await userEvent.click(screen.getByText('All Weeks'))

    await waitFor(() => {
      expect(academicApi.getTimetables).toHaveBeenCalledWith(expect.objectContaining({
        week_pattern: 'all'
      }))
    })
  })

  it('exports timetable to PDF', async () => {
    vi.mocked(academicApi.getPeriods).mockResolvedValue(mockPeriods)
    vi.mocked(academicApi.getTimetables).mockResolvedValue(mockTimetables)
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.getTeachers).mockResolvedValue(mockTeachers)

    // Mock print functionality
    global.window.print = vi.fn()

    renderWithQueryClient(
      <TimetableManagement 
        classId="class-1" 
        academicYearId="year-2024"
        termNumber={1}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Timetable Management')).toBeInTheDocument()
    })

    // Click export button
    const exportButton = screen.getByRole('button', { name: /export timetable/i })
    await userEvent.click(exportButton)

    expect(global.window.print).toHaveBeenCalled()
  })
})
