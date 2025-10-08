import argparse
import json
from datetime import datetime
from typing import List, Dict

LINES_PER_BLOCK = 6

def parse_ts(line: str) -> datetime:
    """
    行頭の [YYYY-mm-dd HH:MM:SS.ffffff] から datetime を取り出す
    """
    # 例: "[2025-10-03 01:48:05.514] 01_start_app"
    # ']' で分割して先頭の [....] を使う
    ts_part = line.split(']')[0].lstrip('[')
    return datetime.strptime(ts_part, '%Y-%m-%d %H:%M:%S.%f')

def log_to_blocks(lines: List[str]) -> List[Dict[str, float]]:
    """
    6行を1ブロックとして順に処理し、各ブロックの差分(ms)を返す
    戻り値： [{"enclave_initializing": float, "processing": float}, ...]
    """
    if len(lines) % LINES_PER_BLOCK != 0:
        raise ValueError(f"行数が {LINES_PER_BLOCK} の倍数ではありません: {len(lines)} 行")

    blocks = []
    for b in range(len(lines) // LINES_PER_BLOCK):
        base = b * LINES_PER_BLOCK
        line_start_app           = lines[base + 0].rstrip('\n')
        line_enclave_initialized = lines[base + 2].rstrip('\n')
        line_start_processing    = lines[base + 3].rstrip('\n')
        line_finish_processing   = lines[base + 4].rstrip('\n')

        # タイムスタンプ抽出
        ts_start_app           = parse_ts(line_start_app)
        ts_enclave_initialized = parse_ts(line_enclave_initialized)
        ts_start_processing    = parse_ts(line_start_processing)
        ts_finish_processing   = parse_ts(line_finish_processing)

        # 差分(ms)
        time_enclave_initializing = (ts_enclave_initialized - ts_start_app).total_seconds() * 1000.0
        time_processing = (ts_finish_processing - ts_start_processing).total_seconds() * 1000.0

        blocks.append({
            "enclave_initializing": time_enclave_initializing,
            "processing": time_processing,
        })
    return blocks

def group_by_group_size_and_average(blocks: List[Dict[str, float]], group_size: int = 10):
    """
    blocks を group_size 個ずつに分けて平均を計算
    戻り値は、各グループの平均と、グループ内の値の配列を含む構造
    """
    if len(blocks) % group_size != 0:
        raise ValueError(f"ブロック数({len(blocks)})が group_size({group_size}) の倍数ではありません")

    groups = []
    n_groups = len(blocks) // group_size
    for g in range(n_groups):
        start = g * group_size
        end = start + group_size
        chunk = blocks[start:end]

        vals_enclave_initializing = [b["enclave_initializing"] for b in chunk]
        vals_processing = [b["processing"] for b in chunk]

        avg_enclave_initializing = sum(vals_enclave_initializing) / group_size
        avg_processing = sum(vals_processing) / group_size

        groups.append({
            "group_index": g,                      # 0始まり
            "block_range_inclusive": [start + 1, end],  # 1始まりで表示（例: 1〜10）
            "averages_ms": {
                "enclave_initializing": avg_enclave_initializing,
                "processing": avg_processing,
            },
            "values_ms": {
                "enclave_initializing": vals_enclave_initializing,
                "processing": vals_processing,
            }
        })
    return groups

def compute_and_dump_json(log_path: str, output_json_path: str, group_size: int = 10):
    """
    ログを読み、差分→10ブロック平均→JSONへ保存
    JSON には「各グループの平均」と「計算に使った各ブロックの値」も記録します。
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = log_to_blocks(lines)
    groups = group_by_group_size_and_average(blocks, group_size=group_size)

    result = {
        "meta": {
            "total_blocks": len(blocks),
            "group_size": group_size,
            "note": "times are milliseconds (ms)"
        },
        "groups": groups,
        "all_values_ms": {
            "enclave_initializing": [b["enclave_initializing"] for b in blocks],
            "processing": [b["processing"] for b in blocks],
        }
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("output")
    args = parser.parse_args()

    compute_and_dump_json(args.log, args.output, group_size=10)
