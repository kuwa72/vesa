"""
Document routes for the API.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from vesa.models.document import Document, DocumentRelationship, DocumentSearchResult, DocumentGraph
from vesa.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    """Dependency for document service."""
    return DocumentService()


@router.post("/", response_model=Document)
async def create_document(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    service: DocumentService = Depends(get_document_service)
):
    """Create a new document."""
    return service.create_document(title, content, metadata)


@router.get("/{doc_id}", response_model=Document)
async def get_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Get a document by ID."""
    document = service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{doc_id}", response_model=Document)
async def update_document(
    doc_id: str,
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    service: DocumentService = Depends(get_document_service)
):
    """Update a document."""
    document = service.update_document(doc_id, title, content, metadata)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Delete a document."""
    success = service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success", "message": "Document deleted"}


@router.get("/search/", response_model=List[DocumentSearchResult])
async def search_documents(
    query: str,
    limit: int = 10,
    service: DocumentService = Depends(get_document_service)
):
    """Search for documents."""
    return service.search_documents(query, limit)


@router.post("/relationships/", response_model=DocumentRelationship)
async def create_relationship(
    source_id: str,
    target_id: str,
    relationship_type: str,
    properties: Optional[Dict[str, Any]] = None,
    service: DocumentService = Depends(get_document_service)
):
    """Create a relationship between documents."""
    relationship = service.create_relationship(source_id, target_id, relationship_type, properties)
    if not relationship:
        raise HTTPException(status_code=404, detail="One or both documents not found")
    return relationship


@router.get("/{doc_id}/related/", response_model=List[Document])
async def get_related_documents(
    doc_id: str,
    relationship_type: Optional[str] = None,
    service: DocumentService = Depends(get_document_service)
):
    """Get documents related to a document."""
    document = service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return service.get_related_documents(doc_id, relationship_type)


@router.get("/graph/", response_model=DocumentGraph)
async def get_document_graph(
    depth: int = 2,
    service: DocumentService = Depends(get_document_service)
):
    """Get the document graph."""
    return service.get_document_graph(depth)
