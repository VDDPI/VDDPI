#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import sys
from pathlib import Path
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read JSON: {path} -> {e}", file=sys.stderr)
        sys.exit(1)

def prettify_label(name: str) -> str:
    """snake_case → Title Case"""
    return ' '.join(word.capitalize() for word in name.split('_'))

def data_to_map(d: dict) -> dict:
    """
    {"groups": [{"training_data": "1k", "averages_ms": {...}}, ...]} を
    {training_data: {key: val, ...}} に変換
    """
    m = {}
    for g in d.get("groups", []):
        training_data = g.get("training_data")
        if training_data is None:
            continue
        m[training_data] = g.get("averages_ms", {}) or {}
    return m

def plot_stacked_grouped_bars_svg(
    data_a: dict,
    data_b: dict,
    stack_order: list[str],
    dataset_labels=("Dataset A", "Dataset B"),
    title="Stacked Averages by training_data (two datasets)",
    svg_path="stacked_grouped.svg"
) -> str:
    # できるだけ日本語フォント警告を避けたいので既定のDejaVuを明示
    try:
        matplotlib.rcParams["font.family"] = "DejaVu Sans"
    except Exception:
        pass

    map_a = data_to_map(data_a)
    map_b = data_to_map(data_b)

    group_indices = sorted(set(map_a.keys()) | set(map_b.keys()), key=lambda s: int(re.findall(r"\d+", s)[0]))
    if not group_indices:
        raise ValueError("No groups found in either dataset.")

    return plot_stacked_grouped_bars_svg_color_hatch(map_a, map_b, group_indices, stack_order, svg_path, dataset_labels)
    
def plot_stacked_grouped_bars_svg_color_hatch(
    map_a, map_b, group_indices, stack_order, svg_path, dataset_labels
):
    x = np.arange(len(group_indices), dtype=float)
    width = 0.30
    offset = (width / 2.0) + (width * 0.1)

    fig, ax = plt.subplots(figsize=(max(6.0, len(group_indices)*0.6+2.5), 5.0), dpi=120)

    # ---- 色とハッチ（模様）設定 ----
    left_edgecolor  = "#1f77b4"  # 青
    left_facecolor  = "#BCE4FF"
    right_edgecolor = "#d62728"  # 赤
    right_facecolor = "#FFBDBE"
    # 種別ごとの模様（必要に応じて増減）
    hatch_map = {
        "enclave_initializing": "",
        "policy_checking": "///",
        "processing": "...",
    }

    bottoms_a = np.zeros(len(group_indices), dtype=float)
    bottoms_b = np.zeros(len(group_indices), dtype=float)

    # 凡例（スタック種別）用のプロキシ
    stack_handles, stack_labels = [], []

    for key in stack_order:
        vals_a = [float(map_a.get(gi, {}).get(key, 0.0)) for gi in group_indices]
        vals_b = [float(map_b.get(gi, {}).get(key, 0.0)) for gi in group_indices]
        hatch = hatch_map.get(key, "")  # 未定義キーは模様なし

        # 左（青）
        bars_a = ax.bar(
            x - offset, vals_a, width,
            bottom=bottoms_a,
            facecolor=left_facecolor,
            edgecolor=left_edgecolor,
            linewidth=1.0,
            hatch=hatch
        )
        # 右（赤）
        bars_b = ax.bar(
            x + offset, vals_b, width,
            bottom=bottoms_b,
            facecolor=right_facecolor,
            edgecolor=right_edgecolor,
            linewidth=1.0,
            hatch=hatch
        )

        bottoms_a += np.array(vals_a)
        bottoms_b += np.array(vals_b)

        # スタック種別の凡例（模様だけで示すため白地のパッチを作成）
        stack_handles.append(Patch(facecolor="white", edgecolor="black", hatch=hatch))
        stack_labels.append(prettify_label(key))

    # ---- 凡例：スタック種別（左） + データセット（右） ----
    legend_stack = ax.legend(
        reversed(stack_handles), reversed(stack_labels),
        title="Stack Components",
        loc="upper left", bbox_to_anchor=(0.02, 0.98), frameon=True
    )
    ax.add_artist(legend_stack)

    dataset_handles = [
        Patch(facecolor=left_facecolor,  edgecolor=left_edgecolor, label=dataset_labels[0]),
        Patch(facecolor=right_facecolor, edgecolor=right_edgecolor, label=dataset_labels[1]),
    ]
    legend_datasets = ax.legend(
        handles=dataset_handles, title="System",
        loc="upper left", bbox_to_anchor=(0.27, 0.98), frameon=True
    )
    ax.add_artist(legend_datasets)

    ax.set_axisbelow(True)  # グリッドをデータ（棒）より背面に
    ax.yaxis.grid(True, linestyle='-', color='#e5e7eb', linewidth=1.0, zorder=0)
    #ax.grid(True, axis='y', linestyle='-', color='#e5e7eb', linewidth=1.0)

    # ---- 軸など ----
    ax.set_xticks(x)
    ax.set_xticklabels([str(gi) for gi in group_indices])
    ax.set_xlabel("Number of Training Data Samples")
    ax.set_ylabel("Time (ms)")

    fig.tight_layout()
    fig.savefig(svg_path, format="svg")
    plt.close(fig)

    return svg_path

def parse_args():
    p = argparse.ArgumentParser(
        description="Two JSON datasets -> grouped stacked bar chart (SVG). "
                    "X: training_data, Y: milliseconds, stacks: averages_ms"
    )
    p.add_argument("json_a", type=Path, help="JSON file for dataset A")
    p.add_argument("json_b", type=Path, help="JSON file for dataset B")
    p.add_argument("-o", "--output", type=Path, default=Path("stacked_grouped.svg"), help="Output SVG path")
    p.add_argument("--order", nargs="+", required=True,
                   help="Stacking order of averages_ms keys (missing keys are ignored)")
    p.add_argument("--label-a", default="Dataset A", help="Label for dataset A")
    p.add_argument("--label-b", default="Dataset B", help="Label for dataset B")
    p.add_argument("--title", default="Stacked Averages by training_data (two datasets)", help="Chart title")
    return p.parse_args()

def main():
    args = parse_args()
    data_a = load_json(args.json_a)
    data_b = load_json(args.json_b)
    svg = plot_stacked_grouped_bars_svg(
        data_a=data_a,
        data_b=data_b,
        stack_order=args.order,
        dataset_labels=(args.label_a, args.label_b),
        title=args.title,
        svg_path=str(args.output)
    )
    print(f"Saved: {svg}")

if __name__ == "__main__":
    main()