"""
Document service for handling document operations.
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from vesa.database.vector_db import VectorDatabase
from vesa.database.cozo_db import CozoDatabase
from vesa.models.document import Document, DocumentMetadata, DocumentRelationship, DocumentSearchResult, DocumentGraph


class DocumentService:
    """Service for document operations."""
    
    def __init__(self):
        """Initialize the document service."""
        self.vector_db = VectorDatabase()
        
        # CozoDBの初期化
        try:
            self.graph_db = CozoDatabase()
            # 接続テスト - 簡単なクエリを実行
            test_result = self.graph_db.client.run("?[] <- []") 
            self.graph_db_available = True
        except Exception as e:
            print(f"CozoDB connection error: {e}")
            # エラーが発生した場合はグラフDBを無効化
            self.graph_db_available = False
            # グラフDBがなくても基本機能は動作する
    
    def create_document(self, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """
        Create a new document.
        
        Args:
            title: Document title
            content: Document content
            metadata: Optional metadata
            
        Returns:
            Created document
        """
        if metadata is None:
            metadata = {}
            
        doc_id = str(uuid.uuid4())
        
        # Create metadata
        doc_metadata = DocumentMetadata(
            author=metadata.get("author", ""),
            tags=metadata.get("tags", []),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            path=metadata.get("path")
        )
        
        # Create document
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            metadata=doc_metadata
        )
        
        # Store in vector database
        self.vector_db.add_document(
            doc_id=doc_id,
            content=content,
            metadata={
                "title": title,
                **doc_metadata.dict()
            }
        )
        
        # Store in graph database if available
        if self.graph_db_available:
            try:
                self.graph_db.create_document_node(
                    doc_id=doc_id,
                    title=title,
                    metadata=doc_metadata.dict()
                )
            except Exception as e:
                print(f"Error creating document node: {e}")
        
        return document
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document or None if not found
        """
        doc_data = self.vector_db.get_document(doc_id)
        if not doc_data:
            return None
        
        # メタデータを処理して、適切な型に変換
        processed_metadata = self._process_metadata_for_model(doc_data["metadata"])
            
        return Document(
            id=doc_data["id"],
            title=processed_metadata["title"],
            content=doc_data["content"],
            metadata=DocumentMetadata(**processed_metadata)
        )
        
    def _process_metadata_for_model(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        ChromaDBから取得したメタデータをモデル用に処理します。
        特に文字列に変換されたリストを元に戻します。
        
        Args:
            metadata: ChromaDBから取得したメタデータ
            
        Returns:
            処理済みのメタデータ
        """
        processed = metadata.copy()
        
        # タグを文字列からリストに変換
        if "tags" in processed and isinstance(processed["tags"], str):
            if processed["tags"]:
                processed["tags"] = [tag.strip() for tag in processed["tags"].split(",")]
            else:
                processed["tags"] = []
        
        # created_atとupdated_atが文字列の場合はdatetimeに変換
        for date_field in ["created_at", "updated_at"]:
            if date_field in processed and isinstance(processed[date_field], str):
                try:
                    # ISO形式の日時文字列をdatetimeに変換
                    from datetime import datetime
                    processed[date_field] = datetime.fromisoformat(processed[date_field])
                except (ValueError, TypeError):
                    # 変換できない場合は現在時刻を使用
                    processed[date_field] = datetime.now()
        
        return processed
    
    def update_document(self, doc_id: str, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Document]:
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID
            title: New title
            content: New content
            metadata: New metadata
            
        Returns:
            Updated document or None if not found
        """
        existing_doc = self.get_document(doc_id)
        if not existing_doc:
            return None
            
        if metadata is None:
            metadata = {}
            
        # Update metadata
        doc_metadata = DocumentMetadata(
            author=metadata.get("author", existing_doc.metadata.author),
            tags=metadata.get("tags", existing_doc.metadata.tags),
            created_at=existing_doc.metadata.created_at,
            updated_at=datetime.now(),
            path=metadata.get("path", existing_doc.metadata.path)
        )
        
        # Update document
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            metadata=doc_metadata
        )
        
        # Update in vector database
        self.vector_db.update_document(
            doc_id=doc_id,
            content=content,
            metadata={
                "title": title,
                **doc_metadata.dict()
            }
        )
        
        # Update in graph database if available
        if self.graph_db_available:
            try:
                self.graph_db.create_document_node(
                    doc_id=doc_id,
                    title=title,
                    metadata=doc_metadata.dict()
                )
            except Exception as e:
                print(f"Error updating document node: {e}")
        
        return document
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        doc = self.get_document(doc_id)
        if not doc:
            return False
            
        # Delete from vector database
        self.vector_db.delete_document(doc_id)
        
        # Delete from graph database if available
        if self.graph_db_available:
            try:
                self.graph_db.delete_document_node(doc_id)
            except Exception as e:
                print(f"Error deleting document node: {e}")
        
        return True
    
    def search_documents(self, query: str, limit: int = 10) -> List[DocumentSearchResult]:
        """
        Search for documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of document search results
        """
        results = self.vector_db.search_documents(query, n_results=limit)
        
        search_results = []
        for result in results:
            # メタデータを処理して、適切な型に変換
            processed_metadata = self._process_metadata_for_model(result["metadata"])
            
            doc = Document(
                id=result["id"],
                title=processed_metadata["title"],
                content=result["content"],
                metadata=DocumentMetadata(**processed_metadata)
            )
            
            search_results.append(DocumentSearchResult(
                document=doc,
                score=1.0 - (result["distance"] or 0) if result["distance"] is not None else 1.0
            ))
            
        return search_results
    
    def create_relationship(self, source_id: str, target_id: str, rel_type: str, properties: Optional[Dict[str, Any]] = None) -> Optional[DocumentRelationship]:
        """
        Create a relationship between documents.
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            rel_type: Relationship type
            properties: Relationship properties
            
        Returns:
            Created relationship or None if documents not found
        """
        source_doc = self.get_document(source_id)
        target_doc = self.get_document(target_id)
        
        if not source_doc or not target_doc:
            return None
            
        if properties is None:
            properties = {}
            
        # Create relationship in graph database if available
        if self.graph_db_available:
            try:
                self.graph_db.create_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    rel_type=rel_type,
                    properties=properties
                )
            except Exception as e:
                print(f"Error creating relationship: {e}")
        
        return DocumentRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,
            properties=properties
        )
    
    def get_related_documents(self, doc_id: str, rel_type: Optional[str] = None) -> List[Document]:
        """
        Get documents related to a document.
        
        Args:
            doc_id: Document ID
            rel_type: Optional relationship type filter
            
        Returns:
            List of related documents
        """
        if not self.graph_db_available:
            return []
            
        try:
            related = self.graph_db.get_related_documents(doc_id, rel_type)
        except Exception as e:
            print(f"Error getting related documents: {e}")
            return []
        
        documents = []
        for rel in related:
            doc_id = rel["id"]
            doc = self.get_document(doc_id)
            if doc:
                documents.append(doc)
                
        return documents
    
    def get_document_graph(self, depth: int = 2) -> DocumentGraph:
        """
        Get the document graph.
        
        Args:
            depth: Maximum relationship depth
            
        Returns:
            Document graph
        """
        if not self.graph_db_available:
            return DocumentGraph(nodes=[], relationships=[])
            
        try:
            graph_data = self.graph_db.get_document_graph(depth)
        except Exception as e:
            print(f"Error getting document graph: {e}")
            return DocumentGraph(nodes=[], relationships=[])
        
        nodes = []
        for node_data in graph_data["nodes"]:
            doc = self.get_document(node_data["id"])
            if doc:
                nodes.append(doc)
                
        relationships = []
        for rel_data in graph_data["relationships"]:
            rel = DocumentRelationship(
                source_id=rel_data["source_id"],
                target_id=rel_data["target_id"],
                relationship_type=rel_data["relationship_type"],
                properties=rel_data["properties"]
            )
            relationships.append(rel)
            
        return DocumentGraph(
            nodes=nodes,
            relationships=relationships
        )
