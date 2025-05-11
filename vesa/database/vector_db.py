"""
Vector database connection and operations.
"""
from typing import List, Dict, Any, Optional

from vesa.database.cozo_db import CozoDatabase

class VectorDatabase:
    """Vector database client for document storage and retrieval."""
    
    def __init__(self):
        """Initialize the vector database connection."""
        self.db = CozoDatabase()
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """
        Add a document to the vector database.
        
        Args:
            doc_id: Unique identifier for the document
            content: Text content of the document
            metadata: Additional metadata for the document
        """
        self.db.add_vector_document(doc_id, content, metadata)
        
    # CozoDBはメタデータの処理を内部で行うため、このメソッドは不要
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            
        Returns:
            List of documents with their metadata and similarity scores
        """
        return self.db.search_vector_documents(query, n_results)
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Document data or None if not found
        """
        return self.db.get_vector_document(doc_id)
    
    def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID to update
            content: New content
            metadata: New metadata
        """
        self.db.update_vector_document(doc_id, content, metadata)
    
    def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from the database.
        
        Args:
            doc_id: Document ID to delete
        """
        self.db.delete_vector_document(doc_id)
