import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

TS_FMT = "%Y-%m-%d %H:%M:%S.%f"

def _strip(s: str) -> str:
    return s.strip().strip(",").strip()


def _find_after(s: str, token: str, start: int = 0) -> int:
    """token の直後の位置（インデックス）を返す。見つからなければ -1。"""
    i = s.find(token, start)
    if i == -1:
        return -1
    return i + len(token)


def _read_until(s: str, start: int, stop_chars: str) -> str:
    """start から stop_chars のいずれかが出る手前までを返す。"""
    j = start
    n = len(s)
    while j < n and s[j] not in stop_chars:
        j += 1
    return s[start:j]


def parse_benchlog_line_no_regex(line: str):
    """
    例：
    ___BENCH___ Data processing (start_total:2025-10-07 15:47:41.060, ..., elapsed_check_policy_ms:261, ç:1233, ...)
    から
      start_total(str), elapsed_check_policy_ms(int), elapsed_process_data_ms(int) を返す
    """
    # start_total
    pos = _find_after(line, "start_total:")
    if pos == -1:
        raise ValueError("start_total not found")
    start_total_str = _read_until(line, pos, ",)")
    start_total_str = _strip(start_total_str)

    # elapsed_check_policy_ms
    pos = _find_after(line, "elapsed_check_policy_ms:")
    if pos == -1:
        raise ValueError("elapsed_check_policy_ms not found")
    check_str = _read_until(line, pos, ",)")
    check_str = _strip(check_str)
    if not check_str or not check_str[0].isdigit() and check_str[0] != "-":
        # 数値以外が先頭なら後続の数字だけ拾う（保険）
        k = 0
        while k < len(check_str) and not (check_str[k].isdigit() or check_str[k] == "-"):
            k += 1
        check_str = check_str[k:]
    check_ms = int("".join(ch for ch in check_str if ch.isdigit() or ch == "-"))

    # elapsed_process_data_ms（誤記 ç にも対応）
    pos = _find_after(line, "elapsed_process_data_ms:")
    if pos != -1:
        proc_str = _read_until(line, pos, ",)")
    else:
        # フォールバック：誤記 'ç:'
        pos = _find_after(line, "ç:")
        if pos == -1:
            raise ValueError("elapsed_process_data_ms (or ç) not found")
        proc_str = _read_until(line, pos, ",)")
    proc_str = _strip(proc_str)
    if not proc_str or not proc_str[0].isdigit() and proc_str[0] != "-":
        k = 0
        while k < len(proc_str) and not (proc_str[k].isdigit() or proc_str[k] == "-"):
            k += 1
        proc_str = proc_str[k:]
    proc_ms = int("".join(ch for ch in proc_str if ch.isdigit() or ch == "-"))

    return start_total_str, check_ms, proc_ms


def parse_applog_start_servers_no_regex(lines: List[str]) -> List[str]:
    """
    例：
    [2025-10-07 15:47:46.899] Start server (port:8002)
    から [] 内のタイムスタンプを抽出（Start server の行のみ）
    """
    ts_list: List[str] = []
    for line in lines:
        if "Start server" not in line:
            continue
        # 先頭の '[' と最初の ']' の間をとる
        lb = line.find("[")
        rb = line.find("]", lb + 1) if lb != -1 else -1
        if lb != -1 and rb != -1:
            ts = line[lb + 1 : rb].strip()
            ts_list.append(ts)
    return ts_list


def load_lines(path: Path) -> List[str]:
    with path.open(encoding="utf-8") as f:
        return f.readlines()


def avg(xs: List[float]) -> float:
    return round(sum(xs) / len(xs), 3) if xs else 0.0


def build_group(group_index: int, benchlog_path: Path, applog_path: Path) -> Dict[str, Any]:
    benchlog_lines = load_lines(benchlog_path)
    applog_lines = load_lines(applog_path)

    # applog: Start server タイムスタンプ配列
    start_servers = parse_applog_start_servers_no_regex(applog_lines)
    if len(start_servers) < len(benchlog_lines):
        raise ValueError(
            f"Group {group_index}: Not enough 'Start server' lines in {applog_path.name}. "
            f"Expected >= {len(benchlog_lines)}, got {len(start_servers)}"
        )

    enclave_initializing_vals: List[float] = []
    processing_vals: List[float] = []
    check_vals: List[float] = []

    for i, l1 in enumerate(benchlog_lines):
        start_total_str, check_ms, proc_ms = parse_benchlog_line_no_regex(l1)
        start_total_dt = datetime.strptime(start_total_str, TS_FMT)
        start_server_dt = datetime.strptime(start_servers[i], TS_FMT)
        diff_ms = int(round((start_server_dt - start_total_dt).total_seconds() * 1000))

        enclave_initializing_vals.append(float(diff_ms))
        processing_vals.append(float(proc_ms))
        check_vals.append(float(check_ms))

    group = {
        "group_index": group_index,
        "block_range_inclusive": [group_index * 10 + 1, group_index * 10 + len(enclave_initializing_vals)],
        "averages_ms": {
            # ご指定のマッピング
            "enclave_initializing": avg(enclave_initializing_vals),
            "policy_checking": avg(check_vals),
            "processing": avg(processing_vals),
        },
        "values_ms": {
            "enclave_initializing": enclave_initializing_vals,
            "policy_checking": check_vals,
            "processing": processing_vals,
        }
    }
    return group


def main():
    import argparse

    p = argparse.ArgumentParser(description="Analyze benchlog/applog blocks (no regex) and output JSON in requested schema.")
    p.add_argument("input_dir", type=str, help="Directory containing eval_data_processing_cache-*k.log and app-*k.log")
    p.add_argument("output", type=str, help="Output JSON path")
    args = p.parse_args()

    base = Path(args.input_dir)

    groups: List[Dict[str, Any]] = []
    total_blocks = 0

    test_num = 10 # 1k ... 10k

    for gi in range(1, test_num + 1):
        benchlog = base / f"eval_data_processing_cache-{gi}k.log"
        applog = base / f"app-{gi}k.log"
        if not benchlog.exists():
            raise FileNotFoundError(f"Missing {benchlog}")
        if not applog.exists():
            raise FileNotFoundError(f"Missing {applog}")

        g = build_group(gi, benchlog, applog)
        groups.append(g)
        total_blocks += len(g["values_ms"]["enclave_initializing"])

    result = {
        "meta": {
            "total_blocks": total_blocks,
            "group_size": total_blocks / test_num,
            "note": "times are milliseconds (ms)",
        },
        "groups": groups,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote {args.output}")


if __name__ == "__main__":
    main()