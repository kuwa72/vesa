import unittest
from unittest.mock import MagicMock, patch, call
import os
import json
from vesa.database.cozo_db import CozoDatabase

# Expected arguments for self.client.run() calls within _create_vector_document_schema
EXPECTED_VECTOR_DOCUMENT_SCHEMA_SCRIPT = """
        ::create vector_document {
            id: String,
            content: String,
            embedding: List<Float>,
            metadata: Json,
            created_at: String,
            updated_at: String
        }
        """

EXPECTED_VECTOR_DOCUMENT_INDEX_SCRIPT = """
            ::hnsw create vector_document:embedding_idx {{
                dim: 384,
                dtype: F32,
                fields: [embedding],
                distance: L2
            }}
            """


class TestCozoDb(unittest.TestCase):
    def setUp(self):
        """Set up for test methods."""
        self.mock_client = MagicMock()
        self.patcher = patch('vesa.database.cozo_db.Client')
        self.MockClient = self.patcher.start()
        self.MockClient.return_value = self.mock_client

        self.test_db_path = "./test_vesa.db"
        self.original_cozo_db_path = os.environ.get("COZO_DB_PATH")
        os.environ["COZO_DB_PATH"] = self.test_db_path

        # CozoDatabase() in setUp will call _verify_or_create_schemas.
        # Since test_vesa.db won't exist, db_exists is False, so force_create=True.
        self.cozo_db_instance = CozoDatabase()
        # Reset mock_client calls that occurred during CozoDatabase.__init__ for subsequent specific tests.
        self.mock_client.reset_mock()

    def tearDown(self):
        """Tear down after test methods."""
        self.patcher.stop()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if self.original_cozo_db_path is None:
            if "COZO_DB_PATH" in os.environ and os.environ["COZO_DB_PATH"] == self.test_db_path:
                 del os.environ["COZO_DB_PATH"]
        else:
            os.environ["COZO_DB_PATH"] = self.original_cozo_db_path

    def test_initialization_and_schema_creation(self):
        """Test CozoDatabase initializes and creates schemas (force_create=True path)."""
        # Re-initialize CozoDatabase to capture calls made during __init__
        # Or, analyze calls made by self.cozo_db_instance in setUp. For clarity, let's re-init.
        # Reset the main mock client that tracks calls to Cozo Client
        self.MockClient.return_value.reset_mock() # Reset the mock_client instance that was returned
        
        # Before creating a new instance for this test, ensure _relation_exists behaves as expected for init
        # However, for the init path where db does not exist, force_create=True is used, bypassing _relation_exists.
        CozoDatabase() # This will call _verify_or_create_schemas with force_create=True

        # Check that the schema creation methods were called via self.mock_client.run
        # These calls happen because _verify_or_create_schemas calls each _create_*_schema with force=True.
        expected_calls_for_vector_schema = [
            call(EXPECTED_VECTOR_DOCUMENT_SCHEMA_SCRIPT),
            call(EXPECTED_VECTOR_DOCUMENT_INDEX_SCRIPT)
        ]
        # Use the mock_client instance that the CozoDatabase instance uses
        self.MockClient.return_value.run.assert_any_call(EXPECTED_VECTOR_DOCUMENT_SCHEMA_SCRIPT)
        self.MockClient.return_value.run.assert_any_call(EXPECTED_VECTOR_DOCUMENT_INDEX_SCRIPT)
        # Add asserts for other schemas if necessary, e.g.:
        # EXPECTED_DOCUMENT_SCHEMA = """...define similarly..."""
        # self.MockClient.return_value.run.assert_any_call(EXPECTED_DOCUMENT_SCHEMA)

    @patch.object(CozoDatabase, '_relation_exists')
    def test_create_vector_document_schema_force_creation(self, mock_relation_exists):
        """Test _create_vector_document_schema with force=True."""
        # force=True means _relation_exists should not be called by _create_vector_document_schema itself.
        self.cozo_db_instance._create_vector_document_schema(force=True)
        
        expected_calls = [
            call(EXPECTED_VECTOR_DOCUMENT_SCHEMA_SCRIPT),
            call(EXPECTED_VECTOR_DOCUMENT_INDEX_SCRIPT)
        ]
        self.mock_client.run.assert_has_calls(expected_calls, any_order=False)
        mock_relation_exists.assert_not_called()

    @patch.object(CozoDatabase, '_relation_exists')
    def test_create_vector_document_schema_relation_exists(self, mock_relation_exists):
        """Test _create_vector_document_schema when relation already exists and force=False."""
        mock_relation_exists.return_value = True # Simulate relation exists
        
        self.cozo_db_instance._create_vector_document_schema(force=False)
        
        self.mock_client.run.assert_not_called() # No schema creation/index calls should be made
        mock_relation_exists.assert_called_once_with("vector_document")

    @patch.object(CozoDatabase, '_relation_exists')
    def test_create_vector_document_schema_relation_does_not_exist(self, mock_relation_exists):
        """Test _create_vector_document_schema when relation does not exist and force=False."""
        mock_relation_exists.return_value = False # Simulate relation does not exist
        
        self.cozo_db_instance._create_vector_document_schema(force=False)
        
        expected_calls = [
            call(EXPECTED_VECTOR_DOCUMENT_SCHEMA_SCRIPT),
            call(EXPECTED_VECTOR_DOCUMENT_INDEX_SCRIPT)
        ]
        self.mock_client.run.assert_has_calls(expected_calls, any_order=False)
        mock_relation_exists.assert_called_once_with("vector_document")

    @patch('vesa.database.cozo_db.datetime') # To mock datetime.utcnow
    @patch.object(CozoDatabase, '_process_metadata_for_storage') # To mock this specific method
    def test_create_document_node_success(self, mock_process_metadata, mock_datetime_class):
        """Test successful creation of a document node via client.put."""
        # Setup mock for datetime.utcnow().isoformat()
        mock_now_iso = "2023-10-26T10:00:00.000000"
        mock_datetime_class.utcnow.return_value.isoformat.return_value = mock_now_iso

        # Setup mock for _process_metadata_for_storage to return metadata as is
        # This is suitable because our input_metadata doesn't contain datetime objects needing conversion.
        # If it did, we'd need a more sophisticated side_effect or return_value.
        def simple_metadata_processor(metadata):
            return metadata
        mock_process_metadata.side_effect = simple_metadata_processor

        doc_id = "test_doc_001"
        title = "Test Document Title"
        input_metadata = {"source": "unit_test", "version": 1}

        # With _process_metadata_for_storage mocked to return input, this is what we expect.
        expected_processed_metadata = input_metadata.copy()

        self.cozo_db_instance.create_document_node(
            doc_id=doc_id,
            title=title,
            metadata=input_metadata
        )

        # Check that _process_metadata_for_storage was called correctly
        mock_process_metadata.assert_called_once_with(input_metadata or {})

        expected_document_data = {
            'id': doc_id,
            'title': title,
            'content': '',  # As per implementation
            'created_at': mock_now_iso,
            'updated_at': mock_now_iso,
            'metadata': expected_processed_metadata
        }

        self.mock_client.put.assert_called_once_with('document', expected_document_data)
        # Verify that the fallback self.mock_client.run() was not called for this case
        # This depends on how many times run() might be called by other parts during init or other schema checks if any.
        # For a clean test, ensure mock_client is reset if necessary or focus on 'put'.
        # Given the structure, if put succeeds, run for insertion won't be called.
        # Filter calls to run if there are many unrelated ones:
        manual_query_marker = ":put document {" # A distinctive part of the manual fallback query
        run_calls_for_manual_put = [
            c for c in self.mock_client.run.call_args_list 
            if manual_query_marker in c.args[0]
        ]
        self.assertEqual(len(run_calls_for_manual_put), 0, "Fallback manual query should not have been used.")

    @patch('vesa.database.cozo_db.datetime') # To mock datetime.utcnow
    @patch.object(CozoDatabase, '_process_metadata_for_storage') # To mock this specific method
    def test_create_document_node_fallback_to_manual_query(self, mock_process_metadata, mock_datetime_class):
        """Test create_document_node falls back to manual query if client.put fails."""
        # Setup mock for datetime.utcnow().isoformat()
        mock_now_iso = "2023-10-26T12:00:00.000000"
        mock_datetime_class.utcnow.return_value.isoformat.return_value = mock_now_iso

        # Setup mock for _process_metadata_for_storage
        def simple_metadata_processor(metadata):
            return metadata
        mock_process_metadata.side_effect = simple_metadata_processor

        # Configure client.put to raise an exception
        self.mock_client.put.side_effect = Exception("Simulated client.put failure")

        doc_id = "test_doc_002"
        title = "Test Document with \"Quotes\""
        input_metadata = {"source": "fallback_test", "priority": "high"}
        expected_processed_metadata = input_metadata.copy()

        # Call the method that should trigger the fallback
        self.cozo_db_instance.create_document_node(
            doc_id=doc_id,
            title=title,
            metadata=input_metadata
        )

        # Assert that client.put was called (and failed)
        expected_put_data = {
            'id': doc_id,
            'title': title,
            'content': '',
            'created_at': mock_now_iso,
            'updated_at': mock_now_iso,
            'metadata': expected_processed_metadata
        }
        self.mock_client.put.assert_called_once_with('document', expected_put_data)

        # Assert that _process_metadata_for_storage was called
        mock_process_metadata.assert_called_once_with(input_metadata or {})

        escaped_title = title.replace('"', '""')
        metadata_json_str = json.dumps(expected_processed_metadata) # Use the processed metadata
        
        # Reconstruct expected_manual_query to match how it's built in cozo_db.py (triple-quoted f-string)
        # Ensure indentation inside this f-string matches the Actual Call from debug output
        # Actual call had 16 spaces before ":put document", expected had 12. Add 4 spaces.
        expected_manual_query = f'''
                :put document {{
                    "id": "{doc_id}",
                    "title": "{escaped_title}",
                    "content": "",
                    "created_at": "{mock_now_iso}",
                    "updated_at": "{mock_now_iso}",
                    "metadata": {metadata_json_str}
                }}
                '''

        actual_run_calls = self.mock_client.run.call_args_list
        found_match_in_assert = False
        for i, call_args_tuple in enumerate(actual_run_calls):
            actual_query_arg = call_args_tuple[0][0] # query is the first positional arg
            if actual_query_arg == expected_manual_query:
                found_match_in_assert = True
                break
        self.assertTrue(found_match_in_assert, "Expected manual query not found in actual calls to client.run")

if __name__ == '__main__':
    unittest.main()
