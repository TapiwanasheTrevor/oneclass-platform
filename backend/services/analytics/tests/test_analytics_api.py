import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from services.analytics.routes.analytics import router as analytics_router
from services.analytics.routes.reports import router as reports_router
from shared.middleware.tenant_middleware import TenantContext

@pytest.fixture
def app():
    """Create test FastAPI app"""
    test_app = FastAPI()
    test_app.include_router(analytics_router)
    test_app.include_router(reports_router)
    return test_app

@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_tenant_context():
    """Mock tenant context"""
    return TenantContext(
        school_id="550e8400-e29b-41d4-a716-446655440001",
        school_name="Demo High School",
        school_code="DEMO",
        subscription_tier="professional",
        enabled_modules=["sis", "finance", "academic", "advanced_reporting"],
        school_settings={}
    )

@pytest.fixture
def mock_user_session():
    """Mock user session"""
    return MagicMock(
        user_id="550e8400-e29b-41d4-a716-446655440101",
        role="admin",
        permissions=["analytics:read", "analytics:write"]
    )

class TestAnalyticsAPI:
    """Test cases for Analytics API endpoints"""
    
    def test_analytics_overview_success(self, client, monkeypatch, mock_tenant_context, mock_user_session):
        """Test successful analytics overview retrieval"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.analytics.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.analytics.get_tenant_context", 
                          lambda request: mock_tenant_context)
        
        # Mock analytics service
        mock_service = AsyncMock()
        mock_overview = MagicMock()
        mock_overview.dict.return_value = {
            "school_id": mock_tenant_context.school_id,
            "period": "monthly",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "generated_at": datetime.utcnow().isoformat(),
            "student_metrics": {
                "total_students": {"value": 450, "change_percentage": 5.2, "trend": "up", "format": "number"},
                "active_students": {"value": 425, "change_percentage": 3.1, "trend": "up", "format": "number"},
                "attendance_rate": {"value": 87.5, "change_percentage": 2.1, "trend": "up", "format": "percentage"}
            },
            "academic_metrics": {
                "average_grade": {"value": 78.2, "change_percentage": 1.5, "trend": "up", "format": "percentage"},
                "pass_rate": {"value": 82.5, "change_percentage": 3.2, "trend": "up", "format": "percentage"}
            },
            "financial_metrics": {
                "total_revenue": {"value": 125000, "change_percentage": 8.5, "trend": "up", "format": "currency"},
                "collection_rate": {"value": 89.3, "change_percentage": 2.8, "trend": "up", "format": "percentage"}
            },
            "system_metrics": {
                "active_users": {"value": 380, "change_percentage": 12.1, "trend": "up", "format": "number"}
            },
            "insights": [
                {"type": "success", "title": "Improved Attendance", "message": "Student attendance has increased by 2.1%"}
            ],
            "recommendations": [
                {"priority": "medium", "category": "Academic", "action": "Continue monitoring performance", "expected_impact": "Maintain current trends"}
            ]
        }
        mock_service.get_analytics_overview.return_value = mock_overview
        monkeypatch.setattr("services.analytics.routes.analytics.analytics_service", mock_service)
        
        # Make request
        response = client.get("/api/v1/analytics/overview?period=monthly")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "student_metrics" in data
        assert "academic_metrics" in data
        assert "financial_metrics" in data
        assert "system_metrics" in data
        assert "insights" in data
        assert "recommendations" in data
        
        # Verify service was called correctly
        mock_service.get_analytics_overview.assert_called_once()
    
    def test_analytics_dashboard_success(self, client, monkeypatch, mock_tenant_context):
        """Test successful dashboard data retrieval"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.analytics.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.analytics.get_tenant_context", 
                          lambda request: mock_tenant_context)
        
        # Mock analytics service
        mock_service = AsyncMock()
        mock_overview = MagicMock()
        mock_overview.student_metrics.total_students.dict.return_value = {"value": 450, "trend": "up"}
        mock_overview.student_metrics.attendance_rate.dict.return_value = {"value": 87.5, "trend": "up"}
        mock_overview.academic_metrics.average_grade.dict.return_value = {"value": 78.2, "trend": "up"}
        mock_overview.financial_metrics.total_revenue.dict.return_value = {"value": 125000, "trend": "up"}
        mock_overview.insights = []
        mock_overview.recommendations = []
        mock_service.get_analytics_overview.return_value = mock_overview
        monkeypatch.setattr("services.analytics.routes.analytics.analytics_service", mock_service)
        
        # Make request
        response = client.get("/api/v1/analytics/dashboard?period=monthly")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["dashboard_id"] == "main_dashboard"
        assert "widgets" in data
        assert len(data["widgets"]) > 0
        assert "last_updated" in data
    
    def test_analytics_module_not_enabled(self, client, monkeypatch):
        """Test analytics when module is not enabled"""
        # Mock tenant context without analytics module
        mock_context = TenantContext(
            school_id="550e8400-e29b-41d4-a716-446655440001",
            school_name="Basic School",
            school_code="BASIC",
            subscription_tier="basic",
            enabled_modules=["sis"],  # No advanced_reporting
            school_settings={}
        )
        
        monkeypatch.setattr("services.analytics.routes.analytics.get_school_id", 
                          lambda request: mock_context.school_id)
        monkeypatch.setattr("services.analytics.routes.analytics.get_tenant_context", 
                          lambda request: mock_context)
        
        # Make request
        response = client.get("/api/v1/analytics/dashboard")
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "not enabled" in response.json()["detail"]
    
    def test_analytics_insights_success(self, client, monkeypatch, mock_tenant_context):
        """Test successful insights retrieval"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.analytics.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.analytics.get_tenant_context", 
                          lambda request: mock_tenant_context)
        
        # Make request
        response = client.get("/api/v1/analytics/insights?period=monthly")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "recommendations" in data
        assert "generated_at" in data
        assert "period" in data
    
    def test_analytics_test_endpoint(self, client, monkeypatch, mock_tenant_context):
        """Test analytics test endpoint"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.analytics.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.analytics.get_tenant_context", 
                          lambda request: mock_tenant_context)
        
        # Make request
        response = client.get("/api/v1/analytics/test")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "school_id" in data
        assert "enabled_modules" in data
        assert "subscription_tier" in data
    
    def test_analytics_export_endpoint(self, client, monkeypatch, mock_tenant_context):
        """Test analytics export endpoint"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.analytics.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        
        # Make request
        response = client.get("/api/v1/analytics/export?format=csv&period=monthly")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["status"] == "queued"
        assert data["format"] == "csv"
        assert "download_url" in data
        assert "expires_at" in data

class TestReportsAPI:
    """Test cases for Reports API endpoints"""
    
    def test_list_report_templates_success(self, client, monkeypatch, mock_tenant_context, mock_user_session):
        """Test successful report templates listing"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.reports.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.reports.get_user_session", 
                          lambda request: mock_user_session)
        
        # Mock database
        mock_db = AsyncMock()
        mock_db.fetch.return_value = [
            {
                "id": "a1000000-0000-0000-0000-000000000001",
                "name": "Student Performance Report",
                "description": "Academic performance analysis",
                "category": "academic",
                "report_type": "table",
                "is_public": True,
                "created_by": mock_user_session.user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        mock_db.fetchval.return_value = 1
        
        mock_db_manager = AsyncMock()
        mock_db_manager.get_connection.return_value.__aenter__.return_value = mock_db
        monkeypatch.setattr("services.analytics.routes.reports.db_manager", mock_db_manager)
        
        # Make request
        response = client.get("/api/v1/reports/templates")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert len(data["templates"]) == 1
        assert data["templates"][0]["name"] == "Student Performance Report"
    
    def test_create_report_template_success(self, client, monkeypatch, mock_tenant_context, mock_user_session):
        """Test successful report template creation"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.reports.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.reports.get_user_session", 
                          lambda request: mock_user_session)
        monkeypatch.setattr("services.analytics.routes.reports.get_tenant_context", 
                          lambda request: mock_tenant_context)
        
        # Mock database
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "id": "new-template-id",
            "name": "Test Report",
            "description": "Test Description",
            "category": "academic",
            "report_type": "table",
            "is_public": False,
            "created_by": mock_user_session.user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_db_manager = AsyncMock()
        mock_db_manager.get_connection.return_value.__aenter__.return_value = mock_db
        monkeypatch.setattr("services.analytics.routes.reports.db_manager", mock_db_manager)
        
        # Test data
        template_data = {
            "name": "Test Report",
            "description": "Test Description",
            "category": "academic",
            "report_type": "table",
            "data_sources": [{"source": "sis.students"}],
            "filters": {},
            "columns": [],
            "charts": [],
            "is_public": False,
            "allowed_roles": ["admin"]
        }
        
        # Make request
        response = client.post("/api/v1/reports/templates", json=template_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Report"
        assert data["category"] == "academic"
    
    def test_execute_report_success(self, client, monkeypatch, mock_tenant_context, mock_user_session):
        """Test successful report execution"""
        # Mock dependencies
        monkeypatch.setattr("services.analytics.routes.reports.get_school_id", 
                          lambda request: mock_tenant_context.school_id)
        monkeypatch.setattr("services.analytics.routes.reports.get_user_session", 
                          lambda request: mock_user_session)
        
        # Mock database
        mock_db = AsyncMock()
        mock_db.fetchrow.side_effect = [
            # Template query result
            {
                "id": "template-id",
                "name": "Test Template",
                "category": "academic",
                "data_sources": [{"source": "sis.students"}]
            },
            # Execution insert result
            {
                "id": "execution-id",
                "template_id": "template-id",
                "status": "pending",
                "execution_date": datetime.utcnow()
            }
        ]
        
        mock_db_manager = AsyncMock()
        mock_db_manager.get_connection.return_value.__aenter__.return_value = mock_db
        monkeypatch.setattr("services.analytics.routes.reports.db_manager", mock_db_manager)
        
        # Test data
        execution_data = {
            "template_id": "template-id",
            "parameters": {},
            "filters": {},
            "output_format": "json"
        }
        
        # Make request
        response = client.post("/api/v1/reports/execute", json=execution_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["template_id"] == "template-id"
        assert data["status"] == "pending"
    
    def test_report_categories_endpoint(self, client):
        """Test report categories endpoint"""
        # Make request
        response = client.get("/api/v1/reports/categories")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        categories = data["categories"]
        assert len(categories) > 0
        
        # Check expected categories
        category_ids = [cat["id"] for cat in categories]
        assert "academic" in category_ids
        assert "financial" in category_ids
        assert "administrative" in category_ids
        assert "analytics" in category_ids
        assert "custom" in category_ids
    
    def test_module_not_enabled_for_reports(self, client, monkeypatch, mock_user_session):
        """Test reports when module is not enabled"""
        # Mock tenant context without analytics module
        mock_context = TenantContext(
            school_id="550e8400-e29b-41d4-a716-446655440001",
            school_name="Basic School",
            school_code="BASIC",
            subscription_tier="basic",
            enabled_modules=["sis"],  # No advanced_reporting
            school_settings={}
        )
        
        monkeypatch.setattr("services.analytics.routes.reports.get_school_id", 
                          lambda request: mock_context.school_id)
        monkeypatch.setattr("services.analytics.routes.reports.get_user_session", 
                          lambda request: mock_user_session)
        monkeypatch.setattr("services.analytics.routes.reports.get_tenant_context", 
                          lambda request: mock_context)
        
        # Test data
        template_data = {
            "name": "Test Report",
            "category": "academic",
            "report_type": "table",
            "data_sources": [{"source": "sis.students"}],
            "filters": {},
            "columns": [],
            "charts": [],
            "is_public": False,
            "allowed_roles": ["admin"]
        }
        
        # Make request
        response = client.post("/api/v1/reports/templates", json=template_data)
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "not enabled" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])