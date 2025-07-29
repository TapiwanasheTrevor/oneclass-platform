/**
 * Subject Management Component Tests
 * Tests for CRUD operations on subjects
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import SubjectManagement from '../SubjectManagement'
import { academicApi } from '@/lib/academic-api'

// Mock the academic API
vi.mock('@/lib/academic-api', () => ({
  academicApi: {
    getSubjects: vi.fn(),
    createSubject: vi.fn(),
    updateSubject: vi.fn(),
    deleteSubject: vi.fn(),
  }
}))

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  }
}))

const mockSubjects = {
  items: [
    {
      id: 'subj-1',
      code: 'MATH101',
      name: 'Mathematics',
      description: 'Basic mathematics course',
      grade_levels: [10, 11, 12],
      is_core: true,
      is_practical: false,
      requires_lab: false,
      pass_mark: 50.0,
      max_mark: 100.0,
      credit_hours: 3,
      department: 'Mathematics',
      language_of_instruction: 'English',
      display_order: 1,
      is_active: true,
      created_at: '2024-01-15T08:00:00Z',
      updated_at: '2024-01-15T08:00:00Z'
    },
    {
      id: 'subj-2',
      code: 'ENG101',
      name: 'English Language',
      description: 'English language and literature',
      grade_levels: [10, 11, 12, 13],
      is_core: true,
      is_practical: false,
      requires_lab: false,
      pass_mark: 50.0,
      max_mark: 100.0,
      credit_hours: 4,
      department: 'Languages',
      language_of_instruction: 'English',
      display_order: 2,
      is_active: true,
      created_at: '2024-01-15T08:00:00Z',
      updated_at: '2024-01-15T08:00:00Z'
    },
    {
      id: 'subj-3',
      code: 'CHEM101',
      name: 'Chemistry',
      description: 'Basic chemistry with lab work',
      grade_levels: [11, 12, 13],
      is_core: false,
      is_practical: true,
      requires_lab: true,
      pass_mark: 50.0,
      max_mark: 100.0,
      credit_hours: 5,
      department: 'Sciences',
      language_of_instruction: 'English',
      display_order: 3,
      is_active: true,
      created_at: '2024-01-15T08:00:00Z',
      updated_at: '2024-01-15T08:00:00Z'
    }
  ],
  total_count: 3,
  page: 1,
  page_size: 20
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

describe('SubjectManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders subjects list successfully', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Subject Management')).toBeInTheDocument()
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
      expect(screen.getByText('English Language')).toBeInTheDocument()
      expect(screen.getByText('Chemistry')).toBeInTheDocument()
    })

    // Check subject details
    expect(screen.getByText('MATH101')).toBeInTheDocument()
    expect(screen.getByText('ENG101')).toBeInTheDocument()
    expect(screen.getByText('CHEM101')).toBeInTheDocument()

    // Check core/elective indicators
    expect(screen.getAllByText('Core').length).toBeGreaterThan(0)
    expect(screen.getByText('Elective')).toBeInTheDocument()

    // Check practical indicators
    expect(screen.getByText('Lab Required')).toBeInTheDocument()
  })

  it('handles loading state', () => {
    vi.mocked(academicApi.getSubjects).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithQueryClient(<SubjectManagement />)

    expect(screen.getByText('Loading subjects...')).toBeInTheDocument()
  })

  it('handles error state', async () => {
    vi.mocked(academicApi.getSubjects).mockRejectedValue(
      new Error('Failed to fetch subjects')
    )

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load subjects')).toBeInTheDocument()
    })
  })

  it('opens create subject dialog', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Subject Management')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /add subject/i })
    await userEvent.click(createButton)

    expect(screen.getByText('Create New Subject')).toBeInTheDocument()
    expect(screen.getByLabelText('Subject Code')).toBeInTheDocument()
    expect(screen.getByLabelText('Subject Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
  })

  it('creates new subject successfully', async () => {
    const newSubject = {
      id: 'subj-4',
      code: 'PHYS101',
      name: 'Physics',
      description: 'Basic physics course',
      grade_levels: [11, 12],
      is_core: false,
      is_practical: true,
      requires_lab: true,
      pass_mark: 50.0,
      max_mark: 100.0,
      credit_hours: 4,
      department: 'Sciences',
      language_of_instruction: 'English',
      display_order: 4,
      is_active: true,
      created_at: '2024-01-16T08:00:00Z',
      updated_at: '2024-01-16T08:00:00Z'
    }

    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.createSubject).mockResolvedValue(newSubject)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Subject Management')).toBeInTheDocument()
    })

    // Open create dialog
    const createButton = screen.getByRole('button', { name: /add subject/i })
    await userEvent.click(createButton)

    // Fill form
    await userEvent.type(screen.getByLabelText('Subject Code'), 'PHYS101')
    await userEvent.type(screen.getByLabelText('Subject Name'), 'Physics')
    await userEvent.type(screen.getByLabelText('Description'), 'Basic physics course')
    
    // Select grade levels (11, 12)
    const gradeLevelCheckboxes = screen.getAllByRole('checkbox')
    await userEvent.click(gradeLevelCheckboxes[10]) // Grade 11 (index 10)
    await userEvent.click(gradeLevelCheckboxes[11]) // Grade 12 (index 11)

    // Check practical and lab required
    await userEvent.click(screen.getByLabelText('Is Practical'))
    await userEvent.click(screen.getByLabelText('Requires Lab'))

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create subject/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.createSubject).toHaveBeenCalledWith({
        code: 'PHYS101',
        name: 'Physics',
        description: 'Basic physics course',
        grade_levels: [11, 12],
        is_core: false,
        is_practical: true,
        requires_lab: true,
        pass_mark: 50.0,
        max_mark: 100.0,
        credit_hours: 3,
        department: '',
        language_of_instruction: 'English',
        display_order: 1
      })
    })
  })

  it('edits existing subject', async () => {
    const updatedSubject = {
      ...mockSubjects.items[0],
      name: 'Advanced Mathematics',
      description: 'Advanced mathematics course'
    }

    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.updateSubject).mockResolvedValue(updatedSubject)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Find and click edit button for first subject
    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    await userEvent.click(editButtons[0])

    expect(screen.getByText('Edit Subject')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Mathematics')).toBeInTheDocument()

    // Update name
    const nameInput = screen.getByDisplayValue('Mathematics')
    await userEvent.clear(nameInput)
    await userEvent.type(nameInput, 'Advanced Mathematics')

    // Submit form
    const submitButton = screen.getByRole('button', { name: /update subject/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(academicApi.updateSubject).toHaveBeenCalledWith('subj-1', expect.objectContaining({
        name: 'Advanced Mathematics'
      }))
    })
  })

  it('deletes subject with confirmation', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)
    vi.mocked(academicApi.deleteSubject).mockResolvedValue(true)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Find and click delete button for first subject
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    await userEvent.click(deleteButtons[0])

    // Confirm deletion
    expect(screen.getByText('Delete Subject')).toBeInTheDocument()
    expect(screen.getByText('Are you sure you want to delete this subject?')).toBeInTheDocument()

    const confirmButton = screen.getByRole('button', { name: /confirm delete/i })
    await userEvent.click(confirmButton)

    await waitFor(() => {
      expect(academicApi.deleteSubject).toHaveBeenCalledWith('subj-1')
    })
  })

  it('filters subjects by grade level', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Filter by grade 11
    const gradeFilter = screen.getByRole('combobox', { name: /grade level/i })
    await userEvent.click(gradeFilter)
    await userEvent.click(screen.getByText('Grade 11'))

    await waitFor(() => {
      expect(academicApi.getSubjects).toHaveBeenCalledWith(expect.objectContaining({
        grade_level: 11
      }))
    })
  })

  it('filters subjects by department', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Filter by Mathematics department
    const deptFilter = screen.getByRole('combobox', { name: /department/i })
    await userEvent.click(deptFilter)
    await userEvent.click(screen.getByText('Mathematics'))

    await waitFor(() => {
      expect(academicApi.getSubjects).toHaveBeenCalledWith(expect.objectContaining({
        department: 'Mathematics'
      }))
    })
  })

  it('searches subjects by name', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Search for "math"
    const searchInput = screen.getByPlaceholderText(/search subjects/i)
    await userEvent.type(searchInput, 'math')

    await waitFor(() => {
      expect(academicApi.getSubjects).toHaveBeenCalledWith(expect.objectContaining({
        search: 'math'
      }))
    })
  })

  it('validates Zimbabwe grade levels (1-13)', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Subject Management')).toBeInTheDocument()
    })

    // Open create dialog
    const createButton = screen.getByRole('button', { name: /add subject/i })
    await userEvent.click(createButton)

    // Check that grade levels 1-13 are available
    const gradeLevelCheckboxes = screen.getAllByRole('checkbox')
    expect(gradeLevelCheckboxes.length).toBeGreaterThanOrEqual(13)

    // Check specific Zimbabwe grade levels
    expect(screen.getByText('Grade 1')).toBeInTheDocument()
    expect(screen.getByText('Grade 13')).toBeInTheDocument() // A-Level
  })

  it('handles core vs elective subject types', async () => {
    vi.mocked(academicApi.getSubjects).mockResolvedValue(mockSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument()
    })

    // Mathematics should be marked as Core
    expect(screen.getAllByText('Core').length).toBeGreaterThan(0)
    
    // Chemistry should be marked as Elective
    expect(screen.getByText('Elective')).toBeInTheDocument()
  })

  it('handles pagination', async () => {
    const paginatedSubjects = {
      ...mockSubjects,
      total_count: 25,
      page: 1,
      page_size: 20
    }

    vi.mocked(academicApi.getSubjects).mockResolvedValue(paginatedSubjects)

    renderWithQueryClient(<SubjectManagement />)

    await waitFor(() => {
      expect(screen.getByText('Showing 1 to 3 of 25 subjects')).toBeInTheDocument()
    })

    // Should have pagination controls
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument()
  })
})
