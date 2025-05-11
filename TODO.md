# VESA Project

## Project Description
VESA is a wiki-like service built with FastAPI, leveraging CozoDB as both a graph database (for document relationships) and a vector database (for semantic search). Documents are stored with metadata and embeddings for fast retrieval and relationship management.

## Progress Summary
- Implemented schema creation for `document`, `relationship`, and `vector_document`, including HNSW index setup for vector search.
- Fixed CozoDB QueryParser errors by ensuring correct indentation, `strip()` usage, and trailing newlines in schema scripts.
- Improved JSON handling using `json.dumps()` to escape data in `create_document_node` and `create_relationship` methods.
- Enhanced unit tests for schema initialization, document node creation (including fallback manual query), vector document operations, and functional scenario workflows.
- Verified end-to-end functionality with updated scenario tests covering create, retrieve, update, search, and delete operations.
