"""
開発用スクリプト - サーバーの起動とテストを簡単に実行できます。
"""
import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

def run_server(host="127.0.0.1", port=8000):
    """
    開発サーバーを起動します。
    ファイルの変更を監視して自動的に再起動します。
    """
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "vesa.main:app", 
        "--host", host, 
        "--port", str(port), 
        "--reload"
    ]
    
    print(f"サーバーを起動しています: http://{host}:{port}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")

def run_tests():
    """
    シナリオテストを実行します。
    """
    test_path = Path(__file__).parent / "tests" / "functional" / "test_scenarios.py"
    cmd = [sys.executable, str(test_path)]
    
    print("シナリオテストを実行しています...")
    subprocess.run(cmd)

def main():
    """
    メイン関数 - コマンドライン引数を解析して適切な処理を実行します。
    """
    parser = argparse.ArgumentParser(description="VESA 開発ツール")
    parser.add_argument("--test", action="store_true", help="シナリオテストを実行します")
    parser.add_argument("--host", default="127.0.0.1", help="サーバーのホスト (デフォルト: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="サーバーのポート (デフォルト: 8000)")
    
    args = parser.parse_args()
    
    # データディレクトリが存在することを確認
    os.makedirs("./data/chroma", exist_ok=True)
    
    if args.test:
        run_tests()
    else:
        run_server(args.host, args.port)

if __name__ == "__main__":
    main()
