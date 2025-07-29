"""
Reports API Routes
Custom report generation and management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..schemas import (
    ReportTemplateCreate, ReportTemplateResponse, ReportExecutionRequest,
    ReportExecutionResponse, CustomReportRequest, ReportDataResponse,
    ExportRequest, ExportResponse
)
from shared.middleware.tenant_middleware import get_tenant_context, get_school_id, get_user_session
from shared.auth import db_manager

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

@router.get("/templates")
async def list_report_templates(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List available report templates
    """
    school_id = get_school_id(request)
    user_session = get_user_session(request)
    
    try:
        async with db_manager.get_connection() as db:
            # Build query with filters
            where_conditions = ["school_id = $1", "is_active = true"]
            params = [school_id]
            param_count = 1
            
            if category:
                param_count += 1
                where_conditions.append(f"category = ${param_count}")
                params.append(category)
            
            if is_public is not None:
                param_count += 1
                where_conditions.append(f"is_public = ${param_count}")
                params.append(is_public)
            
            # Add user access filter (own reports or public reports)
            if user_session:
                param_count += 1
                where_conditions.append(f"(is_public = true OR created_by = ${param_count})")
                params.append(user_session.user_id)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT id, name, description, category, report_type, is_public, 
                       created_by, created_at, updated_at
                FROM analytics.report_templates
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([limit, offset])
            
            templates = await db.fetch(query, *params)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM analytics.report_templates WHERE {where_clause}"
            total_count = await db.fetchval(count_query, *params[:-2])  # Exclude limit/offset
            
            return {
                "templates": [
                    ReportTemplateResponse(
                        id=str(template["id"]),
                        name=template["name"],
                        description=template["description"],
                        category=template["category"],
                        report_type=template["report_type"],
                        is_public=template["is_public"],
                        created_by=str(template["created_by"]),
                        created_at=template["created_at"],
                        updated_at=template["updated_at"]
                    )
                    for template in templates
                ],
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list report templates: {str(e)}"
        )

@router.post("/templates", response_model=ReportTemplateResponse)
async def create_report_template(
    request: Request,
    template_data: ReportTemplateCreate
):
    """
    Create a new report template
    """
    school_id = get_school_id(request)
    user_session = get_user_session(request)
    tenant = get_tenant_context(request)
    
    if not user_session:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if advanced reporting is enabled
    if "advanced_reporting" not in tenant.enabled_modules:
        raise HTTPException(
            status_code=403,
            detail="Advanced Analytics & Reporting module is not enabled"
        )
    
    try:
        template_id = str(uuid.uuid4())
        
        async with db_manager.get_connection() as db:
            query = """
                INSERT INTO analytics.report_templates 
                (id, school_id, name, description, category, report_type, data_sources, 
                 filters, columns, charts, created_by, is_public, allowed_roles)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id, name, description, category, report_type, is_public, 
                         created_by, created_at, updated_at
            """
            
            result = await db.fetchrow(
                query,
                template_id,
                school_id,
                template_data.name,
                template_data.description,
                template_data.category,
                template_data.report_type,
                template_data.data_sources,
                template_data.filters,
                template_data.columns,
                template_data.charts,
                user_session.user_id,
                template_data.is_public,
                template_data.allowed_roles
            )
            
            return ReportTemplateResponse(
                id=str(result["id"]),
                name=result["name"],
                description=result["description"],
                category=result["category"],
                report_type=result["report_type"],
                is_public=result["is_public"],
                created_by=str(result["created_by"]),
                created_at=result["created_at"],
                updated_at=result["updated_at"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create report template: {str(e)}"
        )

@router.get("/templates/{template_id}")
async def get_report_template(
    request: Request,
    template_id: str
):
    """
    Get a specific report template
    """
    school_id = get_school_id(request)
    user_session = get_user_session(request)
    
    try:
        async with db_manager.get_connection() as db:
            query = """
                SELECT * FROM analytics.report_templates
                WHERE id = $1 AND school_id = $2 AND is_active = true
            """
            
            template = await db.fetchrow(query, template_id, school_id)
            
            if not template:
                raise HTTPException(status_code=404, detail="Report template not found")
            
            # Check access permissions
            if not template["is_public"] and template["created_by"] != user_session.user_id:
                if user_session.role not in template.get("allowed_roles", []):
                    raise HTTPException(status_code=403, detail="Access denied to this report template")
            
            return {
                "id": str(template["id"]),
                "name": template["name"],
                "description": template["description"],
                "category": template["category"],
                "report_type": template["report_type"],
                "data_sources": template["data_sources"],
                "filters": template["filters"],
                "columns": template["columns"],
                "charts": template["charts"],
                "is_public": template["is_public"],
                "allowed_roles": template["allowed_roles"],
                "created_by": str(template["created_by"]),
                "created_at": template["created_at"],
                "updated_at": template["updated_at"]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get report template: {str(e)}"
        )

@router.post("/execute", response_model=ReportExecutionResponse)
async def execute_report(
    request: Request,
    background_tasks: BackgroundTasks,
    execution_request: ReportExecutionRequest
):
    """
    Execute a report template
    """
    school_id = get_school_id(request)
    user_session = get_user_session(request)
    
    if not user_session:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        execution_id = str(uuid.uuid4())
        
        async with db_manager.get_connection() as db:
            # Get template details
            template_query = """
                SELECT * FROM analytics.report_templates
                WHERE id = $1 AND school_id = $2 AND is_active = true
            """
            
            template = await db.fetchrow(template_query, execution_request.template_id, school_id)
            
            if not template:
                raise HTTPException(status_code=404, detail="Report template not found")
            
            # Create execution record
            insert_query = """
                INSERT INTO analytics.report_executions
                (id, school_id, template_id, executed_by, execution_date, 
                 parameters, filters_applied, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
                RETURNING id, template_id, status, execution_date
            """
            
            result = await db.fetchrow(
                insert_query,
                execution_id,
                school_id,
                execution_request.template_id,
                user_session.user_id,
                datetime.utcnow(),
                execution_request.parameters,
                execution_request.filters
            )
            
            # Queue background report generation
            background_tasks.add_task(
                _generate_report_data,
                execution_id,
                school_id,
                template,
                execution_request
            )
            
            return ReportExecutionResponse(
                id=str(result["id"]),
                template_id=str(result["template_id"]),
                status=result["status"],
                execution_date=result["execution_date"],
                parameters=execution_request.parameters,
                row_count=None,
                file_path=None,
                download_url=None
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute report: {str(e)}"
        )

@router.get("/executions")
async def list_report_executions(
    request: Request,
    template_id: Optional[str] = Query(None, description="Filter by template ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List report executions
    """
    school_id = get_school_id(request)
    user_session = get_user_session(request)
    
    try:
        async with db_manager.get_connection() as db:
            where_conditions = ["school_id = $1"]
            params = [school_id]
            param_count = 1
            
            if template_id:
                param_count += 1
                where_conditions.append(f"template_id = ${param_count}")
                params.append(template_id)
            
            if status:
                param_count += 1
                where_conditions.append(f"status = ${param_count}")
                params.append(status)
            
            # Filter by user if not admin
            if user_session and user_session.role != 'admin':
                param_count += 1
                where_conditions.append(f"executed_by = ${param_count}")
                params.append(user_session.user_id)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT re.*, rt.name as template_name
                FROM analytics.report_executions re
                LEFT JOIN analytics.report_templates rt ON re.template_id = rt.id
                WHERE {where_clause}
                ORDER BY execution_date DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([limit, offset])
            executions = await db.fetch(query, *params)
            
            results = []
            for execution in executions:
                download_url = None
                if execution["status"] == "completed" and execution["file_path"]:
                    download_url = f"/api/v1/reports/download/{execution['id']}"
                
                results.append({
                    "id": str(execution["id"]),
                    "template_id": str(execution["template_id"]),
                    "template_name": execution["template_name"],
                    "status": execution["status"],
                    "execution_date": execution["execution_date"],
                    "parameters": execution["parameters"],
                    "row_count": execution["row_count"],
                    "file_path": execution["file_path"],
                    "download_url": download_url,
                    "error_message": execution["error_message"]
                })
            
            return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list report executions: {str(e)}"
        )

@router.get("/executions/{execution_id}")
async def get_report_execution(
    request: Request,
    execution_id: str
):
    """
    Get report execution status and results
    """
    school_id = get_school_id(request)
    
    try:
        async with db_manager.get_connection() as db:
            query = """
                SELECT * FROM analytics.report_executions
                WHERE id = $1 AND school_id = $2
            """
            
            execution = await db.fetchrow(query, execution_id, school_id)
            
            if not execution:
                raise HTTPException(status_code=404, detail="Report execution not found")
            
            download_url = None
            if execution["status"] == "completed" and execution["file_path"]:
                download_url = f"/api/v1/reports/download/{execution_id}"
            
            return ReportExecutionResponse(
                id=str(execution["id"]),
                template_id=str(execution["template_id"]),
                status=execution["status"],
                execution_date=execution["execution_date"],
                parameters=execution["parameters"],
                row_count=execution["row_count"],
                file_path=execution["file_path"],
                download_url=download_url
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get report execution: {str(e)}"
        )

@router.post("/custom", response_model=ReportDataResponse)
async def generate_custom_report(
    request: Request,
    report_request: CustomReportRequest
):
    """
    Generate a custom report with specified parameters
    """
    school_id = get_school_id(request)
    tenant = get_tenant_context(request)
    
    # Check if advanced reporting is enabled
    if "advanced_reporting" not in tenant.enabled_modules:
        raise HTTPException(
            status_code=403,
            detail="Advanced Analytics & Reporting module is not enabled"
        )
    
    try:
        # This is a simplified implementation
        # In production, this would dynamically query based on data_source and filters
        
        # Sample data for demonstration
        sample_data = []
        
        if report_request.data_source == "students":
            sample_data = [
                {"id": "1", "name": "John Doe", "grade": "10", "enrollment_date": "2024-01-15"},
                {"id": "2", "name": "Jane Smith", "grade": "11", "enrollment_date": "2024-01-16"},
                {"id": "3", "name": "Bob Wilson", "grade": "9", "enrollment_date": "2024-01-17"}
            ]
        elif report_request.data_source == "financial":
            sample_data = [
                {"invoice_id": "INV-001", "amount": 500.00, "status": "paid", "date": "2024-01-15"},
                {"invoice_id": "INV-002", "amount": 750.00, "status": "pending", "date": "2024-01-16"},
                {"invoice_id": "INV-003", "amount": 600.00, "status": "paid", "date": "2024-01-17"}
            ]
        
        # Apply filters (simplified)
        filtered_data = sample_data
        if report_request.filters:
            # In production, implement proper filtering logic
            pass
        
        # Apply limit
        if report_request.limit:
            filtered_data = filtered_data[:report_request.limit]
        
        return ReportDataResponse(
            columns=report_request.columns,
            data=filtered_data,
            total_rows=len(sample_data),
            page=1,
            page_size=len(filtered_data),
            filters_applied=report_request.filters
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate custom report: {str(e)}"
        )

@router.get("/categories")
async def get_report_categories(request: Request):
    """
    Get available report categories
    """
    return {
        "categories": [
            {
                "id": "academic",
                "name": "Academic Reports",
                "description": "Student performance, grades, and assessments"
            },
            {
                "id": "financial",
                "name": "Financial Reports", 
                "description": "Fee management, payments, and revenue"
            },
            {
                "id": "administrative",
                "name": "Administrative Reports",
                "description": "Staff, operations, and compliance"
            },
            {
                "id": "analytics",
                "name": "Analytics Reports",
                "description": "Data insights and trend analysis"
            },
            {
                "id": "custom",
                "name": "Custom Reports",
                "description": "User-defined reports and queries"
            }
        ]
    }

@router.post("/export", response_model=ExportResponse)
async def export_report_data(
    request: Request,
    background_tasks: BackgroundTasks,
    export_request: ExportRequest
):
    """
    Export report data in various formats
    """
    school_id = get_school_id(request)
    user_session = get_user_session(request)
    
    if not user_session:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    export_id = str(uuid.uuid4())
    
    # Queue background export task
    background_tasks.add_task(
        _process_export,
        export_id,
        school_id,
        export_request
    )
    
    return ExportResponse(
        export_id=export_id,
        status="queued",
        download_url=None,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        created_at=datetime.utcnow()
    )

# Background task functions
async def _generate_report_data(
    execution_id: str,
    school_id: str,
    template: dict,
    execution_request: ReportExecutionRequest
):
    """
    Background task to generate report data
    """
    try:
        # Simulate report generation
        import asyncio
        await asyncio.sleep(2)  # Simulate processing time
        
        # Update execution status
        async with db_manager.get_connection() as db:
            await db.execute(
                """
                UPDATE analytics.report_executions
                SET status = 'completed', execution_time_ms = 2000, row_count = 100,
                    file_path = $1, completed_at = $2
                WHERE id = $3
                """,
                f"/reports/{execution_id}.json",
                datetime.utcnow(),
                execution_id
            )
    except Exception as e:
        # Update with error status
        async with db_manager.get_connection() as db:
            await db.execute(
                """
                UPDATE analytics.report_executions
                SET status = 'failed', error_message = $1, completed_at = $2
                WHERE id = $3
                """,
                str(e),
                datetime.utcnow(),
                execution_id
            )

async def _process_export(
    export_id: str,
    school_id: str,
    export_request: ExportRequest
):
    """
    Background task to process data export
    """
    try:
        # Simulate export processing
        import asyncio
        await asyncio.sleep(3)  # Simulate processing time
        
        # In production, this would generate actual files
        print(f"Export {export_id} completed for school {school_id}")
    except Exception as e:
        print(f"Export {export_id} failed: {str(e)}")