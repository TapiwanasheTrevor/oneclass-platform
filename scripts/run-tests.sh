#!/bin/bash

# Multi-Tenant End-to-End Test Runner
# Runs comprehensive tests for the OneClass Platform multi-tenant system

set -e

echo "🔒 OneClass Platform - Multi-Tenant End-to-End Tests"
echo "===================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "scripts/test-multi-tenant-flow.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
print_status "Installing test dependencies..."
pip install -r scripts/requirements-test.txt

# Check if backend server is running
print_status "Checking backend server status..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    print_error "Backend server is not running!"
    print_error "Please start the backend server first:"
    print_error "  cd backend && python main.py"
    exit 1
fi

print_success "Backend server is running"

# Run the multi-tenant tests
print_status "Running multi-tenant end-to-end tests..."
python scripts/test-multi-tenant-flow.py

# Check test results
if [ $? -eq 0 ]; then
    print_success "All tests completed successfully!"
else
    print_error "Some tests failed. Check the output above for details."
    exit 1
fi

echo ""
print_success "Multi-tenant testing completed!"
echo ""
echo "📋 Test Coverage:"
echo "  ✅ Health endpoints"
echo "  ✅ School creation and tenant setup"
echo "  ✅ Admin authentication"
echo "  ✅ Role-based user creation"
echo "  ✅ Role-based authentication"
echo "  ✅ Tenant isolation"
echo "  ✅ Role-based permissions"
echo "  ✅ User invitations"
echo "  ✅ Profile management"
echo "  ✅ Dashboard access"
echo ""
print_success "Multi-tenant system is production-ready! 🚀"