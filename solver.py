#!/usr/bin/env python3
"""
落ち物パズル全消し最短手順探索プログラム

BFSアルゴリズムを使用して、発火後に追加投下なしで
全消しになる最短手順を厳密に探索します。
"""

from dataclasses import dataclass
from typing import List, Tuple, Set, Optional, Union
from collections import deque
import argparse
import json
import sys


@dataclass(frozen=True)
class Position:
    """盤面上の位置を表すクラス"""
    row: int  # 0が最下段
    col: int  # 0が最左列


@dataclass
class Board:
    """盤面を表すクラス"""
    grid: List[List[str]]  # grid[row][col], 'x'は空
    rows: int
    cols: int
    
    def copy(self) -> 'Board':
        """盤面の深いコピーを返す"""
        return Board(
            grid=[row[:] for row in self.grid],
            rows=self.rows,
            cols=self.cols
        )
    
    def to_tuple(self) -> Tuple[Tuple[str, ...], ...]:
        """盤面をイミュータブルなタプル表現に変換（状態管理用）"""
        return tuple(tuple(row) for row in self.grid)
    
    def get(self, row: int, col: int) -> Optional[str]:
        """指定位置のパネルを取得"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None
    
    def set(self, row: int, col: int, value: str) -> None:
        """指定位置にパネルを設定"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = value
    
    def is_empty(self) -> bool:
        """盤面が空かどうか判定"""
        for row in self.grid:
            for cell in row:
                if cell != 'x':
                    return False
        return True
    
    def __str__(self) -> str:
        """人間可読な形式で盤面を表示"""
        lines = []
        for i in range(self.rows - 1, -1, -1):
            row_str = ' '.join(self.grid[i])
            lines.append(f"{i+1} {row_str}")
        return '\n'.join(lines)


@dataclass
class Step:
    """1手を表すクラス"""
    piece: str      # 投下する色
    column: int     # 投下する列（1-indexed）
    fired: bool     # この手で発火したか


@dataclass
class Solution:
    """解を表すクラス"""
    steps: List[Step]
    fired_step: int  # 発火した手番（1-indexed）
    explored_nodes: int


def parse_board(text: str) -> Board:
    """
    盤面テキストをパースしてBoardオブジェクトを返す
    
    入力形式:
    8 xxxxxw
    7 xxxxxr
    ...
    1 rwgbwr
    
    または行番号なしの形式もサポート
    """
    lines = text.strip().split('\n')
    grid_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            # 行番号あり
            row_data = parts[1]
        else:
            # 行番号なし
            row_data = parts[0] if parts else line
        
        grid_lines.append(list(row_data))
    
    # 下から上の順序で格納されているので逆順にする
    grid_lines.reverse()
    
    if not grid_lines:
        raise ValueError("Empty board")
    
    rows = len(grid_lines)
    cols = len(grid_lines[0])
    
    # 全行の列数が同じかチェック
    for i, row in enumerate(grid_lines):
        if len(row) != cols:
            raise ValueError(f"Row {i+1} has {len(row)} columns, expected {cols}")
    
    return Board(grid=grid_lines, rows=rows, cols=cols)


def parse_next(seq: str) -> List[str]:
    """NEXT文字列をパースして色のリストを返す"""
    return list(seq.strip())


def apply_gravity(board: Board) -> Board:
    """
    重力を適用して落下処理を行う
    破壊的変更を避けるため新しいBoardを返す
    """
    new_board = board.copy()
    
    for col in range(new_board.cols):
        # 各列で下から詰めていく
        write_pos = 0
        for row in range(new_board.rows):
            if new_board.grid[row][col] != 'x':
                if row != write_pos:
                    new_board.grid[write_pos][col] = new_board.grid[row][col]
                    new_board.grid[row][col] = 'x'
                write_pos += 1
    
    return new_board


def find_groups(board: Board, min_len: int = 2) -> List[Set[Position]]:
    """
    同色でmin_len個以上連結しているグループを検出
    各グループはPositionのセットとして返される
    """
    visited = [[False] * board.cols for _ in range(board.rows)]
    groups = []
    
    def dfs(start_row: int, start_col: int, color: str) -> Set[Position]:
        """深さ優先探索で同色の連結成分を探索"""
        stack = [(start_row, start_col)]
        group = set()
        
        while stack:
            row, col = stack.pop()
            if visited[row][col]:
                continue
            
            if board.grid[row][col] != color:
                continue
                
            visited[row][col] = True
            group.add(Position(row, col))
            
            # 上下左右を探索
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < board.rows and 0 <= new_col < board.cols:
                    if not visited[new_row][new_col]:
                        stack.append((new_row, new_col))
        
        return group
    
    # 全セルを走査
    for row in range(board.rows):
        for col in range(board.cols):
            if not visited[row][col] and board.grid[row][col] != 'x':
                group = dfs(row, col, board.grid[row][col])
                if len(group) >= min_len:
                    groups.append(group)
    
    return groups


def remove_groups(board: Board, groups: List[Set[Position]]) -> Board:
    """指定されたグループを削除した新しい盤面を返す"""
    new_board = board.copy()
    
    for group in groups:
        for pos in group:
            new_board.set(pos.row, pos.col, 'x')
    
    return new_board


def resolve_chain(board: Board) -> Board:
    """
    連鎖を最後まで処理して最終盤面を返す
    消去→落下→消去→...を繰り返す
    """
    current_board = board.copy()
    
    while True:
        # 消去可能なグループを探す
        groups = find_groups(current_board)
        if not groups:
            break
        
        # グループを消去
        current_board = remove_groups(current_board, groups)
        
        # 重力を適用
        current_board = apply_gravity(current_board)
    
    return current_board


def drop_piece(board: Board, color: str, col: int) -> Tuple[Board, bool]:
    """
    指定列に色を投下し、(新盤面, 発火したか)を返す
    col は 0-indexed
    """
    new_board = board.copy()
    
    # 投下位置を探す（一番下の空きマス）
    drop_row = -1
    for row in range(new_board.rows):
        if new_board.grid[row][col] == 'x':
            drop_row = row
            break
    
    if drop_row == -1:
        # 列が満杯
        return new_board, False
    
    # ピースを配置
    new_board.set(drop_row, col, color)
    
    # 消去判定
    groups = find_groups(new_board)
    fired = len(groups) > 0
    
    if fired:
        # 発火したら連鎖を最後まで処理
        new_board = resolve_chain(new_board)
    
    return new_board, fired


@dataclass(frozen=True)
class State:
    """探索の状態を表すクラス"""
    board_tuple: Tuple[Tuple[str, ...], ...]  # イミュータブルな盤面表現
    next_index: int  # 次に使うNEXTのインデックス
    unfired: bool    # まだ発火していないか


def solve(board: Board, next_seq: List[str]) -> Optional[Solution]:
    """
    BFSで最短手順を探索
    """
    initial_state = State(
        board_tuple=board.to_tuple(),
        next_index=0,
        unfired=True
    )
    
    queue = deque([(initial_state, [])])  # (状態, 手順)
    visited = {initial_state}
    explored_nodes = 0
    
    while queue:
        state, steps = queue.popleft()
        explored_nodes += 1
        
        # NEXTを使い切った
        if state.next_index >= len(next_seq):
            continue
        
        # 現在の盤面を復元
        current_board = Board(
            grid=[list(row) for row in state.board_tuple],
            rows=board.rows,
            cols=board.cols
        )
        
        # 各列に投下を試す
        for col in range(current_board.cols):
            new_board, fired = drop_piece(
                current_board,
                next_seq[state.next_index],
                col
            )
            
            new_step = Step(
                piece=next_seq[state.next_index],
                column=col + 1,  # 1-indexed
                fired=fired
            )
            new_steps = steps + [new_step]
            
            if fired:
                # 発火した場合
                if new_board.is_empty():
                    # 全消し成功！
                    return Solution(
                        steps=new_steps,
                        fired_step=len(new_steps),
                        explored_nodes=explored_nodes
                    )
                # 全消しできなかった（この枝は終了）
            else:
                # まだ発火していない場合は探索を継続
                new_state = State(
                    board_tuple=new_board.to_tuple(),
                    next_index=state.next_index + 1,
                    unfired=True
                )
                
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, new_steps))
    
    return None


def format_solution_human(solution: Optional[Solution], board: Board, next_seq: List[str]) -> str:
    """解を人間可読形式でフォーマット"""
    if solution is None:
        return "全消しできません。色が足りないか、配置が不可能です。"
    
    lines = [f"最短{len(solution.steps)}手で全消し可能"]
    
    for i, step in enumerate(solution.steps, 1):
        line = f"{i}手目: {step.piece} → {step.column}列"
        if step.fired:
            line += " ← ここで発火"
        lines.append(line)
    
    lines.append(f"\n探索ログ要約：")
    lines.append(f"深さ1〜{len(solution.steps)-1}は全探索したが全消しは不成立。")
    lines.append(f"深さ{len(solution.steps)}で初解を発見（探索状態数{solution.explored_nodes}）。")
    
    return '\n'.join(lines)


def format_solution_json(solution: Optional[Solution], board: Board, next_seq: List[str]) -> str:
    """解をJSON形式でフォーマット"""
    if solution is None:
        return json.dumps({
            "success": False,
            "message": "No solution found"
        }, indent=2)
    
    return json.dumps({
        "success": True,
        "steps": len(solution.steps),
        "moves": [
            {
                "step": i,
                "piece": step.piece,
                "column": step.column,
                "fired": step.fired
            }
            for i, step in enumerate(solution.steps, 1)
        ],
        "fired_at_step": solution.fired_step,
        "explored_nodes": solution.explored_nodes
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='落ち物パズル全消し最短手順探索プログラム',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用例:
  python solver.py --board board.txt --next grgrgrgrgr
  python solver.py --board board.txt --next grgrgrgrgr --format json
  
  または標準入力から:
  python solver.py < input.txt
        '''
    )
    
    parser.add_argument('--board', type=str, help='盤面ファイルパス')
    parser.add_argument('--next', type=str, help='NEXT文字列')
    parser.add_argument('--format', choices=['human', 'json'], default='human',
                       help='出力形式 (default: human)')
    
    args = parser.parse_args()
    
    # 入力の読み取り
    if args.board and args.next:
        # ファイルから読み取り
        with open(args.board, 'r') as f:
            board_text = f.read()
        next_seq = parse_next(args.next)
    else:
        # 標準入力から読み取り
        input_text = sys.stdin.read()
        lines = input_text.strip().split('\n')
        
        board_lines = []
        next_line = None
        reading_board = False
        
        for line in lines:
            line = line.strip()
            if line.upper() == 'BOARD:':
                reading_board = True
                continue
            elif line.upper().startswith('NEXT:'):
                reading_board = False
                next_line = line[5:].strip()
                continue
            elif reading_board or (not next_line and line):
                board_lines.append(line)
        
        if not board_lines:
            print("エラー: 盤面が指定されていません", file=sys.stderr)
            sys.exit(1)
        
        if not next_line:
            print("エラー: NEXTが指定されていません", file=sys.stderr)
            sys.exit(1)
        
        board_text = '\n'.join(board_lines)
        next_seq = parse_next(next_line)
    
    # パースと探索
    try:
        board = parse_board(board_text)
        solution = solve(board, next_seq)
        
        if args.format == 'json':
            print(format_solution_json(solution, board, next_seq))
        else:
            print(format_solution_human(solution, board, next_seq))
            
    except Exception as e:
        if args.format == 'json':
            print(json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2))
        else:
            print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
