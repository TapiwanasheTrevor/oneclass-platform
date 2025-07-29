"""
OpenAPI Documentation Generator
Generates comprehensive API documentation for the OneClass Platform
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
import json
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OpenAPIGenerator:
    """Generate comprehensive OpenAPI documentation"""
    
    def __init__(self, app: FastAPI, title: str = "OneClass Platform API", version: str = "1.0.0"):
        self.app = app
        self.title = title
        self.version = version
        self.base_url = "https://api.oneclass.ac.zw"
        self.contact_info = {
            "name": "OneClass Platform Team",
            "url": "https://oneclass.ac.zw/support",
            "email": "api-support@oneclass.ac.zw"
        }
        self.license_info = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    
    def generate_openapi_schema(self) -> Dict[str, Any]:
        """Generate comprehensive OpenAPI schema"""
        if self.app.openapi_schema:
            return self.app.openapi_schema
        
        openapi_schema = get_openapi(
            title=self.title,
            version=self.version,
            description=self._get_api_description(),
            routes=self.app.routes,
            servers=[
                {
                    "url": self.base_url,
                    "description": "Production server"
                },
                {
                    "url": "https://staging-api.oneclass.ac.zw",
                    "description": "Staging server"
                },
                {
                    "url": "http://localhost:8000",
                    "description": "Local development server"
                }
            ]
        )
        
        # Add custom information
        openapi_schema["info"]["contact"] = self.contact_info
        openapi_schema["info"]["license"] = self.license_info
        openapi_schema["info"]["termsOfService"] = "https://oneclass.ac.zw/terms"
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = self._get_security_schemes()
        
        # Add tags
        openapi_schema["tags"] = self._get_api_tags()
        
        # Add custom examples
        self._add_custom_examples(openapi_schema)
        
        # Add external docs
        openapi_schema["externalDocs"] = {
            "description": "OneClass Platform Documentation",
            "url": "https://docs.oneclass.ac.zw"
        }
        
        self.app.openapi_schema = openapi_schema
        return self.app.openapi_schema
    
    def _get_api_description(self) -> str:
        """Get comprehensive API description"""
        return """
## OneClass Platform API

The OneClass Platform API provides comprehensive school management functionality for educational institutions in Zimbabwe. This RESTful API enables integration with student information systems, learning management systems, and third-party applications.

### Key Features

- **Multi-tenant Architecture**: Support for multiple schools with isolated data
- **Role-based Access Control**: Granular permissions for different user types
- **Mobile-first Design**: Optimized for mobile applications
- **Real-time Updates**: WebSocket support for live data
- **Comprehensive Reporting**: Advanced analytics and reporting capabilities
- **Integration Support**: Webhooks and API keys for third-party integrations

### Authentication

The API uses JWT (JSON Web Tokens) for authentication. All requests must include a valid access token in the Authorization header:

```
Authorization: Bearer <your-access-token>
```

### Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Free tier**: 1,000 requests per hour
- **Premium tier**: 10,000 requests per hour
- **Enterprise tier**: 100,000 requests per hour

### Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

### Versioning

The API uses URL versioning. The current version is v1:

```
https://api.oneclass.ac.zw/api/v1/
```

### SDKs and Libraries

Official SDKs are available for:
- **Python**: `pip install oneclass-sdk`
- **JavaScript/Node.js**: `npm install oneclass-sdk`
- **PHP**: `composer require oneclass/sdk`
- **Mobile**: iOS and Android SDKs available

### Support

For API support, please contact:
- **Email**: api-support@oneclass.ac.zw
- **Documentation**: https://docs.oneclass.ac.zw
- **Status Page**: https://status.oneclass.ac.zw
        """
    
    def _get_security_schemes(self) -> Dict[str, Any]:
        """Define security schemes"""
        return {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT access token obtained from login endpoint"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for mobile applications and integrations"
            },
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": f"{self.base_url}/auth/authorize",
                        "tokenUrl": f"{self.base_url}/auth/token",
                        "scopes": {
                            "read": "Read access to resources",
                            "write": "Write access to resources",
                            "admin": "Administrative access"
                        }
                    }
                }
            }
        }
    
    def _get_api_tags(self) -> List[Dict[str, Any]]:
        """Define API tags for grouping endpoints"""
        return [
            {
                "name": "Authentication",
                "description": "User authentication and session management"
            },
            {
                "name": "Users",
                "description": "User management and profiles"
            },
            {
                "name": "Schools",
                "description": "School management and configuration"
            },
            {
                "name": "Students",
                "description": "Student information and enrollment"
            },
            {
                "name": "Teachers",
                "description": "Teacher management and assignments"
            },
            {
                "name": "Classes",
                "description": "Class management and scheduling"
            },
            {
                "name": "Grades",
                "description": "Grade management and reporting"
            },
            {
                "name": "Attendance",
                "description": "Attendance tracking and reporting"
            },
            {
                "name": "Finance",
                "description": "Financial management and billing"
            },
            {
                "name": "Analytics",
                "description": "Analytics and reporting"
            },
            {
                "name": "Mobile",
                "description": "Mobile app authentication and features"
            },
            {
                "name": "SSO",
                "description": "Single Sign-On integration"
            },
            {
                "name": "Domains",
                "description": "Custom domain management"
            },
            {
                "name": "Notifications",
                "description": "Push notifications and messaging"
            },
            {
                "name": "Integrations",
                "description": "Third-party integrations and webhooks"
            },
            {
                "name": "System",
                "description": "System administration and health checks"
            }
        ]
    
    def _add_custom_examples(self, schema: Dict[str, Any]):
        """Add custom examples to the schema"""
        # Add example responses for common endpoints
        if "paths" in schema:
            for path, methods in schema["paths"].items():
                for method, operation in methods.items():
                    if isinstance(operation, dict):
                        self._add_operation_examples(operation, path, method)
    
    def _add_operation_examples(self, operation: Dict[str, Any], path: str, method: str):
        """Add examples to a specific operation"""
        # Add examples based on endpoint type
        if "/auth/login" in path:
            self._add_login_examples(operation)
        elif "/users" in path:
            self._add_user_examples(operation)
        elif "/students" in path:
            self._add_student_examples(operation)
        elif "/schools" in path:
            self._add_school_examples(operation)
    
    def _add_login_examples(self, operation: Dict[str, Any]):
        """Add login endpoint examples"""
        if "requestBody" in operation:
            operation["requestBody"]["content"]["application/json"]["examples"] = {
                "standard_login": {
                    "summary": "Standard login",
                    "value": {
                        "username": "teacher@harare-primary.oneclass.ac.zw",
                        "password": "securepassword123"
                    }
                },
                "mobile_login": {
                    "summary": "Mobile app login",
                    "value": {
                        "username": "student@bulawayo-high.oneclass.ac.zw",
                        "password": "mypassword",
                        "device_id": "mobile_device_123"
                    }
                }
            }
    
    def _add_user_examples(self, operation: Dict[str, Any]):
        """Add user endpoint examples"""
        if "responses" in operation and "200" in operation["responses"]:
            if "content" in operation["responses"]["200"]:
                operation["responses"]["200"]["content"]["application/json"]["examples"] = {
                    "teacher_profile": {
                        "summary": "Teacher profile",
                        "value": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "sarah.chikwanha",
                            "email": "sarah.chikwanha@harare-primary.oneclass.ac.zw",
                            "first_name": "Sarah",
                            "last_name": "Chikwanha",
                            "role": "teacher",
                            "school_id": "school_123",
                            "is_active": True,
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    },
                    "student_profile": {
                        "summary": "Student profile",
                        "value": {
                            "id": "456e7890-e89b-12d3-a456-426614174001",
                            "username": "john.doe",
                            "email": "john.doe@bulawayo-high.oneclass.ac.zw",
                            "first_name": "John",
                            "last_name": "Doe",
                            "role": "student",
                            "school_id": "school_456",
                            "grade": "Form 4",
                            "is_active": True,
                            "created_at": "2024-02-01T09:15:00Z"
                        }
                    }
                }
    
    def _add_student_examples(self, operation: Dict[str, Any]):
        """Add student endpoint examples"""
        if "responses" in operation and "200" in operation["responses"]:
            if "content" in operation["responses"]["200"]:
                operation["responses"]["200"]["content"]["application/json"]["examples"] = {
                    "student_record": {
                        "summary": "Complete student record",
                        "value": {
                            "id": "789e0123-e89b-12d3-a456-426614174002",
                            "student_id": "STU2024001",
                            "first_name": "Tendai",
                            "last_name": "Mukamuri",
                            "email": "tendai.mukamuri@mutare-secondary.oneclass.ac.zw",
                            "date_of_birth": "2008-05-15",
                            "grade": "Form 2",
                            "class": "2A",
                            "parent_contact": "+263777123456",
                            "address": "123 Main Street, Mutare",
                            "enrollment_date": "2024-01-10",
                            "is_active": True,
                            "academic_performance": {
                                "gpa": 3.8,
                                "rank": 5,
                                "total_students": 45
                            }
                        }
                    }
                }
    
    def _add_school_examples(self, operation: Dict[str, Any]):
        """Add school endpoint examples"""
        if "responses" in operation and "200" in operation["responses"]:
            if "content" in operation["responses"]["200"]:
                operation["responses"]["200"]["content"]["application/json"]["examples"] = {
                    "primary_school": {
                        "summary": "Primary school",
                        "value": {
                            "id": "abc12345-e89b-12d3-a456-426614174003",
                            "name": "Harare Primary School",
                            "subdomain": "harare-primary",
                            "type": "Primary",
                            "address": "456 School Road, Harare",
                            "phone": "+263242123456",
                            "email": "info@harare-primary.oneclass.ac.zw",
                            "website": "https://harare-primary.oneclass.ac.zw",
                            "principal": "Mrs. Grace Moyo",
                            "student_count": 850,
                            "teacher_count": 45,
                            "established": "1995",
                            "is_active": True
                        }
                    },
                    "secondary_school": {
                        "summary": "Secondary school",
                        "value": {
                            "id": "def67890-e89b-12d3-a456-426614174004",
                            "name": "Bulawayo High School",
                            "subdomain": "bulawayo-high",
                            "type": "Secondary",
                            "address": "789 Education Avenue, Bulawayo",
                            "phone": "+263292987654",
                            "email": "admin@bulawayo-high.oneclass.ac.zw",
                            "website": "https://bulawayo-high.oneclass.ac.zw",
                            "principal": "Mr. David Ncube",
                            "student_count": 1200,
                            "teacher_count": 68,
                            "established": "1987",
                            "is_active": True
                        }
                    }
                }
    
    def save_schema_to_file(self, file_path: str, format: str = "json"):
        """Save OpenAPI schema to file"""
        schema = self.generate_openapi_schema()
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "yaml":
            with open(path, 'w') as f:
                yaml.dump(schema, f, default_flow_style=False)
        else:
            with open(path, 'w') as f:
                json.dump(schema, f, indent=2)
        
        logger.info(f"OpenAPI schema saved to {file_path}")
    
    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate Postman collection from OpenAPI schema"""
        schema = self.generate_openapi_schema()
        
        collection = {
            "info": {
                "name": f"{self.title} Collection",
                "description": schema["info"]["description"],
                "version": self.version,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": self.base_url,
                    "type": "string"
                },
                {
                    "key": "access_token",
                    "value": "your_access_token_here",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Convert OpenAPI paths to Postman requests
        if "paths" in schema:
            for path, methods in schema["paths"].items():
                folder = self._create_postman_folder(path)
                
                for method, operation in methods.items():
                    if isinstance(operation, dict):
                        request = self._create_postman_request(path, method, operation)
                        folder["item"].append(request)
                
                if folder["item"]:
                    collection["item"].append(folder)
        
        return collection
    
    def _create_postman_folder(self, path: str) -> Dict[str, Any]:
        """Create Postman folder for API path"""
        # Extract folder name from path
        parts = path.strip('/').split('/')
        folder_name = parts[0].title() if parts else "Root"
        
        return {
            "name": folder_name,
            "description": f"Endpoints for {folder_name.lower()}",
            "item": []
        }
    
    def _create_postman_request(self, path: str, method: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Create Postman request from OpenAPI operation"""
        request = {
            "name": operation.get("summary", f"{method.upper()} {path}"),
            "request": {
                "method": method.upper(),
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "url": {
                    "raw": f"{{{{base_url}}}}{path}",
                    "host": ["{{base_url}}"],
                    "path": path.strip('/').split('/')
                },
                "description": operation.get("description", "")
            }
        }
        
        # Add request body if present
        if "requestBody" in operation:
            request["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(self._extract_example_from_request_body(operation["requestBody"]), indent=2)
            }
        
        return request
    
    def _extract_example_from_request_body(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Extract example from request body"""
        if "content" in request_body:
            for content_type, content in request_body["content"].items():
                if "examples" in content:
                    # Return first example
                    for example_name, example in content["examples"].items():
                        return example.get("value", {})
                elif "example" in content:
                    return content["example"]
        
        return {}
    
    def save_postman_collection(self, file_path: str):
        """Save Postman collection to file"""
        collection = self.generate_postman_collection()
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(collection, f, indent=2)
        
        logger.info(f"Postman collection saved to {file_path}")


def generate_custom_swagger_ui(openapi_url: str, title: str = "OneClass Platform API") -> HTMLResponse:
    """Generate custom Swagger UI with OneClass branding"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
        <link rel="shortcut icon" href="https://oneclass.ac.zw/favicon.ico" />
        <style>
            .swagger-ui .topbar {{
                background-color: #1e40af;
                border-bottom: 1px solid #3b82f6;
            }}
            .swagger-ui .topbar .download-url-wrapper .download-url-button {{
                background-color: #3b82f6;
                color: white;
            }}
            .swagger-ui .info .title {{
                color: #1e40af;
            }}
            .swagger-ui .scheme-container {{
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
            }}
            .swagger-ui .opblock.opblock-post {{
                border-color: #10b981;
                background: rgba(16, 185, 129, 0.1);
            }}
            .swagger-ui .opblock.opblock-get {{
                border-color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
            }}
            .swagger-ui .opblock.opblock-put {{
                border-color: #f59e0b;
                background: rgba(245, 158, 11, 0.1);
            }}
            .swagger-ui .opblock.opblock-delete {{
                border-color: #ef4444;
                background: rgba(239, 68, 68, 0.1);
            }}
            .custom-header {{
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
                color: white;
                padding: 1rem;
                text-align: center;
                margin-bottom: 2rem;
            }}
            .custom-header h1 {{
                margin: 0;
                font-size: 2rem;
                font-weight: bold;
            }}
            .custom-header p {{
                margin: 0.5rem 0 0 0;
                opacity: 0.9;
            }}
        </style>
    </head>
    <body>
        <div class="custom-header">
            <h1>OneClass Platform API</h1>
            <p>Comprehensive school management system for educational institutions</p>
        </div>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '{openapi_url}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                tryItOutEnabled: true,
                requestInterceptor: function(request) {{
                    // Add custom headers or modify requests
                    request.headers['X-API-Client'] = 'swagger-ui';
                    return request;
                }},
                responseInterceptor: function(response) {{
                    // Handle responses
                    return response;
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


def generate_custom_redoc(openapi_url: str, title: str = "OneClass Platform API") -> HTMLResponse:
    """Generate custom ReDoc documentation with OneClass branding"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="shortcut icon" href="https://oneclass.ac.zw/favicon.ico" />
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            }}
            .custom-header {{
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
                color: white;
                padding: 2rem;
                text-align: center;
            }}
            .custom-header h1 {{
                margin: 0;
                font-size: 2.5rem;
                font-weight: bold;
            }}
            .custom-header p {{
                margin: 1rem 0 0 0;
                font-size: 1.2rem;
                opacity: 0.9;
            }}
        </style>
    </head>
    <body>
        <div class="custom-header">
            <h1>OneClass Platform API</h1>
            <p>Comprehensive school management system for educational institutions</p>
        </div>
        <redoc spec-url="{openapi_url}"></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)