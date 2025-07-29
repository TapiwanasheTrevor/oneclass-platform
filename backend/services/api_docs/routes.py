"""
API Documentation Routes
Routes for serving OpenAPI documentation and related endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional
import json
from pathlib import Path
import logging

from shared.auth import get_current_user
from shared.exceptions import ValidationError
from .generator import OpenAPIGenerator, generate_custom_swagger_ui, generate_custom_redoc
from .schemas import DocumentationConfigUpdate, DocumentationGenerationRequest, DocumentationGenerationResponse

logger = logging.getLogger(__name__)

# Security scheme for protected documentation endpoints
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/api/v1/docs", tags=["Documentation"])


@router.get("/openapi.json", response_class=JSONResponse)
async def get_openapi_schema():
    """
    Get OpenAPI schema in JSON format
    
    Returns the complete OpenAPI 3.0 schema for the OneClass Platform API.
    This endpoint is publicly accessible and used by documentation tools.
    """
    try:
        from main import app  # Import the main FastAPI app
        
        generator = OpenAPIGenerator(app)
        schema = generator.generate_openapi_schema()
        
        return JSONResponse(content=schema)
    
    except Exception as e:
        logger.error(f"Failed to generate OpenAPI schema: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate API documentation")


@router.get("/openapi.yaml", response_class=HTMLResponse)
async def get_openapi_yaml():
    """
    Get OpenAPI schema in YAML format
    
    Returns the complete OpenAPI 3.0 schema in YAML format for easier reading
    and integration with tools that prefer YAML.
    """
    try:
        from main import app
        import yaml
        
        generator = OpenAPIGenerator(app)
        schema = generator.generate_openapi_schema()
        
        yaml_content = yaml.dump(schema, default_flow_style=False)
        
        return HTMLResponse(
            content=f"<pre>{yaml_content}</pre>",
            headers={"Content-Type": "text/plain"}
        )
    
    except Exception as e:
        logger.error(f"Failed to generate OpenAPI YAML: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate API documentation")


@router.get("/", response_class=HTMLResponse)
async def get_swagger_ui():
    """
    Serve custom Swagger UI documentation
    
    Returns a customized Swagger UI interface with OneClass Platform branding.
    This is the main interactive documentation interface for developers.
    """
    try:
        openapi_url = "/api/v1/docs/openapi.json"
        return generate_custom_swagger_ui(openapi_url, "OneClass Platform API")
    
    except Exception as e:
        logger.error(f"Failed to generate Swagger UI: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load documentation interface")


@router.get("/redoc", response_class=HTMLResponse)
async def get_redoc():
    """
    Serve ReDoc documentation
    
    Returns a ReDoc interface for the API documentation with custom styling.
    ReDoc provides an alternative view of the API documentation.
    """
    try:
        openapi_url = "/api/v1/docs/openapi.json"
        return generate_custom_redoc(openapi_url, "OneClass Platform API")
    
    except Exception as e:
        logger.error(f"Failed to generate ReDoc: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load documentation interface")


@router.get("/postman", response_class=JSONResponse)
async def get_postman_collection():
    """
    Get Postman collection for API testing
    
    Returns a Postman collection file that can be imported into Postman
    for easy API testing and exploration.
    """
    try:
        from main import app
        
        generator = OpenAPIGenerator(app)
        collection = generator.generate_postman_collection()
        
        return JSONResponse(
            content=collection,
            headers={
                "Content-Disposition": "attachment; filename=oneclass-platform-api.postman_collection.json"
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to generate Postman collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate Postman collection")


@router.get("/health", response_class=JSONResponse)
async def documentation_health():
    """
    Health check for documentation service
    
    Returns the status of the documentation generation service and
    information about available documentation formats.
    """
    try:
        from main import app
        
        generator = OpenAPIGenerator(app)
        
        # Test schema generation
        schema = generator.generate_openapi_schema()
        endpoint_count = len(schema.get("paths", {}))
        
        return JSONResponse(content={
            "status": "healthy",
            "service": "API Documentation Generator",
            "version": "1.0.0",
            "endpoints_documented": endpoint_count,
            "available_formats": [
                "OpenAPI JSON",
                "OpenAPI YAML", 
                "Swagger UI",
                "ReDoc",
                "Postman Collection"
            ],
            "last_updated": schema.get("info", {}).get("version", "1.0.0")
        })
    
    except Exception as e:
        logger.error(f"Documentation health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=500
        )


@router.post("/generate", response_class=JSONResponse)
async def generate_documentation(
    format: str = "json",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate and save API documentation
    
    Generates API documentation in the specified format and saves it to the file system.
    Requires authentication and admin privileges.
    
    **Parameters:**
    - format: Documentation format (json, yaml, postman)
    
    **Returns:**
    - Generation status and file path
    """
    try:
        # Check user permissions
        if current_user.get("role") not in ["admin", "developer"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to generate documentation"
            )
        
        from main import app
        
        generator = OpenAPIGenerator(app)
        
        # Create documentation directory
        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            file_path = docs_dir / "openapi.json"
            generator.save_schema_to_file(str(file_path), "json")
        
        elif format.lower() == "yaml":
            file_path = docs_dir / "openapi.yaml"
            generator.save_schema_to_file(str(file_path), "yaml")
        
        elif format.lower() == "postman":
            file_path = docs_dir / "postman_collection.json"
            generator.save_postman_collection(str(file_path))
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Supported formats: json, yaml, postman"
            )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Documentation generated successfully",
            "format": format,
            "file_path": str(file_path),
            "generated_by": current_user.get("username"),
            "timestamp": "2024-01-01T00:00:00Z"  # This would be datetime.utcnow()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate documentation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate documentation: {str(e)}"
        )


@router.get("/stats", response_class=JSONResponse)
async def get_documentation_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get API documentation statistics
    
    Returns statistics about the API documentation including endpoint counts,
    tag distribution, and coverage metrics.
    """
    try:
        from main import app
        
        generator = OpenAPIGenerator(app)
        schema = generator.generate_openapi_schema()
        
        # Calculate statistics
        paths = schema.get("paths", {})
        total_endpoints = len(paths)
        
        methods_count = {}
        tags_count = {}
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    # Count HTTP methods
                    method_upper = method.upper()
                    methods_count[method_upper] = methods_count.get(method_upper, 0) + 1
                    
                    # Count tags
                    operation_tags = operation.get("tags", [])
                    for tag in operation_tags:
                        tags_count[tag] = tags_count.get(tag, 0) + 1
        
        # Component statistics
        components = schema.get("components", {})
        schemas_count = len(components.get("schemas", {}))
        security_schemes_count = len(components.get("securitySchemes", {}))
        
        return JSONResponse(content={
            "total_endpoints": total_endpoints,
            "methods_distribution": methods_count,
            "tags_distribution": tags_count,
            "components": {
                "schemas": schemas_count,
                "security_schemes": security_schemes_count
            },
            "api_info": {
                "title": schema.get("info", {}).get("title", ""),
                "version": schema.get("info", {}).get("version", ""),
                "description_length": len(schema.get("info", {}).get("description", "")),
                "servers": len(schema.get("servers", []))
            },
            "generated_at": "2024-01-01T00:00:00Z"  # This would be datetime.utcnow()
        })
    
    except Exception as e:
        logger.error(f"Failed to get documentation stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve documentation statistics"
        )


@router.post("/refresh", response_class=JSONResponse)
async def refresh_documentation(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Refresh API documentation cache
    
    Clears the cached OpenAPI schema and regenerates it. This is useful
    when new endpoints are added or existing ones are modified.
    """
    try:
        # Check user permissions
        if current_user.get("role") not in ["admin", "developer"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to refresh documentation"
            )
        
        from main import app
        
        # Clear cached schema
        app.openapi_schema = None
        
        # Generate new schema
        generator = OpenAPIGenerator(app)
        schema = generator.generate_openapi_schema()
        
        return JSONResponse(content={
            "success": True,
            "message": "Documentation cache refreshed successfully",
            "endpoints_count": len(schema.get("paths", {})),
            "refreshed_by": current_user.get("username"),
            "timestamp": "2024-01-01T00:00:00Z"  # This would be datetime.utcnow()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh documentation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to refresh documentation cache"
        )


@router.get("/export/{format}", response_class=JSONResponse)
async def export_documentation(
    format: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Export API documentation in various formats
    
    Exports the API documentation for download in the specified format.
    Supports JSON, YAML, and Postman collection formats.
    """
    try:
        from main import app
        
        generator = OpenAPIGenerator(app)
        
        if format.lower() == "json":
            schema = generator.generate_openapi_schema()
            filename = "oneclass-platform-api.json"
            content = json.dumps(schema, indent=2)
            content_type = "application/json"
        
        elif format.lower() == "yaml":
            import yaml
            schema = generator.generate_openapi_schema()
            filename = "oneclass-platform-api.yaml"
            content = yaml.dump(schema, default_flow_style=False)
            content_type = "application/yaml"
        
        elif format.lower() == "postman":
            collection = generator.generate_postman_collection()
            filename = "oneclass-platform-api.postman_collection.json"
            content = json.dumps(collection, indent=2)
            content_type = "application/json"
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Supported formats: json, yaml, postman"
            )
        
        return JSONResponse(
            content={
                "filename": filename,
                "content": content,
                "content_type": content_type,
                "size": len(content),
                "exported_by": current_user.get("username"),
                "timestamp": "2024-01-01T00:00:00Z"
            },
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export documentation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to export documentation"
        )