#!/usr/bin/env python3
"""
Multi-Tenant End-to-End Test Script
Tests the complete multi-tenant flow for the OneClass Platform
"""

import asyncio
import aiohttp
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Test configuration"""
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    test_school_subdomain: str = f"test-school-{uuid.uuid4().hex[:8]}"
    test_admin_email: str = f"admin-{uuid.uuid4().hex[:8]}@testschool.com"
    test_teacher_email: str = f"teacher-{uuid.uuid4().hex[:8]}@testschool.com"
    test_student_email: str = f"student-{uuid.uuid4().hex[:8]}@testschool.com"
    test_parent_email: str = f"parent-{uuid.uuid4().hex[:8]}@testschool.com"
    timeout: int = 30

class MultiTenantFlowTester:
    """End-to-end multi-tenant flow tester"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.school_id: Optional[str] = None
        self.admin_user_id: Optional[str] = None
        self.teacher_user_id: Optional[str] = None
        self.student_user_id: Optional[str] = None
        self.parent_user_id: Optional[str] = None
        self.admin_token: Optional[str] = None
        self.teacher_token: Optional[str] = None
        self.student_token: Optional[str] = None
        self.parent_token: Optional[str] = None
        self.test_results: List[Dict[str, Any]] = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Log test result with colored output"""
        status = f"{Fore.GREEN}✓ PASS" if success else f"{Fore.RED}✗ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s){Style.RESET_ALL}")
        if details:
            print(f"  {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_health_endpoints(self):
        """Test 1: Health check endpoints"""
        start_time = time.time()
        
        try:
            # Test main health endpoint
            async with self.session.get(f"{self.config.base_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
            
            # Test API health endpoint
            async with self.session.get(f"{self.config.base_url}/api/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
            
            # Test user management health endpoint
            async with self.session.get(f"{self.config.base_url}/api/v1/users/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
                assert "user_management" in data["service"]
            
            duration = time.time() - start_time
            self.log_test_result("Health Endpoints", True, "All health endpoints responding correctly", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Health Endpoints", False, f"Error: {str(e)}", duration)
    
    async def test_school_creation(self):
        """Test 2: School creation and tenant setup"""
        start_time = time.time()
        
        try:
            # Create school
            school_data = {
                "name": "Test School for E2E Testing",
                "subdomain": self.config.test_school_subdomain,
                "school_type": "secondary",
                "admin_email": self.config.test_admin_email,
                "admin_first_name": "Test",
                "admin_last_name": "Admin",
                "admin_password": "TestPass123!",
                "subscription_tier": "premium"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/platform/schools",
                json=school_data
            ) as response:
                assert response.status == 201
                data = await response.json()
                self.school_id = data["school"]["id"]
                self.admin_user_id = data["admin_user"]["id"]
                
            # Verify school resolution by subdomain
            async with self.session.get(
                f"{self.config.base_url}/api/v1/platform/schools/resolve/{self.config.test_school_subdomain}"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["subdomain"] == self.config.test_school_subdomain
                assert data["is_active"] == True
            
            duration = time.time() - start_time
            self.log_test_result("School Creation", True, f"School created with ID: {self.school_id}", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("School Creation", False, f"Error: {str(e)}", duration)
    
    async def test_admin_authentication(self):
        """Test 3: Admin authentication and token generation"""
        start_time = time.time()
        
        try:
            # Authenticate admin user
            auth_data = {
                "email": self.config.test_admin_email,
                "password": "TestPass123!"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/auth/login",
                json=auth_data,
                headers={"x-school-id": self.school_id}
            ) as response:
                assert response.status == 200
                data = await response.json()
                self.admin_token = data["access_token"]
                assert data["user"]["role"] == "school_admin"
            
            # Test token validation
            async with self.session.get(
                f"{self.config.base_url}/api/v1/auth/me",
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "x-school-id": self.school_id
                }
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["role"] == "school_admin"
                assert data["school_id"] == self.school_id
            
            duration = time.time() - start_time
            self.log_test_result("Admin Authentication", True, "Admin authenticated successfully", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Admin Authentication", False, f"Error: {str(e)}", duration)
    
    async def test_role_based_user_creation(self):
        """Test 4: Role-based user creation"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "x-school-id": self.school_id,
                "Content-Type": "application/json"
            }
            
            # Create teacher
            teacher_data = {
                "email": self.config.test_teacher_email,
                "first_name": "Test",
                "last_name": "Teacher",
                "role": "teacher",
                "department": "Mathematics",
                "position": "Math Teacher",
                "send_invitation": False,
                "password": "TestPass123!"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/users",
                json=teacher_data,
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                self.teacher_user_id = data["id"]
                assert data["role"] == "teacher"
            
            # Create student
            student_data = {
                "email": self.config.test_student_email,
                "first_name": "Test",
                "last_name": "Student",
                "role": "student",
                "grade_level": "10",
                "student_id": "ST001",
                "send_invitation": False,
                "password": "TestPass123!"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/users",
                json=student_data,
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                self.student_user_id = data["id"]
                assert data["role"] == "student"
            
            # Create parent
            parent_data = {
                "email": self.config.test_parent_email,
                "first_name": "Test",
                "last_name": "Parent",
                "role": "parent",
                "send_invitation": False,
                "password": "TestPass123!"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/users",
                json=parent_data,
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                self.parent_user_id = data["id"]
                assert data["role"] == "parent"
            
            # List users to verify creation
            async with self.session.get(
                f"{self.config.base_url}/api/v1/users",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["total"] >= 4  # admin + teacher + student + parent
            
            duration = time.time() - start_time
            self.log_test_result("Role-based User Creation", True, "All user types created successfully", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Role-based User Creation", False, f"Error: {str(e)}", duration)
    
    async def test_role_based_authentication(self):
        """Test 5: Role-based authentication for different user types"""
        start_time = time.time()
        
        try:
            users_to_test = [
                (self.config.test_teacher_email, "teacher"),
                (self.config.test_student_email, "student"),
                (self.config.test_parent_email, "parent")
            ]
            
            for email, expected_role in users_to_test:
                auth_data = {
                    "email": email,
                    "password": "TestPass123!"
                }
                
                async with self.session.post(
                    f"{self.config.base_url}/api/v1/auth/login",
                    json=auth_data,
                    headers={"x-school-id": self.school_id}
                ) as response:
                    assert response.status == 200
                    data = await response.json()
                    token = data["access_token"]
                    assert data["user"]["role"] == expected_role
                    
                    # Store tokens for later tests
                    if expected_role == "teacher":
                        self.teacher_token = token
                    elif expected_role == "student":
                        self.student_token = token
                    elif expected_role == "parent":
                        self.parent_token = token
            
            duration = time.time() - start_time
            self.log_test_result("Role-based Authentication", True, "All user roles authenticated successfully", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Role-based Authentication", False, f"Error: {str(e)}", duration)
    
    async def test_tenant_isolation(self):
        """Test 6: Tenant isolation and security"""
        start_time = time.time()
        
        try:
            # Create a second school for isolation testing
            second_school_data = {
                "name": "Second Test School",
                "subdomain": f"second-{uuid.uuid4().hex[:8]}",
                "school_type": "primary",
                "admin_email": f"admin2-{uuid.uuid4().hex[:8]}@testschool.com",
                "admin_first_name": "Second",
                "admin_last_name": "Admin",
                "admin_password": "TestPass123!",
                "subscription_tier": "basic"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/platform/schools",
                json=second_school_data
            ) as response:
                assert response.status == 201
                second_school_data = await response.json()
                second_school_id = second_school_data["school"]["id"]
            
            # Try to access first school's users with second school's context
            headers = {
                "Authorization": f"Bearer {self.teacher_token}",
                "x-school-id": second_school_id,  # Wrong school ID
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{self.config.base_url}/api/v1/users",
                headers=headers
            ) as response:
                # Should fail due to tenant isolation
                assert response.status in [401, 403]
            
            duration = time.time() - start_time
            self.log_test_result("Tenant Isolation", True, "Tenant isolation working correctly", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Tenant Isolation", False, f"Error: {str(e)}", duration)
    
    async def test_role_based_permissions(self):
        """Test 7: Role-based permissions and access control"""
        start_time = time.time()
        
        try:
            # Test teacher permissions - should be able to read users but not create admins
            teacher_headers = {
                "Authorization": f"Bearer {self.teacher_token}",
                "x-school-id": self.school_id,
                "Content-Type": "application/json"
            }
            
            # Teacher should be able to read users
            async with self.session.get(
                f"{self.config.base_url}/api/v1/users",
                headers=teacher_headers
            ) as response:
                assert response.status == 200
            
            # Teacher should NOT be able to create admin users
            admin_user_data = {
                "email": f"fake-admin-{uuid.uuid4().hex[:8]}@testschool.com",
                "first_name": "Fake",
                "last_name": "Admin",
                "role": "school_admin",
                "password": "TestPass123!"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/users",
                json=admin_user_data,
                headers=teacher_headers
            ) as response:
                assert response.status in [401, 403]  # Should be forbidden
            
            # Test student permissions - should have limited access
            student_headers = {
                "Authorization": f"Bearer {self.student_token}",
                "x-school-id": self.school_id,
                "Content-Type": "application/json"
            }
            
            # Student should NOT be able to create users
            async with self.session.post(
                f"{self.config.base_url}/api/v1/users",
                json=admin_user_data,
                headers=student_headers
            ) as response:
                assert response.status in [401, 403]  # Should be forbidden
            
            duration = time.time() - start_time
            self.log_test_result("Role-based Permissions", True, "Permission system working correctly", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Role-based Permissions", False, f"Error: {str(e)}", duration)
    
    async def test_user_invitations(self):
        """Test 8: User invitation system"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "x-school-id": self.school_id,
                "Content-Type": "application/json"
            }
            
            # Create invitation
            invitation_data = {
                "email": f"invited-{uuid.uuid4().hex[:8]}@testschool.com",
                "role": "teacher",
                "first_name": "Invited",
                "last_name": "Teacher",
                "department": "Science",
                "position": "Science Teacher",
                "expires_in_days": 7
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v1/users/invitations",
                json=invitation_data,
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                invitation_id = data["id"]
                assert data["status"] == "pending"
                assert data["role"] == "teacher"
            
            # List invitations
            async with self.session.get(
                f"{self.config.base_url}/api/v1/users/invitations",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert len(data) >= 1
                assert any(inv["id"] == invitation_id for inv in data)
            
            duration = time.time() - start_time
            self.log_test_result("User Invitations", True, "Invitation system working correctly", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("User Invitations", False, f"Error: {str(e)}", duration)
    
    async def test_profile_management(self):
        """Test 9: User profile management"""
        start_time = time.time()
        
        try:
            # Update teacher profile
            teacher_headers = {
                "Authorization": f"Bearer {self.teacher_token}",
                "x-school-id": self.school_id,
                "Content-Type": "application/json"
            }
            
            profile_data = {
                "address": "123 Test Street, Test City",
                "emergency_contact_name": "Emergency Contact",
                "emergency_contact_phone": "+1234567890",
                "qualifications": [
                    {"degree": "Bachelor of Mathematics", "institution": "Test University", "year": 2020}
                ]
            }
            
            async with self.session.put(
                f"{self.config.base_url}/api/v1/users/{self.teacher_user_id}/profile",
                json=profile_data,
                headers=teacher_headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["address"] == profile_data["address"]
                assert data["emergency_contact_name"] == profile_data["emergency_contact_name"]
            
            # Get updated profile
            async with self.session.get(
                f"{self.config.base_url}/api/v1/users/{self.teacher_user_id}/profile",
                headers=teacher_headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["address"] == profile_data["address"]
            
            duration = time.time() - start_time
            self.log_test_result("Profile Management", True, "Profile management working correctly", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Profile Management", False, f"Error: {str(e)}", duration)
    
    async def test_dashboard_access(self):
        """Test 10: Role-specific dashboard access"""
        start_time = time.time()
        
        try:
            # Test different dashboard access patterns
            dashboard_tests = [
                (self.admin_token, "admin", "/admin"),
                (self.teacher_token, "teacher", "/staff"),
                (self.student_token, "student", "/student"),
                (self.parent_token, "parent", "/parent")
            ]
            
            for token, role, expected_path in dashboard_tests:
                # Simulate dashboard access request
                headers = {
                    "Authorization": f"Bearer {token}",
                    "x-school-id": self.school_id,
                    "x-tenant-subdomain": self.config.test_school_subdomain
                }
                
                # Test API endpoint access for dashboard data
                async with self.session.get(
                    f"{self.config.base_url}/api/v1/auth/me",
                    headers=headers
                ) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data["role"] == role
                    # In a real frontend, this would determine dashboard routing
            
            duration = time.time() - start_time
            self.log_test_result("Dashboard Access", True, "Role-specific dashboard access working", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("Dashboard Access", False, f"Error: {str(e)}", duration)
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"{Fore.BLUE}🚀 Starting Multi-Tenant End-to-End Tests{Style.RESET_ALL}")
        print(f"📋 Test Configuration:")
        print(f"   Base URL: {self.config.base_url}")
        print(f"   School Subdomain: {self.config.test_school_subdomain}")
        print(f"   Admin Email: {self.config.test_admin_email}")
        print()
        
        test_methods = [
            self.test_health_endpoints,
            self.test_school_creation,
            self.test_admin_authentication,
            self.test_role_based_user_creation,
            self.test_role_based_authentication,
            self.test_tenant_isolation,
            self.test_role_based_permissions,
            self.test_user_invitations,
            self.test_profile_management,
            self.test_dashboard_access
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed with exception: {e}")
                self.log_test_result(test_method.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary"""
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        total_duration = sum(result["duration"] for result in self.test_results)
        
        print(f"\n{Fore.BLUE}📊 Test Summary{Style.RESET_ALL}")
        print(f"   Total Tests: {len(self.test_results)}")
        print(f"   {Fore.GREEN}Passed: {passed}")
        print(f"   {Fore.RED}Failed: {failed}")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Success Rate: {(passed/len(self.test_results)*100):.1f}%{Style.RESET_ALL}")
        
        if failed > 0:
            print(f"\n{Fore.RED}❌ Failed Tests:{Style.RESET_ALL}")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test_name']}: {result['details']}")
        else:
            print(f"\n{Fore.GREEN}🎉 All tests passed!{Style.RESET_ALL}")
        
        # Save results to file
        with open(f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📝 Test results saved to test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

async def main():
    """Main test runner"""
    config = TestConfig()
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.base_url}/health") as response:
                if response.status != 200:
                    print(f"{Fore.RED}❌ Server is not running at {config.base_url}{Style.RESET_ALL}")
                    return
    except aiohttp.ClientError:
        print(f"{Fore.RED}❌ Cannot connect to server at {config.base_url}{Style.RESET_ALL}")
        print("   Please ensure the backend server is running:")
        print("   cd backend && python main.py")
        return
    
    # Run tests
    async with MultiTenantFlowTester(config) as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())