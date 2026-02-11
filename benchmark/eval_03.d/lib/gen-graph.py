#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

FONTSIZE = 20

CPU_COLOR = '#FF6B6B'      # コーラルレッド
MEMORY_COLOR = '#4ECDC4'   # ターコイズ
REGION_COLOR = '#495057'  # グレー

def infer_bar_width(timestamps: pd.Series) -> float:
    '''Return bar width in matplotlib date units (days).'''
    if len(timestamps) < 2:
        # default: 1 second in days
        return 1.0 / (24 * 3600)
    diffs = timestamps.sort_values().diff().dropna().dt.total_seconds().to_numpy()
    if diffs.size == 0:
        return 1.0 / (24 * 3600)
    # Use median spacing; clamp to [0.2s, 60s] for sanity, expressed in days.
    med = float(np.median(diffs))
    med = max(0.2, min(med, 60.0))
    return med / (24 * 3600)


def plot_cpu_mem_svg(json_file: str, out_svg: str) -> None:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    points: List[Dict[str, Any]] = data['points']
    periods: List[Dict[str, Any]] = data.get('periods', [])

    df = pd.DataFrame(points)
    if df.empty:
        raise SystemExit('No points found in JSON.')

    # Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    t0 = df['timestamp'].iloc[0]
    df['elapsed_sec'] = (df['timestamp'] - t0).dt.total_seconds()

    # For periods, convert start/end to elapsed seconds too
    for p in periods:
        p['start_sec'] = (pd.to_datetime(p['start']) - t0).total_seconds()
        p['end_sec'] = (pd.to_datetime(p['end']) - t0).total_seconds()

    # Figure & axes
    fig, ax = plt.subplots(figsize=(12, 6))
    ax2 = ax.twinx()

    # --- Draw order control ---
    # 1) Memory: line + filled area (secondary axis)
    line_mem, = ax2.plot(df['elapsed_sec'], df['mem'],
        color=MEMORY_COLOR, label='Memory (MB)', linewidth=1.5, zorder=1.5)
    ax2.fill_between(df['elapsed_sec'], df['mem'],
        color=MEMORY_COLOR, alpha=0.25, zorder=1)

    # 2) CPU line (primary axis)
    line_cpu, = ax.plot(df['elapsed_sec'], df['cpu'],
                        color=CPU_COLOR, label='CPU (%)', linewidth=2.0, zorder=3)

    # 3) Bring primary axis to the front
    ax.set_zorder(3)
    ax.patch.set_visible(False)  # keep background transparent so bars remain visible

    ax.set_ylabel('CPU (%)', fontsize=FONTSIZE)
    ax2.set_ylabel('Memory (MB)', fontsize=FONTSIZE)

    # Shade parallel_num periods on the primary axis (behind line but above bars)
    # parallel_numラベルの縦位置を交互にずらす
    for i, p in enumerate(periods):
        start = p["start_sec"]
        end = p["end_sec"]
        ax.axvspan(start, end, facecolor=REGION_COLOR, alpha=0.2, zorder=0.5)
        mid = (start + end) / 2

        mid = start + (end - start) / 2
        # 偶数・奇数で縦位置を交互にする（重なり防止）
        y_pos = 0.92 if i % 2 == 0 else 0.85
        ax.text(mid, y_pos, f"Parallel: {p.get('parallel_num', '?')}",
                transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=FONTSIZE*0.6, zorder=4)

    # X-axis formatting
    ax.set_xlabel("Elapsed Time (seconds)", fontsize=FONTSIZE)

    # Title
    start_all = pd.to_datetime(data.get('start', df['timestamp'].min()))
    end_all = pd.to_datetime(data.get('end', df['timestamp'].max()))

    # Grid & legend
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, zorder=0)
    handles = [line_cpu, line_mem]
    labels = ['CPU (%)', 'Memory (MB)']
    ax.legend(handles, labels, loc='upper right', fontsize=FONTSIZE*0.6, frameon=True)

    ax.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)

    ax.tick_params(axis='both', labelsize=FONTSIZE*0.8)   # X軸のフォントサイズを10ptに
    ax2.tick_params(axis='both', labelsize=FONTSIZE*0.8)  # 右Y軸（Memory）

    fig.tight_layout()
    Path(out_svg).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_svg, format='svg')
    print(f'Saved: {out_svg}')


def main():
    parser = argparse.ArgumentParser(description='Plot CPU (line) on top of Memory (bar) to an SVG. Shades parallel_num periods.')
    parser.add_argument('json_file', help='Path to graph_data.json')
    parser.add_argument('out', help='Output SVG path (default: graph_cpu_mem.svg)')
    args = parser.parse_args()
    plot_cpu_mem_svg(args.json_file, args.out)


if __name__ == '__main__':
    main()
