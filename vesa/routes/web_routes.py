"""
Web routes for the application.
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from vesa.services.document_service import DocumentService
from vesa.utils.markdown_utils import render_markdown

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="vesa/templates")

# Add markdown filter to Jinja2 templates
templates.env.filters["markdown"] = render_markdown


def get_document_service() -> DocumentService:
    """Dependency for document service."""
    return DocumentService()


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    service: DocumentService = Depends(get_document_service)
):
    """Home page."""
    # Get recent documents for display
    recent_docs = service.search_documents("", limit=10)
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "documents": [result.document for result in recent_docs]
        }
    )


@router.get("/documents/new", response_class=HTMLResponse)
async def new_document_form(request: Request):
    """New document form."""
    return templates.TemplateResponse(
        "document_form.html",
        {
            "request": request,
            "document": None,
            "is_new": True
        }
    )


@router.post("/documents/new")
async def create_document(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
    service: DocumentService = Depends(get_document_service)
):
    """Create a new document."""
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    metadata = {"tags": tag_list}
    
    document = service.create_document(title, content, metadata)
    return RedirectResponse(f"/documents/{document.id}", status_code=303)


@router.get("/documents/{doc_id}", response_class=HTMLResponse)
async def view_document(
    request: Request,
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """View a document."""
    document = service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    related_docs = service.get_related_documents(doc_id)
    
    return templates.TemplateResponse(
        "document_view.html",
        {
            "request": request,
            "document": document,
            "related_documents": related_docs
        }
    )


@router.get("/documents/{doc_id}/edit", response_class=HTMLResponse)
async def edit_document_form(
    request: Request,
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Edit document form."""
    document = service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return templates.TemplateResponse(
        "document_form.html",
        {
            "request": request,
            "document": document,
            "is_new": False
        }
    )


@router.post("/documents/{doc_id}/edit")
async def update_document(
    request: Request,
    doc_id: str,
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
    service: DocumentService = Depends(get_document_service)
):
    """Update a document."""
    document = service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    metadata = {"tags": tag_list}
    
    service.update_document(doc_id, title, content, metadata)
    return RedirectResponse(f"/documents/{doc_id}", status_code=303)


@router.get("/search", response_class=HTMLResponse)
async def search_form(
    request: Request,
    q: Optional[str] = None,
    service: DocumentService = Depends(get_document_service)
):
    """Search form and results."""
    results = []
    if q:
        results = service.search_documents(q)
        
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": q,
            "results": results
        }
    )


@router.get("/graph", response_class=HTMLResponse)
async def document_graph(
    request: Request,
    service: DocumentService = Depends(get_document_service)
):
    """Document relationship graph visualization."""
    graph = service.get_document_graph()
    
    return templates.TemplateResponse(
        "graph.html",
        {
            "request": request,
            "graph": graph
        }
    )
