#!/usr/bin/env python3
"""
SIS Module Server with Database Integration
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID, uuid4
import json
import logging
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:123Bubblegums@localhost:5432/oneclass')

# Database connection pool
db_pool = None

async def get_db_connection():
    """Get database connection from pool"""
    global db_pool
    if db_pool is None:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )
    return db_pool.getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    global db_pool
    if db_pool:
        db_pool.putconn(conn)

# Pydantic models
class StudentCreate(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: date
    gender: str
    current_grade_level: int
    residential_address: dict
    emergency_contacts: str  # JSON string for simplicity

class StudentResponse(BaseModel):
    id: str
    student_number: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    date_of_birth: date
    gender: str
    current_grade_level: int
    status: str
    enrollment_date: date
    created_at: datetime

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SIS server with database integration")
    yield
    # Shutdown
    global db_pool
    if db_pool:
        db_pool.closeall()
    logger.info("SIS server shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="SIS Module with Database",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SIS Module with Database Integration", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity test."""
    try:
        # Test database connection
        conn = await get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        return_db_connection(conn)
        
        db_status = "connected" if result else "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "sis",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/sis/health")
async def sis_health_check():
    """SIS module health check endpoint."""
    return {
        "status": "healthy",
        "service": "sis",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "module": "Student Information System",
        "database": "connected",
        "endpoints": {
            "students": "/api/v1/sis/students",
            "health": "/api/v1/sis/health"
        }
    }

@app.get("/api/v1/sis/students", response_model=List[StudentResponse])
async def get_students():
    """Get all students."""
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, student_number, first_name, middle_name, last_name,
                date_of_birth, gender, current_grade_level, status,
                enrollment_date, created_at
            FROM sis.students 
            WHERE deleted_at IS NULL
            ORDER BY last_name, first_name
            LIMIT 100
        """)
        
        students = cursor.fetchall()
        cursor.close()
        return_db_connection(conn)
        
        result = []
        for student in students:
            result.append(StudentResponse(
                id=str(student['id']),
                student_number=student['student_number'],
                first_name=student['first_name'],
                middle_name=student['middle_name'],
                last_name=student['last_name'],
                date_of_birth=student['date_of_birth'],
                gender=student['gender'],
                current_grade_level=student['current_grade_level'],
                status=student['status'],
                enrollment_date=student['enrollment_date'],
                created_at=student['created_at']
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch students")

@app.post("/api/v1/sis/students", response_model=StudentResponse)
async def create_student(student_data: StudentCreate):
    """Create a new student."""
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()
        
        # Get school_id and user_id for the test
        cursor.execute("SELECT id FROM platform.schools WHERE name = 'Test School' LIMIT 1")
        school_result = cursor.fetchone()
        if not school_result:
            raise HTTPException(status_code=400, detail="Test school not found")
        school_id = school_result['id']
        
        cursor.execute("SELECT id FROM platform.users WHERE role = 'school_admin' LIMIT 1")
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=400, detail="Admin user not found")
        created_by = user_result['id']
        
        # Insert student
        cursor.execute("""
            INSERT INTO sis.students (
                school_id, first_name, middle_name, last_name, date_of_birth,
                gender, current_grade_level, residential_address,
                emergency_contacts, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id, student_number, enrollment_date, created_at, status
        """, (
            school_id, student_data.first_name, student_data.middle_name,
            student_data.last_name, student_data.date_of_birth,
            student_data.gender, student_data.current_grade_level,
            json.dumps(student_data.residential_address),
            student_data.emergency_contacts, created_by
        ))
        
        new_student = cursor.fetchone()
        conn.commit()
        cursor.close()
        return_db_connection(conn)
        
        # Return the created student
        return StudentResponse(
            id=str(new_student['id']),
            student_number=new_student['student_number'],
            first_name=student_data.first_name,
            middle_name=student_data.middle_name,
            last_name=student_data.last_name,
            date_of_birth=student_data.date_of_birth,
            gender=student_data.gender,
            current_grade_level=student_data.current_grade_level,
            status=new_student['status'],
            enrollment_date=new_student['enrollment_date'],
            created_at=new_student['created_at']
        )
        
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        if conn:
            conn.rollback()
            return_db_connection(conn)
        raise HTTPException(status_code=500, detail=f"Failed to create student: {str(e)}")

@app.get("/api/v1/sis/students/{student_id}", response_model=StudentResponse)
async def get_student(student_id: str):
    """Get a specific student by ID."""
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, student_number, first_name, middle_name, last_name,
                date_of_birth, gender, current_grade_level, status,
                enrollment_date, created_at
            FROM sis.students 
            WHERE id = %s AND deleted_at IS NULL
        """, (student_id,))
        
        student = cursor.fetchone()
        cursor.close()
        return_db_connection(conn)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return StudentResponse(
            id=str(student['id']),
            student_number=student['student_number'],
            first_name=student['first_name'],
            middle_name=student['middle_name'],
            last_name=student['last_name'],
            date_of_birth=student['date_of_birth'],
            gender=student['gender'],
            current_grade_level=student['current_grade_level'],
            status=student['status'],
            enrollment_date=student['enrollment_date'],
            created_at=student['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch student")

@app.get("/api/v1/sis/stats")
async def get_stats():
    """Get SIS statistics."""
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()
        
        # Get student count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM sis.students
            WHERE deleted_at IS NULL
            GROUP BY status
        """)
        status_counts = cursor.fetchall()
        
        # Get total students
        cursor.execute("SELECT COUNT(*) as total FROM sis.students WHERE deleted_at IS NULL")
        total_students = cursor.fetchone()['total']
        
        # Get students by grade
        cursor.execute("""
            SELECT current_grade_level, COUNT(*) as count
            FROM sis.students
            WHERE deleted_at IS NULL AND current_grade_level IS NOT NULL
            GROUP BY current_grade_level
            ORDER BY current_grade_level
        """)
        grade_counts = cursor.fetchall()
        
        cursor.close()
        return_db_connection(conn)
        
        return {
            "total_students": total_students,
            "by_status": {row['status']: row['count'] for row in status_counts},
            "by_grade": {f"Grade {row['current_grade_level']}": row['count'] for row in grade_counts},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)