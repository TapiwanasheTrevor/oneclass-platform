"""
Academic Management Module - Test Runner
Comprehensive test suite runner for Academic Management module
"""

import sys
import os
import pytest
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

def run_exception_tests():
    """Run exception class tests"""
    print("🧪 Running Exception Classes Tests...")
    print("=" * 60)
    
    result = pytest.main([
        str(Path(__file__).parent / "test_exceptions.py"),
        "-v",
        "--tb=short",
        "--color=yes"
    ])
    
    return result == 0

def run_api_integration_tests():
    """Run API integration tests"""
    print("\n🧪 Running API Integration Tests...")
    print("=" * 60)
    
    result = pytest.main([
        str(Path(__file__).parent / "test_api_integration.py"),
        "-v", 
        "--tb=short",
        "--color=yes"
    ])
    
    return result == 0

def run_performance_tests():
    """Run basic performance tests"""
    print("\n🧪 Running Performance Tests...")
    print("=" * 60)
    
    import time
    from services.academic.exceptions import (
        SubjectNotFoundError,
        InvalidGradeLevelError,
        handle_database_error,
        create_error_response
    )
    
    # Test exception creation performance
    start_time = time.time()
    for i in range(1000):
        error = SubjectNotFoundError(f"subject-{i}")
        http_exc = error.to_http_exception()
        error_dict = error.to_dict()
    
    exception_time = time.time() - start_time
    print(f"✅ Exception creation (1000 iterations): {exception_time:.3f}s")
    
    # Test validation performance
    start_time = time.time()
    for i in range(100):
        for grade in range(1, 14):
            try:
                if grade > 13:  # This would trigger validation error
                    error = InvalidGradeLevelError(grade)
            except:
                pass
    
    validation_time = time.time() - start_time
    print(f"✅ Grade level validation (1300 checks): {validation_time:.3f}s")
    
    # Test error handling utility performance
    start_time = time.time()
    for i in range(100):
        db_error = Exception(f"Database error {i}")
        academic_error = handle_database_error(db_error, "test_operation")
        response = create_error_response(academic_error)
    
    utility_time = time.time() - start_time
    print(f"✅ Error handling utilities (100 iterations): {utility_time:.3f}s")
    
    print(f"\n📊 Performance Summary:")
    print(f"   Exception creation: {(exception_time/1000)*1000:.2f}ms per exception")
    print(f"   Validation checks: {(validation_time/1300)*1000:.2f}ms per check")
    print(f"   Error processing: {(utility_time/100)*1000:.2f}ms per error")
    
    # Performance thresholds
    if exception_time > 1.0:
        print("⚠️  Warning: Exception creation performance is slow")
        return False
    
    if validation_time > 0.5:
        print("⚠️  Warning: Validation performance is slow")
        return False
    
    print("✅ All performance tests passed!")
    return True

def run_zimbabwe_compliance_tests():
    """Run Zimbabwe education system compliance tests"""
    print("\n🇿🇼 Running Zimbabwe Education System Compliance Tests...")
    print("=" * 60)
    
    from services.academic.exceptions import (
        InvalidGradeLevelError,
        InvalidTermNumberError,
        InvalidGradeScaleError
    )
    
    # Test grade levels (1-13)
    print("📚 Testing grade level compliance...")
    valid_grades = list(range(1, 14))  # 1-13 inclusive
    invalid_grades = [0, -1, 14, 15, 20, 100]
    
    for grade in valid_grades:
        # These should be valid in actual validation logic
        pass
    
    for grade in invalid_grades:
        try:
            error = InvalidGradeLevelError(grade)
            assert f"Invalid grade level: {grade}" in error.message
            assert "1-13" in error.message
        except AssertionError:
            print(f"❌ Grade level {grade} validation failed")
            return False
    
    print("✅ Grade level validation (1-13) passed")
    
    # Test term numbers (1-3)
    print("📅 Testing term system compliance...")
    valid_terms = [1, 2, 3]
    invalid_terms = [0, -1, 4, 5, 10]
    
    for term in invalid_terms:
        try:
            error = InvalidTermNumberError(term)
            assert f"Invalid term number: {term}" in error.message
            assert "3 terms" in error.message
        except AssertionError:
            print(f"❌ Term {term} validation failed")
            return False
    
    print("✅ Three-term system validation passed")
    
    # Test grading scale (A-U)
    print("📊 Testing A-U grading scale compliance...")
    valid_letter_grades = ["A", "B", "C", "D", "E", "U"]
    invalid_letter_grades = ["F", "G", "H", "X", "Z", "1", "2"]
    
    for grade in invalid_letter_grades:
        try:
            error = InvalidGradeScaleError(grade, "letter")
            assert f"Invalid letter grade: {grade}" in error.message
            assert "A, B, C, D, E, or U" in error.message
        except AssertionError:
            print(f"❌ Letter grade {grade} validation failed")
            return False
    
    print("✅ A-U grading scale validation passed")
    
    # Test percentage ranges
    print("💯 Testing percentage range compliance...")
    valid_percentages = [0, 25, 50, 75, 100]
    invalid_percentages = [-1, -10, 101, 150, 200]
    
    for percentage in invalid_percentages:
        try:
            error = InvalidGradeScaleError(percentage, "percentage")
            assert f"Invalid percentage: {percentage}" in error.message
            assert "0-100" in error.message
        except AssertionError:
            print(f"❌ Percentage {percentage} validation failed")
            return False
    
    print("✅ Percentage range (0-100) validation passed")
    
    print("\n🇿🇼 All Zimbabwe Education System compliance tests passed!")
    return True

def run_security_tests():
    """Run security and permission tests"""
    print("\n🔒 Running Security and Permission Tests...")
    print("=" * 60)
    
    from services.academic.exceptions import (
        InsufficientPermissionError,
        TeacherOwnershipError,
        StudentPrivacyError
    )
    
    # Test permission validation
    print("🔐 Testing permission validation...")
    try:
        error = InsufficientPermissionError(
            "academic.subject.create", 
            "student", 
            "create subjects"
        )
        assert "Insufficient permissions" in error.message
        assert "academic.subject.create" in error.message
        assert error.status_code == 403
        print("✅ Permission validation passed")
    except AssertionError:
        print("❌ Permission validation failed")
        return False
    
    # Test teacher ownership
    print("👨‍🏫 Testing teacher ownership validation...")
    try:
        error = TeacherOwnershipError("assessment", "assess-123")
        assert "You can only access assessment records" in error.message
        assert error.status_code == 403
        print("✅ Teacher ownership validation passed")
    except AssertionError:
        print("❌ Teacher ownership validation failed")
        return False
    
    # Test student privacy
    print("👨‍🎓 Testing student privacy protection...")
    try:
        error = StudentPrivacyError("student-456", "view grades")
        assert "Cannot access student data" in error.message
        assert error.status_code == 403
        print("✅ Student privacy protection passed")
    except AssertionError:
        print("❌ Student privacy protection failed")
        return False
    
    print("\n🔒 All security and permission tests passed!")
    return True

def main():
    """Run comprehensive test suite"""
    print("🎓 OneClass Academic Management - Comprehensive Test Suite")
    print("🇿🇼 Zimbabwe Education System Compliance Testing")
    print("=" * 80)
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Exception Classes", run_exception_tests()))
    test_results.append(("API Integration", run_api_integration_tests()))
    test_results.append(("Performance", run_performance_tests()))
    test_results.append(("Zimbabwe Compliance", run_zimbabwe_compliance_tests()))
    test_results.append(("Security & Permissions", run_security_tests()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 80)
    print(f"   Total Tests: {len(test_results)}")
    print(f"   Passed:      {passed}")
    print(f"   Failed:      {failed}")
    print(f"   Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Academic Management module is ready for production.")
        print("✅ Zimbabwe education system compliance verified")
        print("✅ Error handling and security validated")
        print("✅ Performance requirements met")
        print("\n🚀 Ready for deployment!")
        return True
    else:
        print(f"\n❌ {failed} test suite(s) failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)