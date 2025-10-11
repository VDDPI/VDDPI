import csv
import json
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

def extract_processing_periods(run_log_path: str) -> List[Dict[str, Any]]:
    """run.logからparallel_numごとの処理期間を抽出して返す。"""
    open_runs: List[Tuple[int, datetime, str]] = []  # (parallel_num, start_dt, start_str)
    periods: List[Dict[str, Any]] = []

    def ts_from_line(line: str) -> Optional[str]:
        try:
            return line.split("]")[0].strip("[")
        except Exception:
            return None

    def parallel_num_from_line(line: str) -> Optional[int]:
        try:
            return int(line.split("parallel_num:")[1].split(")")[0])
        except Exception:
            return None

    with open(run_log_path, "r", encoding="utf-8") as f:
        for line in f:
            if "Starting data processing" in line:
                start_raw = ts_from_line(line)
                pnum = parallel_num_from_line(line)
                if start_raw and pnum is not None:
                    start_dt = datetime.strptime(start_raw, "%Y-%m-%d %H:%M:%S.%f")
                    open_runs.append((pnum, start_dt, start_raw))
                continue

            if "All data processing completed" in line:
                if not open_runs:
                    continue
                end_raw = ts_from_line(line)
                if not end_raw:
                    continue
                end_dt = datetime.strptime(end_raw, "%Y-%m-%d %H:%M:%S.%f")
                pnum, start_dt, start_raw = open_runs.pop()
                duration = (end_dt - start_dt).total_seconds()
                periods.append({
                    "parallel_num": pnum,
                    "start": start_raw,
                    "end": end_raw,
                    "duration_sec": round(duration, 3)
                })

    if open_runs:
        for pnum, _, s in open_runs:
            print(f"⚠️ 未完了の処理あり: parallel_num={pnum}, start={s}")

    print(f"✅ {len(periods)} 件の処理期間を抽出しました。")
    return periods


def gen_graph_data(run_log_path: str, stats_csv_path: str, output_json_path: str):
    # ===== フェーズ開始・終了を取得 =====
    start_str = None
    end_str = None
    with open(run_log_path, "r", encoding="utf-8") as f:
        for line in f:
            if "Phase3: Data processing" in line:
                start_str = line.split("]")[0].strip("[")
            elif "Finalization" in line:
                end_str = line.split("]")[0].strip("[")

    if not start_str or not end_str:
        raise ValueError("開始または終了の行が見つかりません。")

    start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S.%f")
    end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S.%f")
    print(f"フェーズ期間: {start_time} ～ {end_time}")

    # ===== parallel_numごとの処理期間を抽出 =====
    periods = extract_processing_periods(run_log_path)

    # ===== stats.csvから範囲内データを抽出 =====
    data_points: List[Dict[str, Any]] = []
    with open(stats_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            if start_time <= ts <= end_time:
                data_points.append({
                    "timestamp": row["timestamp"],
                    "cpu": float(row["cpu_usage_percent"]),
                    "mem": float(row["mem_used_mb"]),
                })

    # ===== JSON形式で出力 =====
    graph_data = {
        "start": start_str,
        "end": end_str,
        "periods": periods,
        "points": data_points
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON出力完了: {output_json_path}（データ数: {len(data_points)} 件）")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Generate JSON graph data including per-parallel processing periods.")
    p.add_argument("runlog", type=str, help="Path to run.log")
    p.add_argument("stats", type=str, help="Path to consumer_host_stats.csv")
    p.add_argument("output", type=str, help="Output JSON path")
    args = p.parse_args()

    gen_graph_data(args.runlog, args.stats, args.output)


if __name__ == "__main__":
    main()