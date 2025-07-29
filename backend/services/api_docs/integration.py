"""
API Documentation Integration
Integration utilities for FastAPI applications
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import logging

from .generator import OpenAPIGenerator
from .routes import router
from .markdown_generator import MarkdownGenerator, generate_markdown_docs

logger = logging.getLogger(__name__)


def setup_api_documentation(
    app: FastAPI,
    title: str = "OneClass Platform API",
    version: str = "1.0.0",
    description: Optional[str] = None,
    enable_ui: bool = True,
    enable_redoc: bool = True,
    enable_postman: bool = True,
    enable_markdown: bool = True,
    custom_css: Optional[str] = None,
    custom_js: Optional[str] = None
) -> OpenAPIGenerator:
    """
    Set up comprehensive API documentation for a FastAPI application
    
    Args:
        app: FastAPI application instance
        title: API title
        version: API version
        description: API description
        enable_ui: Enable Swagger UI
        enable_redoc: Enable ReDoc
        enable_postman: Enable Postman collection
        enable_markdown: Enable markdown documentation
        custom_css: Custom CSS for documentation
        custom_js: Custom JavaScript for documentation
    
    Returns:
        OpenAPIGenerator instance
    """
    # Create generator
    generator = OpenAPIGenerator(app, title, version)
    
    # Set custom description if provided
    if description:
        generator.info["description"] = description
    
    # Include documentation routes
    app.include_router(router)
    
    # Add CORS middleware for documentation endpoints
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store generator instance for later use
    app.state.documentation_generator = generator
    
    logger.info(f"API documentation setup complete for {title} v{version}")
    return generator


def generate_all_documentation(
    app: FastAPI,
    output_dir: str = "docs/api",
    formats: Optional[list] = None
) -> Dict[str, str]:
    """
    Generate all documentation formats and save to files
    
    Args:
        app: FastAPI application instance
        output_dir: Output directory for documentation files
        formats: List of formats to generate (default: all)
    
    Returns:
        Dictionary mapping format names to file paths
    """
    if formats is None:
        formats = ["json", "yaml", "postman", "markdown"]
    
    # Get generator from app state or create new one
    generator = getattr(app.state, 'documentation_generator', None)
    if not generator:
        generator = OpenAPIGenerator(app)
    
    generated_files = {}
    
    # Generate OpenAPI JSON
    if "json" in formats:
        json_path = f"{output_dir}/openapi.json"
        generator.save_schema_to_file(json_path, "json")
        generated_files["json"] = json_path
    
    # Generate OpenAPI YAML
    if "yaml" in formats:
        yaml_path = f"{output_dir}/openapi.yaml"
        generator.save_schema_to_file(yaml_path, "yaml")
        generated_files["yaml"] = yaml_path
    
    # Generate Postman collection
    if "postman" in formats:
        postman_path = f"{output_dir}/postman_collection.json"
        generator.save_postman_collection(postman_path)
        generated_files["postman"] = postman_path
    
    # Generate Markdown documentation
    if "markdown" in formats:
        markdown_path = f"{output_dir}/README.md"
        schema = generator.generate_openapi_schema()
        generate_markdown_docs(schema, markdown_path)
        generated_files["markdown"] = markdown_path
    
    logger.info(f"Generated documentation in {len(generated_files)} formats")
    return generated_files


def validate_api_documentation(app: FastAPI) -> Dict[str, Any]:
    """
    Validate API documentation completeness and quality
    
    Args:
        app: FastAPI application instance
    
    Returns:
        Validation results
    """
    generator = OpenAPIGenerator(app)
    schema = generator.generate_openapi_schema()
    
    validation_results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "score": 100,
        "recommendations": []
    }
    
    # Check basic schema structure
    required_fields = ["openapi", "info", "paths"]
    for field in required_fields:
        if field not in schema:
            validation_results["errors"].append(f"Missing required field: {field}")
            validation_results["valid"] = False
            validation_results["score"] -= 20
    
    # Check info section
    info = schema.get("info", {})
    if not info.get("title"):
        validation_results["warnings"].append("API title is missing")
        validation_results["score"] -= 5
    
    if not info.get("version"):
        validation_results["warnings"].append("API version is missing")
        validation_results["score"] -= 5
    
    if not info.get("description"):
        validation_results["warnings"].append("API description is missing")
        validation_results["score"] -= 5
    
    # Check paths
    paths = schema.get("paths", {})
    if not paths:
        validation_results["errors"].append("No API paths defined")
        validation_results["valid"] = False
        validation_results["score"] -= 30
    
    # Check for undocumented endpoints
    undocumented_count = 0
    for path, methods in paths.items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                if not operation.get("summary"):
                    undocumented_count += 1
                    validation_results["warnings"].append(f"Missing summary for {method.upper()} {path}")
                
                if not operation.get("description"):
                    validation_results["warnings"].append(f"Missing description for {method.upper()} {path}")
    
    if undocumented_count > 0:
        validation_results["score"] -= min(undocumented_count * 2, 20)
    
    # Check security schemes
    components = schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    if not security_schemes:
        validation_results["warnings"].append("No security schemes defined")
        validation_results["score"] -= 10
    
    # Check examples
    examples_count = 0
    for path, methods in paths.items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                # Check for request body examples
                request_body = operation.get("requestBody", {})
                if request_body:
                    content = request_body.get("content", {})
                    for content_type, content_info in content.items():
                        if "examples" in content_info or "example" in content_info:
                            examples_count += 1
                
                # Check for response examples
                responses = operation.get("responses", {})
                for status_code, response_info in responses.items():
                    response_content = response_info.get("content", {})
                    for content_type, content_info in response_content.items():
                        if "examples" in content_info or "example" in content_info:
                            examples_count += 1
    
    if examples_count == 0:
        validation_results["warnings"].append("No examples found in documentation")
        validation_results["score"] -= 15
    
    # Generate recommendations
    if validation_results["score"] < 90:
        validation_results["recommendations"].append("Add more detailed descriptions to endpoints")
    
    if validation_results["score"] < 80:
        validation_results["recommendations"].append("Include examples for request/response bodies")
    
    if validation_results["score"] < 70:
        validation_results["recommendations"].append("Add security schemes and authentication documentation")
    
    if validation_results["score"] < 60:
        validation_results["recommendations"].append("Review and improve overall documentation coverage")
    
    # Ensure score doesn't go below 0
    validation_results["score"] = max(validation_results["score"], 0)
    
    return validation_results


def get_documentation_metrics(app: FastAPI) -> Dict[str, Any]:
    """
    Get documentation metrics and statistics
    
    Args:
        app: FastAPI application instance
    
    Returns:
        Documentation metrics
    """
    generator = OpenAPIGenerator(app)
    schema = generator.generate_openapi_schema()
    
    paths = schema.get("paths", {})
    components = schema.get("components", {})
    
    # Count endpoints
    total_endpoints = 0
    methods_count = {}
    tags_count = {}
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                total_endpoints += 1
                
                # Count HTTP methods
                method_upper = method.upper()
                methods_count[method_upper] = methods_count.get(method_upper, 0) + 1
                
                # Count tags
                operation_tags = operation.get("tags", [])
                for tag in operation_tags:
                    tags_count[tag] = tags_count.get(tag, 0) + 1
    
    # Count schemas
    schemas_count = len(components.get("schemas", {}))
    security_schemes_count = len(components.get("securitySchemes", {}))
    
    # Calculate documentation coverage
    documented_endpoints = 0
    for path, methods in paths.items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                if (operation.get("summary") and 
                    operation.get("description") and 
                    operation.get("responses")):
                    documented_endpoints += 1
    
    coverage_percentage = (documented_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
    
    return {
        "total_endpoints": total_endpoints,
        "documented_endpoints": documented_endpoints,
        "coverage_percentage": round(coverage_percentage, 2),
        "methods_distribution": methods_count,
        "tags_distribution": tags_count,
        "schemas_count": schemas_count,
        "security_schemes_count": security_schemes_count,
        "api_version": schema.get("info", {}).get("version", "unknown"),
        "openapi_version": schema.get("openapi", "unknown")
    }


def update_documentation_config(
    app: FastAPI,
    config: Dict[str, Any]
) -> bool:
    """
    Update documentation configuration
    
    Args:
        app: FastAPI application instance
        config: Configuration updates
    
    Returns:
        Success status
    """
    try:
        generator = getattr(app.state, 'documentation_generator', None)
        if not generator:
            generator = OpenAPIGenerator(app)
            app.state.documentation_generator = generator
        
        # Update generator properties
        if "title" in config:
            generator.title = config["title"]
        
        if "version" in config:
            generator.version = config["version"]
        
        if "base_url" in config:
            generator.base_url = config["base_url"]
        
        if "contact_info" in config:
            generator.contact_info.update(config["contact_info"])
        
        if "license_info" in config:
            generator.license_info.update(config["license_info"])
        
        # Clear cached schema to force regeneration
        app.openapi_schema = None
        
        logger.info("Documentation configuration updated successfully")
        return True
    
    except Exception as e:
        logger.error(f"Failed to update documentation config: {str(e)}")
        return False


def export_documentation_bundle(
    app: FastAPI,
    output_path: str,
    include_formats: Optional[list] = None
) -> str:
    """
    Export complete documentation bundle as ZIP file
    
    Args:
        app: FastAPI application instance
        output_path: Output ZIP file path
        include_formats: Formats to include in bundle
    
    Returns:
        Path to created ZIP file
    """
    import zipfile
    import tempfile
    import os
    from pathlib import Path
    
    if include_formats is None:
        include_formats = ["json", "yaml", "postman", "markdown"]
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate all documentation formats
        generated_files = generate_all_documentation(
            app, 
            temp_dir, 
            include_formats
        )
        
        # Create ZIP file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for format_name, file_path in generated_files.items():
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
        
        logger.info(f"Documentation bundle exported to {output_path}")
        return str(output_path)


# Decorator for automatic documentation enhancement
def enhance_endpoint_docs(
    summary: str = None,
    description: str = None,
    tags: list = None,
    response_examples: Dict[str, Any] = None
):
    """
    Decorator to enhance endpoint documentation
    
    Args:
        summary: Endpoint summary
        description: Endpoint description
        tags: Endpoint tags
        response_examples: Response examples
    """
    def decorator(func):
        if summary:
            func.__doc__ = f"{summary}\n\n{func.__doc__ or ''}"
        
        # Store metadata for OpenAPI generation
        if not hasattr(func, "__openapi_metadata__"):
            func.__openapi_metadata__ = {}
        
        if summary:
            func.__openapi_metadata__["summary"] = summary
        if description:
            func.__openapi_metadata__["description"] = description
        if tags:
            func.__openapi_metadata__["tags"] = tags
        if response_examples:
            func.__openapi_metadata__["response_examples"] = response_examples
        
        return func
    
    return decorator