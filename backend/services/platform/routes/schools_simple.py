"""
Simple school routes that bypass tenant middleware
These endpoints are truly public and don't require any dependencies
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import asyncio
import asyncpg
import os

router = APIRouter(prefix="/schools-simple", tags=["simple-schools"])


async def get_db_connection():
    """Get direct database connection bypassing all middleware"""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:123Bubblegums@localhost:5432/oneclass")
    return await asyncpg.connect(database_url)


@router.get("/by-id/{school_id}")
async def get_school_by_id_simple(school_id: str):
    """
    Get school information by ID - completely bypasses tenant middleware
    """
    try:
        # Validate school_id format
        if not school_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid school ID"
            )

        # Direct database connection
        conn = await get_db_connection()

        try:
            # Query school by ID
            query = """
                SELECT
                    id,
                    name,
                    subdomain,
                    school_type,
                    status,
                    logo_url
                FROM platform.schools
                WHERE id = $1
                AND status IN ('active', 'setup')
            """

            row = await conn.fetchrow(query, school_id)

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"School not found for ID: {school_id}"
                )

            return {
                "subdomain": row['subdomain'],
                "schoolName": row['name'],
                "schoolId": str(row['id']),
                "type": row['school_type'] or 'school',
                "status": row['status'],
                "logo_url": row['logo_url']
            }

        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch school by ID: {str(e)}"
        )


@router.get("/by-subdomain/{subdomain}")
async def get_school_by_subdomain_simple(subdomain: str):
    """
    Get school information by subdomain - completely bypasses tenant middleware
    """
    try:
        # Validate subdomain format
        if not subdomain or len(subdomain) < 2 or len(subdomain) > 63:
            raise HTTPException(
                status_code=400,
                detail="Invalid subdomain format"
            )
        
        # Direct database connection
        conn = await get_db_connection()
        
        try:
            # Query school by subdomain
            query = """
                SELECT 
                    id,
                    name,
                    subdomain,
                    school_type,
                    status,
                    logo_url
                FROM platform.schools 
                WHERE subdomain = $1
                AND status IN ('active', 'setup')
            """
            
            row = await conn.fetchrow(query, subdomain)
            
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"School not found for subdomain: {subdomain}"
                )
            
            return {
                "subdomain": row['subdomain'],
                "schoolName": row['name'],
                "schoolId": str(row['id']),
                "type": row['school_type'] or 'school',
                "status": row['status'],
                "logo_url": row['logo_url']
            }
            
        finally:
            await conn.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch school by subdomain: {str(e)}"
        )


@router.get("/health")
async def health_check_simple():
    """Simple health check that bypasses all middleware"""
    return {
        "status": "healthy",
        "service": "simple-schools",
        "bypass": "tenant-middleware"
    }


@router.get("/test-db")
async def test_database_connection():
    """Test direct database connection"""
    try:
        conn = await get_db_connection()
        try:
            result = await conn.fetchval("SELECT COUNT(*) FROM platform.schools")
            return {
                "status": "connected",
                "school_count": result,
                "message": "Database connection successful"
            }
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )
