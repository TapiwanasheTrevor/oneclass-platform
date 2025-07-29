/**
 * Tests for FinanceDashboard component
 * Tests data fetching, rendering, and user interactions
 */

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, beforeEach, describe, it, expect } from 'vitest'
import FinanceDashboard from '../FinanceDashboard'
import { financeApi } from '@/lib/finance-api'
import { useAuth } from '@/hooks/useAuth'
import { useSchoolContext } from '@/hooks/useSchoolContext'

// Mock the API
vi.mock('@/lib/finance-api', () => ({
  financeApi: {
    getFinanceDashboard: vi.fn(),
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

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <span data-testid="badge" className={className}>{children}</span>
  ),
}))

vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value }: { value: number }) => (
    <div data-testid="progress" data-value={value}>Progress: {value}%</div>
  ),
}))

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: { children: React.ReactNode; value: string; onValueChange: (value: string) => void }) => (
    <div data-testid="tabs" data-value={value}>
      <button onClick={() => onValueChange('current')}>Current Term</button>
      <button onClick={() => onValueChange('ytd')}>Year to Date</button>
      {children}
    </div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <button data-testid="tabs-trigger" data-value={value}>{children}</button>
  ),
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button data-testid="button" onClick={onClick}>{children}</button>
  ),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  DollarSign: () => <span data-testid="dollar-sign-icon">$</span>,
  TrendingUp: () => <span data-testid="trending-up-icon">↗</span>,
  AlertCircle: () => <span data-testid="alert-circle-icon">!</span>,
  CheckCircle: () => <span data-testid="check-circle-icon">✓</span>,
  Download: () => <span data-testid="download-icon">↓</span>,
  Send: () => <span data-testid="send-icon">→</span>,
  Plus: () => <span data-testid="plus-icon">+</span>,
  CreditCard: () => <span data-testid="credit-card-icon">💳</span>,
  Clock: () => <span data-testid="clock-icon">🕐</span>,
  Users: () => <span data-testid="users-icon">👥</span>,
  FileText: () => <span data-testid="file-text-icon">📄</span>,
  Wallet: () => <span data-testid="wallet-icon">💼</span>,
}))

const mockDashboardData = {
  school_id: 'school-123',
  academic_year_id: 'ay-2025',
  current_term_invoiced: 150000,
  current_term_collected: 120000,
  current_term_outstanding: 30000,
  current_term_collection_rate: 80,
  year_to_date_invoiced: 450000,
  year_to_date_collected: 360000,
  year_to_date_outstanding: 90000,
  year_to_date_collection_rate: 80,
  recent_payments: [
    {
      id: 'payment-1',
      student_name: 'John Smith',
      amount: 500,
      payment_date: '2025-07-15',
      status: 'completed',
      payment_method: { name: 'EcoCash' }
    },
    {
      id: 'payment-2',
      student_name: 'Jane Doe',
      amount: 750,
      payment_date: '2025-07-16',
      status: 'completed',
      payment_method: { name: 'Bank Transfer' }
    }
  ],
  overdue_invoices_count: 5,
  pending_payments_count: 3,
  monthly_collection_trend: [],
  payment_method_breakdown: [
    { method: 'EcoCash', amount: 50000, count: 100, percentage: 41.7 },
    { method: 'Bank Transfer', amount: 40000, count: 80, percentage: 33.3 },
    { method: 'Cash', amount: 30000, count: 60, percentage: 25.0 }
  ],
  fee_category_breakdown: []
}

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
  getGradeDisplay: (grade: number) => `Grade ${grade}`
}

describe('FinanceDashboard', () => {
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
        <FinanceDashboard academicYearId={academicYearId} />
      </QueryClientProvider>
    )
  }

  it('renders loading state initially', () => {
    vi.mocked(financeApi.getFinanceDashboard).mockImplementation(() => new Promise(() => {}))

    renderComponent()

    expect(screen.getByTestId('card')).toBeInTheDocument()
    expect(screen.getAllByTestId('card')).toHaveLength(4) // Loading skeleton cards
  })

  it('renders dashboard data after successful fetch', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Financial Overview')).toBeInTheDocument()
    })

    // Check key metrics are displayed
    expect(screen.getByText('$150,000')).toBeInTheDocument() // Current term invoiced
    expect(screen.getByText('$120,000')).toBeInTheDocument() // Current term collected
    expect(screen.getByText('$30,000')).toBeInTheDocument() // Outstanding
    expect(screen.getByText('80%')).toBeInTheDocument() // Collection rate
  })

  it('displays recent payments list', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Recent Payments')).toBeInTheDocument()
    })

    expect(screen.getByText('John Smith')).toBeInTheDocument()
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByText('$500')).toBeInTheDocument()
    expect(screen.getByText('$750')).toBeInTheDocument()
  })

  it('shows payment method breakdown', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Payment Methods')).toBeInTheDocument()
    })

    expect(screen.getByText('EcoCash')).toBeInTheDocument()
    expect(screen.getByText('Bank Transfer')).toBeInTheDocument()
    expect(screen.getByText('Cash')).toBeInTheDocument()
    expect(screen.getByText('$50,000')).toBeInTheDocument()
  })

  it('displays alerts for overdue invoices', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('5 overdue invoices')).toBeInTheDocument()
    })

    expect(screen.getByText('3 pending payments')).toBeInTheDocument()
  })

  it('switches between current term and year to date', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Current Term')).toBeInTheDocument()
    })

    // Initially shows current term data
    expect(screen.getByText('$150,000')).toBeInTheDocument()

    // Click year to date tab
    const ytdButton = screen.getByText('Year to Date')
    ytdButton.click()

    await waitFor(() => {
      expect(screen.getByText('$450,000')).toBeInTheDocument() // YTD invoiced
    })
  })

  it('handles API error gracefully', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockRejectedValue(new Error('API Error'))

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Unable to load dashboard')).toBeInTheDocument()
    })

    expect(screen.getByText('There was an error loading the finance dashboard.')).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('formats currency using school context', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('$150,000')).toBeInTheDocument()
    })

    // Verify formatCurrency was called
    expect(mockSchoolContext.formatCurrency).toHaveBeenCalledWith(150000)
  })

  it('shows correct collection rate styling', async () => {
    const lowCollectionData = {
      ...mockDashboardData,
      current_term_collection_rate: 65 // Low collection rate
    }

    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(lowCollectionData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('65%')).toBeInTheDocument()
    })

    // Should show "Needs Attention" badge
    expect(screen.getByText('Needs Attention')).toBeInTheDocument()
  })

  it('shows no recent payments message when empty', async () => {
    const noPaymentsData = {
      ...mockDashboardData,
      recent_payments: []
    }

    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(noPaymentsData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('No recent payments')).toBeInTheDocument()
    })
  })

  it('calculates progress bar value correctly', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      const progressBar = screen.getByTestId('progress')
      expect(progressBar).toHaveAttribute('data-value', '80')
    })
  })

  it('displays quick action buttons', async () => {
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    expect(screen.getByText('Record Payment')).toBeInTheDocument()
    expect(screen.getByText('Generate Invoice')).toBeInTheDocument()
    expect(screen.getByText('Send Reminders')).toBeInTheDocument()
    expect(screen.getByText('Export Report')).toBeInTheDocument()
  })

  it('refreshes data every 30 seconds', async () => {
    const mockGetDashboard = vi.mocked(financeApi.getFinanceDashboard)
    mockGetDashboard.mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(1)
    })

    // Fast-forward time by 30 seconds
    vi.advanceTimersByTime(30000)

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledTimes(2)
    })
  })

  it('calls API with correct academic year ID', async () => {
    const mockGetDashboard = vi.mocked(financeApi.getFinanceDashboard)
    mockGetDashboard.mockResolvedValue(mockDashboardData)

    const testAcademicYearId = 'ay-2025-test'
    renderComponent(testAcademicYearId)

    await waitFor(() => {
      expect(mockGetDashboard).toHaveBeenCalledWith(testAcademicYearId)
    })
  })

  it('shows low collection rate alert', async () => {
    const lowCollectionData = {
      ...mockDashboardData,
      current_term_collection_rate: 65
    }

    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(lowCollectionData)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Low collection rate (65%)')).toBeInTheDocument()
    })
  })

  it('handles missing school context gracefully', async () => {
    vi.mocked(useSchoolContext).mockReturnValue(null)
    vi.mocked(financeApi.getFinanceDashboard).mockResolvedValue(mockDashboardData)

    renderComponent()

    await waitFor(() => {
      // Should use fallback currency formatting
      expect(screen.getByText('$150,000')).toBeInTheDocument()
    })
  })
})