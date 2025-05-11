"""
シナリオテスト - VESAアプリケーションの主要機能をテストします。
"""
import os
import sys
import unittest
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vesa.services.document_service import DocumentService
from vesa.models.document import Document, DocumentMetadata


class ScenarioTests(unittest.TestCase):
    """VESAアプリケーションの主要機能をテストするシナリオテスト"""
    
    def setUp(self):
        """テストの前準備"""
        self.service = DocumentService()
        self.test_docs = []
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # テスト中に作成したドキュメントを削除
        for doc_id in self.test_docs:
            try:
                self.service.delete_document(doc_id)
                print(f"テストドキュメント削除: {doc_id}")
            except Exception as e:
                print(f"ドキュメント削除エラー: {e}")
    
    def test_create_document(self):
        """ドキュメント作成のテスト"""
        title = f"テストドキュメント {uuid.uuid4()}"
        content = "# テスト内容\n\nこれはテストです。"
        tags = ["テスト", "自動化"]
        
        # ドキュメント作成
        doc = self.service.create_document(
            title=title,
            content=content,
            metadata={"tags": tags}
        )
        
        # 作成したドキュメントIDを記録（後でクリーンアップするため）
        self.test_docs.append(doc.id)
        
        # 検証
        self.assertIsNotNone(doc)
        self.assertEqual(doc.title, title)
        self.assertEqual(doc.content, content)
        self.assertEqual(doc.metadata.tags, tags)
        
        print(f"✅ ドキュメント作成テスト成功: {doc.id}")
        return doc
    
    def test_get_document(self):
        """ドキュメント取得のテスト"""
        # まずドキュメントを作成
        created_doc = self.test_create_document()
        
        # ドキュメント取得
        doc = self.service.get_document(created_doc.id)
        
        # 検証
        self.assertIsNotNone(doc)
        self.assertEqual(doc.id, created_doc.id)
        self.assertEqual(doc.title, created_doc.title)
        self.assertEqual(doc.content, created_doc.content)
        
        print(f"✅ ドキュメント取得テスト成功: {doc.id}")
        return doc
    
    def test_update_document(self):
        """ドキュメント更新のテスト"""
        # まずドキュメントを作成
        created_doc = self.test_create_document()
        
        # 更新内容
        new_title = f"更新されたドキュメント {uuid.uuid4()}"
        new_content = "# 更新された内容\n\nこれは更新テストです。"
        new_tags = ["更新", "テスト"]
        
        # ドキュメント更新
        updated_doc = self.service.update_document(
            doc_id=created_doc.id,
            title=new_title,
            content=new_content,
            metadata={"tags": new_tags}
        )
        
        # 検証
        self.assertIsNotNone(updated_doc)
        self.assertEqual(updated_doc.id, created_doc.id)
        self.assertEqual(updated_doc.title, new_title)
        self.assertEqual(updated_doc.content, new_content)
        self.assertEqual(updated_doc.metadata.tags, new_tags)
        
        print(f"✅ ドキュメント更新テスト成功: {updated_doc.id}")
        return updated_doc
    
    def test_search_documents(self):
        """ドキュメント検索のテスト"""
        # ユニークな検索キーワードを含むドキュメントを作成
        unique_keyword = f"unique{uuid.uuid4().hex[:8]}"
        title = f"検索テスト {unique_keyword}"
        content = f"# 検索テスト\n\nこれは{unique_keyword}を含む検索テストです。"
        
        doc = self.service.create_document(
            title=title,
            content=content,
            metadata={"tags": ["検索", "テスト"]}
        )
        self.test_docs.append(doc.id)
        
        # 少し待ってからベクトルDBに反映されるようにする
        import time
        time.sleep(1)
        
        # 検索実行
        results = self.service.search_documents(unique_keyword)
        
        # 検証
        self.assertGreater(len(results), 0)
        found = False
        for result in results:
            if result.document.id == doc.id:
                found = True
                break
        
        self.assertTrue(found, f"作成したドキュメントが検索結果に見つかりませんでした: {unique_keyword}")
        print(f"✅ ドキュメント検索テスト成功: {unique_keyword}")
    
    def test_delete_document(self):
        """ドキュメント削除のテスト"""
        # まずドキュメントを作成
        created_doc = self.test_create_document()
        
        # ドキュメント削除
        result = self.service.delete_document(created_doc.id)
        
        # 検証
        self.assertTrue(result)
        
        # 削除されたことを確認
        doc = self.service.get_document(created_doc.id)
        self.assertIsNone(doc)
        
        # クリーンアップリストから削除（すでに削除済みのため）
        if created_doc.id in self.test_docs:
            self.test_docs.remove(created_doc.id)
        
        print(f"✅ ドキュメント削除テスト成功: {created_doc.id}")
    
    def test_full_scenario(self):
        """完全なシナリオテスト（作成→取得→更新→検索→削除）"""
        print("\n🔄 完全なシナリオテストを開始します...")
        
        # 1. ドキュメント作成
        title = f"シナリオテスト {uuid.uuid4()}"
        content = "# シナリオテスト\n\nこれは完全なシナリオテストです。"
        tags = ["シナリオ", "テスト"]
        
        doc = self.service.create_document(
            title=title,
            content=content,
            metadata={"tags": tags}
        )
        self.test_docs.append(doc.id)
        print(f"  ✓ ドキュメント作成: {doc.id}")
        
        # 2. ドキュメント取得
        retrieved_doc = self.service.get_document(doc.id)
        self.assertEqual(retrieved_doc.id, doc.id)
        print(f"  ✓ ドキュメント取得: {retrieved_doc.id}")
        
        # 3. ドキュメント更新
        new_title = f"更新されたシナリオテスト {uuid.uuid4()}"
        new_content = "# 更新されたシナリオテスト\n\nこれは更新された完全なシナリオテストです。"
        new_tags = ["更新", "シナリオ", "テスト"]
        
        updated_doc = self.service.update_document(
            doc_id=doc.id,
            title=new_title,
            content=new_content,
            metadata={"tags": new_tags}
        )
        self.assertEqual(updated_doc.title, new_title)
        print(f"  ✓ ドキュメント更新: {updated_doc.id}")
        
        # 4. ドキュメント検索
        import time
        time.sleep(1)  # インデックス更新を待つ
        
        results = self.service.search_documents("シナリオテスト")
        found = False
        for result in results:
            if result.document.id == doc.id:
                found = True
                break
        self.assertTrue(found)
        print(f"  ✓ ドキュメント検索: {doc.id}")
        
        # 5. ドキュメント削除
        result = self.service.delete_document(doc.id)
        self.assertTrue(result)
        
        # 削除されたことを確認
        deleted_doc = self.service.get_document(doc.id)
        self.assertIsNone(deleted_doc)
        
        # クリーンアップリストから削除（すでに削除済みのため）
        if doc.id in self.test_docs:
            self.test_docs.remove(doc.id)
        
        print(f"  ✓ ドキュメント削除: {doc.id}")
        print("✅ 完全なシナリオテスト成功!")


if __name__ == "__main__":
    print("=" * 80)
    print(f"VESA シナリオテスト - 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 個別のテストを実行
    test_suite = unittest.TestSuite()
    test_suite.addTest(ScenarioTests('test_full_scenario'))
    
    # すべてのテストを実行する場合はこちらを使用
    # test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(ScenarioTests)
    
    unittest.TextTestRunner(verbosity=2).run(test_suite)
