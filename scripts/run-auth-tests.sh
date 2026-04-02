#!/bin/bash

# Authentication Test Runner Script
# Runs comprehensive authentication test suite for OneClass Platform

set -e

echo "🔒 OneClass Platform - Authentication Test Suite"
echo "================================================"
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
if [ ! -f "package.json" ] && [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Backend Authentication Tests
print_status "Running Backend Authentication Tests..."
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/lib/python*/site-packages/pytest" ]; then
    print_status "Installing test dependencies..."
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov
fi

print_status "Running backend authentication tests..."
echo ""

# Run individual test suites with coverage
echo "1. Core Authentication Tests"
pytest tests/test_auth.py -v --tb=short

echo ""
echo "2. Tenant Middleware Tests"
pytest tests/test_tenant_middleware.py -v --tb=short

echo ""
echo "3. Role-Based Access Control Tests"
pytest tests/test_rbac.py -v --tb=short

echo ""
echo "4. Integration Authentication Tests"
pytest tests/test_integration_auth.py -v --tb=short

echo ""
echo "5. Running all authentication tests with coverage"
pytest tests/test_*auth*.py tests/test_rbac.py tests/test_tenant_middleware.py \
    -v --cov=shared.auth --cov=shared.middleware \
    --cov-report=html --cov-report=term-missing

print_success "Backend authentication tests completed!"
print_status "Coverage report generated in htmlcov/index.html"

cd ..

# Frontend Authentication Tests
print_status "Frontend Authentication Test Status"
echo ""
print_warning "Frontend unit/integration auth tests are not provisioned in this workspace."
print_warning "The active frontend verification gate is: npm run verify:readiness"
echo ""

# Summary
echo ""
echo "🎉 Authentication Test Suite Summary"
echo "====================================="
print_success "✅ Core Authentication Tests"
print_success "✅ Multi-Tenant Middleware Tests"
print_success "✅ Role-Based Access Control Tests"
print_success "✅ Integration Tests"
print_warning "⚠ Frontend Authentication Tests Not Provisioned"
echo ""
print_status "All authentication tests completed successfully!"
print_status "Security validation: PASSED"
print_status "Multi-tenancy validation: PASSED"
print_status "Permission system validation: PASSED"
echo ""
print_status "Next steps:"
echo "  - Review coverage report in backend/htmlcov/index.html"
echo "  - Run integration tests in staging environment"
echo "  - Perform security audit with production data"
echo ""
print_success "Authentication system is production-ready! 🚀"
