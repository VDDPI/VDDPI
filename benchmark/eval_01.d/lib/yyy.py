#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark logs (cache / no-cache / no-sgx) + memory CSV -> SVG chart

- Parses benchmark logs:
    ___BENCH___ Data processing (Start:YYYY-MM-DD HH:MM:SS, End:..., Duration_ms:1234, data_processed:True, cached:True|False)
- Parses memory CSV like docker stats export:
    Timestamp,Container,MemUsage,CPU%,NetI/O,BlockI/O
    2025-09-05 02:58:56,gramine-consumer,38.56MiB / 7.708GiB,78.49%,2.56kB / 689B,34MB / 0B
- Matches each run to the closest memory sample within 60s of the run's median time
- Plots:
    * Duration_ms as line charts (Cache blue #2E86AB, No-cache orange #F18F01, Third green #28A745)
    * Matched MemUsage (MiB) as bar charts on a secondary Y-axis, same colors semi-transparent (cache/no-cache only)
- X-axis is run index (1..N). If >=100, tick density is reduced automatically.
"""

import argparse
import sys
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ---------- Parsing functions ----------

def parse_benchmark_log(path: str, expected_cached: Optional[bool] = None) -> pd.DataFrame:
    """
    Robust parser:
      - Case-insensitive keys (start/Start/START all OK)
      - Spaces after colons allowed
      - Timestamps parsed with pandas.to_datetime (supports milliseconds/ISO8601/timezones)
    """
    outer = re.compile(
        r"___BENCH___\s+Data\s+processing\s+.*\(\s*(?P<body>.*?)\s*\)\s*$",
        re.IGNORECASE
    )

    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln, raw in enumerate(f, 1):
                line = raw.strip()
                m = outer.search(line)
                if not m:
                    continue

                body = m.group("body")
                # Split by comma -> convert "k:v" to dict (keys lowercased)
                kv = {}
                for p in [x.strip() for x in body.split(",")]:
                    if ":" not in p:
                        continue
                    k, v = p.split(":", 1)
                    kv[k.strip().lower()] = v.strip()

                # Required keys
                for req in ("start", "end", "duration_ms", "cached"):
                    if req not in kv:
                        print(f"[WARN] {path}:{ln} missing key '{req}' in: {body}", file=sys.stderr)
                        break
                else:
                    # Date/time
                    s = pd.to_datetime(kv["start"], errors="coerce")
                    e = pd.to_datetime(kv["end"], errors="coerce")
                    if pd.isna(s) or pd.isna(e):
                        print(f"[WARN] {path}:{ln} datetime parse failed: start='{kv['start']}' end='{kv['end']}'", file=sys.stderr)
                        continue
                    start = s.to_pydatetime()
                    end = e.to_pydatetime()

                    # duration_ms
                    dm = re.search(r"(-?\d+)", kv["duration_ms"])
                    if not dm:
                        print(f"[WARN] {path}:{ln} duration_ms parse failed: {kv['duration_ms']}", file=sys.stderr)
                        continue
                    dur_ms = int(dm.group(1))

                    # cached
                    cstr = kv["cached"].lower()
                    if cstr in ("true", "t", "1", "yes", "y"):
                        cached_flag = True
                    elif cstr in ("false", "f", "0", "no", "n"):
                        cached_flag = False
                    else:
                        print(f"[WARN] {path}:{ln} cached parse failed: {kv['cached']}", file=sys.stderr)
                        continue

                    # Filter by expected value if needed
                    if expected_cached is not None and cached_flag != expected_cached:
                        continue

                    rows.append({
                        "start_time": start,
                        "end_time": end,
                        "duration_ms": dur_ms,
                        "cached": cached_flag,
                        "median_time": start + (end - start) / 2,
                    })
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed reading {path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print(f"[WARN] No valid BENCH lines found in {path}.", file=sys.stderr)

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["start_time", "end_time", "duration_ms", "cached", "median_time"])
    df = df.sort_values("start_time").reset_index(drop=True)
    df.insert(0, "run", np.arange(1, len(df) + 1))
    df["cumulative_ms"] = df["duration_ms"].cumsum() if not df.empty else df.get("duration_ms")
    return df

def parse_memory_usage_csv(path: str) -> pd.DataFrame:
    """
    Parse memory CSV. Extract Timestamp and the FIRST value of MemUsage as MiB.
    Returns DataFrame with columns: timestamp (datetime), mem_mib (float), container (str)
    """
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed reading {path}: {e}", file=sys.stderr)
        sys.exit(1)

    if "Timestamp" not in df.columns or "MemUsage" not in df.columns:
        print(f"[ERROR] memory CSV must have 'Timestamp' and 'MemUsage' columns.", file=sys.stderr)
        sys.exit(1)

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    # Container (optional)
    container_col = df["Container"] if "Container" in df.columns else ""

    # Convert "38.56MiB / 7.708GiB" -> take left side "38.56MiB" and convert to MiB
    def to_mib(s: str) -> Optional[float]:
        if not isinstance(s, str):
            return np.nan
        left = s.split("/", 1)[0].strip()
        m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*([KMGT]?i?B|[KMGT]?B)\s*$", left, flags=re.IGNORECASE)
        if not m:
            return np.nan
        val = float(m.group(1))
        unit = m.group(2).lower()

        # Normalize units to MiB
        # Accept both SI-ish (kB, MB, GB, TB) and IEC (KiB, MiB, GiB, TiB)
        if unit in ("b",):
            return val / (1024 ** 2)
        if unit in ("kb", "kib"):
            return val / 1024.0
        if unit in ("mb", "mib"):
            return val
        if unit in ("gb", "gib"):
            return val * 1024.0
        if unit in ("tb", "tib"):
            return val * 1024.0 * 1024.0
        return np.nan

    df["mem_mib"] = df["MemUsage"].apply(to_mib)
    out = pd.DataFrame({"timestamp": df["timestamp"], "mem_mib": df["mem_mib"], "container": container_col})
    out = out.dropna(subset=["timestamp", "mem_mib"]).sort_values("timestamp").reset_index(drop=True)
    if out.empty:
        print(f"[WARN] No valid memory rows parsed from {path}.", file=sys.stderr)
    return out


def find_closest_memory_usage(mem_df: pd.DataFrame, target_dt: pd.Timestamp,
                              tolerance_seconds: int = 60) -> Tuple[Optional[float], Optional[pd.Timestamp], Optional[float]]:
    """
    Find the mem_mib closest to target_dt within tolerance_seconds.
    Returns (mem_mib, found_timestamp, delta_seconds) or (np.nan, None, None) if not found.
    """
    if mem_df is None or mem_df.empty or pd.isna(target_dt):
        return (np.nan, None, None)

    # Compute absolute time difference
    deltas = (mem_df["timestamp"] - target_dt).abs()
    idx = deltas.idxmin()
    delta_sec = abs((mem_df.loc[idx, "timestamp"] - target_dt).total_seconds())

    if delta_sec <= tolerance_seconds:
        return (float(mem_df.loc[idx, "mem_mib"]), pd.Timestamp(mem_df.loc[idx, "timestamp"]), float(delta_sec))
    return (np.nan, None, None)


# ---------- Plotting ----------

def create_cumulative_graph_with_memory(output_svg: str,
                                        df_nocache: pd.DataFrame,
                                        df_cache: pd.DataFrame,
                                        df_nosgx: pd.DataFrame,
                                        mem_df: pd.DataFrame) -> None:
    """
    Build an SVG:
      - Left Y: duration_ms (line) - 3 lines: cache, nocache, nosgx
      - Right Y: matched mem_mib (bars) - only for cache and nocache
      - Colors: cache=#2E86AB, nocache=#F18F01, nosgx=#28A745
    """
    # Prepare matched memory (only for cache and nocache)
    def attach_memory(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        mem_vals = []
        mem_ts = []
        deltas = []
        for t in df["median_time"]:
            m, ts, d = find_closest_memory_usage(mem_df, pd.Timestamp(t), tolerance_seconds=60)
            mem_vals.append(m)
            mem_ts.append(ts)
            deltas.append(d)
        df = df.copy()
        df["matched_mem_mib"] = mem_vals
        df["matched_mem_timestamp"] = mem_ts
        df["matched_mem_delta_sec"] = deltas
        return df

    df_nocache = attach_memory(df_nocache)
    df_cache = attach_memory(df_cache)
    # df_nosgx does not get memory matching

    # X positions (offset so lines don't fully overlap)
    x_nc = df_nocache["run"].to_numpy() - 0.2 if not df_nocache.empty else np.array([])
    x_c = df_cache["run"].to_numpy() if not df_cache.empty else np.array([])
    x_nosgx = df_nosgx["run"].to_numpy() + 0.2 if not df_nosgx.empty else np.array([])

    max_runs = 0
    if not df_nocache.empty:
        max_runs = max(max_runs, int(df_nocache["run"].max()))
    if not df_cache.empty:
        max_runs = max(max_runs, int(df_cache["run"].max()))
    if not df_nosgx.empty:
        max_runs = max(max_runs, int(df_nosgx["run"].max()))
    if max_runs == 0:
        print("[ERROR] Nothing to plot (no runs).", file=sys.stderr)
        sys.exit(1)

    # Figure
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Lines: Duration (ms)
    if not df_cache.empty:
        ax1.plot(x_c, df_cache["cumulative_ms"], marker="o", linewidth=1.6,
                 label="Cache: Time (ms)", color="#2E86AB")
    if not df_nocache.empty:
        ax1.plot(x_nc, df_nocache["cumulative_ms"], marker="o", linewidth=1.6,
                 label="No-cache: Time (ms)", color="#F18F01")
    if not df_nosgx.empty:
        ax1.plot(x_nosgx, df_nosgx["cumulative_ms"], marker="o", linewidth=1.6,
                 label="Third: Time (ms)", color="#28A745")

    ax1.set_xlabel("Run #")
    ax1.set_ylabel("Duration (ms)")
    ax1.grid(True, axis="y", alpha=0.25)

    # X ticks thinning if >=100 runs
    if max_runs >= 100:
        step = int(np.ceil(max_runs / 20.0))
        ticks = np.arange(1, max_runs + 1, step)
    else:
        ticks = np.arange(1, max_runs + 1, 1)
    ax1.set_xticks(ticks)

    # Bars: Memory (MiB) on secondary axis (only cache and nocache)
    ax2 = ax1.twinx()
    bar_w = 0.18
    if not df_cache.empty:
        ax2.bar(x_c - 0.1, df_cache["matched_mem_mib"], width=bar_w, alpha=0.35,
                label="Cache: Mem (MiB)", color="#2E86AB", zorder=1)
    if not df_nocache.empty:
        ax2.bar(x_nc + 0.1, df_nocache["matched_mem_mib"], width=bar_w, alpha=0.35,
                label="No-cache: Mem (MiB)", color="#F18F01", zorder=1)
    ax2.set_ylabel("Memory (MiB)")

    # Combined legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)

    plt.tight_layout()
    try:
        plt.savefig(output_svg, format="svg", bbox_inches="tight")
        print(f"[INFO] Saved SVG: {output_svg}")
    except Exception as e:
        print(f"[ERROR] Failed to save SVG: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        plt.close(fig)


# ---------- Stats printing ----------

def _print_stats(tag: str, df: pd.DataFrame):
    print(f"\n=== {tag} ===")
    if df is None or df.empty:
        print("No runs.")
        return
    n = len(df)
    total = int(df["duration_ms"].sum())
    mean = float(df["duration_ms"].mean())
    med = float(df["duration_ms"].median())
    dmin = int(df["duration_ms"].min())
    dmax = int(df["duration_ms"].max())
    t0 = df["start_time"].min()
    t1 = df["end_time"].max()
    print(f"Runs: {n}")
    print(f"Time range: {t0} -> {t1}")
    print(f"Duration_ms: total={total}, mean={mean:.1f}, median={med:.1f}, min={dmin}, max={dmax}")
    print(f"Cumulative last (ms): {int(df['cumulative_ms'].iloc[-1]) if n>0 else 0}")

    # Memory match stats (only if memory data exists)
    if "matched_mem_mib" in df.columns:
        matched = df["matched_mem_mib"].notna().sum()
        print(f"Memory matched within 60s: {matched}/{n}")
        if matched > 0:
            mem_mean = df["matched_mem_mib"].dropna().mean()
            mem_med = df["matched_mem_mib"].dropna().median()
            print(f"MemUsage (MiB): mean={mem_mean:.2f}, median={mem_med:.2f}")


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(
        description="Parse benchmark logs & memory CSV, then plot durations (lines) and memory (bars) as SVG."
    )
    ap.add_argument("output_svg", help="Path to output SVG file")
    ap.add_argument("nocache_log", help="No-cache benchmark log file (cached:False)")
    ap.add_argument("cache_log", help="Cache benchmark log file (cached:True)")
    ap.add_argument("nosgx_log", help="No-SGX benchmark log file")
    ap.add_argument("memory_csv", help="Memory usage CSV file")
    args = ap.parse_args()

    # Parse inputs
    df_nc = parse_benchmark_log(args.nocache_log, expected_cached=False)
    df_c = parse_benchmark_log(args.cache_log, expected_cached=True)
    df_nosgx = parse_benchmark_log(args.nosgx_log, expected_cached=True)
    mem_df = parse_memory_usage_csv(args.memory_csv)

    # Print stats
    _print_stats("NO-CACHE (cached=False)", df_nc)
    _print_stats("CACHE (cached=True)", df_c)
    _print_stats("NO-SGX", df_nosgx)

    # Plot
    create_cumulative_graph_with_memory(args.output_svg, df_nc, df_c, df_nosgx, mem_df)

if __name__ == "__main__":
    main()
