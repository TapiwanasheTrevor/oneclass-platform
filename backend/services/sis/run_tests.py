#!/usr/bin/env python3
"""
Test runner for SIS module
"""

import sys
import os
import pytest

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Set environment variables for testing
os.environ['ENVIRONMENT'] = 'test'
os.environ['TEST_DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost:5432/sis_test'

def run_tests():
    """Run all SIS tests"""
    test_args = [
        'tests/',
        '-v',
        '--tb=short',
        '--disable-warnings',
        '--asyncio-mode=auto'
    ]
    
    # Add coverage if requested
    if '--coverage' in sys.argv:
        test_args.extend([
            '--cov=.',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing'
        ])
    
    # Run specific test if provided
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        test_args = [sys.argv[1]] + test_args[1:]
    
    return pytest.main(test_args)

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)