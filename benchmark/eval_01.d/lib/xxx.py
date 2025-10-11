#!/usr/bin/env python3
"""
Multi-log analyzer with SVG graph output

Usage:
    python3 log_analyzer.py output.svg log1.log log2.log log3.log ...

Example:
    python3 log_analyzer.py \
        graph_app_registration.svg \
        eval_app_registration.log \
        eval_obtaining_app_id.log \
        eval_code_analysis.log
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta
import numpy as np
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import argparse

FONTSIZE=20

def parse_log_file(log_file):
    """
    単一のログファイルを解析してDataFrameに変換
    
    Parameters:
    log_file: ログファイルのパス
    
    Returns:
    pandas.DataFrame: 解析されたデータ
    """
    data = []
    log_path = Path(log_file)
    
    if not log_path.exists():
        print(f"Warning: Log file not found: {log_file}")
        return pd.DataFrame()
    
    print(f"Parsing log file: {log_file}")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or not line.startswith('___BENCH___'):
                continue
            
            # 正規表現でデータを抽出
            # ___BENCH___ App registration (Start:2025-09-03 11:12:16, End:2025-09-03 11:12:28, Duration_ms:11637)
            pattern = r'___BENCH___ (.+?) \(Start:([^,]+), End:([^,]+), Duration_ms:(\d+)(?:, .*)?\)'
            match = re.match(pattern, line)
            
            if match:
                operation_name = match.group(1)
                duration_ms = int(match.group(4))
                data.append({
                    'operation': operation_name,
                    'duration_ms': duration_ms,
                    'log_name': log_path.stem,
                    'line_number': line_num
                })
            else:
                print(f"Warning: Could not parse line {line_num} in {log_file}: {line}")
    
    df = pd.DataFrame(data)
    if not df.empty:
        print(f"  Parsed {len(df)} records from {log_file}")
    else:
        print(f"  No valid records found in {log_file}")
    
    return df

def create_multi_log_graph(output_path, log_files, show_flag):
    """
    複数のログファイルからグラフを作成
    
    Parameters:
    output_path: 出力SVGファイルのパス
    log_files: ログファイルのリスト
    """
    
    if not log_files:
        print("Error: No log files specified")
        sys.exit(1)
    
    print(f"=== Multi-Log Analysis ===")
    print(f"Output file: {output_path}")
    print(f"Input files: {len(log_files)} files")
    
    # 全ログファイルを解析
    all_dataframes = []
    for log_file in log_files:
        df = parse_log_file(log_file)
        if not df.empty:
            all_dataframes.append(df)
    
    if not all_dataframes:
        print("Error: No valid data found in any log files")
        sys.exit(1)
    
    # 全データを結合
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    # 試行番号（同一ログ×同一オペレーション内で 1..N）を付与
    # まず、同一ログ×オペレーション内での出現順に並べる（line_number があればそれを使用）
    if 'line_number' in combined_df.columns:
        combined_df = combined_df.sort_values(['log_name','operation','line_number']).reset_index(drop=True)
    else:
        combined_df = combined_df.sort_values(['log_name','operation']).reset_index(drop=True)
    combined_df['trial_index'] = combined_df.groupby(['log_name','operation']).cumcount() + 1
    
    print(f"\n=== Combined Data Summary ===")
    print(f"Total records: {len(combined_df)}")
    print(f"Duration range: {combined_df['duration_ms'].min()} - {combined_df['duration_ms'].max()} ms")
    print(f"Operations: {combined_df['operation'].unique()}")
    print(f"Log files: {combined_df['log_name'].unique()}")
    
    # グラフの作成
    plt.figure(figsize=(12, 6))
    
    # ログファイルから拡張子を除去
    log_names = [Path(log_file).stem for log_file in log_files]

    # ログファイル別に色分け
    colors = [plt.cm.Set1(i) for i in range(len(log_names))]
    color_map = {log_name: colors[i] for i, log_name in enumerate(log_names)}
    
    # オペレーション別にマーカーを変える
    operations_unique = combined_df['operation'].unique()
    
    # 同じログファイルのデータを線で結ぶ
    for log_name in log_names:
        log_data = combined_df[combined_df['log_name'] == log_name]
        for operation in log_data['operation'].unique():
            op_data = log_data[log_data['operation'] == operation]
            if len(op_data) > 1:
                plt.plot(op_data['trial_index'], op_data['duration_ms'],
                        color=color_map[log_name], alpha=1.0, linewidth=2, linestyle='-',
                        label=f'{operation}')

    # グラフの装飾
    plt.xlabel('Number of Trials', fontsize=FONTSIZE)
    plt.ylabel('Processing Time (ms)', fontsize=FONTSIZE)
    plt.grid(True, alpha=0.3)
    
    # Y軸の範囲を調整
    y_min = 0
    y_max = combined_df['duration_ms'].max() * 1.2
    plt.ylim(y_min, y_max)
    
    # X軸の試行番号表示を調整（整数目盛）
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    x_min = max(1, combined_df['trial_index'].min())
    x_max = combined_df['trial_index'].max()
    print(f"Debug: trial_index range: {x_min} to {x_max}")

    plt.xlim(x_min, x_max)
    if x_max - x_min <= 10:
        plt.xticks(range(x_min, x_max + 1))  # 全ての値を表示
    else:
        # きりの良い間隔を計算
        data_range = x_max - x_min
        if data_range <= 50:
            step = 10
        elif data_range <= 200:
            step = 50
        elif data_range <= 500:
            step = 100
        else:
            step = 200
        # 1から始めて、きりの良い数字で目盛りを設定
        ticks = [1]  # 必ず1を含める
        current = ((x_min // step) + 1) * step  # 最初のきりの良い数字
        while current <= x_max:
            if current != 1:  # 1は既に追加済み
                ticks.append(current)
            current += step
        # 最大値も追加（きりの良い数字でない場合）
        if ticks[-1] != x_max:
            ticks.append(x_max)
        plt.xticks(ticks)

    plt.tick_params(axis='both', which='major', labelsize=FONTSIZE*0.8)
    plt.legend(loc='upper right', framealpha=0.6, fontsize=FONTSIZE*0.6)

    # SVG形式で保存
    plt.savefig(output_path, format='svg', dpi=300, bbox_inches='tight', pad_inches=0.1)
    
    # 詳細統計を出力
    print(f"\n" + "="*70)
    print("DETAILED ANALYSIS RESULTS")
    print("="*70)
    
    # ログファイル別統計
    print(f"\nLog File Statistics:")
    for log_name in log_names:
        log_data = combined_df[combined_df['log_name'] == log_name]
        print(f"  {log_name}:")
        print(f"    • Records: {len(log_data)}")
        print(f"    • Duration avg: {log_data['duration_ms'].mean():.1f} ms")
        print(f"    • Duration range: {log_data['duration_ms'].min()}-{log_data['duration_ms'].max()} ms")
        print(f"    • Operations: {list(log_data['operation'].unique())}")
    
    # オペレーション別統計
    print(f"\nOperation Statistics:")
    for operation in operations_unique:
        op_data = combined_df[combined_df['operation'] == operation]
        print(f"  {operation}:")
        print(f"    • Records: {len(op_data)}")
        print(f"    • Duration avg: {op_data['duration_ms'].mean():.1f} ms")
        print(f"    • Duration range: {op_data['duration_ms'].min()}-{op_data['duration_ms'].max()} ms")
        print(f"    • Std dev: {op_data['duration_ms'].std():.1f} ms")
    
    print(f"\nGraph saved as: {output_path}")

    if show_flag:
        plt.show()
    
    return combined_df

def main(input_list, output_path, show_flag):
    """メイン関数"""
    
    log_files = input_list
    
    # 出力ファイルの拡張子チェック
    if not output_path.lower().endswith('.svg'):
        print(f"Warning: Output file '{output_path}' does not have .svg extension")
    
    # ログファイルの存在チェック
    missing_files = []
    for log_file in log_files:
        if not Path(log_file).exists():
            missing_files.append(log_file)
    
    if missing_files:
        print("Error: The following log files were not found:")
        for missing_file in missing_files:
            print(f"  - {missing_file}")
        sys.exit(1)
    
    try:
        # グラフ作成
        df_result = create_multi_log_graph(output_path, log_files, show_flag)
        print(f"\n✓ Analysis completed successfully!")
        print(f"✓ Graph saved to: {output_path}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--show", action="store_true")
    parser.add_argument("output")
    parser.add_argument("input", nargs='+')

    args = parser.parse_args()

    main(args.input, args.output, args.show)

# 使用例:
# python3 log_analyzer.py graph_app_registration.svg eval_app_registration.log eval_obtaining_app_id.log eval_code_analysis.log