/**
 * Tests for InvoiceManagement component
 * Tests invoice CRUD operations, bulk generation, and filtering
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, beforeEach, describe, it, expect } from 'vitest'
import InvoiceManagement from '../InvoiceManagement'
import { financeApi } from '@/lib/finance-api'
import { useAuth } from '@/hooks/useAuth'
import { useSchoolContext } from '@/hooks/useSchoolContext'

// Mock the API
vi.mock('@/lib/finance-api', () => ({
  financeApi: {
    getInvoices: vi.fn(),
    getFeeStructures: vi.fn(),
    createInvoice: vi.fn(),
    bulkGenerateInvoices: vi.fn(),
    sendInvoice: vi.fn(),
  },
}))

// Mock hooks
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

vi.mock('@/hooks/useSchoolContext', () => ({
  useSchoolContext: vi.fn(),
}))

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div data-testid="card-content">{children}</div>,
  CardDescription: ({ children }: { children: React.ReactNode }) => <div data-testid="card-description">{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <div data-testid="card-title">{children}</div>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size }: { 
    children: React.ReactNode
    onClick?: () => void
    disabled?: boolean
    variant?: string
    size?: string
  }) => (
    <button 
      data-testid="button" 
      onClick={onClick} 
      disabled={disabled}
      data-variant={variant}
      data-size={size}
    >
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/input', () => ({
  Input: ({ placeholder, value, onChange, className }: { 
    placeholder?: string
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
    className?: string
  }) => (
    <input 
      data-testid="input"
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={className}
    />
  ),
}))

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: { children: React.ReactNode }) => <table data-testid="table">{children}</table>,
  TableBody: ({ children }: { children: React.ReactNode }) => <tbody data-testid="table-body">{children}</tbody>,
  TableCell: ({ children }: { children: React.ReactNode }) => <td data-testid="table-cell">{children}</td>,
  TableHead: ({ children }: { children: React.ReactNode }) => <th data-testid="table-head">{children}</th>,
  TableHeader: ({ children }: { children: React.ReactNode }) => <thead data-testid="table-header">{children}</thead>,
  TableRow: ({ children }: { children: React.ReactNode }) => <tr data-testid="table-row">{children}</tr>,
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ value, onValueChange, children }: { 
    value?: string
    onValueChange?: (value: string) => void
    children: React.ReactNode
  }) => (
    <select 
      data-testid="select"
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
    >
      {children}
    </select>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => <div data-testid="select-content">{children}</div>,
  SelectItem: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <option data-testid="select-item" value={value}>{children}</option>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="select-trigger">{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span data-testid="select-value">{placeholder}</span>,
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <span data-testid="badge" className={className}>{children}</span>
  ),
}))

vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({ checked, onCheckedChange }: { 
    checked?: boolean
    onCheckedChange?: (checked: boolean) => void
  }) => (
    <input 
      data-testid="checkbox"
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
    />
  ),
}))

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: { 
    children: React.ReactNode
    open?: boolean
    onOpenChange?: (open: boolean) => void
  }) => (
    <div data-testid="dialog" data-open={open}>
      {open && children}
    </div>
  ),
  DialogContent: ({ children }: { children: React.ReactNode }) => <div data-testid="dialog-content">{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div data-testid="dialog-header">{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <div data-testid="dialog-title">{children}</div>,
  DialogTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="dialog-trigger">{children}</div>,
}))

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-menu">{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <div data-testid="dropdown-item" onClick={onClick}>{children}</div>
  ),
  DropdownMenuLabel: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-label">{children}</div>,
  DropdownMenuSeparator: () => <div data-testid="dropdown-separator" />,
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-trigger">{children}</div>,
}))

vi.mock('@/components/ui/use-toast', () => ({
  toast: vi.fn(),
}))

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn((date, formatStr) => {
    if (typeof date === 'string') {
      return new Date(date).toLocaleDateString()
    }
    return date.toLocaleDateString()
  }),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Search: () => <span data-testid="search-icon">🔍</span>,
  Plus: () => <span data-testid="plus-icon">+</span>,
  MoreHorizontal: () => <span data-testid="more-icon">⋯</span>,
  Eye: () => <span data-testid="eye-icon">👁</span>,
  Edit: () => <span data-testid="edit-icon">✏️</span>,
  Send: () => <span data-testid="send-icon">📤</span>,
  Download: () => <span data-testid="download-icon">⬇️</span>,
  Filter: () => <span data-testid="filter-icon">🔽</span>,
  CalendarIcon: () => <span data-testid="calendar-icon">📅</span>,
  FileText: () => <span data-testid="file-text-icon">📄</span>,
  Clock: () => <span data-testid="clock-icon">⏰</span>,
  CheckCircle: () => <span data-testid="check-circle-icon">✅</span>,
  AlertCircle: () => <span data-testid="alert-circle-icon">⚠️</span>,
  DollarSign: () => <span data-testid="dollar-sign-icon">💲</span>,
  Users: () => <span data-testid="users-icon">👥</span>,
  Loader2: () => <span data-testid="loader-icon">⏳</span>,
}))

const mockInvoicesData = {
  invoices: [
    {
      id: 'invoice-1',
      invoice_number: 'INV-2025-001',
      student_name: 'John Smith',
      student_number: 'STU-001',
      grade_level: 'Form 1',
      due_date: '2025-08-15',
      total_amount: 500.00,
      paid_amount: 200.00,
      outstanding_amount: 300.00,
      payment_status: 'partial',
      status: 'sent',
      currency: 'USD',
      sent_to_parent: true,
      reminder_count: 1
    },
    {
      id: 'invoice-2',
      invoice_number: 'INV-2025-002',
      student_name: 'Jane Doe',
      student_number: 'STU-002',
      grade_level: 'Form 2',
      due_date: '2025-08-10',
      total_amount: 750.00,
      paid_amount: 0.00,
      outstanding_amount: 750.00,
      payment_status: 'overdue',
      status: 'sent',
      currency: 'USD',
      sent_to_parent: true,
      reminder_count: 2
    }
  ],
  total_count: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
  has_next: false,
  has_previous: false
}

const mockFeeStructures = [
  {
    id: 'fee-struct-1',
    name: 'Form 1 Fees 2025',
    description: 'Standard fees for Form 1',
    academic_year_id: 'ay-2025',
    grade_levels: [1],
    is_default: true,
    applicable_from: '2025-01-01',
    status: 'active',
    total_amount: 500.00
  },
  {
    id: 'fee-struct-2',
    name: 'Form 2 Fees 2025',
    description: 'Standard fees for Form 2',
    academic_year_id: 'ay-2025',
    grade_levels: [2],
    is_default: true,
    applicable_from: '2025-01-01',
    status: 'active',
    total_amount: 750.00
  }
]

const mockUser = {
  id: 'user-123',
  email: 'admin@school.com',
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin',
  school_id: 'school-123',
  school_name: 'Test School',
  permissions: ['finance:read', 'finance:write'],
  available_features: ['finance'],
  preferred_language: 'en',
  timezone: 'Africa/Harare'
}

const mockSchoolContext = {
  school: {
    id: 'school-123',
    name: 'Test School',
    type: 'secondary',
    config: {},
    domains: []
  },
  branding: {
    primary_color: '#3B82F6',
    secondary_color: '#64748B',
    accent_color: '#10B981',
    font_family: 'Inter'
  },
  features: { finance: true },
  subscription: {
    tier: 'premium',
    limits: {
      max_students: 1000,
      max_staff: 50,
      storage_limit_gb: 100
    }
  },
  academic: {
    year_start_month: 1,
    terms_per_year: 3,
    grading_system: {}
  },
  regional: {
    timezone: 'Africa/Harare',
    currency: 'USD',
    date_format: 'DD/MM/YYYY',
    primary_language: 'en',
    secondary_language: 'sn'
  },
  hasFeature: (feature: string) => true,
  canAccess: (permission: string) => true,
  formatCurrency: (amount: number) => `$${amount.toLocaleString()}`,
  formatDate: (date: Date) => date.toLocaleDateString('en-ZW'),
  getGradeDisplay: (grade: number) => `Form ${grade}`
}

describe('InvoiceManagement', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      token: 'mock-token'
    })

    vi.mocked(useSchoolContext).mockReturnValue(mockSchoolContext)
  })

  const renderComponent = (academicYearId: string = 'ay-2025') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <InvoiceManagement academicYearId={academicYearId} />
      </QueryClientProvider>
    )
  }

  it('renders loading state initially', () => {
    vi.mocked(financeApi.getInvoices).mockImplementation(() => new Promise(() => {}))
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    expect(screen.getByTestId('loader-icon')).toBeInTheDocument()
  })

  it('renders invoice list after successful fetch', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    expect(screen.getByText('INV-2025-001')).toBeInTheDocument()
    expect(screen.getByText('John Smith')).toBeInTheDocument()
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByText('$500')).toBeInTheDocument()
    expect(screen.getByText('$750')).toBeInTheDocument()
  })

  it('displays invoice statistics cards', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Total Invoices')).toBeInTheDocument()
    })

    expect(screen.getByText('2')).toBeInTheDocument() // Total count
    expect(screen.getByText('Paid Invoices')).toBeInTheDocument()
    expect(screen.getByText('Overdue')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument() // Overdue count
  })

  it('filters invoices by status', async () => {
    const mockGetInvoices = vi.mocked(financeApi.getInvoices)
    mockGetInvoices.mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    // Find and interact with status filter
    const statusFilter = screen.getAllByTestId('select')[0]
    fireEvent.change(statusFilter, { target: { value: 'overdue' } })

    await waitFor(() => {
      expect(mockGetInvoices).toHaveBeenCalledWith(
        expect.objectContaining({
          payment_status: 'overdue'
        })
      )
    })
  })

  it('searches invoices by text', async () => {
    const mockGetInvoices = vi.mocked(financeApi.getInvoices)
    mockGetInvoices.mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search invoices...')
    await user.type(searchInput, 'John')

    await waitFor(() => {
      expect(mockGetInvoices).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'John'
        })
      )
    })
  })

  it('opens create invoice dialog', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Create Invoice')).toBeInTheDocument()
    })

    const createButton = screen.getByText('Create Invoice')
    await user.click(createButton)

    expect(screen.getByText('Create New Invoice')).toBeInTheDocument()
  })

  it('creates new invoice successfully', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)
    vi.mocked(financeApi.createInvoice).mockResolvedValue({
      id: 'new-invoice',
      invoice_number: 'INV-2025-003',
      student_name: 'New Student',
      total_amount: 300.00,
      payment_status: 'pending'
    })

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Create Invoice')).toBeInTheDocument()
    })

    // Open create dialog
    const createButton = screen.getByText('Create Invoice')
    await user.click(createButton)

    // Fill form fields
    const studentInput = screen.getByPlaceholderText('Search and select student...')
    await user.type(studentInput, 'student-123')

    // Select fee structure
    const feeStructureSelect = screen.getAllByTestId('select')[0]
    fireEvent.change(feeStructureSelect, { target: { value: 'fee-struct-1' } })

    // Submit form
    const submitButton = screen.getByText('Create Invoice')
    await user.click(submitButton)

    await waitFor(() => {
      expect(financeApi.createInvoice).toHaveBeenCalledWith(
        expect.objectContaining({
          student_id: 'student-123',
          fee_structure_id: 'fee-struct-1',
          academic_year_id: 'ay-2025'
        })
      )
    })
  })

  it('opens bulk generate dialog', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Bulk Generate')).toBeInTheDocument()
    })

    const bulkButton = screen.getByText('Bulk Generate')
    await user.click(bulkButton)

    expect(screen.getByText('Bulk Generate Invoices')).toBeInTheDocument()
  })

  it('bulk generates invoices successfully', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)
    vi.mocked(financeApi.bulkGenerateInvoices).mockResolvedValue({
      total_invoices_generated: 25,
      total_students_processed: 25,
      total_amount: 12500.00,
      failed_students: [],
      invoice_ids: []
    })

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Bulk Generate')).toBeInTheDocument()
    })

    // Open bulk dialog
    const bulkButton = screen.getByText('Bulk Generate')
    await user.click(bulkButton)

    // Select fee structure
    const feeStructureSelect = screen.getAllByTestId('select')[0]
    fireEvent.change(feeStructureSelect, { target: { value: 'fee-struct-1' } })

    // Select grade levels
    const gradeCheckboxes = screen.getAllByTestId('checkbox')
    await user.click(gradeCheckboxes[0]) // Select first grade

    // Submit bulk generation
    const generateButton = screen.getByText('Generate Invoices')
    await user.click(generateButton)

    await waitFor(() => {
      expect(financeApi.bulkGenerateInvoices).toHaveBeenCalledWith(
        expect.objectContaining({
          fee_structure_id: 'fee-struct-1',
          grade_levels: expect.arrayContaining([1])
        })
      )
    })
  })

  it('sends invoice to parent', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)
    vi.mocked(financeApi.sendInvoice).mockResolvedValue(undefined)

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    // Open dropdown menu for first invoice
    const dropdownTrigger = screen.getAllByTestId('dropdown-trigger')[0]
    await user.click(dropdownTrigger)

    // Click send to parent
    const sendButton = screen.getByText('Send to Parent')
    await user.click(sendButton)

    await waitFor(() => {
      expect(financeApi.sendInvoice).toHaveBeenCalledWith('invoice-1')
    })
  })

  it('handles invoice selection for bulk operations', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    // Select individual invoices
    const checkboxes = screen.getAllByTestId('checkbox')
    await user.click(checkboxes[1]) // First invoice checkbox (header checkbox is index 0)

    // Should update selection state
    expect(checkboxes[1]).toBeChecked()
  })

  it('selects all invoices', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    // Select all checkbox
    const selectAllCheckbox = screen.getAllByTestId('checkbox')[0]
    await user.click(selectAllCheckbox)

    // All invoice checkboxes should be checked
    const checkboxes = screen.getAllByTestId('checkbox')
    checkboxes.slice(1).forEach(checkbox => {
      expect(checkbox).toBeChecked()
    })
  })

  it('displays correct payment status badges', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    // Check status badges
    const partialBadge = screen.getByText('partial')
    const overdueBadge = screen.getByText('overdue')

    expect(partialBadge).toBeInTheDocument()
    expect(overdueBadge).toBeInTheDocument()
  })

  it('shows pagination when there are multiple pages', async () => {
    const multiPageData = {
      ...mockInvoicesData,
      total_pages: 3,
      has_next: true,
      has_previous: false
    }

    vi.mocked(financeApi.getInvoices).mockResolvedValue(multiPageData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })

    expect(screen.getByText('Showing 1 to 2 of 2 invoices')).toBeInTheDocument()
    expect(screen.getByText('Previous')).toBeInTheDocument()
    expect(screen.getByText('Next')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(financeApi.getInvoices).mockRejectedValue(new Error('API Error'))
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    // Should handle error without crashing
    await waitFor(() => {
      expect(screen.getByText('Invoice Management')).toBeInTheDocument()
    })
  })

  it('formats currency correctly', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('$500')).toBeInTheDocument()
    })

    expect(mockSchoolContext.formatCurrency).toHaveBeenCalledWith(500.00)
  })

  it('shows export button in header', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Export')).toBeInTheDocument()
    })
  })

  it('displays correct total value in statistics', async () => {
    vi.mocked(financeApi.getInvoices).mockResolvedValue(mockInvoicesData)
    vi.mocked(financeApi.getFeeStructures).mockResolvedValue(mockFeeStructures)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Total Value')).toBeInTheDocument()
    })

    // Should show sum of all invoice amounts
    expect(screen.getByText('$1,250')).toBeInTheDocument()
  })
})