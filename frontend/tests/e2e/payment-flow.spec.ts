/**
 * End-to-End tests for payment processing flow
 * Tests complete user workflows from invoice creation to payment completion
 */

import { test, expect } from '@playwright/test'

test.describe('Payment Processing Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/auth/me', async route => {
      await route.fulfill({
        json: {
          id: 'user-123',
          email: 'admin@testschool.com',
          first_name: 'Admin',
          last_name: 'User',
          role: 'admin',
          school_id: 'school-123',
          school_name: 'Test School',
          permissions: ['finance:read', 'finance:write'],
          available_features: ['finance']
        }
      })
    })

    // Mock school context
    await page.route('**/schools/school-123/context', async route => {
      await route.fulfill({
        json: {
          id: 'school-123',
          name: 'Test School',
          type: 'secondary',
          config: {
            currency: 'USD',
            timezone: 'Africa/Harare',
            date_format: 'DD/MM/YYYY',
            language_primary: 'en',
            primary_color: '#3B82F6',
            secondary_color: '#64748B',
            features_enabled: { finance: true },
            subscription_tier: 'premium'
          },
          domains: []
        }
      })
    })

    // Navigate to finance dashboard
    await page.goto('/finance')
  })

  test('complete invoice creation and payment flow', async ({ page }) => {
    // Mock fee structures
    await page.route('**/api/v1/finance/fee-management/structures*', async route => {
      await route.fulfill({
        json: [
          {
            id: 'fee-struct-1',
            name: 'Form 1 Fees 2025',
            description: 'Standard fees for Form 1',
            academic_year_id: 'ay-2025',
            grade_levels: [1],
            status: 'active',
            total_amount: 500.00
          }
        ]
      })
    })

    // Mock initial empty invoices
    await page.route('**/api/v1/finance/invoices*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            invoices: [],
            total_count: 0,
            page: 1,
            page_size: 20,
            total_pages: 1,
            has_next: false,
            has_previous: false
          }
        })
      }
    })

    // Wait for page to load
    await expect(page.locator('text=Finance Dashboard')).toBeVisible()

    // Navigate to invoice management
    await page.click('text=Invoice Management')
    await expect(page.locator('text=Create Invoice')).toBeVisible()

    // Start invoice creation
    await page.click('text=Create Invoice')
    await expect(page.locator('text=Create New Invoice')).toBeVisible()

    // Fill invoice form
    await page.fill('[placeholder="Search and select student..."]', 'student-123')
    await page.selectOption('select', 'fee-struct-1')
    await page.click('[placeholder="Pick a date"]')
    await page.click('text=30') // Select 30th of current month
    await page.fill('textarea', 'Term 1 fees for student')

    // Mock successful invoice creation
    await page.route('**/api/v1/finance/invoices', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          json: {
            id: 'invoice-123',
            invoice_number: 'INV-2025-001',
            student_id: 'student-123',
            student_name: 'John Smith',
            total_amount: 500.00,
            paid_amount: 0.00,
            outstanding_amount: 500.00,
            payment_status: 'pending',
            due_date: '2025-08-30',
            currency: 'USD',
            line_items: [
              {
                description: 'Term 1 Fees',
                quantity: 1,
                unit_price: 500.00,
                line_total: 500.00
              }
            ]
          }
        })
      }
    })

    // Submit invoice creation
    await page.click('button:has-text("Create Invoice")')

    // Verify success message
    await expect(page.locator('text=Invoice created successfully')).toBeVisible()

    // Mock updated invoices list
    await page.route('**/api/v1/finance/invoices*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-123',
                invoice_number: 'INV-2025-001',
                student_name: 'John Smith',
                student_number: 'STU-001',
                grade_level: 'Form 1',
                due_date: '2025-08-30',
                total_amount: 500.00,
                paid_amount: 0.00,
                outstanding_amount: 500.00,
                payment_status: 'pending',
                status: 'sent'
              }
            ],
            total_count: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
            has_next: false,
            has_previous: false
          }
        })
      }
    })

    // Verify invoice appears in list
    await expect(page.locator('text=INV-2025-001')).toBeVisible()
    await expect(page.locator('text=John Smith')).toBeVisible()
    await expect(page.locator('text=$500')).toBeVisible()

    // Test payment initiation
    await page.click('[data-testid="dropdown-trigger"]')
    await page.click('text=Record Payment')

    // Mock payment methods
    await page.route('**/api/v1/finance/payments/methods*', async route => {
      await route.fulfill({
        json: [
          {
            id: 'method-1',
            name: 'EcoCash',
            code: 'ECOCASH',
            type: 'mobile_money',
            is_active: true
          },
          {
            id: 'method-2',
            name: 'Bank Transfer',
            code: 'BANK',
            type: 'bank_transfer',
            is_active: true
          }
        ]
      })
    })

    // Fill payment form
    await page.selectOption('select', 'method-1')
    await page.fill('[placeholder="Amount"]', '500.00')
    await page.fill('[placeholder="Payer name"]', 'John Parent')
    await page.fill('[placeholder="Email"]', 'parent@example.com')
    await page.fill('[placeholder="Phone"]', '+263771234567')
    await page.fill('[placeholder="Transaction ID"]', 'ECOCASH-123456')

    // Mock successful payment creation
    await page.route('**/api/v1/finance/payments', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          json: {
            id: 'payment-123',
            payment_reference: 'PAY-2025-001',
            student_id: 'student-123',
            amount: 500.00,
            currency: 'USD',
            payment_method_id: 'method-1',
            payer_name: 'John Parent',
            payer_email: 'parent@example.com',
            payer_phone: '+263771234567',
            transaction_id: 'ECOCASH-123456',
            status: 'completed'
          }
        })
      }
    })

    // Submit payment
    await page.click('button:has-text("Record Payment")')

    // Verify payment success
    await expect(page.locator('text=Payment recorded successfully')).toBeVisible()

    // Mock payment allocation
    await page.route('**/api/v1/finance/payments/payment-123/allocate', async route => {
      await route.fulfill({
        json: {
          allocated_amount: 500.00,
          allocations: [
            {
              invoice_id: 'invoice-123',
              amount: 500.00
            }
          ]
        }
      })
    })

    // Allocate payment to invoice
    await page.click('text=Allocate Payment')
    await page.check('input[type="checkbox"]') // Select the invoice
    await page.click('button:has-text("Allocate")')

    // Verify allocation success
    await expect(page.locator('text=Payment allocated successfully')).toBeVisible()

    // Mock updated invoice with payment
    await page.route('**/api/v1/finance/invoices*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-123',
                invoice_number: 'INV-2025-001',
                student_name: 'John Smith',
                student_number: 'STU-001',
                grade_level: 'Form 1',
                due_date: '2025-08-30',
                total_amount: 500.00,
                paid_amount: 500.00,
                outstanding_amount: 0.00,
                payment_status: 'paid',
                status: 'paid'
              }
            ],
            total_count: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
            has_next: false,
            has_previous: false
          }
        })
      }
    })

    // Refresh page to see updated status
    await page.reload()

    // Verify invoice is now paid
    await expect(page.locator('text=paid')).toBeVisible()
    await expect(page.locator('text=$500').first()).toBeVisible() // Total amount
    await expect(page.locator('text=$500').nth(1)).toBeVisible() // Paid amount
  })

  test('bulk invoice generation flow', async ({ page }) => {
    // Mock fee structures
    await page.route('**/api/v1/finance/fee-management/structures*', async route => {
      await route.fulfill({
        json: [
          {
            id: 'fee-struct-1',
            name: 'Form 1 Fees 2025',
            grade_levels: [1],
            status: 'active',
            total_amount: 500.00
          }
        ]
      })
    })

    // Navigate to invoice management
    await page.click('text=Invoice Management')
    await expect(page.locator('text=Bulk Generate')).toBeVisible()

    // Start bulk generation
    await page.click('text=Bulk Generate')
    await expect(page.locator('text=Bulk Generate Invoices')).toBeVisible()

    // Fill bulk generation form
    await page.selectOption('select', 'fee-struct-1')
    await page.click('[placeholder="Pick a date"]')
    await page.click('text=30') // Select due date
    await page.check('input[type="checkbox"]') // Select grade level

    // Mock successful bulk generation
    await page.route('**/api/v1/finance/invoices/bulk-generate', async route => {
      await route.fulfill({
        json: {
          total_invoices_generated: 25,
          total_students_processed: 25,
          total_amount: 12500.00,
          failed_students: [],
          invoice_ids: ['invoice-1', 'invoice-2', 'invoice-3']
        }
      })
    })

    // Submit bulk generation
    await page.click('button:has-text("Generate Invoices")')

    // Verify success message
    await expect(page.locator('text=Generated 25 invoices for 25 students')).toBeVisible()
  })

  test('Paynow online payment flow', async ({ page }) => {
    // Mock invoice with outstanding amount
    await page.route('**/api/v1/finance/invoices*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-123',
                invoice_number: 'INV-2025-001',
                student_name: 'John Smith',
                student_number: 'STU-001',
                grade_level: 'Form 1',
                due_date: '2025-08-30',
                total_amount: 500.00,
                paid_amount: 0.00,
                outstanding_amount: 500.00,
                payment_status: 'pending',
                status: 'sent'
              }
            ],
            total_count: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
            has_next: false,
            has_previous: false
          }
        })
      }
    })

    // Navigate to invoice management
    await page.click('text=Invoice Management')
    await expect(page.locator('text=INV-2025-001')).toBeVisible()

    // Initiate online payment
    await page.click('[data-testid="dropdown-trigger"]')
    await page.click('text=Pay Online')

    // Mock Paynow payment initiation
    await page.route('**/api/v1/finance/payments/paynow/initiate', async route => {
      await route.fulfill({
        json: {
          payment_id: 'paynow-123',
          paynow_reference: 'PR-123456',
          redirect_url: 'https://paynow.co.zw/interface/initiate?guid=123',
          poll_url: 'https://paynow.co.zw/interface/poll?guid=123',
          status: 'ok',
          success: true,
          hash_valid: true
        }
      })
    })

    // Fill payment details
    await page.fill('[placeholder="Email"]', 'parent@example.com')
    await page.fill('[placeholder="Phone"]', '+263771234567')
    await page.click('button:has-text("Initiate Payment")')

    // Verify redirect URL is provided
    await expect(page.locator('text=Redirecting to Paynow')).toBeVisible()
    await expect(page.locator('a[href*="paynow.co.zw"]')).toBeVisible()

    // Mock payment status checking
    await page.route('**/api/v1/finance/payments/paynow/status/paynow-123', async route => {
      await route.fulfill({
        json: {
          status: 'Paid',
          amount: 500.00,
          paynow_reference: 'PR-123456',
          hash_valid: true
        }
      })
    })

    // Simulate payment completion check
    await page.click('text=Check Payment Status')

    // Verify payment completion
    await expect(page.locator('text=Payment completed successfully')).toBeVisible()
  })

  test('mobile money payment flow', async ({ page }) => {
    // Mock invoice
    await page.route('**/api/v1/finance/invoices*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-123',
                invoice_number: 'INV-2025-001',
                student_name: 'John Smith',
                total_amount: 500.00,
                paid_amount: 0.00,
                outstanding_amount: 500.00,
                payment_status: 'pending'
              }
            ],
            total_count: 1,
            page: 1,
            page_size: 20,
            total_pages: 1
          }
        })
      }
    })

    // Navigate to invoice management
    await page.click('text=Invoice Management')
    await page.click('[data-testid="dropdown-trigger"]')
    await page.click('text=Mobile Money')

    // Mock mobile money payment initiation
    await page.route('**/api/v1/finance/payments/paynow/mobile', async route => {
      await route.fulfill({
        json: {
          payment_id: 'mobile-123',
          success: true,
          instructions: 'Dial *151*2*1*573646# to complete payment',
          poll_url: 'https://paynow.co.zw/interface/poll?guid=456'
        }
      })
    })

    // Fill mobile money details
    await page.fill('[placeholder="Phone"]', '+263771234567')
    await page.selectOption('select', 'ecocash')
    await page.click('button:has-text("Send Payment Request")')

    // Verify mobile money instructions
    await expect(page.locator('text=Dial *151*2*1*573646# to complete payment')).toBeVisible()
    await expect(page.locator('text=Payment request sent')).toBeVisible()
  })

  test('payment reconciliation flow', async ({ page }) => {
    // Mock payments needing reconciliation
    await page.route('**/api/v1/finance/payments*', async route => {
      await route.fulfill({
        json: {
          payments: [
            {
              id: 'payment-1',
              payment_reference: 'PAY-2025-001',
              student_name: 'John Smith',
              amount: 500.00,
              payment_date: '2025-07-15',
              status: 'completed',
              reconciled: false,
              transaction_id: 'BANK-123456'
            },
            {
              id: 'payment-2',
              payment_reference: 'PAY-2025-002',
              student_name: 'Jane Doe',
              amount: 750.00,
              payment_date: '2025-07-16',
              status: 'completed',
              reconciled: false,
              transaction_id: 'ECOCASH-789012'
            }
          ],
          total_count: 2,
          page: 1,
          page_size: 20,
          total_pages: 1
        }
      })
    })

    // Navigate to reconciliation
    await page.click('text=Reconciliation')
    await expect(page.locator('text=Payment Reconciliation')).toBeVisible()

    // Select payments for reconciliation
    await page.check('input[type="checkbox"]') // Select all
    await expect(page.locator('text=2 payments selected')).toBeVisible()

    // Mock reconciliation process
    await page.route('**/api/v1/finance/payments/reconcile', async route => {
      await route.fulfill({
        json: {
          reconciled_count: 2,
          total_amount: 1250.00
        }
      })
    })

    // Mark as reconciled
    await page.click('button:has-text("Mark as Reconciled")')

    // Verify reconciliation success
    await expect(page.locator('text=2 payments reconciled successfully')).toBeVisible()
  })

  test('invoice filtering and search', async ({ page }) => {
    // Mock invoices with different statuses
    await page.route('**/api/v1/finance/invoices*', async route => {
      const url = route.request().url()
      const urlParams = new URLSearchParams(url.split('?')[1])
      
      if (urlParams.get('payment_status') === 'overdue') {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-overdue',
                invoice_number: 'INV-2025-002',
                student_name: 'Jane Doe',
                payment_status: 'overdue',
                total_amount: 750.00
              }
            ],
            total_count: 1
          }
        })
      } else if (urlParams.get('search') === 'John') {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-john',
                invoice_number: 'INV-2025-001',
                student_name: 'John Smith',
                payment_status: 'pending',
                total_amount: 500.00
              }
            ],
            total_count: 1
          }
        })
      } else {
        await route.fulfill({
          json: {
            invoices: [
              {
                id: 'invoice-1',
                invoice_number: 'INV-2025-001',
                student_name: 'John Smith',
                payment_status: 'pending',
                total_amount: 500.00
              },
              {
                id: 'invoice-2',
                invoice_number: 'INV-2025-002',
                student_name: 'Jane Doe',
                payment_status: 'overdue',
                total_amount: 750.00
              }
            ],
            total_count: 2
          }
        })
      }
    })

    // Navigate to invoice management
    await page.click('text=Invoice Management')
    await expect(page.locator('text=John Smith')).toBeVisible()
    await expect(page.locator('text=Jane Doe')).toBeVisible()

    // Test status filtering
    await page.selectOption('select', 'overdue')
    await expect(page.locator('text=John Smith')).not.toBeVisible()
    await expect(page.locator('text=Jane Doe')).toBeVisible()

    // Test search functionality
    await page.selectOption('select', 'all') // Reset filter
    await page.fill('[placeholder="Search invoices..."]', 'John')
    await expect(page.locator('text=John Smith')).toBeVisible()
    await expect(page.locator('text=Jane Doe')).not.toBeVisible()
  })

  test('error handling and validation', async ({ page }) => {
    // Navigate to invoice management
    await page.click('text=Invoice Management')
    await page.click('text=Create Invoice')

    // Try to submit empty form
    await page.click('button:has-text("Create Invoice")')

    // Verify validation errors
    await expect(page.locator('text=Please fill in all required fields')).toBeVisible()

    // Test invalid phone number
    await page.fill('[placeholder="Phone"]', '1234567890')
    await expect(page.locator('text=Invalid Zimbabwe phone number')).toBeVisible()

    // Test API error handling
    await page.route('**/api/v1/finance/invoices', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 500,
          json: { detail: 'Internal server error' }
        })
      }
    })

    // Fill form correctly and submit
    await page.fill('[placeholder="Search and select student..."]', 'student-123')
    await page.selectOption('select', 'fee-struct-1')
    await page.click('button:has-text("Create Invoice")')

    // Verify error message
    await expect(page.locator('text=Failed to create invoice')).toBeVisible()
  })
})