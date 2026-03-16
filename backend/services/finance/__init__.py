# Finance Service Module
# Complete Finance & Billing system for OneClass educational platform

__version__ = "1.0.0"
__description__ = "Finance & Billing module with Zimbabwe-specific payment processing"

# Note: Imports are lazy to avoid circular dependency when the main app
# registers individual route modules. The standalone sub-app is only
# needed when running Finance as its own microservice.


def get_finance_app():
    """Get the standalone Finance FastAPI sub-app (lazy import)."""
    from .main import app
    return app
