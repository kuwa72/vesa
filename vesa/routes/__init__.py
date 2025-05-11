"""
Routes initialization module.
"""
from vesa.routes.document_routes import router as document_router
from vesa.routes.web_routes import router as web_router

# Export routers
__all__ = ['document_router', 'web_router']
