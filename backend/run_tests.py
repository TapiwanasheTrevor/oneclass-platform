#!/usr/bin/env python3
"""
Test runner for OneClass Platform
"""
import os
import sys
import subprocess

def run_tests():
    """Run all tests and display results"""
    print("🧪 Running OneClass Platform Tests...")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ["JWT_SECRET"] = "test-secret-key"
    os.environ["USE_LOCAL_STORAGE"] = "true"
    os.environ["LOCAL_STORAGE_PATH"] = "./test_storage"
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ]
    
    result = subprocess.run(cmd)
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)