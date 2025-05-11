# VESA

VESAはベクトルデータベースとグラフデータベースを活用したWikiシステムです。esaクローンとして開発されており、AIから見るためのデータベースを整備するために使用することを目的としています。

## 特徴

- バックエンドとしてベクトルデータベースを使用する
- ドキュメント同士の関係をグラフデータベースとして持つ
- CMSというよりはベクトル＋グラフデータベースのフロントエンド的な位置づけ
- AIから見るためのデータベースを整備するために使用

## 技術スタック

- **バックエンド**: FastAPI (Python)
- **データベース**: CozoDB (ベクトル検索とグラフ機能を統合)
- **フロントエンド**: Jinja2テンプレート, Bootstrap 5, JavaScript

## セットアップ方法

### 前提条件

- Python 3.9以上

### インストール手順

1. リポジトリをクローン

```bash
git clone https://github.com/kuwa72/vesa.git
cd vesa
```

2. 仮想環境を作成して有効化

```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
# または
source venv/bin/activate.fish  # Fishシェルの場合
# または
.\venv\Scripts\activate  # Windowsの場合
```

3. 依存関係をインストール

```bash
pip install -r requirements.txt
```

4. 環境変数を設定

`.env.example`ファイルを`.env`にコピーして、必要に応じて設定を変更します。

5. アプリケーションを起動

```bash
python run.py
```

アプリケーションは`http://127.0.0.1:8000`で実行されます。

## 使い方

### ドキュメントの作成と編集

1. ナビゲーションバーの「新規作成」ボタンをクリックします
2. タイトル、内容、タグを入力します
3. 「保存」ボタンをクリックして保存します

### ドキュメントの検索

1. ナビゲーションバーの検索ボックスにキーワードを入力します
2. 検索結果からドキュメントを選択して閲覧します

### ドキュメント間の関係

1. ドキュメント表示画面で「関連ドキュメント」セクションを確認します
2. グラフ表示画面でドキュメント間の関係を視覚的に確認できます

## 開発者向け情報

### プロジェクト構造

```
vesa/
├── data/           # データ保存ディレクトリ
├── docs/           # ドキュメント
├── tests/          # テスト
├── venv/           # 仮想環境
├── vesa/           # メインアプリケーション
│   ├── database/   # データベース接続
│   ├── models/     # データモデル
│   ├── routes/     # APIルート
│   ├── services/   # ビジネスロジック
│   ├── static/     # 静的ファイル
│   ├── templates/  # HTMLテンプレート
│   └── utils/      # ユーティリティ関数
├── .env            # 環境変数
├── .env.example    # 環境変数のサンプル
├── README.md       # このファイル
├── requirements.txt # 依存関係
└── run.py          # 起動スクリプト
```

### APIエンドポイント

- `GET /api/documents/{doc_id}` - ドキュメントの取得
- `POST /api/documents/` - ドキュメントの作成
- `PUT /api/documents/{doc_id}` - ドキュメントの更新
- `DELETE /api/documents/{doc_id}` - ドキュメントの削除
- `GET /api/documents/search/` - ドキュメントの検索
- `POST /api/documents/relationships/` - ドキュメント間の関係作成
- `GET /api/documents/{doc_id}/related/` - 関連ドキュメントの取得
- `GET /api/documents/graph/` - ドキュメントグラフの取得

## ライセンス

MITライセンス