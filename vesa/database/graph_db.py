"""
Graph database connection and operations.
"""
from typing import List, Dict, Any, Optional

from vesa.database.cozo_db import CozoDatabase

class GraphDatabase:
    """Graph database client for document relationships."""
    
    def __init__(self):
        """Initialize the graph database connection."""
        self.db = CozoDatabase()
    
    def close(self):
        """Close the database connection."""
        # CozoDBは明示的なクローズが不要
        pass
    
    def create_document_node(self, doc_id: str, title: str, metadata: Dict[str, Any]) -> None:
        """
        Create a document node in the graph database.
        
        Args:
            doc_id: Unique identifier for the document
            title: Document title
            metadata: Additional metadata for the document
        """
        self.db.create_document_node(doc_id, title, metadata)
    
    def create_relationship(self, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any] = None) -> None:
        """
        Create a relationship between two documents.
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            rel_type: Type of relationship
            properties: Additional properties for the relationship
        """
        self.db.create_relationship(source_id, target_id, rel_type, properties)
    
    def get_related_documents(self, doc_id: str, rel_type: Optional[str] = None, direction: str = "OUTGOING") -> List[Dict[str, Any]]:
        """
        Get documents related to the specified document.
        
        Args:
            doc_id: Document ID to find relationships for
            rel_type: Optional relationship type filter
            direction: Direction of relationship ('OUTGOING', 'INCOMING', or 'BOTH')
            
        Returns:
            List of related documents with relationship information
        """
        # 注: CozoDBの実装では現在directionパラメータは使用していません
        # 将来的に必要であれば、CozoDBの実装を拡張する必要があります
        return self.db.get_related_documents(doc_id, rel_type)
    
    def delete_document_node(self, doc_id: str) -> None:
        """
        Delete a document node and all its relationships.
        
        Args:
            doc_id: Document ID to delete
        """
        self.db.delete_document_node(doc_id)
    
    def get_document_graph(self, depth: int = 2) -> Dict[str, Any]:
        """
        Get the entire document graph up to a certain depth.
        
        Args:
            depth: Maximum relationship depth to traverse
            
        Returns:
            Graph data structure with nodes and relationships
        """
        return self.db.get_document_graph(depth)
