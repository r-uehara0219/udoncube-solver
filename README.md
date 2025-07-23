# 落ち物パズル全消し最短手順探索プログラム

BFS（幅優先探索）アルゴリズムを使用して、発火後に追加投下なしで全消しになる最短手順を厳密に探索するPythonプログラムです。

## 特徴

- **最短性保証**: BFSアルゴリズムにより、見つかった解が最短手順であることを保証
- **厳密探索**: 全ての可能な手順を系統的に探索
- **柔軟な入力**: コマンドライン引数または標準入力からの入力に対応
- **2つの出力形式**: 人間可読形式とJSON形式の出力をサポート
- **包括的なテスト**: pytestによる自動テストでロジックの正確性を保証

## 動作環境

- Python 3.10以上
- 追加のパッケージは不要（標準ライブラリのみ使用）

## インストール

```bash
# リポジトリをクローンまたはファイルをダウンロード
git clone <repository-url>
cd <repository-directory>

# 実行権限を付与（必要な場合）
chmod +x solver.py
```

## 使用方法

### コマンドライン引数を使用

```bash
# 基本的な使用方法
python solver.py --board board.txt --next grgrgrgrgr

# JSON形式で出力
python solver.py --board board.txt --next grgrgrgrgr --format json

# ヘルプを表示
python solver.py --help
```

### 標準入力を使用

```bash
python solver.py < input.txt
```

## 入力形式

### 盤面ファイル形式

盤面は下から上へ向かって行を記述します。各セルは1文字で表現します。

#### 形式1: 行番号付き

```
8 xxxxxw
7 xxxxxr
6 xxxxxw
5 xxxxxr
4 pbxxxg
3 rgbxxr
2 gpwxbw
1 rwgbwr
```

#### 形式2: 行番号なし

```
xxxxxw
xxxxxr
xxxxxw
xxxxxr
pbxxxg
rgbxxr
gpwxbw
rwgbwr
```

- `x`: 空きマス
- その他の1文字: 色を表す（例: r=赤, g=緑, b=青, w=白, p=紫, y=黄）

### 標準入力形式

```
BOARD:
8 xxxxxw
7 xxxxxr
6 xxxxxw
5 xxxxxr
4 pbxxxg
3 rgbxxr
2 gpwxbw
1 rwgbwr
NEXT: grgrgrgrgr
```

## 出力形式

### 人間可読形式（デフォルト）

```
最短5手で全消し可能
1手目: g → 4列
2手目: r → 2列
3手目: g → 5列
4手目: r → 3列
5手目: g → 5列 ← ここで発火

探索ログ要約：
深さ1〜4は全探索したが全消しは不成立。
深さ5で初解を発見（探索状態数1234）。
```

### JSON形式

```json
{
  "success": true,
  "steps": 5,
  "moves": [
    { "step": 1, "piece": "g", "column": 4, "fired": false },
    { "step": 2, "piece": "r", "column": 2, "fired": false },
    { "step": 3, "piece": "g", "column": 5, "fired": false },
    { "step": 4, "piece": "r", "column": 3, "fired": false },
    { "step": 5, "piece": "g", "column": 5, "fired": true }
  ],
  "fired_at_step": 5,
  "explored_nodes": 1234
}
```

## ゲームルール

1. **消去条件**: 同色のパネルが縦または横に2個以上接触すると消える（斜めは不可）
2. **重力**: パネルが消えた後、上のパネルは重力で落下
3. **連鎖**: 落下後に新たに2個以上接触したパネルがあれば再度消去（連鎖）
4. **発火**: 最初の消去が起きた瞬間を「発火」と呼ぶ
5. **投下制限**: 発火までは何手でも投下可能だが、発火後は追加投下不可
6. **勝利条件**: 発火後の連鎖ですべてのパネルが消えれば全消し成功

## 実装の詳細

### 主要なクラス

- `Board`: 盤面を表現するクラス
- `Position`: 盤面上の位置を表すクラス
- `Step`: 1手を表すクラス
- `Solution`: 解を表すクラス
- `State`: 探索状態を表すクラス（BFS用）

### 主要な関数

- `parse_board()`: 盤面テキストをパース
- `apply_gravity()`: 重力を適用してパネルを落下
- `find_groups()`: 消去可能なグループを検出
- `resolve_chain()`: 連鎖を最後まで処理
- `drop_piece()`: パネルを投下し、発火判定
- `solve()`: BFSで最短解を探索

## テスト

```bash
# pytestがインストールされていない場合
pip install pytest

# テストを実行
pytest test_solver.py -v

# または
python -m pytest test_solver.py -v
```

## 使用例

### 例1: 基本的な使用

```bash
# board.txtを作成
cat > board.txt << EOF
8 xxxxxw
7 xxxxxr
6 xxxxxw
5 xxxxxr
4 pbxxxg
3 rgbxxr
2 gpwxbw
1 rwgbwr
EOF

# 実行
python solver.py --board board.txt --next grgrgrgrgr
```

### 例2: 標準入力から実行

```bash
cat > input.txt << EOF
BOARD:
8 xxxxxw
7 xxxxxr
6 xxxxxw
5 xxxxxr
4 pbxxxg
3 rgbxxr
2 gpwxbw
1 rwgbwr
NEXT: grgrgrgrgr
EOF

python solver.py < input.txt
```

## パフォーマンスについて

- 状態数は盤面サイズとNEXTの長さに依存
- 枝刈りにより同一状態の重複探索を回避
- 典型的な6×8盤面では数秒以内に解を発見

## バージョン

1.0.0 - 初期リリース
