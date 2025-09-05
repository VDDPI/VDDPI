#!/usr/bin/env python3
"""
累積Duration_ms折れ線グラフ作成プログラム

Usage:
    python3 cumulative_graph.py
    
このプログラムは2つのログファイルを読み込み、
横軸：実行回数（1回目、2回目、...）
縦軸：Duration_msの累積値
で折れ線グラフを作成します。
"""

import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime
import numpy as np
from pathlib import Path
import argparse

def parse_benchmark_log(log_file):
    """
    ベンチマークログファイルを解析してDataFrameに変換
    
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
        execution_count = 0
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or not line.startswith('___BENCH___'):
                continue
            
            # 正規表現でデータを抽出
            pattern = r'___BENCH___ (.+?) \(Start:([^,]+), End:([^,]+), Duration_ms:(\d+)(?:, scenario:([^,]+))?(?:, .*)?\)'
            match = re.match(pattern, line)
            
            if match:
                execution_count += 1
                operation_name = match.group(1)
                start_time = match.group(2)
                end_time = match.group(3)
                duration_ms = int(match.group(4))
                scenario = match.group(5) if match.group(5) else 'unknown'
                
                data.append({
                    'execution_number': execution_count,
                    'operation': operation_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_ms': duration_ms,
                    'scenario': scenario,
                    'log_file': log_path.stem,
                    'line_number': line_num
                })
            else:
                print(f"Warning: Could not parse line {line_num} in {log_file}: {line}")
    
    df = pd.DataFrame(data)
    if not df.empty:
        # 累積Duration_msを計算
        df['cumulative_duration_ms'] = df['duration_ms'].cumsum()
        print(f"  Parsed {len(df)} records from {log_file}")
        print(f"  Total duration: {df['cumulative_duration_ms'].iloc[-1]} ms")
    else:
        print(f"  No valid records found in {log_file}")
    
    return df

def create_cumulative_graph(cache_log, nocache_log, output_file='cumulative_duration.svg'):
    """
    2つのログファイルから累積Duration_msの折れ線グラフを作成
    
    Parameters:
    cache_log: キャッシュありのログファイル
    nocache_log: キャッシュなしのログファイル
    output_file: 出力ファイル名
    """
    
    print("=== Cumulative Duration Analysis ===")
    
    # 各ログファイルを解析
    df_cache = parse_benchmark_log(cache_log)
    df_nocache = parse_benchmark_log(nocache_log)
    
    if df_cache.empty and df_nocache.empty:
        print("Error: No valid data found in any log files")
        return
    
    # グラフの作成
    plt.figure(figsize=(12, 8))
    
    # キャッシュありのデータをプロット
    if not df_cache.empty:
        plt.plot(df_cache['execution_number'], df_cache['cumulative_duration_ms'],
                linewidth=2.5, color='#2E86AB',
                label=f'Cache (scenario: {df_cache["scenario"].iloc[0]})')
    
    # キャッシュなしのデータをプロット
    if not df_nocache.empty:
        plt.plot(df_nocache['execution_number'], df_nocache['cumulative_duration_ms'],
                linewidth=2.5, color='#F18F01',
                label=f'No Cache (scenario: {df_nocache["scenario"].iloc[0]})')
    
    # グラフの装飾
    plt.xlabel('Number of Providers', fontsize=12, fontweight='bold')
    plt.ylabel('Duration (ms)', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(framealpha=0.9, fontsize=11)
    
    # X軸を整数に設定
    max_executions = 0
    if not df_cache.empty:
        max_executions = max(max_executions, df_cache['execution_number'].max())
    if not df_nocache.empty:
        max_executions = max(max_executions, df_nocache['execution_number'].max())
    
    plt.xlim(0.5, max_executions + 0.5)

    tick_interval = max(1, max_executions // 10)

    # X軸の目盛りを設定
    tick_positions = list(range(tick_interval, max_executions + 1, tick_interval))
    
    # 最初（1回目）と最後を必ず含める
    if 1 not in tick_positions:
        tick_positions.insert(0, 1)
    if max_executions not in tick_positions:
        tick_positions.append(max_executions)

    plt.xticks(tick_positions)
    
    # Y軸のフォーマットを改善
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    
    # レイアウト調整
    plt.tight_layout()
    
    # SVG形式で保存
    plt.savefig(output_file, format='svg', dpi=300, bbox_inches='tight')
    
    # 詳細統計を出力
    print("\n" + "="*60)
    print("DETAILED ANALYSIS RESULTS")
    print("="*60)
    
    if not df_cache.empty:
        print(f"\nCache Scenario:")
        print(f"  • Executions: {len(df_cache)}")
        print(f"  • Individual durations: {df_cache['duration_ms'].min()}-{df_cache['duration_ms'].max()} ms")
        print(f"  • Average per execution: {df_cache['duration_ms'].mean():.1f} ms")
        print(f"  • Total cumulative: {df_cache['cumulative_duration_ms'].iloc[-1]:,} ms")
        print(f"  • Final execution time: {df_cache['cumulative_duration_ms'].iloc[-1] / 1000:.1f} seconds")
    
    if not df_nocache.empty:
        print(f"\nNo Cache Scenario:")
        print(f"  • Executions: {len(df_nocache)}")
        print(f"  • Individual durations: {df_nocache['duration_ms'].min()}-{df_nocache['duration_ms'].max()} ms")
        print(f"  • Average per execution: {df_nocache['duration_ms'].mean():.1f} ms")
        print(f"  • Total cumulative: {df_nocache['cumulative_duration_ms'].iloc[-1]:,} ms")
        print(f"  • Final execution time: {df_nocache['cumulative_duration_ms'].iloc[-1] / 1000:.1f} seconds")
    
    # パフォーマンス比較
    if not df_cache.empty and not df_nocache.empty:
        print(f"\nPerformance Comparison:")
        min_executions = min(len(df_cache), len(df_nocache))
        cache_avg = df_cache['duration_ms'].mean()
        nocache_avg = df_nocache['duration_ms'].mean()
        avg_improvement = nocache_avg - cache_avg
        avg_improvement_percent = (avg_improvement / nocache_avg) * 100
        
        print(f"  • Average improvement per execution: {avg_improvement:.1f} ms ({avg_improvement_percent:.1f}%)")
        print(f"  • Cache efficiency: {cache_avg/nocache_avg*100:.1f}% of no-cache time")
        
        if min_executions > 1:
            total_improvement = (df_nocache['cumulative_duration_ms'].iloc[min_executions-1] - 
                               df_cache['cumulative_duration_ms'].iloc[min_executions-1])
            print(f"  • Total time saved ({min_executions} executions): {total_improvement:,} ms ({total_improvement/1000:.1f} seconds)")
    
    print(f"\nGraph saved as: {output_file}")
    plt.show()
    
    return df_cache, df_nocache

def main(nocache_log_file, cache_log_file, output_svg):
    """メイン関数"""
    
    try:
        # グラフ作成
        df_cache, df_nocache = create_cumulative_graph(cache_log_file, nocache_log_file, output_svg)
        
        print(f"\n✓ Analysis completed successfully!")
        print(f"✓ Graph saved to: {output_svg}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--show", action="store_true")
    parser.add_argument("output_svg")
    parser.add_argument("nocache_tee_file")
    parser.add_argument("cache_tee_file")

    args = parser.parse_args()

    main(args.nocache_tee_file, args.cache_tee_file, args.output_svg)

# 使用例:
# python3 cumulative_graph.py