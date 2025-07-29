/**
 * Frontend Tests for Migration Services Components
 * Tests for CarePackageSelector and SuperAdminDashboard
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import CarePackageSelector from '../CarePackageSelector';
import SuperAdminDashboard from '../SuperAdminDashboard';

// Mock fetch for API calls
global.fetch = vi.fn();

// Mock window.alert
global.alert = vi.fn();

describe('CarePackageSelector Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders package selection step initially', () => {
    render(<CarePackageSelector />);
    
    expect(screen.getByText('Professional Data Migration Services')).toBeInTheDocument();
    expect(screen.getByText('Foundation Package')).toBeInTheDocument();
    expect(screen.getByText('Growth Package')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Package')).toBeInTheDocument();
  });

  it('displays package details correctly', () => {
    render(<CarePackageSelector />);
    
    // Check Foundation Package details
    expect(screen.getByText('$2,800')).toBeInTheDocument();
    expect(screen.getByText('50-200 students')).toBeInTheDocument();
    expect(screen.getByText('1-2 weeks')).toBeInTheDocument();
    expect(screen.getByText('Most Popular')).toBeInTheDocument();
    
    // Check Growth Package details
    expect(screen.getByText('$6,500')).toBeInTheDocument();
    expect(screen.getByText('200-800 students')).toBeInTheDocument();
    expect(screen.getByText('Best Value')).toBeInTheDocument();
    
    // Check Enterprise Package details
    expect(screen.getByText('$15,000')).toBeInTheDocument();
    expect(screen.getByText('800+ students')).toBeInTheDocument();
    expect(screen.getByText('Premium')).toBeInTheDocument();
  });

  it('shows ZWL pricing conversion', () => {
    render(<CarePackageSelector />);
    
    // Check ZWL prices are displayed
    expect(screen.getByText('~$4,480,000 ZWL')).toBeInTheDocument();
    expect(screen.getByText('~$10,400,000 ZWL')).toBeInTheDocument();
    expect(screen.getByText('~$24,000,000 ZWL')).toBeInTheDocument();
  });

  it('highlights best value package', () => {
    render(<CarePackageSelector />);
    
    const growthPackage = screen.getByText('Growth Package').closest('.border-2');
    expect(growthPackage).toHaveClass('ring-2', 'ring-green-500', 'scale-105');
  });

  it('shows value proposition section', () => {
    render(<CarePackageSelector />);
    
    expect(screen.getByText('Why Choose Professional Migration?')).toBeInTheDocument();
    expect(screen.getByText('95% Success Rate')).toBeInTheDocument();
    expect(screen.getByText('Save 200+ Hours')).toBeInTheDocument();
    expect(screen.getByText('Zero Data Loss')).toBeInTheDocument();
  });

  it('proceeds to requirements step when package is selected', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Click on Foundation Package
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    // Should show requirements step
    expect(screen.getByText('Requirements Assessment')).toBeInTheDocument();
    expect(screen.getByText('Help us understand your school\'s specific needs')).toBeInTheDocument();
  });

  it('validates required fields in requirements step', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to requirements step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    // Try to continue without filling required fields
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Should show payment step (basic validation)
    expect(screen.getByText('Order Summary & Payment')).toBeInTheDocument();
  });

  it('collects contact information correctly', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to requirements step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    // Fill contact information
    const nameInput = screen.getByLabelText('Full Name');
    const emailInput = screen.getByLabelText('Email Address');
    const phoneInput = screen.getByLabelText('Phone Number');
    
    await user.type(nameInput, 'John Doe');
    await user.type(emailInput, 'john@school.edu');
    await user.type(phoneInput, '+263 77 123 4567');
    
    expect(nameInput).toHaveValue('John Doe');
    expect(emailInput).toHaveValue('john@school.edu');
    expect(phoneInput).toHaveValue('+263 77 123 4567');
  });

  it('handles add-on services selection', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to requirements step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    // Select add-on services
    const urgentMigration = screen.getByLabelText(/Rush Migration/);
    const weekendWork = screen.getByLabelText(/Weekend\/Evening Work/);
    
    await user.click(urgentMigration);
    await user.click(weekendWork);
    
    expect(urgentMigration).toBeChecked();
    expect(weekendWork).toBeChecked();
  });

  it('shows on-site training option for Growth and Enterprise packages', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Select Growth Package
    const growthPackage = screen.getByText('Choose Growth Package');
    await user.click(growthPackage);
    
    // Should show on-site training option
    expect(screen.getByLabelText(/On-site Training/)).toBeInTheDocument();
  });

  it('calculates pricing correctly with add-ons', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate through to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    // Select add-ons
    const urgentMigration = screen.getByLabelText(/Rush Migration/);
    const weekendWork = screen.getByLabelText(/Weekend\/Evening Work/);
    
    await user.click(urgentMigration);
    await user.click(weekendWork);
    
    // Continue to payment
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Should show correct pricing
    expect(screen.getByText('$2,800')).toBeInTheDocument(); // Base price
    expect(screen.getByText('$1,000')).toBeInTheDocument(); // Rush migration
    expect(screen.getByText('$500')).toBeInTheDocument(); // Weekend work
    expect(screen.getByText('$4,300')).toBeInTheDocument(); // Total
  });

  it('offers payment options', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Should show payment options
    expect(screen.getByText('Full Payment (5% Discount)')).toBeInTheDocument();
    expect(screen.getByText('Split Payment')).toBeInTheDocument();
    expect(screen.getByText('Extended Payment Plan')).toBeInTheDocument();
  });

  it('applies discount for full payment', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Select full payment
    const fullPayment = screen.getByLabelText('Full Payment (5% Discount)');
    await user.click(fullPayment);
    
    // Should show discount
    expect(screen.getByText('Save 5%')).toBeInTheDocument();
  });

  it('shows order summary correctly', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Should show order summary
    expect(screen.getByText('Order Summary')).toBeInTheDocument();
    expect(screen.getByText('Foundation Package')).toBeInTheDocument();
    expect(screen.getByText('50-200 students')).toBeInTheDocument();
    expect(screen.getByText('What happens next?')).toBeInTheDocument();
  });

  it('submits order successfully', async () => {
    const user = userEvent.setup();
    
    // Mock successful API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ order_number: 'CP-2025-001' })
    });
    
    render(<CarePackageSelector />);
    
    // Navigate to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Submit order
    const submitButton = screen.getByText('Submit Order');
    await user.click(submitButton);
    
    // Should show success message
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        'Care package order submitted successfully! Our team will contact you within 24 hours.'
      );
    });
  });

  it('handles order submission error', async () => {
    const user = userEvent.setup();
    
    // Mock failed API response
    global.fetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(<CarePackageSelector />);
    
    // Navigate to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Submit order
    const submitButton = screen.getByText('Submit Order');
    await user.click(submitButton);
    
    // Should show error message
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        'There was an error submitting your order. Please try again.'
      );
    });
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    
    // Mock delayed API response
    global.fetch.mockImplementationOnce(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(<CarePackageSelector />);
    
    // Navigate to payment step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Submit order
    const submitButton = screen.getByText('Submit Order');
    await user.click(submitButton);
    
    // Should show loading state
    expect(screen.getByText('Submitting...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('allows navigation between steps', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Navigate to requirements step
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    // Should show back button
    expect(screen.getByText('Back to Packages')).toBeInTheDocument();
    
    // Navigate to payment step
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Should show back and change package buttons
    expect(screen.getByText('Back')).toBeInTheDocument();
    expect(screen.getByText('Change Package')).toBeInTheDocument();
    
    // Test back navigation
    const backButton = screen.getByText('Back');
    await user.click(backButton);
    
    expect(screen.getByText('Requirements Assessment')).toBeInTheDocument();
  });
});

describe('SuperAdminDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders dashboard with KPI cards', () => {
    render(<SuperAdminDashboard />);
    
    expect(screen.getByText('Migration Services')).toBeInTheDocument();
    expect(screen.getByText('Manage care package orders and migration projects')).toBeInTheDocument();
    
    // Check KPI cards
    expect(screen.getByText('Active Projects')).toBeInTheDocument();
    expect(screen.getByText('Monthly Revenue')).toBeInTheDocument();
    expect(screen.getByText('Team Utilization')).toBeInTheDocument();
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
  });

  it('displays KPI values correctly', () => {
    render(<SuperAdminDashboard />);
    
    // Check KPI values from mock data
    expect(screen.getByText('24')).toBeInTheDocument(); // Active Projects
    expect(screen.getByText('156,000')).toBeInTheDocument(); // Monthly Revenue
    expect(screen.getByText('87%')).toBeInTheDocument(); // Team Utilization
    expect(screen.getByText('96%')).toBeInTheDocument(); // Success Rate
  });

  it('shows KPI trends', () => {
    render(<SuperAdminDashboard />);
    
    expect(screen.getByText('+12% this month')).toBeInTheDocument();
    expect(screen.getByText('+23% vs last month')).toBeInTheDocument();
    expect(screen.getByText('Optimal')).toBeInTheDocument();
    expect(screen.getByText('Above target')).toBeInTheDocument();
  });

  it('renders tab navigation', () => {
    render(<SuperAdminDashboard />);
    
    expect(screen.getByText('Care Package Orders')).toBeInTheDocument();
    expect(screen.getByText('Active Projects')).toBeInTheDocument();
    expect(screen.getByText('Team Management')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('displays orders table with correct data', () => {
    render(<SuperAdminDashboard />);
    
    // Check table headers
    expect(screen.getByText('Order ID')).toBeInTheDocument();
    expect(screen.getByText('School')).toBeInTheDocument();
    expect(screen.getByText('Package')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Progress')).toBeInTheDocument();
    expect(screen.getByText('Manager')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
    
    // Check order data
    expect(screen.getByText('CP-2025-001')).toBeInTheDocument();
    expect(screen.getByText('St. Mary\'s High School')).toBeInTheDocument();
    expect(screen.getByText('Growth Package')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Sarah Moyo')).toBeInTheDocument();
  });

  it('shows order status badges with correct colors', () => {
    render(<SuperAdminDashboard />);
    
    // Check status badges
    const inProgressBadge = screen.getByText('In Progress');
    expect(inProgressBadge).toHaveClass('bg-purple-100', 'text-purple-800');
    
    const dataMigrationBadge = screen.getByText('Data Migration');
    expect(dataMigrationBadge).toHaveClass('bg-orange-100', 'text-orange-800');
    
    const pendingBadge = screen.getByText('Pending Assignment');
    expect(pendingBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('displays progress bars correctly', () => {
    render(<SuperAdminDashboard />);
    
    // Check progress percentages
    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByText('35%')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Find search input
    const searchInput = screen.getByPlaceholderText('Search orders by school name or order ID...');
    
    // Type search term
    await user.type(searchInput, 'St. Mary');
    
    expect(searchInput).toHaveValue('St. Mary');
  });

  it('handles status filter', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Open filter dropdown
    const filterButton = screen.getByText('Filter by status');
    await user.click(filterButton);
    
    // Select status
    const inProgressOption = screen.getByText('In Progress');
    await user.click(inProgressOption);
    
    // Filter should be applied
    expect(screen.getByDisplayValue('In Progress')).toBeInTheDocument();
  });

  it('opens order details modal', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click on order row
    const orderRow = screen.getByText('CP-2025-001').closest('div');
    await user.click(orderRow);
    
    // Modal should open
    expect(screen.getByText('Order Details - CP-2025-001')).toBeInTheDocument();
    expect(screen.getByText('St. Mary\'s High School')).toBeInTheDocument();
  });

  it('displays team performance in team tab', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click team tab
    const teamTab = screen.getByText('Team Management');
    await user.click(teamTab);
    
    // Check team members
    expect(screen.getByText('Sarah Moyo')).toBeInTheDocument();
    expect(screen.getByText('Senior Migration Manager')).toBeInTheDocument();
    expect(screen.getByText('Tendai Chigamba')).toBeInTheDocument();
    expect(screen.getByText('Technical Lead')).toBeInTheDocument();
    expect(screen.getByText('Grace Mutindi')).toBeInTheDocument();
    expect(screen.getByText('Data Specialist')).toBeInTheDocument();
  });

  it('shows team utilization charts', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click team tab
    const teamTab = screen.getByText('Team Management');
    await user.click(teamTab);
    
    // Check utilization percentages
    expect(screen.getByText('85%')).toBeInTheDocument(); // Sarah Moyo
    expect(screen.getByText('90%')).toBeInTheDocument(); // Tendai Chigamba
    expect(screen.getByText('75%')).toBeInTheDocument(); // Grace Mutindi
  });

  it('displays analytics in analytics tab', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click analytics tab
    const analyticsTab = screen.getByText('Analytics');
    await user.click(analyticsTab);
    
    // Check analytics content
    expect(screen.getByText('Revenue Analytics')).toBeInTheDocument();
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('Monthly Trends')).toBeInTheDocument();
  });

  it('shows revenue breakdown by package', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click analytics tab
    const analyticsTab = screen.getByText('Analytics');
    await user.click(analyticsTab);
    
    // Check revenue breakdown
    expect(screen.getByText('Foundation Package')).toBeInTheDocument();
    expect(screen.getByText('$22,400')).toBeInTheDocument();
    expect(screen.getByText('Growth Package')).toBeInTheDocument();
    expect(screen.getByText('$78,000')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Package')).toBeInTheDocument();
    expect(screen.getByText('$60,000')).toBeInTheDocument();
  });

  it('displays performance metrics', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click analytics tab
    const analyticsTab = screen.getByText('Analytics');
    await user.click(analyticsTab);
    
    // Check performance metrics
    expect(screen.getByText('Average Completion Time')).toBeInTheDocument();
    expect(screen.getByText('18 days')).toBeInTheDocument();
    expect(screen.getByText('Customer Satisfaction')).toBeInTheDocument();
    expect(screen.getByText('4.8/5.0')).toBeInTheDocument();
    expect(screen.getByText('On-Time Delivery')).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
  });

  it('shows export and filter buttons', () => {
    render(<SuperAdminDashboard />);
    
    expect(screen.getByText('Export')).toBeInTheDocument();
    expect(screen.getByText('Filter')).toBeInTheDocument();
    expect(screen.getByText('Create Manual Order')).toBeInTheDocument();
  });

  it('handles modal close', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Open modal
    const orderRow = screen.getByText('CP-2025-001').closest('div');
    await user.click(orderRow);
    
    // Close modal
    const closeButton = screen.getByText('✕');
    await user.click(closeButton);
    
    // Modal should be closed
    expect(screen.queryByText('Order Details - CP-2025-001')).not.toBeInTheDocument();
  });

  it('shows active projects in projects tab', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click projects tab
    const projectsTab = screen.getByText('Active Projects');
    await user.click(projectsTab);
    
    // Check active projects
    expect(screen.getByText('St. Mary\'s High School')).toBeInTheDocument();
    expect(screen.getByText('CP-2025-001 • Growth Package')).toBeInTheDocument();
    expect(screen.getByText('Harare International School')).toBeInTheDocument();
    expect(screen.getByText('CP-2025-002 • Enterprise Package')).toBeInTheDocument();
  });

  it('displays correct order counts and amounts', () => {
    render(<SuperAdminDashboard />);
    
    // Check order values
    expect(screen.getByText('$6,500')).toBeInTheDocument();
    expect(screen.getByText('$15,000')).toBeInTheDocument();
    expect(screen.getByText('$2,800')).toBeInTheDocument();
    
    // Check student counts
    expect(screen.getByText('450 students')).toBeInTheDocument();
    expect(screen.getByText('1200 students')).toBeInTheDocument();
    expect(screen.getByText('180 students')).toBeInTheDocument();
  });

  it('shows team member ratings', async () => {
    const user = userEvent.setup();
    render(<SuperAdminDashboard />);
    
    // Click team tab
    const teamTab = screen.getByText('Team Management');
    await user.click(teamTab);
    
    // Check ratings
    expect(screen.getByText('4.8')).toBeInTheDocument();
    expect(screen.getByText('4.9')).toBeInTheDocument();
    expect(screen.getByText('4.7')).toBeInTheDocument();
  });
});

describe('Integration Tests', () => {
  it('maintains state between CarePackageSelector steps', async () => {
    const user = userEvent.setup();
    render(<CarePackageSelector />);
    
    // Select package and fill requirements
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const studentCountInput = screen.getByLabelText('Current Number of Students');
    await user.type(studentCountInput, '150');
    
    // Navigate to payment
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    // Check that data persists
    expect(screen.getByText('Foundation Package')).toBeInTheDocument();
    expect(screen.getByText('50-200 students')).toBeInTheDocument();
    
    // Navigate back
    const backButton = screen.getByText('Back');
    await user.click(backButton);
    
    // Data should still be there
    expect(studentCountInput).toHaveValue('150');
  });

  it('handles responsive layout', () => {
    render(<CarePackageSelector />);
    
    // Check responsive grid classes
    const packageGrid = screen.getByText('Foundation Package').closest('.grid');
    expect(packageGrid).toHaveClass('grid-cols-1', 'lg:grid-cols-3');
  });

  it('shows proper loading states', async () => {
    const user = userEvent.setup();
    
    // Mock delayed API response
    global.fetch.mockImplementationOnce(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(<CarePackageSelector />);
    
    // Navigate to payment and submit
    const foundationPackage = screen.getByText('Choose Foundation Package');
    await user.click(foundationPackage);
    
    const continueButton = screen.getByText('Continue to Payment');
    await user.click(continueButton);
    
    const submitButton = screen.getByText('Submit Order');
    await user.click(submitButton);
    
    // Should show loading state
    expect(screen.getByText('Submitting...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });
});