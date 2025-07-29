/**
 * Test fixtures and mock data for Frontend Finance module tests
 * Provides consistent test data across all frontend test files
 */

import { 
  FeeCategory, 
  FeeStructure, 
  FeeItem, 
  Invoice, 
  Payment, 
  PaymentMethod, 
  FinanceDashboard,
  PaynowPaymentRequest,
  PaynowPaymentResponse
} from '@/lib/finance-api'

// Mock User and School Data
export const mockUser = {
  id: 'user-123',
  email: 'admin@testschool.com',
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin',
  school_id: 'school-123',
  school_name: 'Test School',
  permissions: ['finance:read', 'finance:write', 'finance:admin'],
  available_features: ['finance', 'analytics', 'reports'],
  preferred_language: 'en',
  timezone: 'Africa/Harare'
}

export const mockTeacherUser = {
  ...mockUser,
  id: 'teacher-456',
  email: 'teacher@testschool.com',
  first_name: 'Teacher',
  last_name: 'User',
  role: 'teacher',
  permissions: ['finance:read'],
}

export const mockSchoolContext = {
  school: {
    id: 'school-123',
    name: 'Test School',
    type: 'secondary',
    config: {
      currency: 'USD',
      timezone: 'Africa/Harare',
      date_format: 'DD/MM/YYYY',
      language_primary: 'en',
      language_secondary: 'sn',
      primary_color: '#3B82F6',
      secondary_color: '#64748B',
      accent_color: '#10B981',
      font_family: 'Inter',
      features_enabled: { finance: true, analytics: true },
      subscription_tier: 'premium',
      max_students: 1000,
      academic_year_start_month: 1,
      terms_per_year: 3
    },
    domains: [
      { domain: 'testschool.oneclass.zw', is_primary: true, is_custom: false }
    ]
  },
  branding: {
    logo_url: '/test-logo.png',
    primary_color: '#3B82F6',
    secondary_color: '#64748B',
    accent_color: '#10B981',
    font_family: 'Inter'
  },
  features: { finance: true, analytics: true },
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
    grading_system: {
      type: 'zimbabwe',
      grades: ['A', 'B', 'C', 'D', 'E', 'U']
    }
  },
  regional: {
    timezone: 'Africa/Harare',
    currency: 'USD',
    date_format: 'DD/MM/YYYY',
    primary_language: 'en',
    secondary_language: 'sn'
  },
  hasFeature: (feature: string) => true,
  canAccess: (permission: string) => mockUser.permissions.includes(permission),
  formatCurrency: (amount: number) => `$${amount.toLocaleString()}`,
  formatDate: (date: Date) => date.toLocaleDateString('en-ZW'),
  getGradeDisplay: (grade: number) => {
    if (grade <= 7) return `Grade ${grade}`
    if (grade === 12) return 'Form 5 (Lower 6)'
    if (grade === 13) return 'Form 6 (Upper 6)'
    return `Form ${grade - 6}`
  }
}

// Fee Categories
export const mockFeeCategories: FeeCategory[] = [
  {
    id: 'cat-1',
    name: 'Tuition Fees',
    code: 'TUITION',
    description: 'Regular tuition fees for academic instruction',
    is_mandatory: true,
    is_refundable: false,
    allows_partial_payment: true,
    display_order: 1,
    is_active: true
  },
  {
    id: 'cat-2',
    name: 'Sports Fees',
    code: 'SPORTS',
    description: 'Sports and extracurricular activities',
    is_mandatory: false,
    is_refundable: true,
    allows_partial_payment: false,
    display_order: 2,
    is_active: true
  },
  {
    id: 'cat-3',
    name: 'Laboratory Fees',
    code: 'LAB',
    description: 'Science laboratory usage and materials',
    is_mandatory: true,
    is_refundable: false,
    allows_partial_payment: true,
    display_order: 3,
    is_active: true
  },
  {
    id: 'cat-4',
    name: 'Library Fees',
    code: 'LIBRARY',
    description: 'Library membership and resources',
    is_mandatory: false,
    is_refundable: true,
    allows_partial_payment: false,
    display_order: 4,
    is_active: true
  }
]

// Fee Structures
export const mockFeeStructures: FeeStructure[] = [
  {
    id: 'fs-1',
    name: 'Form 1 Fee Structure 2025',
    description: 'Standard fee structure for Form 1 students',
    academic_year_id: 'ay-2025',
    grade_levels: [1],
    class_ids: ['class-1a', 'class-1b'],
    is_default: true,
    applicable_from: '2025-01-01',
    applicable_to: '2025-12-31',
    status: 'active',
    total_amount: 500.00,
    items: [
      {
        id: 'item-1',
        name: 'Term 1 Tuition',
        description: 'Tuition for Term 1',
        base_amount: 400.00,
        currency: 'USD',
        frequency: 'term',
        allows_installments: true,
        max_installments: 3,
        late_fee_amount: 10.00,
        fee_category_id: 'cat-1',
        fee_category: mockFeeCategories[0]
      },
      {
        id: 'item-2',
        name: 'Sports Fee',
        description: 'Annual sports fee',
        base_amount: 100.00,
        currency: 'USD',
        frequency: 'annual',
        allows_installments: false,
        max_installments: 1,
        late_fee_amount: 5.00,
        fee_category_id: 'cat-2',
        fee_category: mockFeeCategories[1]
      }
    ]
  },
  {
    id: 'fs-2',
    name: 'Form 2 Fee Structure 2025',
    description: 'Standard fee structure for Form 2 students',
    academic_year_id: 'ay-2025',
    grade_levels: [2],
    class_ids: ['class-2a', 'class-2b'],
    is_default: true,
    applicable_from: '2025-01-01',
    applicable_to: '2025-12-31',
    status: 'active',
    total_amount: 600.00
  },
  {
    id: 'fs-3',
    name: 'Form 3-4 Fee Structure 2025',
    description: 'Combined fee structure for Form 3 and 4',
    academic_year_id: 'ay-2025',
    grade_levels: [3, 4],
    class_ids: [],
    is_default: true,
    applicable_from: '2025-01-01',
    applicable_to: '2025-12-31',
    status: 'active',
    total_amount: 750.00
  }
]

// Payment Methods
export const mockPaymentMethods: PaymentMethod[] = [
  {
    id: 'pm-1',
    name: 'EcoCash',
    code: 'ECOCASH',
    type: 'mobile_money',
    is_active: true,
    requires_reference: true,
    supports_partial_payment: true,
    transaction_fee_percentage: 1.5,
    transaction_fee_fixed: 0.00,
    display_order: 1,
    icon_url: '/icons/ecocash.png'
  },
  {
    id: 'pm-2',
    name: 'OneMoney',
    code: 'ONEMONEY',
    type: 'mobile_money',
    is_active: true,
    requires_reference: true,
    supports_partial_payment: true,
    transaction_fee_percentage: 1.5,
    transaction_fee_fixed: 0.00,
    display_order: 2,
    icon_url: '/icons/onemoney.png'
  },
  {
    id: 'pm-3',
    name: 'Bank Transfer',
    code: 'BANK',
    type: 'bank_transfer',
    is_active: true,
    requires_reference: true,
    supports_partial_payment: true,
    transaction_fee_percentage: 0.0,
    transaction_fee_fixed: 0.00,
    display_order: 3,
    icon_url: '/icons/bank.png'
  },
  {
    id: 'pm-4',
    name: 'Cash',
    code: 'CASH',
    type: 'cash',
    is_active: true,
    requires_reference: false,
    supports_partial_payment: true,
    transaction_fee_percentage: 0.0,
    transaction_fee_fixed: 0.00,
    display_order: 4,
    icon_url: '/icons/cash.png'
  }
]

// Invoices
export const mockInvoices: Invoice[] = [
  {
    id: 'inv-1',
    invoice_number: 'INV-2025-001',
    student_id: 'student-1',
    student_name: 'John Smith',
    student_number: 'STU-001',
    grade_level: 'Form 1',
    invoice_date: '2025-07-01',
    due_date: '2025-08-15',
    academic_year_id: 'ay-2025',
    term_id: 'term-1',
    subtotal: 500.00,
    discount_amount: 0.00,
    tax_amount: 0.00,
    total_amount: 500.00,
    paid_amount: 200.00,
    outstanding_amount: 300.00,
    payment_status: 'partial',
    status: 'sent',
    currency: 'USD',
    sent_to_parent: true,
    reminder_count: 1,
    line_items: [
      {
        id: 'line-1',
        description: 'Term 1 Tuition',
        quantity: 1,
        unit_price: 400.00,
        discount_amount: 0.00,
        line_total: 400.00
      },
      {
        id: 'line-2',
        description: 'Sports Fee',
        quantity: 1,
        unit_price: 100.00,
        discount_amount: 0.00,
        line_total: 100.00
      }
    ]
  },
  {
    id: 'inv-2',
    invoice_number: 'INV-2025-002',
    student_id: 'student-2',
    student_name: 'Jane Doe',
    student_number: 'STU-002',
    grade_level: 'Form 2',
    invoice_date: '2025-07-01',
    due_date: '2025-08-10',
    academic_year_id: 'ay-2025',
    term_id: 'term-1',
    subtotal: 600.00,
    discount_amount: 0.00,
    tax_amount: 0.00,
    total_amount: 600.00,
    paid_amount: 0.00,
    outstanding_amount: 600.00,
    payment_status: 'overdue',
    status: 'sent',
    currency: 'USD',
    sent_to_parent: true,
    reminder_count: 2,
    line_items: [
      {
        id: 'line-3',
        description: 'Term 1 Tuition',
        quantity: 1,
        unit_price: 500.00,
        discount_amount: 0.00,
        line_total: 500.00
      },
      {
        id: 'line-4',
        description: 'Lab Fee',
        quantity: 1,
        unit_price: 100.00,
        discount_amount: 0.00,
        line_total: 100.00
      }
    ]
  },
  {
    id: 'inv-3',
    invoice_number: 'INV-2025-003',
    student_id: 'student-3',
    student_name: 'Mike Johnson',
    student_number: 'STU-003',
    grade_level: 'Form 3',
    invoice_date: '2025-07-01',
    due_date: '2025-08-20',
    academic_year_id: 'ay-2025',
    term_id: 'term-1',
    subtotal: 750.00,
    discount_amount: 0.00,
    tax_amount: 0.00,
    total_amount: 750.00,
    paid_amount: 750.00,
    outstanding_amount: 0.00,
    payment_status: 'paid',
    status: 'paid',
    currency: 'USD',
    sent_to_parent: true,
    reminder_count: 0,
    line_items: [
      {
        id: 'line-5',
        description: 'Term 1 Tuition',
        quantity: 1,
        unit_price: 600.00,
        discount_amount: 0.00,
        line_total: 600.00
      },
      {
        id: 'line-6',
        description: 'Advanced Lab Fee',
        quantity: 1,
        unit_price: 150.00,
        discount_amount: 0.00,
        line_total: 150.00
      }
    ]
  }
]

// Payments
export const mockPayments: Payment[] = [
  {
    id: 'pay-1',
    payment_reference: 'PAY-2025-001',
    student_id: 'student-1',
    student_name: 'John Smith',
    student_number: 'STU-001',
    amount: 200.00,
    currency: 'USD',
    payment_date: '2025-07-15',
    payment_method_id: 'pm-1',
    payment_method: mockPaymentMethods[0],
    transaction_id: 'ECOCASH-123456',
    status: 'completed',
    payer_name: 'John Parent',
    payer_email: 'parent@example.com',
    payer_phone: '+263771234567',
    reconciled: false,
    notes: 'Partial payment for Term 1 fees'
  },
  {
    id: 'pay-2',
    payment_reference: 'PAY-2025-002',
    student_id: 'student-3',
    student_name: 'Mike Johnson',
    student_number: 'STU-003',
    amount: 750.00,
    currency: 'USD',
    payment_date: '2025-07-16',
    payment_method_id: 'pm-3',
    payment_method: mockPaymentMethods[2],
    transaction_id: 'BANK-789012',
    status: 'completed',
    payer_name: 'Mike Parent',
    payer_email: 'mike@example.com',
    payer_phone: '+263772345678',
    reconciled: true,
    notes: 'Full payment for Term 1 fees'
  },
  {
    id: 'pay-3',
    payment_reference: 'PAY-2025-003',
    student_id: 'student-2',
    student_name: 'Jane Doe',
    student_number: 'STU-002',
    amount: 300.00,
    currency: 'USD',
    payment_date: '2025-07-17',
    payment_method_id: 'pm-2',
    payment_method: mockPaymentMethods[1],
    transaction_id: 'ONEMONEY-345678',
    status: 'pending',
    payer_name: 'Jane Parent',
    payer_email: 'jane@example.com',
    payer_phone: '+263773456789',
    reconciled: false,
    notes: 'Pending payment verification'
  }
]

// Finance Dashboard
export const mockFinanceDashboard: FinanceDashboard = {
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
      id: 'pay-recent-1',
      student_name: 'John Smith',
      amount: 500,
      payment_date: '2025-07-15',
      status: 'completed',
      payment_method: { name: 'EcoCash' }
    },
    {
      id: 'pay-recent-2',
      student_name: 'Jane Doe',
      amount: 750,
      payment_date: '2025-07-16',
      status: 'completed',
      payment_method: { name: 'Bank Transfer' }
    },
    {
      id: 'pay-recent-3',
      student_name: 'Mike Johnson',
      amount: 600,
      payment_date: '2025-07-17',
      status: 'pending',
      payment_method: { name: 'OneMoney' }
    }
  ],
  overdue_invoices_count: 5,
  pending_payments_count: 3,
  monthly_collection_trend: [
    { month: '2025-01', expected: 100000, collected: 85000, rate: 85 },
    { month: '2025-02', expected: 120000, collected: 96000, rate: 80 },
    { month: '2025-03', expected: 110000, collected: 99000, rate: 90 },
    { month: '2025-04', expected: 130000, collected: 104000, rate: 80 },
    { month: '2025-05', expected: 115000, collected: 92000, rate: 80 },
    { month: '2025-06', expected: 125000, collected: 100000, rate: 80 },
    { month: '2025-07', expected: 140000, collected: 112000, rate: 80 }
  ],
  payment_method_breakdown: [
    { method: 'EcoCash', amount: 50000, count: 100, percentage: 41.7 },
    { method: 'Bank Transfer', amount: 40000, count: 80, percentage: 33.3 },
    { method: 'OneMoney', amount: 20000, count: 40, percentage: 16.7 },
    { method: 'Cash', amount: 10000, count: 20, percentage: 8.3 }
  ],
  fee_category_breakdown: [
    { category: 'Tuition', amount: 80000, percentage: 66.7 },
    { category: 'Sports', amount: 25000, percentage: 20.8 },
    { category: 'Laboratory', amount: 15000, percentage: 12.5 }
  ]
}

// Paynow Integration
export const mockPaynowPaymentRequest: PaynowPaymentRequest = {
  student_id: 'student-1',
  invoice_ids: ['inv-1'],
  amount: 500.00,
  payer_email: 'parent@example.com',
  payer_phone: '+263771234567'
}

export const mockPaynowPaymentResponse: PaynowPaymentResponse = {
  payment_id: 'paynow-123456',
  paynow_reference: 'PR-789012',
  poll_url: 'https://paynow.co.zw/interface/poll/?guid=123',
  redirect_url: 'https://paynow.co.zw/interface/initiate/?guid=123',
  status: 'ok',
  success: true,
  hash_valid: true
}

export const mockPaynowErrorResponse: PaynowPaymentResponse = {
  payment_id: 'paynow-error',
  paynow_reference: '',
  poll_url: '',
  redirect_url: '',
  status: 'error',
  success: false,
  hash_valid: false,
  error: 'Invalid email address'
}

// Pagination Data
export const mockPaginatedInvoices = {
  invoices: mockInvoices,
  total_count: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
  has_next: false,
  has_previous: false
}

export const mockPaginatedPayments = {
  payments: mockPayments,
  total_count: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
  has_next: false,
  has_previous: false
}

// Bulk Operations
export const mockBulkInvoiceGeneration = {
  fee_structure_id: 'fs-1',
  due_date: '2025-08-30',
  academic_year_id: 'ay-2025',
  term_id: 'term-1',
  grade_levels: [1, 2],
  class_ids: ['class-1a', 'class-1b', 'class-2a'],
  notes: 'Bulk generated invoices for Term 1'
}

export const mockBulkInvoiceResult = {
  total_invoices_generated: 75,
  total_students_processed: 75,
  total_amount: 37500.00,
  failed_students: [],
  invoice_ids: ['inv-bulk-1', 'inv-bulk-2', 'inv-bulk-3']
}

// Validation Test Data
export const validZimbabwePhoneNumbers = [
  '+263771234567',
  '+263712345678',
  '+263782345678',
  '+263773456789',
  '+263714567890'
]

export const invalidZimbabwePhoneNumbers = [
  '1234567890',
  '+1234567890',
  '+263712345',
  '+2637123456789',
  '+263abc1234567',
  '263771234567',
  '+263 77 123 4567',
  '+263-77-123-4567'
]

export const validCurrencies = ['USD', 'ZWL']
export const invalidCurrencies = ['EUR', 'GBP', 'JPY', 'CAD', 'AUD']

// API Response Helpers
export const createMockApiResponse = <T>(data: T, status = 200) => ({
  data,
  status,
  statusText: status === 200 ? 'OK' : 'Error',
  headers: {},
  config: {}
})

export const createMockApiError = (message: string, status = 500) => ({
  response: {
    data: { detail: message },
    status,
    statusText: 'Error',
    headers: {},
    config: {}
  }
})

// Date Helpers
export const getTodayISO = () => new Date().toISOString().split('T')[0]
export const getFutureDateISO = (days: number) => {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().split('T')[0]
}
export const getPastDateISO = (days: number) => {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split('T')[0]
}

// Test State Helpers
export const getEmptyInvoiceState = () => ({
  invoices: [],
  total_count: 0,
  page: 1,
  page_size: 20,
  total_pages: 1,
  has_next: false,
  has_previous: false
})

export const getEmptyPaymentState = () => ({
  payments: [],
  total_count: 0,
  page: 1,
  page_size: 20,
  total_pages: 1,
  has_next: false,
  has_previous: false
})

export const getEmptyDashboardState = (): FinanceDashboard => ({
  school_id: 'school-123',
  academic_year_id: 'ay-2025',
  current_term_invoiced: 0,
  current_term_collected: 0,
  current_term_outstanding: 0,
  current_term_collection_rate: 0,
  year_to_date_invoiced: 0,
  year_to_date_collected: 0,
  year_to_date_outstanding: 0,
  year_to_date_collection_rate: 0,
  recent_payments: [],
  overdue_invoices_count: 0,
  pending_payments_count: 0,
  monthly_collection_trend: [],
  payment_method_breakdown: [],
  fee_category_breakdown: []
})

// Performance Test Data
export const createLargeInvoiceDataset = (count: number) => {
  const invoices = []
  for (let i = 1; i <= count; i++) {
    invoices.push({
      ...mockInvoices[0],
      id: `inv-${i}`,
      invoice_number: `INV-2025-${i.toString().padStart(3, '0')}`,
      student_name: `Student ${i}`,
      student_number: `STU-${i.toString().padStart(3, '0')}`,
      total_amount: Math.floor(Math.random() * 1000) + 100
    })
  }
  return invoices
}

export const createLargePaymentDataset = (count: number) => {
  const payments = []
  for (let i = 1; i <= count; i++) {
    payments.push({
      ...mockPayments[0],
      id: `pay-${i}`,
      payment_reference: `PAY-2025-${i.toString().padStart(3, '0')}`,
      student_name: `Student ${i}`,
      student_number: `STU-${i.toString().padStart(3, '0')}`,
      amount: Math.floor(Math.random() * 1000) + 100
    })
  }
  return payments
}