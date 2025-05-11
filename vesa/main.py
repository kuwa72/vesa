"""
VESA - Main application module.
"""
import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from vesa.routes.document_routes import router as document_router
from vesa.routes.web_routes import router as web_router
from vesa.utils.markdown_utils import render_markdown

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="VESA",
    description="ベクトル＋グラフデータベースWiki",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="vesa/static"), name="static")

# Include routers
app.include_router(document_router)
app.include_router(web_router)

# Templates
templates = Jinja2Templates(directory="vesa/templates")

# Add markdown filter to Jinja2 templates
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # Add markdown filter to Jinja2 templates
    templates.env.filters["markdown"] = render_markdown
    
    # Create data directories if they don't exist
    os.makedirs("./data/chroma", exist_ok=True)
    os.makedirs("./data/cozo", exist_ok=True)

# Error handlers
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Any) -> HTMLResponse:
    """Handle 404 errors."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 404,
            "error_message": "ページが見つかりません"
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Any) -> HTMLResponse:
    """Handle 500 errors."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "サーバーエラーが発生しました"
        },
        status_code=500
    )

# Root redirect
@app.get("/", include_in_schema=False)
async def root_redirect(request: Request):
    """Redirect root to home page."""
    return web_router.url_path_for("home")
