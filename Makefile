.PHONY: run test clean install help

# デフォルトのターゲット
help:
	@echo "使用可能なコマンド:"
	@echo "  make run      - 開発サーバーを起動（ファイル変更時に自動再起動）"
	@echo "  make test     - シナリオテストを実行"
	@echo "  make clean    - キャッシュファイルとpycファイルを削除"
	@echo "  make install  - 依存関係をインストール"

# 開発サーバーを起動
run:
	python dev.py

# テストを実行
test:
	python dev.py --test

# キャッシュファイルとpycファイルを削除
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	@echo "クリーンアップ完了"

# 依存関係をインストール
install:
	pip install -r requirements.txt
