#!/usr/bin/env python3
"""
Simple test server for SIS module health check
"""
from fastapi import FastAPI
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SIS Module Test Server", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "SIS Module Test Server", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring."""
    return {
        "status": "healthy",
        "service": "sis",
        "version": "1.0.0",
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
        "endpoints": {
            "students": "/api/v1/sis/students",
            "guardians": "/api/v1/sis/guardians",
            "attendance": "/api/v1/sis/attendance",
            "health": "/api/v1/sis/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)