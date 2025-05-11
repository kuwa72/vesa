"""
Document model definition.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    
    author: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    path: Optional[str] = Field(default=None)
    

class Document(BaseModel):
    """Document model representing a wiki page."""
    
    id: str
    title: str
    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the document to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata.dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a document from a dictionary."""
        metadata = data.get("metadata", {})
        if isinstance(metadata, dict) and not isinstance(metadata, DocumentMetadata):
            metadata = DocumentMetadata(**metadata)
            
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            metadata=metadata
        )


class DocumentRelationship(BaseModel):
    """Relationship between documents."""
    
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    

class DocumentSearchResult(BaseModel):
    """Search result for a document."""
    
    document: Document
    score: float = 0.0
    

class DocumentGraph(BaseModel):
    """Graph of documents and their relationships."""
    
    nodes: List[Document] = Field(default_factory=list)
    relationships: List[DocumentRelationship] = Field(default_factory=list)
