"""
Markdown Documentation Generator
Generates comprehensive markdown documentation for developers
"""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

from .generator import OpenAPIGenerator

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """Generate markdown documentation from OpenAPI schema"""
    
    def __init__(self, openapi_schema: Dict[str, Any]):
        self.schema = openapi_schema
        self.info = openapi_schema.get("info", {})
        self.paths = openapi_schema.get("paths", {})
        self.components = openapi_schema.get("components", {})
        self.servers = openapi_schema.get("servers", [])
        self.tags = openapi_schema.get("tags", [])
    
    def generate_full_documentation(self) -> str:
        """Generate complete markdown documentation"""
        sections = [
            self._generate_header(),
            self._generate_table_of_contents(),
            self._generate_overview(),
            self._generate_authentication(),
            self._generate_rate_limiting(),
            self._generate_error_handling(),
            self._generate_endpoints_by_tag(),
            self._generate_schemas(),
            self._generate_examples(),
            self._generate_sdk_information(),
            self._generate_changelog(),
            self._generate_support()
        ]
        
        return "\n\n".join(filter(None, sections))
    
    def _generate_header(self) -> str:
        """Generate documentation header"""
        title = self.info.get("title", "API Documentation")
        version = self.info.get("version", "1.0.0")
        description = self.info.get("description", "")
        
        header = f"""# {title}

**Version:** {version}

{description}

---
"""
        return header
    
    def _generate_table_of_contents(self) -> str:
        """Generate table of contents"""
        toc = """## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Endpoints](#endpoints)"""
        
        # Add tag-based sections
        for tag in self.tags:
            tag_name = tag.get("name", "")
            tag_anchor = tag_name.lower().replace(" ", "-")
            toc += f"\n   - [{tag_name}](#{tag_anchor})"
        
        toc += """
6. [Data Models](#data-models)
7. [Examples](#examples)
8. [SDKs](#sdks)
9. [Changelog](#changelog)
10. [Support](#support)"""
        
        return toc
    
    def _generate_overview(self) -> str:
        """Generate overview section"""
        overview = """## Overview

The OneClass Platform API provides comprehensive school management functionality for educational institutions in Zimbabwe. This RESTful API enables integration with student information systems, learning management systems, and third-party applications.

### Key Features

- **Multi-tenant Architecture**: Support for multiple schools with isolated data
- **Role-based Access Control**: Granular permissions for different user types
- **Mobile-first Design**: Optimized for mobile applications
- **Real-time Updates**: WebSocket support for live data
- **Comprehensive Reporting**: Advanced analytics and reporting capabilities
- **Integration Support**: Webhooks and API keys for third-party integrations

### Base URLs

"""
        
        for server in self.servers:
            url = server.get("url", "")
            description = server.get("description", "")
            overview += f"- **{description}**: `{url}`\n"
        
        return overview
    
    def _generate_authentication(self) -> str:
        """Generate authentication section"""
        auth_section = """## Authentication

The API uses JWT (JSON Web Tokens) for authentication. All requests must include a valid access token in the Authorization header:

```http
Authorization: Bearer <your-access-token>
```

### Getting an Access Token

To obtain an access token, make a POST request to the login endpoint:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

### Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Token Refresh

When your access token expires, use the refresh token to get a new one:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

### API Keys

For mobile applications and server-to-server integrations, you can use API keys:

```http
X-API-Key: your-api-key
```

### Security Schemes

The API supports multiple authentication methods:

"""
        
        security_schemes = self.components.get("securitySchemes", {})
        for scheme_name, scheme_info in security_schemes.items():
            scheme_type = scheme_info.get("type", "")
            description = scheme_info.get("description", "")
            auth_section += f"- **{scheme_name}** ({scheme_type}): {description}\n"
        
        return auth_section
    
    def _generate_rate_limiting(self) -> str:
        """Generate rate limiting section"""
        return """## Rate Limiting

API requests are rate-limited to ensure fair usage:

| Tier | Requests per Hour | Requests per Minute |
|------|------------------|---------------------|
| Free | 1,000 | 20 |
| Premium | 10,000 | 200 |
| Enterprise | 100,000 | 2,000 |

### Rate Limit Headers

Each API response includes rate limit information in the headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded

When you exceed the rate limit, the API returns a 429 status code:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```"""
    
    def _generate_error_handling(self) -> str:
        """Generate error handling section"""
        return """## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request parameters |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation errors |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

### Error Response Format

```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

- `validation_error`: Request validation failed
- `authentication_error`: Authentication failed
- `authorization_error`: Insufficient permissions
- `not_found`: Resource not found
- `conflict`: Resource already exists
- `rate_limit_exceeded`: Rate limit exceeded
- `server_error`: Internal server error"""
    
    def _generate_endpoints_by_tag(self) -> str:
        """Generate endpoints organized by tags"""
        endpoints_section = "## Endpoints\n\n"
        
        # Group paths by tags
        tag_groups = {}
        for path, methods in self.paths.items():
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    operation_tags = operation.get("tags", ["Untagged"])
                    for tag in operation_tags:
                        if tag not in tag_groups:
                            tag_groups[tag] = []
                        tag_groups[tag].append({
                            "path": path,
                            "method": method.upper(),
                            "operation": operation
                        })
        
        # Generate documentation for each tag group
        for tag_name in sorted(tag_groups.keys()):
            tag_info = next((tag for tag in self.tags if tag.get("name") == tag_name), {})
            tag_description = tag_info.get("description", "")
            
            endpoints_section += f"### {tag_name}\n\n"
            if tag_description:
                endpoints_section += f"{tag_description}\n\n"
            
            for endpoint in tag_groups[tag_name]:
                endpoints_section += self._generate_endpoint_documentation(
                    endpoint["path"], 
                    endpoint["method"], 
                    endpoint["operation"]
                )
                endpoints_section += "\n\n"
        
        return endpoints_section
    
    def _generate_endpoint_documentation(self, path: str, method: str, operation: Dict[str, Any]) -> str:
        """Generate documentation for a single endpoint"""
        summary = operation.get("summary", f"{method} {path}")
        description = operation.get("description", "")
        
        endpoint_doc = f"#### {method} {path}\n\n"
        endpoint_doc += f"**{summary}**\n\n"
        
        if description:
            endpoint_doc += f"{description}\n\n"
        
        # Parameters
        parameters = operation.get("parameters", [])
        if parameters:
            endpoint_doc += "**Parameters:**\n\n"
            endpoint_doc += "| Name | Type | Location | Required | Description |\n"
            endpoint_doc += "|------|------|----------|----------|-------------|\n"
            
            for param in parameters:
                name = param.get("name", "")
                param_type = param.get("schema", {}).get("type", "string")
                location = param.get("in", "")
                required = "Yes" if param.get("required", False) else "No"
                param_description = param.get("description", "")
                
                endpoint_doc += f"| {name} | {param_type} | {location} | {required} | {param_description} |\n"
            
            endpoint_doc += "\n"
        
        # Request body
        request_body = operation.get("requestBody", {})
        if request_body:
            endpoint_doc += "**Request Body:**\n\n"
            content = request_body.get("content", {})
            
            for content_type, content_info in content.items():
                endpoint_doc += f"Content-Type: `{content_type}`\n\n"
                
                # Add example if available
                examples = content_info.get("examples", {})
                if examples:
                    first_example = list(examples.values())[0]
                    example_value = first_example.get("value", {})
                    endpoint_doc += "```json\n"
                    endpoint_doc += json.dumps(example_value, indent=2)
                    endpoint_doc += "\n```\n\n"
        
        # Responses
        responses = operation.get("responses", {})
        if responses:
            endpoint_doc += "**Responses:**\n\n"
            
            for status_code, response_info in responses.items():
                description = response_info.get("description", "")
                endpoint_doc += f"**{status_code}** - {description}\n\n"
                
                # Add response examples
                content = response_info.get("content", {})
                for content_type, content_info in content.items():
                    examples = content_info.get("examples", {})
                    if examples:
                        first_example = list(examples.values())[0]
                        example_value = first_example.get("value", {})
                        endpoint_doc += "```json\n"
                        endpoint_doc += json.dumps(example_value, indent=2)
                        endpoint_doc += "\n```\n\n"
        
        return endpoint_doc
    
    def _generate_schemas(self) -> str:
        """Generate data models section"""
        schemas_section = "## Data Models\n\n"
        
        schemas = self.components.get("schemas", {})
        if not schemas:
            return schemas_section + "No data models defined.\n"
        
        for schema_name, schema_info in schemas.items():
            schemas_section += f"### {schema_name}\n\n"
            
            description = schema_info.get("description", "")
            if description:
                schemas_section += f"{description}\n\n"
            
            # Properties table
            properties = schema_info.get("properties", {})
            if properties:
                schemas_section += "| Property | Type | Required | Description |\n"
                schemas_section += "|----------|------|----------|-------------|\n"
                
                required_fields = schema_info.get("required", [])
                
                for prop_name, prop_info in properties.items():
                    prop_type = prop_info.get("type", "")
                    prop_format = prop_info.get("format", "")
                    if prop_format:
                        prop_type += f" ({prop_format})"
                    
                    is_required = "Yes" if prop_name in required_fields else "No"
                    prop_description = prop_info.get("description", "")
                    
                    schemas_section += f"| {prop_name} | {prop_type} | {is_required} | {prop_description} |\n"
                
                schemas_section += "\n"
            
            # Example
            example = schema_info.get("example", {})
            if example:
                schemas_section += "**Example:**\n\n"
                schemas_section += "```json\n"
                schemas_section += json.dumps(example, indent=2)
                schemas_section += "\n```\n\n"
        
        return schemas_section
    
    def _generate_examples(self) -> str:
        """Generate examples section"""
        return """## Examples

### Quick Start

Here's a simple example to get you started:

```python
import requests

# Login to get access token
login_response = requests.post(
    "https://api.oneclass.ac.zw/api/v1/auth/login",
    json={
        "username": "teacher@harare-primary.oneclass.ac.zw",
        "password": "your-password"
    }
)

token = login_response.json()["access_token"]

# Use the token to make authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# Get user profile
profile_response = requests.get(
    "https://api.oneclass.ac.zw/api/v1/users/profile",
    headers=headers
)

print(profile_response.json())
```

### JavaScript Example

```javascript
const API_BASE = 'https://api.oneclass.ac.zw/api/v1';

// Login function
async function login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    return data.access_token;
}

// Get students
async function getStudents(token) {
    const response = await fetch(`${API_BASE}/students`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return await response.json();
}

// Usage
const token = await login('teacher@school.oneclass.ac.zw', 'password');
const students = await getStudents(token);
console.log(students);
```

### cURL Examples

```bash
# Login
curl -X POST "https://api.oneclass.ac.zw/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "teacher@school.oneclass.ac.zw",
    "password": "your-password"
  }'

# Get students (replace TOKEN with actual token)
curl -X GET "https://api.oneclass.ac.zw/api/v1/students" \\
  -H "Authorization: Bearer TOKEN"

# Create a new student
curl -X POST "https://api.oneclass.ac.zw/api/v1/students" \\
  -H "Authorization: Bearer TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@school.oneclass.ac.zw",
    "grade": "Form 1",
    "date_of_birth": "2008-05-15"
  }'
```"""
    
    def _generate_sdk_information(self) -> str:
        """Generate SDK information section"""
        return """## SDKs

Official SDKs are available for popular programming languages:

### Python SDK

```bash
pip install oneclass-sdk
```

```python
from oneclass_sdk import OneClassClient

client = OneClassClient(
    base_url="https://api.oneclass.ac.zw",
    username="your-username",
    password="your-password"
)

# Get students
students = client.students.list()
print(students)

# Create a new student
new_student = client.students.create({
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@school.oneclass.ac.zw",
    "grade": "Form 2"
})
```

### JavaScript/Node.js SDK

```bash
npm install oneclass-sdk
```

```javascript
const OneClass = require('oneclass-sdk');

const client = new OneClass({
    baseUrl: 'https://api.oneclass.ac.zw',
    username: 'your-username',
    password: 'your-password'
});

// Get students
const students = await client.students.list();
console.log(students);
```

### PHP SDK

```bash
composer require oneclass/sdk
```

```php
<?php
require_once 'vendor/autoload.php';

use OneClass\\SDK\\Client;

$client = new Client([
    'base_url' => 'https://api.oneclass.ac.zw',
    'username' => 'your-username',
    'password' => 'your-password'
]);

// Get students
$students = $client->students->list();
print_r($students);
?>
```

### Mobile SDKs

- **iOS SDK**: Available through CocoaPods and Swift Package Manager
- **Android SDK**: Available through JitPack and Maven Central

For detailed SDK documentation, visit our [Developer Portal](https://docs.oneclass.ac.zw/sdks)."""
    
    def _generate_changelog(self) -> str:
        """Generate changelog section"""
        return """## Changelog

### Version 1.0.0 (2024-01-01)

#### New Features
- Initial release of the OneClass Platform API
- Multi-tenant architecture with school isolation
- Role-based access control system
- Mobile authentication with biometric support
- Real-time notifications via WebSocket
- Comprehensive reporting and analytics
- SSO integration (SAML/LDAP)
- Custom domain support

#### Endpoints Added
- Authentication endpoints (`/auth/*`)
- User management (`/users/*`)
- Student information system (`/students/*`)
- School management (`/schools/*`)
- Grade management (`/grades/*`)
- Attendance tracking (`/attendance/*`)
- Financial management (`/finance/*`)
- Analytics and reporting (`/analytics/*`)

#### Security Enhancements
- JWT-based authentication
- API key support for mobile apps
- Rate limiting implementation
- Input validation and sanitization
- CORS configuration
- Security headers

#### Documentation
- OpenAPI 3.0 specification
- Interactive Swagger UI
- Postman collection
- SDK documentation
- Code examples

### Future Releases

See our [roadmap](https://github.com/oneclass/platform/projects) for upcoming features and improvements."""
    
    def _generate_support(self) -> str:
        """Generate support section"""
        return """## Support

### Documentation

- **API Reference**: [https://docs.oneclass.ac.zw/api](https://docs.oneclass.ac.zw/api)
- **Developer Guide**: [https://docs.oneclass.ac.zw/guide](https://docs.oneclass.ac.zw/guide)
- **SDK Documentation**: [https://docs.oneclass.ac.zw/sdks](https://docs.oneclass.ac.zw/sdks)
- **Tutorials**: [https://docs.oneclass.ac.zw/tutorials](https://docs.oneclass.ac.zw/tutorials)

### Community

- **Developer Forum**: [https://forum.oneclass.ac.zw](https://forum.oneclass.ac.zw)
- **GitHub Repository**: [https://github.com/oneclass/platform](https://github.com/oneclass/platform)
- **Discord Server**: [https://discord.gg/oneclass](https://discord.gg/oneclass)

### Support Channels

- **Technical Support**: api-support@oneclass.ac.zw
- **Bug Reports**: [GitHub Issues](https://github.com/oneclass/platform/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/oneclass/platform/discussions)
- **Security Issues**: security@oneclass.ac.zw

### Status Page

Monitor API status and uptime: [https://status.oneclass.ac.zw](https://status.oneclass.ac.zw)

### Service Level Agreement

- **Uptime**: 99.9% availability
- **Response Time**: < 200ms for most endpoints
- **Support Response**: 24 hours for technical issues

### Terms of Service

By using this API, you agree to our [Terms of Service](https://oneclass.ac.zw/terms) and [Privacy Policy](https://oneclass.ac.zw/privacy).

---

*This documentation is automatically generated from the OpenAPI specification. Last updated: 2024-01-01*"""
    
    def save_to_file(self, file_path: str):
        """Save markdown documentation to file"""
        documentation = self.generate_full_documentation()
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        logger.info(f"Markdown documentation saved to {file_path}")
    
    def generate_section(self, section_name: str) -> str:
        """Generate a specific section of documentation"""
        section_methods = {
            "header": self._generate_header,
            "toc": self._generate_table_of_contents,
            "overview": self._generate_overview,
            "authentication": self._generate_authentication,
            "rate_limiting": self._generate_rate_limiting,
            "error_handling": self._generate_error_handling,
            "endpoints": self._generate_endpoints_by_tag,
            "schemas": self._generate_schemas,
            "examples": self._generate_examples,
            "sdks": self._generate_sdk_information,
            "changelog": self._generate_changelog,
            "support": self._generate_support
        }
        
        method = section_methods.get(section_name.lower())
        if method:
            return method()
        else:
            raise ValueError(f"Unknown section: {section_name}")


def generate_markdown_docs(openapi_schema: Dict[str, Any], output_path: str):
    """Generate markdown documentation from OpenAPI schema"""
    generator = MarkdownGenerator(openapi_schema)
    generator.save_to_file(output_path)
    return output_path