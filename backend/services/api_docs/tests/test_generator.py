"""
Tests for OpenAPI Documentation Generator
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi import FastAPI

from backend.services.api_docs.generator import OpenAPIGenerator, generate_custom_swagger_ui, generate_custom_redoc
from backend.services.api_docs.markdown_generator import MarkdownGenerator, generate_markdown_docs


class TestOpenAPIGenerator:
    """Test OpenAPI generator functionality"""
    
    @pytest.fixture
    def mock_app(self):
        app = FastAPI(title="Test API", version="1.0.0")
        
        @app.get("/test")
        async def test_endpoint():
            """Test endpoint"""
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def generator(self, mock_app):
        return OpenAPIGenerator(mock_app)
    
    def test_generator_initialization(self, generator):
        """Test generator initialization"""
        assert generator.title == "OneClass Platform API"
        assert generator.version == "1.0.0"
        assert generator.base_url == "https://api.oneclass.ac.zw"
        assert generator.contact_info["name"] == "OneClass Platform Team"
        assert generator.license_info["name"] == "MIT"
    
    def test_generate_openapi_schema(self, generator):
        """Test OpenAPI schema generation"""
        schema = generator.generate_openapi_schema()
        
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        assert "tags" in schema
        assert "servers" in schema
        
        # Check info section
        info = schema["info"]
        assert info["title"] == "OneClass Platform API"
        assert info["version"] == "1.0.0"
        assert "description" in info
        assert "contact" in info
        assert "license" in info
        
        # Check servers
        servers = schema["servers"]
        assert len(servers) == 3
        assert servers[0]["url"] == "https://api.oneclass.ac.zw"
        assert servers[1]["url"] == "https://staging-api.oneclass.ac.zw"
        assert servers[2]["url"] == "http://localhost:8000"
    
    def test_security_schemes(self, generator):
        """Test security schemes generation"""
        schema = generator.generate_openapi_schema()
        security_schemes = schema["components"]["securitySchemes"]
        
        assert "BearerAuth" in security_schemes
        assert "ApiKeyAuth" in security_schemes
        assert "OAuth2" in security_schemes
        
        # Check BearerAuth
        bearer_auth = security_schemes["BearerAuth"]
        assert bearer_auth["type"] == "http"
        assert bearer_auth["scheme"] == "bearer"
        assert bearer_auth["bearerFormat"] == "JWT"
        
        # Check ApiKeyAuth
        api_key_auth = security_schemes["ApiKeyAuth"]
        assert api_key_auth["type"] == "apiKey"
        assert api_key_auth["in"] == "header"
        assert api_key_auth["name"] == "X-API-Key"
        
        # Check OAuth2
        oauth2 = security_schemes["OAuth2"]
        assert oauth2["type"] == "oauth2"
        assert "flows" in oauth2
        assert "authorizationCode" in oauth2["flows"]
    
    def test_api_tags(self, generator):
        """Test API tags generation"""
        schema = generator.generate_openapi_schema()
        tags = schema["tags"]
        
        tag_names = [tag["name"] for tag in tags]
        expected_tags = [
            "Authentication", "Users", "Schools", "Students", "Teachers",
            "Classes", "Grades", "Attendance", "Finance", "Analytics",
            "Mobile", "SSO", "Domains", "Notifications", "Integrations", "System"
        ]
        
        for expected_tag in expected_tags:
            assert expected_tag in tag_names
    
    def test_save_schema_to_file(self, generator, tmp_path):
        """Test saving schema to file"""
        json_file = tmp_path / "test_schema.json"
        yaml_file = tmp_path / "test_schema.yaml"
        
        # Save JSON format
        generator.save_schema_to_file(str(json_file), "json")
        assert json_file.exists()
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert "openapi" in data
            assert data["info"]["title"] == "OneClass Platform API"
        
        # Save YAML format
        generator.save_schema_to_file(str(yaml_file), "yaml")
        assert yaml_file.exists()
        
        # Verify YAML content
        with open(yaml_file, 'r') as f:
            content = f.read()
            assert "openapi:" in content
            assert "OneClass Platform API" in content
    
    def test_generate_postman_collection(self, generator):
        """Test Postman collection generation"""
        collection = generator.generate_postman_collection()
        
        assert "info" in collection
        assert "auth" in collection
        assert "variable" in collection
        assert "item" in collection
        
        # Check info
        info = collection["info"]
        assert info["name"] == "OneClass Platform API Collection"
        assert info["version"] == "1.0.0"
        assert "schema" in info
        
        # Check auth
        auth = collection["auth"]
        assert auth["type"] == "bearer"
        assert "bearer" in auth
        
        # Check variables
        variables = collection["variable"]
        variable_keys = [var["key"] for var in variables]
        assert "base_url" in variable_keys
        assert "access_token" in variable_keys
    
    def test_save_postman_collection(self, generator, tmp_path):
        """Test saving Postman collection"""
        collection_file = tmp_path / "test_collection.json"
        
        generator.save_postman_collection(str(collection_file))
        assert collection_file.exists()
        
        # Verify content
        with open(collection_file, 'r') as f:
            data = json.load(f)
            assert "info" in data
            assert data["info"]["name"] == "OneClass Platform API Collection"
    
    def test_custom_examples(self, generator):
        """Test custom examples addition"""
        schema = generator.generate_openapi_schema()
        
        # This would test the custom examples if we had actual paths with examples
        # For now, we just verify the schema is generated without errors
        assert "paths" in schema
    
    def test_api_description(self, generator):
        """Test API description generation"""
        description = generator._get_api_description()
        
        assert "OneClass Platform API" in description
        assert "Multi-tenant Architecture" in description
        assert "Role-based Access Control" in description
        assert "Mobile-first Design" in description
        assert "Real-time Updates" in description
        assert "Authentication" in description
        assert "Rate Limiting" in description
        assert "Error Handling" in description
        assert "Versioning" in description
        assert "SDKs and Libraries" in description


class TestSwaggerUI:
    """Test Swagger UI generation"""
    
    def test_generate_custom_swagger_ui(self):
        """Test custom Swagger UI generation"""
        openapi_url = "/api/v1/docs/openapi.json"
        html_response = generate_custom_swagger_ui(openapi_url)
        
        assert html_response.status_code == 200
        content = html_response.body.decode()
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in content
        assert "<title>OneClass Platform API</title>" in content
        assert "swagger-ui" in content
        assert openapi_url in content
        
        # Check custom styling
        assert "background-color: #1e40af" in content
        assert "OneClass Platform API" in content
        assert "Comprehensive school management system" in content
    
    def test_generate_custom_redoc(self):
        """Test custom ReDoc generation"""
        openapi_url = "/api/v1/docs/openapi.json"
        html_response = generate_custom_redoc(openapi_url)
        
        assert html_response.status_code == 200
        content = html_response.body.decode()
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in content
        assert "<title>OneClass Platform API</title>" in content
        assert "redoc" in content
        assert openapi_url in content
        
        # Check custom styling
        assert "background: linear-gradient" in content
        assert "OneClass Platform API" in content
        assert "Comprehensive school management system" in content


class TestMarkdownGenerator:
    """Test markdown documentation generator"""
    
    @pytest.fixture
    def mock_schema(self):
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "Test API description"
            },
            "servers": [
                {
                    "url": "https://api.test.com",
                    "description": "Production server"
                }
            ],
            "tags": [
                {
                    "name": "Users",
                    "description": "User management"
                }
            ],
            "paths": {
                "/users": {
                    "get": {
                        "tags": ["Users"],
                        "summary": "Get users",
                        "description": "Retrieve all users",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer"},
                                "required": False,
                                "description": "Maximum number of users to return"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of users",
                                "content": {
                                    "application/json": {
                                        "examples": {
                                            "users_list": {
                                                "summary": "Users list",
                                                "value": [
                                                    {"id": 1, "name": "John Doe"},
                                                    {"id": 2, "name": "Jane Smith"}
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "description": "User model",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "User ID"
                            },
                            "name": {
                                "type": "string",
                                "description": "User name"
                            }
                        },
                        "example": {
                            "id": 1,
                            "name": "John Doe"
                        }
                    }
                },
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "description": "JWT token authentication"
                    }
                }
            }
        }
    
    @pytest.fixture
    def markdown_generator(self, mock_schema):
        return MarkdownGenerator(mock_schema)
    
    def test_markdown_generator_initialization(self, markdown_generator, mock_schema):
        """Test markdown generator initialization"""
        assert markdown_generator.schema == mock_schema
        assert markdown_generator.info == mock_schema["info"]
        assert markdown_generator.paths == mock_schema["paths"]
        assert markdown_generator.components == mock_schema["components"]
        assert markdown_generator.servers == mock_schema["servers"]
        assert markdown_generator.tags == mock_schema["tags"]
    
    def test_generate_header(self, markdown_generator):
        """Test header generation"""
        header = markdown_generator._generate_header()
        
        assert "# Test API" in header
        assert "**Version:** 1.0.0" in header
        assert "Test API description" in header
        assert "---" in header
    
    def test_generate_table_of_contents(self, markdown_generator):
        """Test table of contents generation"""
        toc = markdown_generator._generate_table_of_contents()
        
        assert "## Table of Contents" in toc
        assert "1. [Overview](#overview)" in toc
        assert "2. [Authentication](#authentication)" in toc
        assert "[Users](#users)" in toc
        assert "10. [Support](#support)" in toc
    
    def test_generate_authentication(self, markdown_generator):
        """Test authentication section generation"""
        auth_section = markdown_generator._generate_authentication()
        
        assert "## Authentication" in auth_section
        assert "JWT (JSON Web Tokens)" in auth_section
        assert "Authorization: Bearer <your-access-token>" in auth_section
        assert "POST /api/v1/auth/login" in auth_section
        assert "BearerAuth" in auth_section
    
    def test_generate_endpoints(self, markdown_generator):
        """Test endpoints section generation"""
        endpoints_section = markdown_generator._generate_endpoints_by_tag()
        
        assert "## Endpoints" in endpoints_section
        assert "### Users" in endpoints_section
        assert "#### GET /users" in endpoints_section
        assert "**Get users**" in endpoints_section
        assert "Retrieve all users" in endpoints_section
        assert "**Parameters:**" in endpoints_section
        assert "**Responses:**" in endpoints_section
    
    def test_generate_schemas(self, markdown_generator):
        """Test schemas section generation"""
        schemas_section = markdown_generator._generate_schemas()
        
        assert "## Data Models" in schemas_section
        assert "### User" in schemas_section
        assert "User model" in schemas_section
        assert "| Property | Type | Required | Description |" in schemas_section
        assert "| id | integer | Yes | User ID |" in schemas_section
        assert "| name | string | Yes | User name |" in schemas_section
    
    def test_generate_examples(self, markdown_generator):
        """Test examples section generation"""
        examples_section = markdown_generator._generate_examples()
        
        assert "## Examples" in examples_section
        assert "### Quick Start" in examples_section
        assert "### JavaScript Example" in examples_section
        assert "### cURL Examples" in examples_section
        assert "import requests" in examples_section
        assert "fetch(" in examples_section
        assert "curl -X" in examples_section
    
    def test_generate_full_documentation(self, markdown_generator):
        """Test full documentation generation"""
        full_doc = markdown_generator.generate_full_documentation()
        
        assert "# Test API" in full_doc
        assert "## Table of Contents" in full_doc
        assert "## Overview" in full_doc
        assert "## Authentication" in full_doc
        assert "## Endpoints" in full_doc
        assert "## Data Models" in full_doc
        assert "## Examples" in full_doc
        assert "## Support" in full_doc
    
    def test_save_to_file(self, markdown_generator, tmp_path):
        """Test saving markdown to file"""
        output_file = tmp_path / "test_docs.md"
        
        markdown_generator.save_to_file(str(output_file))
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# Test API" in content
            assert "## Table of Contents" in content
    
    def test_generate_section(self, markdown_generator):
        """Test generating specific sections"""
        header = markdown_generator.generate_section("header")
        assert "# Test API" in header
        
        toc = markdown_generator.generate_section("toc")
        assert "## Table of Contents" in toc
        
        overview = markdown_generator.generate_section("overview")
        assert "## Overview" in overview
        
        # Test invalid section
        with pytest.raises(ValueError, match="Unknown section"):
            markdown_generator.generate_section("invalid_section")
    
    def test_generate_markdown_docs_function(self, mock_schema, tmp_path):
        """Test generate_markdown_docs function"""
        output_file = tmp_path / "generated_docs.md"
        
        result_path = generate_markdown_docs(mock_schema, str(output_file))
        assert result_path == str(output_file)
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# Test API" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])