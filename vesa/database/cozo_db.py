"""
CozoDB connection and operations.
"""
import os
import json
import traceback
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import textwrap

from pycozo.client import Client
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

class CozoDatabase:
    """CozoDB client for document relationships and vector storage."""
    
    def __init__(self):
        """Initialize the CozoDB connection."""
        # データベースファイルのパスを取得
        db_path = os.getenv("COZO_DB_PATH", "vesa.db")
        print(f"Using CozoDB path: {db_path}")
        
        # データベースファイルの存在確認
        db_exists = os.path.exists(db_path)
        print(f"Database file exists: {db_exists}")
        
        # CozoDBクライアントを初期化
        self.client = Client(engine="sqlite", path=db_path)
        print(f"CozoDB client initialized with SQLite engine at {db_path}")
        
        # 文章埋め込みモデルの初期化
        self.embedding_model = None
        
        # スキーマを初期化
        self._verify_or_create_schemas(force_create=not db_exists)
        
    def _create_dummy_client(self):
        """
        Create a dummy client that implements the necessary methods.
        This avoids the dependency on cozo_embedded module.
        """
        class DummyClient:
            def run(self, query, params=None):
                """Simulate running a query"""
                if "document" in query and ":put" in query:
                    return {"ok": True}
                elif "relationship" in query and ":put" in query:
                    return {"ok": True}
                elif "document" in query and ":delete" in query:
                    return {"ok": True}
                elif "relationship" in query and ":delete" in query:
                    return {"ok": True}
                elif "vector_document" in query and ":put" in query:
                    return {"ok": True}
                elif "vector_document" in query and ":delete" in query:
                    return {"ok": True}
                elif "?[id, title, metadata]" in query:
                    # Return empty document list
                    return {"ok": True, "rows": []}
                elif "?[source_id, target_id, rel_type, properties]" in query:
                    # Return empty relationship list
                    return {"ok": True, "rows": []}
                elif "?[id, title, metadata, rel_type, properties]" in query:
                    # Return empty related documents
                    return {"ok": True, "rows": []}
                elif "?[id, content, metadata, score]" in query:
                    # Return empty vector search results
                    return {"ok": True, "rows": []}
                else:
                    # Default empty result
                    return {"ok": True, "rows": []}
                    
        return DummyClient()
    
    def _relation_exists(self, relation_name: str) -> bool:
        """Checks if a relation exists in the database."""
        try:
            relations_data = self.client.run("data :relations")
            if relations_data and 'rows' in relations_data:
                for row in relations_data['rows']:
                    # Assuming the relation name is in the first column of the row
                    if row and len(row) > 0 and row[0] == relation_name:
                        return True
            return False
        except Exception as e:
            print(f"Error checking if relation '{relation_name}' exists: {e}")
            return False

    def _verify_or_create_schemas(self, force_create: bool = False):
        """Verifies that all necessary schemas exist, and creates them if they don't."""
        print(f"Verifying and creating schemas... (force_create={force_create})")
        self._create_document_schema(force=force_create)
        self._create_relationship_schema(force=force_create)
        self._create_vector_document_schema(force=force_create)
        print("Schema verification completed.")
        
    def _create_document_schema(self, force: bool = False):
        relation_name = "document"
        if not force and self._relation_exists(relation_name):
            print(f"Relation '{relation_name}' already exists. Skipping creation.")
            return
        print(f"Creating relation '{relation_name}'...")
        script = textwrap.dedent("""
            ::create document {
                id: String,
                title: String,
                content: String,
                created_at: String,
                updated_at: String,
                metadata: Json
            }
        """
        ).strip() + "\n"
        print(f"Schema script for document: {script!r}")
        self.client.run(script)
        print(f"Successfully created relation '{relation_name}'.")
        
    def _create_relationship_schema(self, force: bool = False):
        relation_name = "relationship"
        if not force and self._relation_exists(relation_name):
            print(f"Relation '{relation_name}' already exists. Skipping creation.")
            return
        print(f"Creating relation '{relation_name}'...")
        script = textwrap.dedent("""
            ::create relationship {
                source_id: String,
                target_id: String,
                rel_type: String,
                properties: Json,
                created_at: String,
                updated_at: String
            }
        """
        ).strip() + "\n"
        print(f"Schema script for relationship: {script!r}")
        self.client.run(script)
        print(f"Successfully created relation '{relation_name}'.")
        
    def _create_vector_document_schema(self, force: bool = False):
        """
        Creates the schema for storing vector documents if it doesn't exist or if force is True.
        """
        relation_name = "vector_document"
        if not force and self._relation_exists(relation_name):
            print(f"Relation '{relation_name}' already exists. Skipping creation.")
            return

        print(f"Creating relation '{relation_name}' (force={force})...")
        
        script = textwrap.dedent("""
            ::create vector_document {
                id: String,
                content: String,
                embedding: List<Float>,
                metadata: Json,
                created_at: String,
                updated_at: String
            }
        """
        ).strip() + "\n"
        print(f"Schema script for vector_document: {script!r}")
        
        self.client.run(script)
        print(f"Successfully created relation '{relation_name}'.")
        
        # CozoDB v0.7.6のHNSWインデックス構文
        index_schema = textwrap.dedent("""
            ::hnsw create vector_document:embedding_idx {
                dim: 384,
                dtype: F32,
                fields: [embedding],
                distance: L2
            }
        """
        ).strip() + "\n"
        print(f"Index schema script: {index_schema!r}")
        self.client.run(index_schema)
        print(f"Successfully created index for relation '{relation_name}'.")
        
    def _process_metadata_for_storage(self, metadata: dict) -> dict:
        """
        Process metadata for storage in CozoDB.
        Convert datetime objects to ISO format strings.
        
        Args:
            metadata: Original metadata dictionary
            
        Returns:
            Processed metadata dictionary
        """
        if metadata is None:
            return {}
            
        processed = {}
        for key, value in metadata.items():
            if isinstance(value, datetime):
                processed[key] = value.isoformat()
            else:
                processed[key] = value
                
        return processed
    
    def create_document_node(self, doc_id: str, title: str, metadata: dict = None) -> None:
        """Create a document node in the graph.

        Args:
            doc_id (str): Document ID.
            title (str): Document title.
            metadata (dict, optional): Document metadata. Defaults to None.
        """
        # Calculate current timestamp
        now = datetime.utcnow().isoformat()

        # Process metadata for storage
        metadata = self._process_metadata_for_storage(metadata or {})

        try:
            # 方法1: クライアントの便利なメソッドを使用
            # これは内部でJSONシリアル化を適切に処理します
            document_data = {
                'id': doc_id,
                'title': title,
                'content': '',  # 空の内容（コンテンツが必要な場合は追加）
                'created_at': now,
                'updated_at': now,
                'metadata': metadata
            }
            self.client.put('document', document_data)
            print(f"Document created successfully: {doc_id}")
        except Exception as e:
            print(f"Error creating document with client.put: {e}")
            
            try:
                # 方法2: 手動でクエリを構築する場合
                # ダブルクォートは二重にすることでエスケープ
                escaped_title = title.replace('"', '""')
                metadata_json = json.dumps(metadata)
                
                query = f'''
                :put document {{
                    "id": "{doc_id}",
                    "title": "{escaped_title}",
                    "content": "",
                    "created_at": "{now}",
                    "updated_at": "{now}",
                    "metadata": {metadata_json}
                }}
                '''
                
                print(f"Trying with manual query: {query}")
                self.client.run(query)
                print(f"Document created successfully with manual query: {doc_id}")
            except Exception as e2:
                print(f"Error creating document with manual query: {e2}")
                raise Exception(f"Error creating document: {e2}") from e2
                
    def create_relationship(self, source_id: str, target_id: str, rel_type: str, properties: dict = None) -> None:
        """
        Create a relationship between two document nodes.
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            rel_type: Relationship type
            properties: Additional properties for the relationship
        """
        now = datetime.utcnow().isoformat()
        
        # Process properties for storage
        processed_properties = self._process_metadata_for_storage(properties or {})
        
        try:
            # 方法1: クライアントの便利なメソッドを使用
            relationship_data = {
                'source_id': source_id,
                'target_id': target_id,
                'rel_type': rel_type,
                'properties': processed_properties,
                'created_at': now,
                'updated_at': now
            }
            self.client.put('relationship', relationship_data)
            print(f"Relationship created successfully: {source_id} -> {rel_type} -> {target_id}")
        except Exception as e:
            print(f"Error creating relationship with client.put: {e}")
            
            try:
                # 方法2: 手動でクエリを構築する場合
                # 入力値のエスケープ処理
                properties_json = json.dumps(processed_properties)
                escaped_source_id = source_id.replace('"', '""')
                escaped_target_id = target_id.replace('"', '""')
                escaped_rel_type = rel_type.replace('"', '""')
                
                query = f'''
                :put relationship {{
                    "source_id": "{escaped_source_id}",
                    "target_id": "{escaped_target_id}",
                    "rel_type": "{escaped_rel_type}",
                    "properties": {properties_json},
                    "created_at": "{now}",
                    "updated_at": "{now}"
                }}
                '''
                
                print(f"Trying with manual query: {query}")
                self.client.run(query)
                print(f"Relationship created successfully with manual query: {source_id} -> {rel_type} -> {target_id}")
            except Exception as e2:
                print(f"Error creating relationship with manual query: {e2}")
                raise Exception(f"Error creating relationship: {e2}") from e2
    
    def get_related_documents(self, doc_id: str, rel_type: str = None) -> list:
        """
        Get documents related to the specified document.
        
        Args:
            doc_id: Document ID to find relationships for
            rel_type: Optional relationship type filter
            
        Returns:
            List of related documents with relationship information
        """
        query = f"""
        ?[id, title, metadata, rel_type, properties] <-
        relationship[source_id, target_id, rel_type, properties, _, _],
        document[id, title, _, _, metadata]
        :where source_id == "{doc_id}" and id == target_id
        """
        
        if rel_type:
            query += f' and rel_type == "{rel_type}"'
        
        result = self.client.run(query)
        
        related_docs = []
        for row in result['rows']:
            id, title, metadata_json, rel_type, properties_json = row
            
            try:
                metadata = json.loads(metadata_json)
                properties = json.loads(properties_json)
            except json.JSONDecodeError:
                metadata = {}
                properties = {}
                
            related_docs.append({
                'id': id,
                'title': title,
                'metadata': metadata,
                'relationship_type': rel_type,
                'relationship_properties': properties
            })
            
        return related_docs
    
    def delete_document_node(self, doc_id: str) -> None:
        """
        Delete a document node and all its relationships.
        
        Args:
            doc_id: Document ID to delete
        """
        # Delete the document
        self.client.run(f"""
        :delete document[id]
        :where id == "{doc_id}"
        """)
        
        # Delete relationships where this document is source or target
        self.client.run(f"""
        :delete relationship[source_id, target_id, rel_type, properties, created_at, updated_at]
        :where source_id == "{doc_id}" or target_id == "{doc_id}"
        """)
    
    def get_document_graph(self, depth: int = 2) -> dict:
        """
        Get the entire document graph up to a certain depth.
        
        Args:
            depth: Maximum relationship depth to traverse
            
        Returns:
            Graph data structure with nodes and relationships
        """
        # Get all documents
        doc_result = self.client.run("""
        ?[id, title, metadata] <- document[id, title, _, _, metadata]
        """)
        
        # Get all relationships
        rel_result = self.client.run("""
        ?[source_id, target_id, rel_type, properties] <- 
        relationship[source_id, target_id, rel_type, properties, _, _]
        """)
        
        nodes = []
        for row in doc_result['rows']:
            id, title, metadata_json = row
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                metadata = {}
                
            nodes.append({
                'id': id,
                'title': title,
                'metadata': metadata
            })
        
        relationships = []
        for row in rel_result['rows']:
            source_id, target_id, rel_type, properties_json = row
            try:
                properties = json.loads(properties_json)
            except json.JSONDecodeError:
                properties = {}
                
            relationships.append({
                'source_id': source_id,
                'target_id': target_id,
                'relationship_type': rel_type,
                'properties': properties
            })
            
        return {
            'nodes': nodes,
            'relationships': relationships
        }
        
    def _get_embedding_model(self):
        """
        Get or initialize the embedding model.
        
        Returns:
            SentenceTransformer model for text embedding
        """
        if self.embedding_model is None:
            # 軽量なモデルを使用
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model
    
    def _get_text_embedding(self, text: str) -> list:
        """
        Get vector embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding as list of floats
        """
        model = self._get_embedding_model()
        embedding = model.encode(text)
        return embedding.tolist()
    
    def add_vector_document(self, doc_id: str, content: str, metadata: dict) -> None:
        """
        Add a document to the vector database.
        
        Args:
            doc_id: Unique identifier for the document
            content: Text content of the document
            metadata: Additional metadata for the document
        """
        now = datetime.utcnow().isoformat()
        
        # テキストをベクトルに変換
        embedding = self._get_text_embedding(content)
        
        # メタデータを処理
        processed_metadata = self._process_metadata_for_storage(metadata or {})
        
        # client.putメソッドを使用して安全にデータを追加
        try:
            document_data = {
                'id': doc_id,
                'content': content,
                'embedding': embedding,  # List<Float>型として渡される
                'metadata': json.dumps(processed_metadata),  # JSONをシリアライズ
                'created_at': now,
                'updated_at': now
            }
            print(f"Adding vector document with ID: {doc_id}")
            self.client.put('vector_document', document_data)
            print(f"Vector document added successfully with ID: {doc_id}")
        except Exception as e:
            print(f"Error adding vector document: {e}")
            print(traceback.format_exc())
            raise Exception(f"Failed to add vector document: {e}")
    
    def search_vector_documents(self, query: str, n_results: int = 5) -> list:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            
        Returns:
            List of documents with their metadata and similarity scores
        """
        try:
            # スキーマが存在するか確認し、必要に応じて作成
            self._verify_or_create_schemas()
            
            # クエリテキストをベクトルに変換
            query_embedding = self._get_text_embedding(query)
            
            # CozoDB v0.7.6のベクトル検索構文
            # HNSWインデックスを使用した近似最近傍検索
            search_query = """
            ?[dist, id, content, metadata] := ~vector_document:embedding_idx{ id, content, metadata |
                query: $query_vec,
                k: $k,
                ef: 50
            }
            """
            
            # クエリパラメータを設定
            query_params = {
                'query_vec': query_embedding,
                'k': n_results
            }
            
            print(f"Executing vector search query with params: {query_params}")
            result = self.client.run(search_query, query_params)
            print(f"Search result: {result}")
            
            # 結果が空の場合は空のリストを返す
            if not result.get('rows'):
                print("No search results found")
                return []
            
            # 結果を整形
            documents = []
            for row in result['rows']:
                dist, id, content, metadata_json = row
                
                try:
                    # JSON文字列からメタデータをロード
                    if isinstance(metadata_json, str):
                        metadata = json.loads(metadata_json)
                    else:
                        metadata = metadata_json
                except (json.JSONDecodeError, TypeError):
                    print(f"Error decoding metadata JSON: {metadata_json}")
                    metadata = {}
                
                # スコアを計算 (距離を類似度に変換)
                # L2距離は小さいほど類似度が高いため、逆数を取る
                score = 1.0 / (1.0 + dist) if dist > 0 else 1.0
                
                document = {
                    'id': id,
                    'content': content,
                    'metadata': metadata,
                    'score': score
                }
                documents.append(document)
            
            return documents
            
        except Exception as e:
            print(f"Error searching vector documents: {e}")
            print(traceback.format_exc())
            return []
    
    def get_vector_document(self, doc_id: str) -> dict:
        """
        Retrieve a document by its ID from the vector database.
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Document data or None if not found
        """
        try:
            print(f"Retrieving document with ID: {doc_id}")
            
            # スキーマが存在するか確認
            try:
                check_schema = self.client.run("::relations")
                relations = check_schema.get('rows', [])
                relation_names = [row[0] for row in relations]
                
                # vector_documentテーブルがない場合は作成
                if 'vector_document' not in relation_names:
                    print("Vector document relation not found, creating it first...")
                    self._create_vector_document_schema()
            except Exception as e:
                print(f"Error checking schema: {e}")
                print(traceback.format_exc())
            
            # CozoDB v0.7.6の構文でドキュメントを取得
            # クエリパラメータを使用して安全にクエリを実行
            query = """
            ?[id, content, metadata] <-
                vector_document[id, content, _, metadata, _, _]
                :where id == $doc_id
            """
            
            # クエリパラメータを設定
            query_params = {
                'doc_id': doc_id
            }
            
            print(f"Executing query with params: {query_params}")
            result = self.client.run(query, query_params)
            print(f"Query result: {result}")
            
            # 結果が空の場合はNoneを返す
            if not result.get('rows'):
                print(f"No document found with ID: {doc_id}")
                return None
            
            # 最初の行を取得
            row = result['rows'][0]
            id, content, metadata_json = row
            
            try:
                # JSON文字列からメタデータをロード
                if isinstance(metadata_json, str):
                    metadata = json.loads(metadata_json)
                else:
                    metadata = metadata_json
            except (json.JSONDecodeError, TypeError):
                print(f"Error decoding metadata JSON: {metadata_json}")
                metadata = {}
            
            document = {
                'id': id,
                'content': content,
                'metadata': metadata
            }
            
            return document
            
        except Exception as e:
            print(f"Error retrieving vector document: {e}")
            print(traceback.format_exc())
            return None
    
    def update_vector_document(self, doc_id: str, content: str, metadata: dict) -> None:
        """
        Update an existing document in the vector database.
        
        Args:
            doc_id: Document ID to update
            content: New content
            metadata: New metadata
        """
        try:
            print(f"Updating document with ID: {doc_id}")
            
            # CozoDBではレコードの更新には一旦削除して再作成するのが最も確実
            # 削除する
            self.delete_vector_document(doc_id)
            
            # 新しいドキュメントを追加する
            self.add_vector_document(doc_id, content, metadata)
            
            print(f"Document updated successfully with ID: {doc_id}")
            return
        except Exception as e:
            print(f"Error updating vector document: {e}")
            print(traceback.format_exc())
            raise Exception(f"Failed to update vector document: {e}") from e
    
    def delete_vector_document(self, doc_id: str) -> None:
        """
        Delete a document from the vector database.
        
        Args:
            doc_id: Document ID to delete
        """
        try:
            print(f"Deleting document with ID: {doc_id}")
            
            # CozoDB v0.7の削除構文
            query = f"""
            :delete vector_document[id, content, embedding, metadata, created_at, updated_at]
            :where id == "{doc_id}"
            """
            
            print(f"Executing delete query: {query}")
            self.client.run(query)
            print(f"Document deleted successfully with ID: {doc_id}")
            return
        except Exception as e:
            print(f"Error deleting vector document: {e}")
            print(traceback.format_exc())
            # 削除に失敗してもエラーを外部に出さないようにする
            # たとえば、ドキュメントが存在しない場合など
            return
