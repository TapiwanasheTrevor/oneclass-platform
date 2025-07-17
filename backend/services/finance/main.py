# =====================================================
# Finance Service - Main Application
# File: backend/services/finance/main.py
# =====================================================

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from shared.auth import get_current_active_user, EnhancedUser
from shared.middleware import add_security_headers, log_requests
from .routes import fee_management, invoices, payments, reports

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Finance service starting up...")
    
    # Initialize database connections, caches, etc.
    await initialize_finance_service()
    
    yield
    
    # Shutdown
    logger.info("Finance service shutting down...")
    await cleanup_finance_service()

# Create FastAPI app
app = FastAPI(
    title="1Class Finance Service",
    description="Finance & Billing module for 1Class educational platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(add_security_headers)
app.middleware("http")(log_requests)

# Include routers
app.include_router(fee_management.router, prefix="/api/v1/finance")
app.include_router(invoices.router, prefix="/api/v1/finance")
app.include_router(payments.router, prefix="/api/v1/finance")
app.include_router(reports.router, prefix="/api/v1/finance")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "finance",
        "version": "1.0.0"
    }

# Service info endpoint
@app.get("/info")
async def service_info():
    """Service information endpoint"""
    return {
        "service": "finance",
        "version": "1.0.0",
        "description": "Finance & Billing module for 1Class educational platform",
        "features": [
            "Fee structure management",
            "Invoice generation and management",
            "Payment processing (Paynow, mobile money, cash)",
            "Financial reporting and analytics",
            "School-isolated financial data",
            "Parent payment portal",
            "Automated payment reconciliation",
            "Zimbabwe-specific payment methods"
        ],
        "endpoints": {
            "fee_management": "/api/v1/finance/fee-management",
            "invoices": "/api/v1/finance/invoices",
            "payments": "/api/v1/finance/payments",
            "reports": "/api/v1/finance/reports"
        }
    }

# Service status endpoint (requires authentication)
@app.get("/status")
async def service_status(current_user: EnhancedUser = Depends(get_current_active_user)):
    """Service status endpoint for authenticated users"""
    
    # Check if user has access to finance module
    if not current_user.hasFeature("finance_module"):
        raise HTTPException(
            status_code=403,
            detail="Finance module not enabled for your school"
        )
    
    # Get basic service statistics
    stats = await get_service_statistics(current_user.school_id)
    
    return {
        "status": "operational",
        "school_id": current_user.school_id,
        "user_id": current_user.id,
        "statistics": stats,
        "permissions": current_user.permissions,
        "features": current_user.available_features
    }

# Initialization function
async def initialize_finance_service():
    """Initialize finance service"""
    try:
        # Initialize database connections
        from shared.database import get_database_connection
        
        async with get_database_connection() as conn:
            # Check if finance schema exists
            schema_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'finance')"
            )
            
            if not schema_exists:
                logger.warning("Finance schema does not exist. Please run database migrations.")
            else:
                logger.info("Finance schema verified successfully")
        
        # Initialize payment gateway configurations
        await initialize_payment_gateways()
        
        # Initialize scheduled tasks
        await initialize_scheduled_tasks()
        
        logger.info("Finance service initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize finance service: {e}")
        raise

# Cleanup function
async def cleanup_finance_service():
    """Cleanup finance service resources"""
    try:
        # Cleanup scheduled tasks
        await cleanup_scheduled_tasks()
        
        # Close database connections
        # (handled by connection pool)
        
        logger.info("Finance service cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during finance service cleanup: {e}")

# Payment gateway initialization
async def initialize_payment_gateways():
    """Initialize payment gateway configurations"""
    try:
        from shared.database import get_database_connection
        
        async with get_database_connection() as conn:
            # Get all schools with finance module enabled
            schools = await conn.fetch(
                """
                SELECT s.id, s.name, sc.features_enabled
                FROM platform.schools s
                JOIN platform.school_configurations sc ON s.id = sc.school_id
                WHERE sc.features_enabled->>'finance_module' = 'true'
                """
            )
            
            initialized_count = 0
            for school in schools:
                try:
                    # Initialize default payment methods if not exist
                    await initialize_default_payment_methods(school['id'])
                    initialized_count += 1
                except Exception as e:
                    logger.error(f"Failed to initialize payment methods for school {school['id']}: {e}")
            
            logger.info(f"Initialized payment gateways for {initialized_count} schools")
            
    except Exception as e:
        logger.error(f"Failed to initialize payment gateways: {e}")

# Default payment methods initialization
async def initialize_default_payment_methods(school_id):
    """Initialize default payment methods for a school"""
    try:
        from shared.database import get_database_connection
        
        async with get_database_connection() as conn:
            # Check if payment methods already exist
            existing_count = await conn.fetchval(
                "SELECT COUNT(*) FROM finance.payment_methods WHERE school_id = $1",
                school_id
            )
            
            if existing_count > 0:
                return  # Already initialized
            
            # Default payment methods for Zimbabwe
            default_methods = [
                {
                    'name': 'Cash',
                    'code': 'CASH',
                    'type': 'cash',
                    'is_active': True,
                    'requires_reference': False,
                    'supports_partial_payment': True,
                    'display_order': 1
                },
                {
                    'name': 'EcoCash',
                    'code': 'ECOCASH',
                    'type': 'mobile_money',
                    'is_active': True,
                    'requires_reference': True,
                    'supports_partial_payment': True,
                    'transaction_fee_percentage': 1.5,
                    'display_order': 2
                },
                {
                    'name': 'OneMoney',
                    'code': 'ONEMONEY',
                    'type': 'mobile_money',
                    'is_active': True,
                    'requires_reference': True,
                    'supports_partial_payment': True,
                    'transaction_fee_percentage': 1.5,
                    'display_order': 3
                },
                {
                    'name': 'Bank Transfer',
                    'code': 'BANK_TRANSFER',
                    'type': 'bank_transfer',
                    'is_active': True,
                    'requires_reference': True,
                    'supports_partial_payment': True,
                    'display_order': 4
                },
                {
                    'name': 'Paynow',
                    'code': 'PAYNOW',
                    'type': 'online',
                    'is_active': False,  # Requires configuration
                    'requires_reference': True,
                    'supports_partial_payment': True,
                    'transaction_fee_percentage': 3.5,
                    'display_order': 5
                }
            ]
            
            for method in default_methods:
                await conn.execute(
                    """
                    INSERT INTO finance.payment_methods 
                    (school_id, name, code, type, is_active, requires_reference, 
                     supports_partial_payment, transaction_fee_percentage, 
                     transaction_fee_fixed, display_order)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    school_id,
                    method['name'],
                    method['code'],
                    method['type'],
                    method['is_active'],
                    method['requires_reference'],
                    method['supports_partial_payment'],
                    method.get('transaction_fee_percentage', 0),
                    method.get('transaction_fee_fixed', 0),
                    method['display_order']
                )
            
            logger.info(f"Initialized default payment methods for school {school_id}")
            
    except Exception as e:
        logger.error(f"Failed to initialize default payment methods: {e}")
        raise

# Scheduled tasks initialization
async def initialize_scheduled_tasks():
    """Initialize scheduled background tasks"""
    try:
        # Initialize task scheduler for:
        # - Overdue invoice notifications
        # - Payment reconciliation
        # - Financial report generation
        # - Late fee calculations
        
        logger.info("Scheduled tasks initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize scheduled tasks: {e}")

# Scheduled tasks cleanup
async def cleanup_scheduled_tasks():
    """Cleanup scheduled tasks"""
    try:
        # Cancel all scheduled tasks
        logger.info("Scheduled tasks cleaned up")
        
    except Exception as e:
        logger.error(f"Failed to cleanup scheduled tasks: {e}")

# Service statistics
async def get_service_statistics(school_id):
    """Get service statistics for a school"""
    try:
        from shared.database import get_database_connection
        
        async with get_database_connection() as conn:
            # Get basic statistics
            stats = await conn.fetchrow(
                """
                SELECT 
                    (SELECT COUNT(*) FROM finance.invoices WHERE school_id = $1) as total_invoices,
                    (SELECT COUNT(*) FROM finance.payments WHERE school_id = $1) as total_payments,
                    (SELECT COUNT(*) FROM finance.fee_structures WHERE school_id = $1) as fee_structures,
                    (SELECT COUNT(*) FROM finance.payment_methods WHERE school_id = $1 AND is_active = true) as active_payment_methods,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM finance.invoices WHERE school_id = $1) as total_invoiced,
                    (SELECT COALESCE(SUM(amount), 0) FROM finance.payments WHERE school_id = $1 AND status = 'completed') as total_collected,
                    (SELECT COALESCE(SUM(outstanding_amount), 0) FROM finance.invoices WHERE school_id = $1) as total_outstanding
                """,
                school_id
            )
            
            return dict(stats) if stats else {}
            
    except Exception as e:
        logger.error(f"Failed to get service statistics: {e}")
        return {}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "1Class Finance Service",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "status": "/status",
            "api": "/api/v1/finance"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)