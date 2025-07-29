"""
Tests for API Documentation Routes
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.services.api_docs.routes import router


class TestDocumentationRoutes:
    """Test API documentation routes"""
    
    @pytest.fixture
    def app(self):
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        return {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "admin"
        }
    
    @pytest.fixture
    def mock_openapi_schema(self):
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "Test API description"
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {
                            "200": {
                                "description": "Success"
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
    
    def test_get_openapi_schema(self, client, mock_openapi_schema):
        """Test getting OpenAPI schema"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
            mock_generator_class.return_value = mock_generator
            
            response = client.get("/api/v1/docs/openapi.json")
            
            assert response.status_code == 200
            assert response.json() == mock_openapi_schema
    
    def test_get_openapi_schema_error(self, client):
        """Test OpenAPI schema error handling"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator_class.side_effect = Exception("Test error")
            
            response = client.get("/api/v1/docs/openapi.json")
            
            assert response.status_code == 500
            assert "Failed to generate API documentation" in response.json()["detail"]
    
    def test_get_openapi_yaml(self, client, mock_openapi_schema):
        """Test getting OpenAPI YAML"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
            mock_generator_class.return_value = mock_generator
            
            response = client.get("/api/v1/docs/openapi.yaml")
            
            assert response.status_code == 200
            assert "openapi: 3.0.0" in response.text
            assert "Test API" in response.text
    
    def test_get_swagger_ui(self, client):
        """Test Swagger UI endpoint"""
        response = client.get("/api/v1/docs/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "OneClass Platform API" in response.text
        assert "swagger-ui" in response.text
    
    def test_get_redoc(self, client):
        """Test ReDoc endpoint"""
        response = client.get("/api/v1/docs/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "OneClass Platform API" in response.text
        assert "redoc" in response.text
    
    def test_get_postman_collection(self, client):
        """Test Postman collection endpoint"""
        mock_collection = {
            "info": {
                "name": "Test API Collection",
                "version": "1.0.0"
            },
            "item": []
        }
        
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_postman_collection.return_value = mock_collection
            mock_generator_class.return_value = mock_generator
            
            response = client.get("/api/v1/docs/postman")
            
            assert response.status_code == 200
            assert response.json() == mock_collection
            assert "attachment" in response.headers["content-disposition"]
    
    def test_documentation_health(self, client, mock_openapi_schema):
        """Test documentation health endpoint"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
            mock_generator_class.return_value = mock_generator
            
            response = client.get("/api/v1/docs/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "API Documentation Generator"
            assert data["endpoints_documented"] == 1
            assert "OpenAPI JSON" in data["available_formats"]
    
    def test_documentation_health_error(self, client):
        """Test documentation health error"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator_class.side_effect = Exception("Health check failed")
            
            response = client.get("/api/v1/docs/health")
            
            assert response.status_code == 500
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "Health check failed" in data["error"]
    
    def test_generate_documentation_unauthorized(self, client):
        """Test generate documentation without authentication"""
        response = client.post("/api/v1/docs/generate")
        
        assert response.status_code == 401
    
    def test_generate_documentation_forbidden(self, client):
        """Test generate documentation with insufficient permissions"""
        mock_user = {
            "id": "user123",
            "username": "testuser",
            "role": "student"
        }
        
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.post("/api/v1/docs/generate")
            
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]
    
    def test_generate_documentation_json(self, client, mock_user, tmp_path):
        """Test generate documentation in JSON format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.save_schema_to_file = Mock()
                mock_generator_class.return_value = mock_generator
                
                with patch('backend.services.api_docs.routes.Path') as mock_path_class:
                    mock_path = Mock()
                    mock_path.mkdir = Mock()
                    mock_path_class.return_value = mock_path
                    
                    response = client.post("/api/v1/docs/generate?format=json")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] == True
                    assert data["format"] == "json"
                    assert data["generated_by"] == "testuser"
                    assert mock_generator.save_schema_to_file.called
    
    def test_generate_documentation_yaml(self, client, mock_user):
        """Test generate documentation in YAML format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.save_schema_to_file = Mock()
                mock_generator_class.return_value = mock_generator
                
                with patch('backend.services.api_docs.routes.Path') as mock_path_class:
                    mock_path = Mock()
                    mock_path.mkdir = Mock()
                    mock_path_class.return_value = mock_path
                    
                    response = client.post("/api/v1/docs/generate?format=yaml")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] == True
                    assert data["format"] == "yaml"
                    assert mock_generator.save_schema_to_file.called
    
    def test_generate_documentation_postman(self, client, mock_user):
        """Test generate documentation in Postman format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.save_postman_collection = Mock()
                mock_generator_class.return_value = mock_generator
                
                with patch('backend.services.api_docs.routes.Path') as mock_path_class:
                    mock_path = Mock()
                    mock_path.mkdir = Mock()
                    mock_path_class.return_value = mock_path
                    
                    response = client.post("/api/v1/docs/generate?format=postman")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] == True
                    assert data["format"] == "postman"
                    assert mock_generator.save_postman_collection.called
    
    def test_generate_documentation_invalid_format(self, client, mock_user):
        """Test generate documentation with invalid format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.post("/api/v1/docs/generate?format=invalid")
            
            assert response.status_code == 400
            assert "Invalid format" in response.json()["detail"]
    
    def test_get_documentation_stats(self, client, mock_user, mock_openapi_schema):
        """Test get documentation statistics"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
                mock_generator_class.return_value = mock_generator
                
                response = client.get("/api/v1/docs/stats")
                
                assert response.status_code == 200
                data = response.json()
                assert "total_endpoints" in data
                assert "methods_distribution" in data
                assert "tags_distribution" in data
                assert "components" in data
                assert "api_info" in data
    
    def test_refresh_documentation(self, client, mock_user, mock_openapi_schema):
        """Test refresh documentation cache"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
                mock_generator_class.return_value = mock_generator
                
                response = client.post("/api/v1/docs/refresh")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert data["message"] == "Documentation cache refreshed successfully"
                assert data["refreshed_by"] == "testuser"
    
    def test_refresh_documentation_forbidden(self, client):
        """Test refresh documentation with insufficient permissions"""
        mock_user = {
            "id": "user123",
            "username": "testuser",
            "role": "student"
        }
        
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.post("/api/v1/docs/refresh")
            
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]
    
    def test_export_documentation_json(self, client, mock_user, mock_openapi_schema):
        """Test export documentation in JSON format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
                mock_generator_class.return_value = mock_generator
                
                response = client.get("/api/v1/docs/export/json")
                
                assert response.status_code == 200
                data = response.json()
                assert data["filename"] == "oneclass-platform-api.json"
                assert data["content_type"] == "application/json"
                assert data["exported_by"] == "testuser"
                assert "attachment" in response.headers["content-disposition"]
    
    def test_export_documentation_yaml(self, client, mock_user, mock_openapi_schema):
        """Test export documentation in YAML format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate_openapi_schema.return_value = mock_openapi_schema
                mock_generator_class.return_value = mock_generator
                
                response = client.get("/api/v1/docs/export/yaml")
                
                assert response.status_code == 200
                data = response.json()
                assert data["filename"] == "oneclass-platform-api.yaml"
                assert data["content_type"] == "application/yaml"
                assert data["exported_by"] == "testuser"
    
    def test_export_documentation_postman(self, client, mock_user):
        """Test export documentation in Postman format"""
        mock_collection = {
            "info": {
                "name": "Test Collection",
                "version": "1.0.0"
            }
        }
        
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate_postman_collection.return_value = mock_collection
                mock_generator_class.return_value = mock_generator
                
                response = client.get("/api/v1/docs/export/postman")
                
                assert response.status_code == 200
                data = response.json()
                assert data["filename"] == "oneclass-platform-api.postman_collection.json"
                assert data["content_type"] == "application/json"
                assert data["exported_by"] == "testuser"
    
    def test_export_documentation_invalid_format(self, client, mock_user):
        """Test export documentation with invalid format"""
        with patch('backend.services.api_docs.routes.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/docs/export/invalid")
            
            assert response.status_code == 400
            assert "Invalid format" in response.json()["detail"]
    
    def test_swagger_ui_error_handling(self, client):
        """Test Swagger UI error handling"""
        with patch('backend.services.api_docs.routes.generate_custom_swagger_ui') as mock_swagger:
            mock_swagger.side_effect = Exception("Swagger error")
            
            response = client.get("/api/v1/docs/")
            
            assert response.status_code == 500
            assert "Failed to load documentation interface" in response.json()["detail"]
    
    def test_redoc_error_handling(self, client):
        """Test ReDoc error handling"""
        with patch('backend.services.api_docs.routes.generate_custom_redoc') as mock_redoc:
            mock_redoc.side_effect = Exception("ReDoc error")
            
            response = client.get("/api/v1/docs/redoc")
            
            assert response.status_code == 500
            assert "Failed to load documentation interface" in response.json()["detail"]
    
    def test_postman_collection_error_handling(self, client):
        """Test Postman collection error handling"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator_class.side_effect = Exception("Postman error")
            
            response = client.get("/api/v1/docs/postman")
            
            assert response.status_code == 500
            assert "Failed to generate Postman collection" in response.json()["detail"]
    
    def test_yaml_error_handling(self, client):
        """Test YAML generation error handling"""
        with patch('backend.services.api_docs.routes.OpenAPIGenerator') as mock_generator_class:
            mock_generator_class.side_effect = Exception("YAML error")
            
            response = client.get("/api/v1/docs/openapi.yaml")
            
            assert response.status_code == 500
            assert "Failed to generate OpenAPI YAML" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])