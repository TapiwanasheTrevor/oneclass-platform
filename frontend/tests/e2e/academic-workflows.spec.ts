/**
 * Academic Management E2E Tests
 * End-to-end tests for complete academic workflows
 */

import { test, expect } from '@playwright/test'

test.describe('Academic Management Workflows', () => {
  test.beforeEach(async ({ page }) => {
    // Login as teacher
    await page.goto('/login')
    await page.fill('[data-testid="email"]', 'teacher@school.co.zw')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    
    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard')
  })

  test('Complete subject management workflow', async ({ page }) => {
    // Navigate to subjects
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="subjects-link"]')
    
    // Wait for subjects page to load
    await expect(page.locator('h1')).toContainText('Subject Management')
    
    // Create new subject
    await page.click('[data-testid="add-subject-button"]')
    
    // Fill subject form
    await page.fill('[data-testid="subject-code"]', 'PHYS101')
    await page.fill('[data-testid="subject-name"]', 'Physics')
    await page.fill('[data-testid="subject-description"]', 'Basic physics course')
    
    // Select grade levels (11, 12)
    await page.check('[data-testid="grade-11"]')
    await page.check('[data-testid="grade-12"]')
    
    // Mark as practical
    await page.check('[data-testid="is-practical"]')
    await page.check('[data-testid="requires-lab"]')
    
    // Set marks and credits
    await page.fill('[data-testid="pass-mark"]', '50')
    await page.fill('[data-testid="max-mark"]', '100')
    await page.fill('[data-testid="credit-hours"]', '4')
    
    // Select department
    await page.selectOption('[data-testid="department"]', 'Sciences')
    
    // Submit form
    await page.click('[data-testid="create-subject-button"]')
    
    // Verify success
    await expect(page.locator('[data-testid="toast"]')).toContainText('Subject created successfully')
    await expect(page.locator('[data-testid="subjects-table"]')).toContainText('PHYS101')
    await expect(page.locator('[data-testid="subjects-table"]')).toContainText('Physics')
    
    // Edit the subject
    await page.click('[data-testid="edit-subject-PHYS101"]')
    
    // Update description
    await page.fill('[data-testid="subject-description"]', 'Advanced physics course with lab work')
    
    // Add grade 13
    await page.check('[data-testid="grade-13"]')
    
    // Update subject
    await page.click('[data-testid="update-subject-button"]')
    
    // Verify update
    await expect(page.locator('[data-testid="toast"]')).toContainText('Subject updated successfully')
    
    // Verify the updated subject appears in the list
    await expect(page.locator('[data-testid="subjects-table"]')).toContainText('Advanced physics course')
  })

  test('Complete timetable management workflow', async ({ page }) => {
    // Navigate to timetable
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="timetable-link"]')
    
    // Wait for timetable page to load
    await expect(page.locator('h1')).toContainText('Timetable Management')
    
    // Create new period first
    await page.click('[data-testid="add-period-button"]')
    
    // Fill period form
    await page.fill('[data-testid="period-name"]', 'Period 5')
    await page.fill('[data-testid="start-time"]', '11:10')
    await page.fill('[data-testid="end-time"]', '11:50')
    
    // Create period
    await page.click('[data-testid="create-period-button"]')
    
    // Verify period created
    await expect(page.locator('[data-testid="toast"]')).toContainText('Period created successfully')
    await expect(page.locator('[data-testid="periods-list"]')).toContainText('Period 5')
    
    // Add timetable entry by clicking empty slot
    await page.click('[data-testid="timetable-slot-monday-period5"]')
    
    // Fill timetable entry form
    await page.selectOption('[data-testid="subject-select"]', 'Mathematics')
    await page.selectOption('[data-testid="teacher-select"]', 'Mr. Smith')
    await page.fill('[data-testid="room-number"]', 'Room 201')
    
    // Mark as practical if needed
    await page.check('[data-testid="is-practical"]')
    
    // Create timetable entry
    await page.click('[data-testid="add-entry-button"]')
    
    // Verify entry created
    await expect(page.locator('[data-testid="toast"]')).toContainText('Timetable entry created successfully')
    await expect(page.locator('[data-testid="timetable-grid"]')).toContainText('Mathematics')
    await expect(page.locator('[data-testid="timetable-grid"]')).toContainText('Mr. Smith')
    await expect(page.locator('[data-testid="timetable-grid"]')).toContainText('Room 201')
    
    // Edit the timetable entry
    await page.click('[data-testid="timetable-entry-monday-period5"]')
    
    // Change room
    await page.fill('[data-testid="room-number"]', 'Room 301')
    
    // Update entry
    await page.click('[data-testid="update-entry-button"]')
    
    // Verify update
    await expect(page.locator('[data-testid="toast"]')).toContainText('Timetable entry updated successfully')
    await expect(page.locator('[data-testid="timetable-grid"]')).toContainText('Room 301')
  })

  test('Complete attendance tracking workflow', async ({ page }) => {
    // Navigate to attendance
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="attendance-link"]')
    
    // Wait for attendance page to load
    await expect(page.locator('h1')).toContainText('Attendance Tracker')
    
    // Select class and subject
    await page.selectOption('[data-testid="class-select"]', 'Form 4A')
    await page.selectOption('[data-testid="subject-select"]', 'Mathematics')
    
    // Start new attendance session
    await page.click('[data-testid="start-session-button"]')
    
    // Fill session details
    await page.fill('[data-testid="session-date"]', '2024-03-20')
    await page.selectOption('[data-testid="session-type"]', 'regular')
    await page.fill('[data-testid="session-notes"]', 'Regular mathematics class')
    
    // Create session
    await page.click('[data-testid="create-session-button"]')
    
    // Verify session created
    await expect(page.locator('[data-testid="toast"]')).toContainText('Attendance session created')
    
    // Wait for student list to load
    await expect(page.locator('[data-testid="students-list"]')).toBeVisible()
    
    // Mark attendance for students
    // Mark first student as present
    await page.click('[data-testid="student-1-present"]')
    
    // Mark second student as late with arrival time
    await page.click('[data-testid="student-2-late"]')
    await page.fill('[data-testid="student-2-arrival-time"]', '08:15')
    
    // Mark third student as absent with excuse
    await page.click('[data-testid="student-3-absent"]')
    await page.check('[data-testid="student-3-excused"]')
    await page.fill('[data-testid="student-3-excuse-reason"]', 'Sick')
    
    // Use quick action for remaining students
    await page.click('[data-testid="mark-remaining-present"]')
    
    // Submit attendance
    await page.click('[data-testid="submit-attendance-button"]')
    
    // Verify attendance submitted
    await expect(page.locator('[data-testid="toast"]')).toContainText('Attendance marked successfully')
    
    // Check attendance statistics updated
    await expect(page.locator('[data-testid="attendance-rate"]')).toBeVisible()
    await expect(page.locator('[data-testid="present-count"]')).toBeVisible()
    await expect(page.locator('[data-testid="absent-count"]')).toBeVisible()
  })

  test('Complete assessment and grading workflow', async ({ page }) => {
    // Navigate to grade book
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="gradebook-link"]')
    
    // Wait for grade book page to load
    await expect(page.locator('h1')).toContainText('Grade Book')
    
    // Create new assessment
    await page.click('[data-testid="create-assessment-button"]')
    
    // Fill assessment form
    await page.fill('[data-testid="assessment-name"]', 'Mid-Term Physics Test')
    await page.fill('[data-testid="assessment-description"]', 'Comprehensive physics assessment covering optics and mechanics')
    
    // Select assessment type and category
    await page.selectOption('[data-testid="assessment-type"]', 'test')
    await page.selectOption('[data-testid="assessment-category"]', 'continuous')
    
    // Set marks and weight
    await page.fill('[data-testid="total-marks"]', '100')
    await page.fill('[data-testid="pass-mark"]', '50')
    await page.fill('[data-testid="weight-percentage"]', '30')
    
    // Set date and duration
    await page.fill('[data-testid="assessment-date"]', '2024-03-25')
    await page.fill('[data-testid="duration-minutes"]', '120')
    
    // Add instructions
    await page.fill('[data-testid="instructions"]', 'Answer all questions. Show all working.')
    
    // Add allowed resources
    await page.fill('[data-testid="resources-allowed"]', 'Calculator, Formula sheet')
    
    // Create assessment
    await page.click('[data-testid="create-assessment-button"]')
    
    // Verify assessment created
    await expect(page.locator('[data-testid="toast"]')).toContainText('Assessment created successfully')
    await expect(page.locator('[data-testid="assessments-list"]')).toContainText('Mid-Term Physics Test')
    
    // View grades for the assessment
    await page.click('[data-testid="view-grades-mid-term-physics-test"]')
    
    // Wait for grades page to load
    await expect(page.locator('h2')).toContainText('Grades: Mid-Term Physics Test')
    
    // Enter grades for students
    // Student 1: 85 marks
    await page.fill('[data-testid="student-1-score"]', '85')
    await page.fill('[data-testid="student-1-feedback"]', 'Excellent understanding of concepts')
    
    // Student 2: 72 marks
    await page.fill('[data-testid="student-2-score"]', '72')
    await page.fill('[data-testid="student-2-feedback"]', 'Good work, improve on problem-solving')
    
    // Student 3: Absent
    await page.check('[data-testid="student-3-absent"]')
    await page.check('[data-testid="student-3-excused"]')
    
    // Student 4: 91 marks
    await page.fill('[data-testid="student-4-score"]', '91')
    await page.fill('[data-testid="student-4-feedback"]', 'Outstanding performance')
    
    // Verify letter grades auto-calculated (Zimbabwe A-U system)
    await expect(page.locator('[data-testid="student-1-letter-grade"]')).toContainText('A')
    await expect(page.locator('[data-testid="student-2-letter-grade"]')).toContainText('B')
    await expect(page.locator('[data-testid="student-4-letter-grade"]')).toContainText('A')
    
    // Submit grades
    await page.click('[data-testid="submit-grades-button"]')
    
    // Verify grades submitted
    await expect(page.locator('[data-testid="toast"]')).toContainText('Grades submitted successfully')
    
    // Check assessment statistics
    await expect(page.locator('[data-testid="class-average"]')).toBeVisible()
    await expect(page.locator('[data-testid="pass-rate"]')).toBeVisible()
    await expect(page.locator('[data-testid="highest-score"]')).toBeVisible()
    
    // Publish assessment
    await page.click('[data-testid="publish-assessment-button"]')
    
    // Confirm publishing
    await page.click('[data-testid="confirm-publish-button"]')
    
    // Verify assessment published
    await expect(page.locator('[data-testid="toast"]')).toContainText('Assessment published successfully')
    await expect(page.locator('[data-testid="assessment-status"]')).toContainText('Published')
  })

  test('Academic dashboard integration workflow', async ({ page }) => {
    // Navigate to academic dashboard
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="dashboard-link"]')
    
    // Wait for dashboard to load
    await expect(page.locator('h1')).toContainText('Academic Management')
    
    // Verify key metrics are displayed
    await expect(page.locator('[data-testid="total-subjects"]')).toBeVisible()
    await expect(page.locator('[data-testid="total-classes"]')).toBeVisible()
    await expect(page.locator('[data-testid="total-students"]')).toBeVisible()
    await expect(page.locator('[data-testid="attendance-rate"]')).toBeVisible()
    
    // Check recent activities
    await expect(page.locator('[data-testid="recent-activities"]')).toBeVisible()
    
    // Check upcoming assessments
    await expect(page.locator('[data-testid="upcoming-assessments"]')).toBeVisible()
    
    // Check attendance trends chart
    await expect(page.locator('[data-testid="attendance-trends-chart"]')).toBeVisible()
    
    // Filter by academic year
    await page.selectOption('[data-testid="academic-year-filter"]', '2024')
    
    // Verify dashboard updates
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden()
    
    // Test dashboard refresh
    await page.click('[data-testid="refresh-dashboard-button"]')
    
    // Verify refresh indicator
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible()
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden()
    
    // Quick navigation to different academic sections
    await page.click('[data-testid="quick-nav-subjects"]')
    await expect(page.locator('h1')).toContainText('Subject Management')
    
    await page.goBack()
    
    await page.click('[data-testid="quick-nav-attendance"]')
    await expect(page.locator('h1')).toContainText('Attendance Tracker')
    
    await page.goBack()
    
    await page.click('[data-testid="quick-nav-assessments"]')
    await expect(page.locator('h1')).toContainText('Grade Book')
  })

  test('Cross-module integration workflow', async ({ page }) => {
    // Navigate to student academic profile (integration with SIS)
    await page.click('[data-testid="sis-menu"]')
    await page.click('[data-testid="students-link"]')
    
    // Select a student
    await page.click('[data-testid="student-row-1"]')
    
    // View academic performance tab
    await page.click('[data-testid="academic-performance-tab"]')
    
    // Verify academic data from Academic module
    await expect(page.locator('[data-testid="overall-average"]')).toBeVisible()
    await expect(page.locator('[data-testid="attendance-rate"]')).toBeVisible()
    await expect(page.locator('[data-testid="subject-grades"]')).toBeVisible()
    
    // Check subject access based on payments (Finance integration)
    await expect(page.locator('[data-testid="subject-access-status"]')).toBeVisible()
    
    // Navigate to finance to check payment status
    await page.click('[data-testid="finance-menu"]')
    await page.click('[data-testid="student-accounts-link"]')
    
    // Search for the same student
    await page.fill('[data-testid="student-search"]', 'John Doe')
    await page.click('[data-testid="search-button"]')
    
    // View student finance details
    await page.click('[data-testid="view-student-finances"]')
    
    // Check academic-related invoices
    await expect(page.locator('[data-testid="academic-fees-section"]')).toBeVisible()
    await expect(page.locator('[data-testid="subject-enrollment-fees"]')).toBeVisible()
    
    // Generate invoice for subject enrollment
    await page.click('[data-testid="generate-subject-invoice-button"]')
    
    // Select subject
    await page.selectOption('[data-testid="subject-select"]', 'Physics')
    
    // Generate invoice
    await page.click('[data-testid="generate-invoice-button"]')
    
    // Verify invoice created
    await expect(page.locator('[data-testid="toast"]')).toContainText('Invoice generated successfully')
    
    // Verify subject access updated in academic module
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="subjects-link"]')
    
    // Check student enrollment status
    await page.click('[data-testid="view-enrollments-physics"]')
    await expect(page.locator('[data-testid="enrollment-status-john-doe"]')).toContainText('Pending Payment')
  })

  test('Zimbabwe-specific academic features', async ({ page }) => {
    // Test Zimbabwe grading scale (A-U)
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="gradebook-link"]')
    
    // View existing assessment grades
    await page.click('[data-testid="view-grades-mathematics-test"]')
    
    // Verify Zimbabwe grading scale is displayed
    await expect(page.locator('[data-testid="grading-scale-reference"]')).toBeVisible()
    await expect(page.locator('[data-testid="grading-scale-reference"]')).toContainText('A: 80-100%')
    await expect(page.locator('[data-testid="grading-scale-reference"]')).toContainText('U: 0-39%')
    
    // Test Zimbabwe grade levels (1-13)
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="subjects-link"]')
    await page.click('[data-testid="add-subject-button"]')
    
    // Verify all Zimbabwe grade levels available
    await expect(page.locator('[data-testid="grade-1"]')).toBeVisible()
    await expect(page.locator('[data-testid="grade-13"]')).toBeVisible() // A-Level
    
    // Test Zimbabwe three-term system
    await page.click('[data-testid="cancel-button"]')
    await page.click('[data-testid="academic-menu"]')
    await page.click('[data-testid="timetable-link"]')
    
    // Verify term selector shows Zimbabwe terms
    await expect(page.locator('[data-testid="term-selector"]')).toBeVisible()
    await page.click('[data-testid="term-selector"]')
    await expect(page.locator('[data-testid="term-1"]')).toContainText('Term 1')
    await expect(page.locator('[data-testid="term-2"]')).toContainText('Term 2')
    await expect(page.locator('[data-testid="term-3"]')).toContainText('Term 3')
    
    // Test Zimbabwe phone number format in guardian notifications
    await page.click('[data-testid="sis-menu"]')
    await page.click('[data-testid="students-link"]')
    await page.click('[data-testid="student-row-1"]')
    await page.click('[data-testid="guardians-tab"]')
    
    // Verify Zimbabwe phone format
    await expect(page.locator('[data-testid="guardian-phone"]')).toContainText('+263')
  })
})

test.describe('Academic Management Error Handling', () => {
  test('Handles network failures gracefully', async ({ page, context }) => {
    // Simulate network failure
    await context.route('**/api/v1/academic/**', route => route.abort())
    
    await page.goto('/academic/dashboard')
    
    // Should show error state
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()
    
    // Restore network and retry
    await context.unroute('**/api/v1/academic/**')
    await page.click('[data-testid="retry-button"]')
    
    // Should load successfully
    await expect(page.locator('h1')).toContainText('Academic Management')
  })

  test('Handles validation errors in forms', async ({ page }) => {
    await page.goto('/academic/subjects')
    
    // Try to create subject with invalid data
    await page.click('[data-testid="add-subject-button"]')
    await page.click('[data-testid="create-subject-button"]') // Submit without required fields
    
    // Should show validation errors
    await expect(page.locator('[data-testid="error-subject-code"]')).toContainText('Subject code is required')
    await expect(page.locator('[data-testid="error-subject-name"]')).toContainText('Subject name is required')
    await expect(page.locator('[data-testid="error-grade-levels"]')).toContainText('At least one grade level is required')
  })

  test('Handles concurrent access conflicts', async ({ page, context }) => {
    // Open subject management in two tabs
    const page2 = await context.newPage()
    
    await page.goto('/academic/subjects')
    await page2.goto('/academic/subjects')
    
    // Edit same subject in both tabs
    await page.click('[data-testid="edit-subject-math"]')
    await page2.click('[data-testid="edit-subject-math"]')
    
    // Make changes in first tab and save
    await page.fill('[data-testid="subject-name"]', 'Advanced Mathematics')
    await page.click('[data-testid="update-subject-button"]')
    
    // Make different changes in second tab and try to save
    await page2.fill('[data-testid="subject-name"]', 'Pure Mathematics')
    await page2.click('[data-testid="update-subject-button"]')
    
    // Should show conflict error
    await expect(page2.locator('[data-testid="conflict-error"]')).toContainText('This subject has been modified by another user')
    await expect(page2.locator('[data-testid="refresh-and-retry-button"]')).toBeVisible()
  })
})
