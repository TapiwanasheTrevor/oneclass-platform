# API Documentation Service

The API Documentation Service provides comprehensive OpenAPI/Swagger documentation generation for the OneClass Platform API. This service automatically generates interactive documentation, API schemas, and client SDKs.

## Features

- **OpenAPI 3.0 Specification**: Complete API specification with detailed schemas
- **Interactive Documentation**: Swagger UI and ReDoc interfaces
- **Multi-format Export**: JSON, YAML, Postman collections, and Markdown
- **Custom Branding**: OneClass Platform themed documentation
- **Example Generation**: Realistic examples for all endpoints
- **Client SDK Support**: Foundation for SDK generation
- **Validation Tools**: Documentation quality validation
- **Metrics & Analytics**: Documentation usage tracking

## Quick Start

### 1. Integration with FastAPI

```python
from fastapi import FastAPI
from backend.services.api_docs.integration import setup_api_documentation

app = FastAPI()

# Setup documentation
generator = setup_api_documentation(
    app,
    title="OneClass Platform API",
    version="1.0.0",
    description="Comprehensive school management system API"
)
```

### 2. Accessing Documentation

Once integrated, documentation is available at:

- **Swagger UI**: `http://localhost:8000/api/v1/docs/`
- **ReDoc**: `http://localhost:8000/api/v1/docs/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/docs/openapi.json`
- **OpenAPI YAML**: `http://localhost:8000/api/v1/docs/openapi.yaml`
- **Postman Collection**: `http://localhost:8000/api/v1/docs/postman`

### 3. Generating Documentation Files

```python
from backend.services.api_docs.integration import generate_all_documentation

# Generate all formats
files = generate_all_documentation(app, "docs/api")

# Generate specific formats
files = generate_all_documentation(app, "docs/api", ["json", "markdown"])
```

## API Endpoints

### Public Endpoints

- `GET /api/v1/docs/openapi.json` - OpenAPI schema in JSON format
- `GET /api/v1/docs/openapi.yaml` - OpenAPI schema in YAML format
- `GET /api/v1/docs/` - Swagger UI interface
- `GET /api/v1/docs/redoc` - ReDoc interface
- `GET /api/v1/docs/postman` - Postman collection download
- `GET /api/v1/docs/health` - Service health check

### Protected Endpoints (Admin/Developer only)

- `POST /api/v1/docs/generate` - Generate documentation files
- `GET /api/v1/docs/stats` - Documentation statistics
- `POST /api/v1/docs/refresh` - Refresh documentation cache
- `GET /api/v1/docs/export/{format}` - Export documentation

## Configuration

### Environment Variables

```bash
# API Documentation Configuration
API_DOCS_TITLE="OneClass Platform API"
API_DOCS_VERSION="1.0.0"
API_DOCS_BASE_URL="https://api.oneclass.ac.zw"
API_DOCS_CONTACT_EMAIL="api-support@oneclass.ac.zw"
API_DOCS_ENABLE_UI=true
API_DOCS_ENABLE_REDOC=true
```

### Programmatic Configuration

```python
from backend.services.api_docs.integration import update_documentation_config

config = {
    "title": "My Custom API",
    "version": "2.0.0",
    "base_url": "https://api.myschool.oneclass.ac.zw",
    "contact_info": {
        "name": "API Support Team",
        "email": "api@myschool.oneclass.ac.zw"
    }
}

update_documentation_config(app, config)
```

## Components

### OpenAPIGenerator

Core class for generating OpenAPI specifications:

```python
from backend.services.api_docs.generator import OpenAPIGenerator

generator = OpenAPIGenerator(app, title="My API", version="1.0.0")
schema = generator.generate_openapi_schema()
```

### MarkdownGenerator

Generates comprehensive markdown documentation:

```python
from backend.services.api_docs.markdown_generator import MarkdownGenerator

markdown_gen = MarkdownGenerator(openapi_schema)
documentation = markdown_gen.generate_full_documentation()
```

### Documentation Routes

FastAPI router with all documentation endpoints:

```python
from backend.services.api_docs.routes import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
```

## Customization

### Custom Branding

The documentation includes OneClass Platform branding by default. To customize:

```python
def custom_swagger_ui(openapi_url: str) -> HTMLResponse:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Custom API</title>
        <style>
            .swagger-ui .topbar {{
                background-color: #my-color;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '{openapi_url}',
                dom_id: '#swagger-ui'
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
```

### Custom Examples

Add custom examples to your endpoints:

```python
from backend.services.api_docs.integration import enhance_endpoint_docs

@enhance_endpoint_docs(
    summary="Get user profile",
    description="Retrieve the current user's profile information",
    tags=["Users"],
    response_examples={
        "200": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
)
@app.get("/users/me")
async def get_user_profile():
    return {"id": "123", "name": "John Doe"}
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest backend/services/api_docs/tests/

# Run specific test file
pytest backend/services/api_docs/tests/test_generator.py

# Run with coverage
pytest backend/services/api_docs/tests/ --cov=backend.services.api_docs
```

## Validation

Validate documentation quality:

```python
from backend.services.api_docs.integration import validate_api_documentation

results = validate_api_documentation(app)
print(f"Documentation score: {results['score']}/100")
print(f"Warnings: {len(results['warnings'])}")
print(f"Errors: {len(results['errors'])}")
```

## Metrics

Get documentation metrics:

```python
from backend.services.api_docs.integration import get_documentation_metrics

metrics = get_documentation_metrics(app)
print(f"Total endpoints: {metrics['total_endpoints']}")
print(f"Coverage: {metrics['coverage_percentage']}%")
```

## Export Options

### ZIP Bundle

Export complete documentation bundle:

```python
from backend.services.api_docs.integration import export_documentation_bundle

bundle_path = export_documentation_bundle(
    app,
    "docs/oneclass-api-docs.zip",
    include_formats=["json", "yaml", "postman", "markdown"]
)
```

### Individual Files

Generate specific documentation files:

```python
from backend.services.api_docs.generator import OpenAPIGenerator

generator = OpenAPIGenerator(app)

# Save OpenAPI JSON
generator.save_schema_to_file("docs/openapi.json", "json")

# Save OpenAPI YAML
generator.save_schema_to_file("docs/openapi.yaml", "yaml")

# Save Postman collection
generator.save_postman_collection("docs/postman_collection.json")
```

## Advanced Usage

### Dynamic Documentation

Update documentation at runtime:

```python
# Add new endpoint documentation
@app.post("/dynamic-endpoint")
async def dynamic_endpoint():
    """This endpoint was added dynamically"""
    return {"message": "Dynamic endpoint"}

# Refresh documentation
generator = app.state.documentation_generator
app.openapi_schema = None  # Clear cache
new_schema = generator.generate_openapi_schema()
```

### Custom Tags

Organize endpoints with custom tags:

```python
custom_tags = [
    {
        "name": "Custom",
        "description": "Custom functionality",
        "externalDocs": {
            "description": "External documentation",
            "url": "https://docs.example.com"
        }
    }
]

generator = OpenAPIGenerator(app)
generator.tags.extend(custom_tags)
```

## Security

### Authentication

Documentation endpoints support role-based access:

```python
from backend.services.api_docs.routes import router
from fastapi import Depends
from shared.auth import get_current_user, require_admin

# Override protected endpoints
@router.post("/generate")
async def generate_docs(user = Depends(require_admin)):
    # Only admins can generate documentation
    pass
```

### Rate Limiting

Apply rate limiting to documentation endpoints:

```python
from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

@app.get("/api/v1/docs/openapi.json")
@limiter.limit("10/minute")
async def get_openapi_schema(request: Request):
    # Rate limited endpoint
    pass
```

## Troubleshooting

### Common Issues

1. **Documentation not updating**: Clear the OpenAPI schema cache
   ```python
   app.openapi_schema = None
   ```

2. **Missing examples**: Ensure examples are properly defined in your OpenAPI operations

3. **Styling issues**: Check custom CSS conflicts with Swagger UI styles

4. **Authentication errors**: Verify JWT tokens and API keys are valid

### Debug Mode

Enable debug logging:

```python
import logging

logging.getLogger("backend.services.api_docs").setLevel(logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- **Email**: api-support@oneclass.ac.zw
- **Documentation**: https://docs.oneclass.ac.zw
- **GitHub Issues**: https://github.com/oneclass/platform/issues