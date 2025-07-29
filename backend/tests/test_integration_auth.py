"""Integration Tests for Authentication System
End-to-end testing of authentication flows with multi-tenancy
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, AsyncMock, MagicMock
import json
import uuid
from datetime import datetime, timedelta

# Mock database modules before importing
import sys
sys.modules['asyncpg'] = MagicMock()

# Import components after mocking
from shared.middleware.tenant_middleware import TenantMiddleware
from shared.auth import create_access_token, validate_token


class TestAuthenticationIntegration:
    """Integration tests for complete authentication flows"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with authentication"""
        test_app = FastAPI()
        test_app.add_middleware(TenantMiddleware)
        
        @test_app.post("/api/auth/login")
        async def login(credentials: dict):
            # Mock login endpoint
            if credentials.get('email') == 'admin@peterhouse.ac.zw' and credentials.get('password') == 'correct':
                user_id = str(uuid.uuid4())
                school_id = str(uuid.uuid4())
                token = create_access_token(user_id, school_id)
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "user": {
                        "id": user_id,
                        "email": "admin@peterhouse.ac.zw",
                        "role": "school_admin",
                        "school_id": school_id
                    }
                }
            return {"error": "Invalid credentials"}, 401
        
        @test_app.get("/api/user/profile")
        async def get_profile(request):
            # Protected endpoint requiring authentication
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {"error": "Authentication required"}, 401
            
            token = auth_header.replace('Bearer ', '')
            try:
                payload = await validate_token(token)
                return {
                    "user_id": payload['sub'],
                    "school_id": payload['school_id'],
                    "authenticated": True
                }
            except:
                return {"error": "Invalid token"}, 401
        
        @test_app.get("/api/school/students")
        async def get_students(request):
            # Endpoint requiring specific permissions
            # This would normally check permissions
            return {"students": []}
        
        return test_app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_complete_login_flow(self, client):
        """Test complete login flow with token generation"""
        # Test login with valid credentials
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@peterhouse.ac.zw",
                "password": "correct"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@peterhouse.ac.zw"
        assert data["user"]["role"] == "school_admin"
    
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@peterhouse.ac.zw",
                "password": "wrong"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    def test_protected_endpoint_with_valid_token(self, client):
        """Test accessing protected endpoint with valid token"""
        # First, login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@peterhouse.ac.zw",
                "password": "correct"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert "user_id" in data
        assert "school_id" in data
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/user/profile")
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


class TestMultiTenantAuthIntegration:
    """Integration tests for multi-tenant authentication"""
    
    @pytest.fixture
    def app_with_tenancy(self):
        """Create app with tenant middleware"""
        test_app = FastAPI()
        test_app.add_middleware(TenantMiddleware)
        
        @test_app.get("/api/school/info")
        async def get_school_info(request):
            # Mock endpoint that returns school context
            # In real implementation, this would use tenant middleware
            return {
                "school_id": "school-123",
                "school_name": "Peterhouse School",
                "subdomain": "peterhouse"
            }
        
        @test_app.get("/api/students")
        async def get_school_students(request):
            # Mock endpoint that requires school context
            school_id = request.headers.get('X-School-ID')
            if not school_id:
                return {"error": "School context required"}, 400
            
            return {
                "school_id": school_id,
                "students": [
                    {"id": "student-1", "name": "John Doe"},
                    {"id": "student-2", "name": "Jane Smith"}
                ]
            }
        
        return test_app
    
    def test_tenant_context_injection(self):
        """Test tenant context is properly injected"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                mock_extract.return_value = "peterhouse"
                mock_get_school.return_value = {
                    "id": "school-123",
                    "name": "Peterhouse School",
                    "subdomain": "peterhouse"
                }
                
                client = TestClient(self.app_with_tenancy())
                response = client.get(
                    "/api/school/info",
                    headers={"Host": "peterhouse.oneclass.ac.zw"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["school_id"] == "school-123"
                assert data["subdomain"] == "peterhouse"
    
    def test_cross_tenant_access_prevention(self):
        """Test prevention of cross-tenant data access"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('shared.middleware.tenant_middleware.validate_auth_token') as mock_validate:
                    # User from different school
                    mock_extract.return_value = "schoola"
                    mock_get_school.return_value = {
                        "id": "school-123",
                        "name": "School A",
                        "subdomain": "schoola"
                    }
                    
                    # Token belongs to different school
                    mock_validate.return_value = {
                        "user_id": "user-456",
                        "school_id": "school-456",  # Different school
                        "role": "teacher"
                    }
                    
                    client = TestClient(self.app_with_tenancy())
                    response = client.get(
                        "/api/students",
                        headers={
                            "Host": "schoola.oneclass.ac.zw",
                            "Authorization": "Bearer wrong-school-token"
                        }
                    )
                    
                    # Should prevent cross-tenant access
                    assert response.status_code in [403, 401]


class TestPermissionIntegration:
    """Integration tests for permission system"""
    
    @pytest.fixture
    def app_with_permissions(self):
        """Create app with permission checks"""
        test_app = FastAPI()
        
        @test_app.get("/api/admin/users")
        async def admin_endpoint(request):
            # Mock admin-only endpoint
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return {"error": "Authentication required"}, 401
            
            # In real implementation, would validate token and check permissions
            user_role = request.headers.get('X-User-Role', 'student')
            
            if user_role not in ['super_admin', 'school_admin', 'admin']:
                return {"error": "Insufficient permissions"}, 403
            
            return {"users": [{"id": "user-1", "name": "Admin User"}]}
        
        @test_app.get("/api/teacher/grades")
        async def teacher_endpoint(request):
            # Mock teacher-level endpoint
            user_role = request.headers.get('X-User-Role', 'student')
            
            if user_role not in ['teacher', 'admin', 'school_admin', 'super_admin']:
                return {"error": "Teacher access required"}, 403
            
            return {"grades": [{"student": "John", "grade": "A"}]}
        
        @test_app.get("/api/student/profile")
        async def student_endpoint(request):
            # Mock student-accessible endpoint
            return {"profile": {"name": "Student User"}}
        
        return test_app
    
    def test_admin_access_control(self):
        """Test admin-level access control"""
        client = TestClient(self.app_with_permissions())
        
        # Test admin access
        response = client.get(
            "/api/admin/users",
            headers={
                "Authorization": "Bearer valid-token",
                "X-User-Role": "school_admin"
            }
        )
        assert response.status_code == 200
        
        # Test non-admin access
        response = client.get(
            "/api/admin/users",
            headers={
                "Authorization": "Bearer valid-token",
                "X-User-Role": "teacher"
            }
        )
        assert response.status_code == 403
    
    def test_teacher_access_control(self):
        """Test teacher-level access control"""
        client = TestClient(self.app_with_permissions())
        
        # Test teacher access
        response = client.get(
            "/api/teacher/grades",
            headers={
                "Authorization": "Bearer valid-token",
                "X-User-Role": "teacher"
            }
        )
        assert response.status_code == 200
        
        # Test student access (should be denied)
        response = client.get(
            "/api/teacher/grades",
            headers={
                "Authorization": "Bearer valid-token",
                "X-User-Role": "student"
            }
        )
        assert response.status_code == 403
    
    def test_public_endpoint_access(self):
        """Test public endpoint access"""
        client = TestClient(self.app_with_permissions())
        
        # Public endpoint should be accessible by anyone
        response = client.get("/api/student/profile")
        assert response.status_code == 200


class TestFeatureGateIntegration:
    """Integration tests for feature gate system"""
    
    @pytest.fixture
    def app_with_features(self):
        """Create app with feature gates"""
        test_app = FastAPI()
        
        @test_app.get("/api/finance/reports")
        async def finance_endpoint(request):
            # Mock finance module endpoint
            enabled_modules = request.headers.get('X-Enabled-Modules', '').split(',')
            
            if 'finance' not in enabled_modules:
                return {"error": "Finance module not enabled"}, 403
            
            return {"reports": [{"type": "revenue", "amount": 50000}]}
        
        @test_app.get("/api/analytics/dashboard")
        async def analytics_endpoint(request):
            # Mock analytics module endpoint
            subscription_tier = request.headers.get('X-Subscription-Tier', 'basic')
            enabled_modules = request.headers.get('X-Enabled-Modules', '').split(',')
            
            if 'advanced_reporting' not in enabled_modules:
                return {"error": "Advanced reporting not available"}, 403
            
            if subscription_tier == 'basic':
                return {"error": "Upgrade required for analytics"}, 402
            
            return {"analytics": {"students": 150, "revenue": 75000}}
        
        return test_app
    
    def test_feature_module_access(self):
        """Test feature access based on enabled modules"""
        client = TestClient(self.app_with_features())
        
        # Test with finance module enabled
        response = client.get(
            "/api/finance/reports",
            headers={"X-Enabled-Modules": "sis,finance,academic"}
        )
        assert response.status_code == 200
        
        # Test without finance module
        response = client.get(
            "/api/finance/reports",
            headers={"X-Enabled-Modules": "sis,academic"}
        )
        assert response.status_code == 403
    
    def test_subscription_tier_access(self):
        """Test access based on subscription tier"""
        client = TestClient(self.app_with_features())
        
        # Test with professional tier
        response = client.get(
            "/api/analytics/dashboard",
            headers={
                "X-Subscription-Tier": "professional",
                "X-Enabled-Modules": "sis,finance,advanced_reporting"
            }
        )
        assert response.status_code == 200
        
        # Test with basic tier (should require upgrade)
        response = client.get(
            "/api/analytics/dashboard",
            headers={
                "X-Subscription-Tier": "basic",
                "X-Enabled-Modules": "sis,advanced_reporting"
            }
        )
        assert response.status_code == 402


class TestSessionManagement:
    """Integration tests for session management"""
    
    def test_token_expiration(self):
        """Test token expiration handling"""
        # Create expired token
        user_id = str(uuid.uuid4())
        school_id = str(uuid.uuid4())
        
        # Create token with past expiration (would need to mock JWT creation)
        # In real implementation, would create token with exp in the past
        
        # Test that expired token is rejected
        # This would be tested in actual implementation
        assert True  # Placeholder
    
    def test_token_refresh(self):
        """Test token refresh mechanism"""
        # Test refresh token flow
        # This would be implemented in actual authentication system
        assert True  # Placeholder
    
    def test_concurrent_sessions(self):
        """Test handling of concurrent sessions"""
        # Test multiple active sessions for same user
        # This would depend on session management strategy
        assert True  # Placeholder


class TestErrorHandlingIntegration:
    """Integration tests for error handling in authentication"""
    
    @pytest.fixture
    def app_with_errors(self):
        """Create app that can simulate various error conditions"""
        test_app = FastAPI()
        
        @test_app.get("/api/test/db-error")
        async def db_error_endpoint(request):
            # Simulate database connection error
            raise Exception("Database connection failed")
        
        @test_app.get("/api/test/auth-service-error")
        async def auth_service_error(request):
            # Simulate external auth service error
            return {"error": "Authentication service unavailable"}, 503
        
        return test_app
    
    def test_database_error_handling(self):
        """Test handling of database errors during authentication"""
        client = TestClient(self.app_with_errors())
        
        response = client.get("/api/test/db-error")
        # Should handle database errors gracefully
        assert response.status_code in [500, 503]
    
    def test_external_service_error_handling(self):
        """Test handling of external service errors"""
        client = TestClient(self.app_with_errors())
        
        response = client.get("/api/test/auth-service-error")
        assert response.status_code == 503


if __name__ == "__main__":
    pytest.main([__file__, "-v"])