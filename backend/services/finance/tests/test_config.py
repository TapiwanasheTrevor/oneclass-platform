"""
Test configuration and coverage settings for Finance module
"""

import pytest
import coverage
import os
from pathlib import Path

# Coverage configuration
COVERAGE_CONFIG = {
    'branch': True,
    'source': ['backend/services/finance'],
    'omit': [
        '*/tests/*',
        '*/test_*',
        '*/__pycache__/*',
        '*/venv/*',
        '*/env/*',
        '*/migrations/*',
        '*/conftest.py'
    ],
    'include': [
        'backend/services/finance/*.py',
        'backend/services/finance/**/*.py'
    ],
    'exclude_lines': [
        'pragma: no cover',
        'def __repr__',
        'raise AssertionError',
        'raise NotImplementedError',
        'if __name__ == .__main__.:',
        'class .*\\(Protocol\\):',
        '@(abc\\.)?abstractmethod'
    ],
    'precision': 2,
    'show_missing': True,
    'skip_covered': False,
    'fail_under': 80.0  # Require 80% coverage
}


def setup_coverage():
    """Set up coverage reporting."""
    cov = coverage.Coverage(**COVERAGE_CONFIG)
    cov.start()
    return cov


def generate_coverage_report(cov):
    """Generate coverage report."""
    cov.stop()
    cov.save()
    
    # Generate console report
    print("\n" + "="*50)
    print("COVERAGE REPORT")
    print("="*50)
    cov.report()
    
    # Generate HTML report
    report_dir = Path("htmlcov")
    report_dir.mkdir(exist_ok=True)
    cov.html_report(directory=str(report_dir))
    print(f"\nHTML coverage report generated: {report_dir}/index.html")
    
    # Generate XML report for CI/CD
    cov.xml_report(outfile="coverage.xml")
    print("XML coverage report generated: coverage.xml")
    
    # Check coverage threshold
    total = cov.report(show_missing=False, skip_covered=False)
    if total < COVERAGE_CONFIG['fail_under']:
        print(f"\nCOVERAGE FAILURE: {total:.2f}% < {COVERAGE_CONFIG['fail_under']:.2f}%")
        return False
    else:
        print(f"\nCOVERAGE SUCCESS: {total:.2f}% >= {COVERAGE_CONFIG['fail_under']:.2f}%")
        return True


# Test execution configuration
TEST_CONFIG = {
    'unit_tests': {
        'path': 'backend/services/finance/tests/test_crud.py',
        'markers': ['unit'],
        'timeout': 30,
        'parallel': True
    },
    'integration_tests': {
        'path': 'backend/services/finance/tests/test_api.py',
        'markers': ['integration'],
        'timeout': 60,
        'parallel': False
    },
    'payment_integration_tests': {
        'path': 'backend/services/finance/tests/test_payment_integration.py',
        'markers': ['integration', 'slow'],
        'timeout': 120,
        'parallel': False
    },
    'performance_tests': {
        'path': 'backend/services/finance/tests/test_performance.py',
        'markers': ['slow'],
        'timeout': 300,
        'parallel': False
    }
}


class TestRunner:
    """Test runner with coverage and reporting."""
    
    def __init__(self):
        self.cov = None
        self.results = {}
    
    def run_test_suite(self, suite_name: str = None):
        """Run specific test suite or all tests."""
        self.cov = setup_coverage()
        
        try:
            if suite_name:
                self._run_single_suite(suite_name)
            else:
                self._run_all_suites()
        finally:
            success = generate_coverage_report(self.cov)
            self._generate_test_report()
            return success
    
    def _run_single_suite(self, suite_name: str):
        """Run a single test suite."""
        config = TEST_CONFIG.get(suite_name)
        if not config:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        args = self._build_pytest_args(config)
        result = pytest.main(args)
        self.results[suite_name] = result
    
    def _run_all_suites(self):
        """Run all test suites."""
        for suite_name, config in TEST_CONFIG.items():
            print(f"\n{'='*20} Running {suite_name} {'='*20}")
            args = self._build_pytest_args(config)
            result = pytest.main(args)
            self.results[suite_name] = result
    
    def _build_pytest_args(self, config):
        """Build pytest arguments from config."""
        args = [
            config['path'],
            '-v',
            '--tb=short',
            f'--timeout={config["timeout"]}',
            '--durations=10'
        ]
        
        # Add markers
        if config.get('markers'):
            for marker in config['markers']:
                args.extend(['-m', marker])
        
        # Add parallel execution
        if config.get('parallel'):
            args.extend(['-n', 'auto'])
        
        return args
    
    def _generate_test_report(self):
        """Generate test execution report."""
        print("\n" + "="*50)
        print("TEST EXECUTION REPORT")
        print("="*50)
        
        total_suites = len(self.results)
        passed_suites = sum(1 for result in self.results.values() if result == 0)
        failed_suites = total_suites - passed_suites
        
        print(f"Total test suites: {total_suites}")
        print(f"Passed: {passed_suites}")
        print(f"Failed: {failed_suites}")
        
        if failed_suites > 0:
            print("\nFailed suites:")
            for suite_name, result in self.results.items():
                if result != 0:
                    print(f"  - {suite_name}: exit code {result}")
        
        print(f"\nOverall success rate: {passed_suites/total_suites*100:.1f}%")


# Performance test configuration
PERFORMANCE_CONFIG = {
    'database_operations': {
        'create_invoices': 1000,
        'create_payments': 500,
        'bulk_operations': 100,
        'max_response_time': 2.0  # seconds
    },
    'api_endpoints': {
        'max_response_time': 1.0,  # seconds
        'concurrent_requests': 50,
        'load_test_duration': 60  # seconds
    },
    'memory_usage': {
        'max_memory_mb': 100,
        'max_db_connections': 10
    }
}


class PerformanceMonitor:
    """Monitor performance during tests."""
    
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'db_connections': 0,
            'errors': []
        }
    
    def record_response_time(self, operation: str, duration: float):
        """Record response time for an operation."""
        self.metrics['response_times'].append({
            'operation': operation,
            'duration': duration,
            'timestamp': pytest.current_timestamp()
        })
    
    def record_memory_usage(self, usage_mb: float):
        """Record memory usage."""
        self.metrics['memory_usage'].append({
            'usage_mb': usage_mb,
            'timestamp': pytest.current_timestamp()
        })
    
    def record_error(self, error: str, context: str = None):
        """Record an error."""
        self.metrics['errors'].append({
            'error': error,
            'context': context,
            'timestamp': pytest.current_timestamp()
        })
    
    def generate_performance_report(self):
        """Generate performance report."""
        print("\n" + "="*50)
        print("PERFORMANCE REPORT")
        print("="*50)
        
        # Response time analysis
        if self.metrics['response_times']:
            response_times = [m['duration'] for m in self.metrics['response_times']]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"Response Times:")
            print(f"  Average: {avg_response_time:.3f}s")
            print(f"  Maximum: {max_response_time:.3f}s")
            print(f"  Minimum: {min_response_time:.3f}s")
            
            slow_operations = [
                m for m in self.metrics['response_times'] 
                if m['duration'] > PERFORMANCE_CONFIG['database_operations']['max_response_time']
            ]
            
            if slow_operations:
                print(f"\nSlow operations ({len(slow_operations)}):")
                for op in slow_operations[:5]:  # Show first 5
                    print(f"  - {op['operation']}: {op['duration']:.3f}s")
        
        # Memory usage analysis
        if self.metrics['memory_usage']:
            memory_usage = [m['usage_mb'] for m in self.metrics['memory_usage']]
            avg_memory = sum(memory_usage) / len(memory_usage)
            max_memory = max(memory_usage)
            
            print(f"\nMemory Usage:")
            print(f"  Average: {avg_memory:.1f}MB")
            print(f"  Maximum: {max_memory:.1f}MB")
            
            if max_memory > PERFORMANCE_CONFIG['memory_usage']['max_memory_mb']:
                print(f"  WARNING: Maximum memory usage exceeds limit!")
        
        # Error analysis
        if self.metrics['errors']:
            print(f"\nErrors: {len(self.metrics['errors'])}")
            for error in self.metrics['errors'][:5]:  # Show first 5
                print(f"  - {error['error']}")
                if error['context']:
                    print(f"    Context: {error['context']}")


# Test data validation
def validate_test_data():
    """Validate test data integrity."""
    print("\n" + "="*50)
    print("TEST DATA VALIDATION")
    print("="*50)
    
    # Check fixture files
    fixture_files = [
        'backend/services/finance/tests/fixtures.py',
        'frontend/tests/fixtures/finance-fixtures.ts'
    ]
    
    for fixture_file in fixture_files:
        if os.path.exists(fixture_file):
            print(f"✓ {fixture_file} exists")
        else:
            print(f"✗ {fixture_file} missing")
    
    # Check test files
    test_files = [
        'backend/services/finance/tests/test_crud.py',
        'backend/services/finance/tests/test_api.py',
        'backend/services/finance/tests/test_payment_integration.py',
        'frontend/components/finance/__tests__/FinanceDashboard.test.tsx',
        'frontend/components/finance/__tests__/InvoiceManagement.test.tsx',
        'frontend/tests/e2e/payment-flow.spec.ts'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✓ {test_file} exists")
        else:
            print(f"✗ {test_file} missing")
    
    print("\nTest data validation complete")


# Main test runner function
def run_finance_tests():
    """Main function to run all finance tests."""
    print("Starting Finance Module Test Suite")
    print("="*50)
    
    # Validate test data
    validate_test_data()
    
    # Run tests with coverage
    runner = TestRunner()
    success = runner.run_test_suite()
    
    if success:
        print("\n✓ All tests passed with sufficient coverage!")
        return 0
    else:
        print("\n✗ Tests failed or coverage insufficient!")
        return 1


if __name__ == "__main__":
    exit(run_finance_tests())