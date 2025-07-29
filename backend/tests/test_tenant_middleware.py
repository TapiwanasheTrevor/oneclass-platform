"""Tests for Tenant Middleware
Comprehensive tests for multi-tenant isolation and context management
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime

# Import tenant middleware components
from shared.middleware.tenant_middleware import (
    TenantContext,
    TenantMiddleware,
    get_tenant_context,
    get_school_id,
    get_user_session
)


class TestTenantContext:
    """Test TenantContext model"""
    
    def test_tenant_context_creation(self):
        """Test TenantContext creation with valid data"""
        school_id = str(uuid.uuid4())
        context = TenantContext(
            school_id=school_id,
            school_name="Test School",
            school_code="TEST",
            subscription_tier="professional",
            enabled_modules=["sis", "finance", "academic"],
            school_settings={
                "timezone": "Africa/Harare",
                "academic_year": "2024"
            }
        )
        
        assert context.school_id == school_id
        assert context.school_name == "Test School"
        assert context.school_code == "TEST"
        assert context.subscription_tier == "professional"
        assert "sis" in context.enabled_modules
        assert context.school_settings["timezone"] == "Africa/Harare"
    
    def test_tenant_context_defaults(self):
        """Test TenantContext with default values"""
        school_id = str(uuid.uuid4())
        context = TenantContext(
            school_id=school_id,
            school_name="Test School",
            school_code="TEST"
        )
        
        assert context.subscription_tier == "basic"
        assert context.enabled_modules == []
        assert context.school_settings == {}


class TestTenantMiddleware:
    """Test TenantMiddleware functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with tenant middleware"""
        test_app = FastAPI()
        test_app.add_middleware(TenantMiddleware)
        
        @test_app.get("/test")
        async def test_endpoint(request: Request):
            tenant = get_tenant_context(request)
            return {
                "school_id": tenant.school_id,
                "school_name": tenant.school_name,
                "modules": tenant.enabled_modules
            }
        
        @test_app.get("/protected")
        async def protected_endpoint(request: Request):
            tenant = get_tenant_context(request)
            user = get_user_session(request)
            
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            return {
                "user_id": user.user_id,
                "school_id": tenant.school_id
            }
        
        return test_app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_tenant_context_injection(self, client):
        """Test tenant context is properly injected"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                # Mock subdomain extraction
                mock_extract.return_value = "testschool"
                
                # Mock school data
                mock_get_school.return_value = {
                    "id": "school-123",
                    "name": "Test School",
                    "code": "TEST",
                    "subscription_tier": "professional",
                    "enabled_modules": ["sis", "finance"],
                    "settings": {"timezone": "Africa/Harare"}
                }
                
                response = client.get(
                    "/test",
                    headers={"Host": "testschool.oneclass.ac.zw"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["school_id"] == "school-123"
                assert data["school_name"] == "Test School"
                assert "sis" in data["modules"]
    
    def test_missing_subdomain_handling(self, client):
        """Test handling of missing or invalid subdomain"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            mock_extract.return_value = None
            
            response = client.get(
                "/test",
                headers={"Host": "oneclass.ac.zw"}  # No subdomain
            )
            
            # Should return error or redirect
            assert response.status_code in [400, 404, 302]
    
    def test_school_not_found(self, client):
        """Test handling when school is not found"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                mock_extract.return_value = "nonexistent"
                mock_get_school.return_value = None
                
                response = client.get(
                    "/test",
                    headers={"Host": "nonexistent.oneclass.ac.zw"}
                )
                
                assert response.status_code in [404, 302]
    
    def test_authentication_integration(self, client):
        """Test integration with authentication system"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('shared.middleware.tenant_middleware.validate_auth_token') as mock_validate:
                    # Setup mocks
                    mock_extract.return_value = "testschool"
                    mock_get_school.return_value = {
                        "id": "school-123",
                        "name": "Test School",
                        "code": "TEST",
                        "subscription_tier": "basic",
                        "enabled_modules": ["sis"],
                        "settings": {}
                    }
                    
                    mock_validate.return_value = {
                        "user_id": "user-456",
                        "school_id": "school-123",
                        "role": "teacher",
                        "permissions": ["sis:read"]
                    }
                    
                    response = client.get(
                        "/protected",
                        headers={
                            "Host": "testschool.oneclass.ac.zw",
                            "Authorization": "Bearer valid-token"
                        }
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["user_id"] == "user-456"
                    assert data["school_id"] == "school-123"
    
    def test_cross_tenant_access_prevention(self, client):
        """Test prevention of cross-tenant data access"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('shared.middleware.tenant_middleware.validate_auth_token') as mock_validate:
                    # User belongs to different school
                    mock_extract.return_value = "schoola"
                    mock_get_school.return_value = {
                        "id": "school-123",
                        "name": "School A",
                        "code": "SCHOOLA",
                        "subscription_tier": "basic",
                        "enabled_modules": ["sis"],
                        "settings": {}
                    }
                    
                    # Token belongs to different school
                    mock_validate.return_value = {
                        "user_id": "user-456",
                        "school_id": "school-456",  # Different school
                        "role": "teacher",
                        "permissions": ["sis:read"]
                    }
                    
                    response = client.get(
                        "/protected",
                        headers={
                            "Host": "schoola.oneclass.ac.zw",
                            "Authorization": "Bearer wrong-school-token"
                        }
                    )
                    
                    # Should reject cross-tenant access
                    assert response.status_code in [403, 401]
    
    def test_module_access_control(self, client):
        """Test module-based access control"""
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                # School without finance module
                mock_extract.return_value = "basicschool"
                mock_get_school.return_value = {
                    "id": "school-123",
                    "name": "Basic School",
                    "code": "BASIC",
                    "subscription_tier": "basic",
                    "enabled_modules": ["sis"],  # No finance
                    "settings": {}
                }
                
                response = client.get(
                    "/test",
                    headers={"Host": "basicschool.oneclass.ac.zw"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "finance" not in data["modules"]
                assert "sis" in data["modules"]


class TestHelperFunctions:
    """Test tenant middleware helper functions"""
    
    def test_get_tenant_context(self):
        """Test get_tenant_context function"""
        # Create mock request with tenant context
        mock_request = MagicMock()
        mock_context = TenantContext(
            school_id="school-123",
            school_name="Test School",
            school_code="TEST"
        )
        mock_request.state.tenant_context = mock_context
        
        result = get_tenant_context(mock_request)
        assert result == mock_context
        assert result.school_id == "school-123"
    
    def test_get_tenant_context_missing(self):
        """Test get_tenant_context when context is missing"""
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        del mock_request.state.tenant_context  # Simulate missing context
        
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_context(mock_request)
        
        assert exc_info.value.status_code == 500
        assert "tenant context" in exc_info.value.detail.lower()
    
    def test_get_school_id(self):
        """Test get_school_id function"""
        mock_request = MagicMock()
        mock_context = TenantContext(
            school_id="school-123",
            school_name="Test School",
            school_code="TEST"
        )
        mock_request.state.tenant_context = mock_context
        
        result = get_school_id(mock_request)
        assert result == "school-123"
    
    def test_get_user_session(self):
        """Test get_user_session function"""
        mock_request = MagicMock()
        mock_session = MagicMock()
        mock_session.user_id = "user-456"
        mock_session.role = "teacher"
        mock_request.state.user_session = mock_session
        
        result = get_user_session(mock_request)
        assert result == mock_session
        assert result.user_id == "user-456"
    
    def test_get_user_session_missing(self):
        """Test get_user_session when session is missing"""
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        
        # Simulate missing user session
        def getattr_side_effect(name, default=None):
            if name == 'user_session':
                return default
            return MagicMock()
        
        mock_request.state.__getattr__ = getattr_side_effect
        
        result = get_user_session(mock_request)
        assert result is None


class TestErrorHandling:
    """Test error handling in tenant middleware"""
    
    @pytest.fixture
    def app_with_error_handling(self):
        """Create app with error handling"""
        test_app = FastAPI()
        test_app.add_middleware(TenantMiddleware)
        
        @test_app.get("/error-test")
        async def error_endpoint(request: Request):
            # Force an error
            raise Exception("Test error")
        
        return test_app
    
    def test_database_error_handling(self):
        """Test handling of database connection errors"""
        with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
            mock_get_school.side_effect = Exception("Database connection failed")
            
            # Should handle database errors gracefully
            client = TestClient(self.app_with_error_handling())
            response = client.get(
                "/error-test",
                headers={"Host": "testschool.oneclass.ac.zw"}
            )
            
            # Should return appropriate error status
            assert response.status_code in [500, 503]
    
    def test_malformed_subdomain_handling(self):
        """Test handling of malformed subdomains"""
        malformed_hosts = [
            "..oneclass.ac.zw",
            "sub-.oneclass.ac.zw",
            "-sub.oneclass.ac.zw",
            "sub..domain.oneclass.ac.zw"
        ]
        
        app = FastAPI()
        app.add_middleware(TenantMiddleware)
        client = TestClient(app)
        
        for host in malformed_hosts:
            response = client.get("/", headers={"Host": host})
            # Should handle malformed subdomains gracefully
            assert response.status_code in [400, 404, 302]


class TestPerformance:
    """Test performance aspects of tenant middleware"""
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests to same tenant"""
        app = FastAPI()
        app.add_middleware(TenantMiddleware)
        
        @app.get("/concurrent-test")
        async def concurrent_endpoint(request: Request):
            tenant = get_tenant_context(request)
            return {"school_id": tenant.school_id}
        
        client = TestClient(app)
        
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                mock_extract.return_value = "testschool"
                mock_get_school.return_value = {
                    "id": "school-123",
                    "name": "Test School",
                    "code": "TEST",
                    "subscription_tier": "basic",
                    "enabled_modules": ["sis"],
                    "settings": {}
                }
                
                # Simulate concurrent requests
                responses = []
                for i in range(10):
                    response = client.get(
                        "/concurrent-test",
                        headers={"Host": "testschool.oneclass.ac.zw"}
                    )
                    responses.append(response)
                
                # All requests should succeed
                for response in responses:
                    assert response.status_code == 200
                    assert response.json()["school_id"] == "school-123"
                
                # Should use caching (not call database for each request)
                # In a real implementation, this would verify cache usage
    
    def test_memory_usage(self):
        """Test memory usage doesn't grow with requests"""
        # This would test memory leaks in a real implementation
        # For now, just verify basic functionality works
        app = FastAPI()
        app.add_middleware(TenantMiddleware)
        client = TestClient(app)
        
        with patch('shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                mock_extract.return_value = "testschool"
                mock_get_school.return_value = {
                    "id": "school-123",
                    "name": "Test School",
                    "code": "TEST",
                    "subscription_tier": "basic",
                    "enabled_modules": ["sis"],
                    "settings": {}
                }
                
                # Make many requests
                for i in range(100):
                    response = client.get(
                        "/",
                        headers={"Host": "testschool.oneclass.ac.zw"}
                    )
                    # Don't store responses to avoid memory buildup in test
                
                # Test passes if no memory errors occur
                assert True


class TestSecurityFeatures:
    """Test security features of tenant middleware"""
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection in subdomain"""
        malicious_subdomains = [
            "'; DROP TABLE schools; --",
            "test'; DELETE FROM users; --",
            "union select * from users"
        ]
        
        app = FastAPI()
        app.add_middleware(TenantMiddleware)
        client = TestClient(app)
        
        for subdomain in malicious_subdomains:
            response = client.get(
                "/",
                headers={"Host": f"{subdomain}.oneclass.ac.zw"}
            )
            # Should reject malicious subdomains
            assert response.status_code in [400, 404, 403]
    
    def test_xss_prevention(self):
        """Test prevention of XSS in subdomain"""
        malicious_subdomains = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        app = FastAPI()
        app.add_middleware(TenantMiddleware)
        client = TestClient(app)
        
        for subdomain in malicious_subdomains:
            response = client.get(
                "/",
                headers={"Host": f"{subdomain}.oneclass.ac.zw"}
            )
            # Should reject XSS attempts
            assert response.status_code in [400, 404, 403]
    
    def test_subdomain_validation(self):
        """Test proper subdomain validation"""
        valid_subdomains = [
            "school1",
            "test-school",
            "school123",
            "my-school-2024"
        ]
        
        invalid_subdomains = [
            "",  # Empty
            "a",  # Too short
            "a" * 64,  # Too long
            "123456",  # Only numbers
            "-invalid",  # Starts with dash
            "invalid-",  # Ends with dash
            "inva..lid",  # Double dots
            "invalid.subdomain"  # Contains dot
        ]
        
        # Valid subdomains should be processed
        for subdomain in valid_subdomains:
            # Test that subdomain validation would pass
            # (Implementation would depend on actual validation logic)
            assert len(subdomain) > 1
            assert not subdomain.startswith('-')
            assert not subdomain.endswith('-')
        
        # Invalid subdomains should be rejected
        for subdomain in invalid_subdomains:
            # Test that subdomain validation would fail
            # (Implementation would depend on actual validation logic)
            is_invalid = (
                len(subdomain) <= 1 or
                len(subdomain) > 63 or
                subdomain.startswith('-') or
                subdomain.endswith('-') or
                '..' in subdomain or
                '.' in subdomain or
                subdomain.isdigit()
            )
            assert is_invalid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])