import pandas as pd
import matplotlib.pyplot as plt
import re
import sys
from datetime import datetime, timedelta
import numpy as np
import matplotlib.dates as mdates

def parse_benchmark_log(log_file):
    """
    ベンチマークログファイルを解析してDataFrameに変換
    
    ログ形式:
    ___BENCH___ App registration (Start:2025-09-03 11:15:18, End:2025-09-03 11:15:25, Duration_ms:6440, scenario:no_cache, data_processed:True, cached:False)
    """
    
    data = []
    
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or not line.startswith('___BENCH___'):
                continue
            
            # 正規表現でデータを抽出
            pattern = r'___BENCH___ (.+?) \(Start:([^,]+), End:([^,]+), Duration_ms:(\d+), scenario:([^,]+), data_processed:([^,]+), cached:([^)]+)\)'
            match = re.match(pattern, line)
            
            if match:
                app_name = match.group(1)
                start_time = match.group(2)
                end_time = match.group(3)
                duration_ms = int(match.group(4))
                scenario = match.group(5)
                data_processed = match.group(6) == 'True'
                cached = match.group(7) == 'True'
                
                # 中央時間を計算
                try:
                    start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                    middle_time = start_dt + (end_dt - start_dt) / 2
                except ValueError:
                    print(f"Warning: Could not parse datetime on line {line_num}: {start_time}, {end_time}")
                    continue
                
                data.append({
                    'app_name': app_name,
                    'start_time': start_dt,
                    'end_time': end_dt,
                    'middle_time': middle_time,
                    'duration_ms': duration_ms,
                    'scenario': scenario,
                    'data_processed': data_processed,
                    'cached': cached,
                    'line_number': line_num
                })
            else:
                print(f"Warning: Could not parse line {line_num}: {line}")
    
    if not data:
        raise ValueError("No valid benchmark data found in the log file")
    
    return pd.DataFrame(data)

def create_duration_bar_chart(log_file, output_file='benchmark_duration_chart.svg'):
    """
    ベンチマークログから処理時間の縦棒グラフを作成
    
    Parameters:
    log_file: ログファイルのパス
    output_file: 出力ファイル名
    """
    
    # ログファイルを解析
    df = parse_benchmark_log(log_file)
    
    print("=== Benchmark Data Analysis ===")
    print(f"Total records: {len(df)}")
    print(f"Time range: {df['start_time'].min()} to {df['end_time'].max()}")
    print(f"Duration range: {df['duration_ms'].min()} - {df['duration_ms'].max()} ms")
    print(f"Scenarios: {df['scenario'].unique()}")
    print(f"Apps: {df['app_name'].unique()}")
    
    # グラフの作成
    plt.figure(figsize=(16, 8))
    
    # シナリオ別に色分け
    scenarios = df['scenario'].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(scenarios)))
    color_map = {scenario: colors[i] for i, scenario in enumerate(scenarios)}
    
    # 各データポイントの色を決定
    bar_colors = [color_map[scenario] for scenario in df['scenario']]
    
    # 縦棒グラフを作成
    bars = plt.bar(df['middle_time'], df['duration_ms'], 
                   color=bar_colors, alpha=0.7, width=timedelta(seconds=2),
                   edgecolor='black', linewidth=0.5)
    
    # グラフの装飾
    plt.title('Benchmark Processing Duration Over Time', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Middle Time (Start + End) / 2', fontsize=12)
    plt.ylabel('Duration (ms)', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Y軸の範囲を調整（データの範囲に合わせる）
    y_min = df['duration_ms'].min() * 0.95
    y_max = df['duration_ms'].max() * 1.05
    plt.ylim(y_min, y_max)
    
    # X軸の時刻表示を調整
    total_time = (df['middle_time'].max() - df['middle_time'].min()).total_seconds()
    
    if total_time <= 600:  # 10分以内
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    elif total_time <= 3600:  # 1時間以内
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    else:  # 1時間以上
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # X軸ラベルを横向きに表示
    plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=0, ha='center')
    
    # 凡例を作成（シナリオ別）
    legend_elements = []
    for scenario in scenarios:
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=color_map[scenario], 
                                           alpha=0.7, label=f'Scenario: {scenario}'))
    
    plt.legend(handles=legend_elements, loc='upper right', framealpha=0.9)
    
    # 統計情報を追加（グラフの下部）
    stats_text = f"Total: {len(df)} records | Duration: {df['duration_ms'].min()}-{df['duration_ms'].max()}ms | Avg: {df['duration_ms'].mean():.0f}ms"
    plt.figtext(0.5, 0.02, stats_text, ha='center', fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
    
    # レイアウト調整
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)  # 下部の統計情報用スペース
    
    # SVG形式で保存
    plt.savefig(output_file, format='svg', dpi=300, bbox_inches='tight')
    
    # 詳細統計を出力
    print("\n" + "="*60)
    print("BENCHMARK PERFORMANCE ANALYSIS")
    print("="*60)
    
    # 全体統計
    print(f"Overall Statistics:")
    print(f"  • Total benchmarks: {len(df)}")
    print(f"  • Duration range: {df['duration_ms'].min()} - {df['duration_ms'].max()} ms")
    print(f"  • Average duration: {df['duration_ms'].mean():.1f} ms")
    print(f"  • Standard deviation: {df['duration_ms'].std():.1f} ms")
    print(f"  • Time span: {(df['end_time'].max() - df['start_time'].min()).total_seconds():.0f} seconds")
    
    # シナリオ別統計
    print(f"\nScenario-wise Analysis:")
    for scenario in scenarios:
        scenario_data = df[df['scenario'] == scenario]
        print(f"  {scenario}:")
        print(f"    • Count: {len(scenario_data)}")
        print(f"    • Avg duration: {scenario_data['duration_ms'].mean():.1f} ms")
        print(f"    • Min-Max: {scenario_data['duration_ms'].min()}-{scenario_data['duration_ms'].max()} ms")
        print(f"    • Std dev: {scenario_data['duration_ms'].std():.1f} ms")
    
    # キャッシュ効果の分析
    if 'cached' in df.columns:
        cached_data = df[df['cached'] == True]
        non_cached_data = df[df['cached'] == False]
        
        if len(cached_data) > 0 and len(non_cached_data) > 0:
            print(f"\nCache Effect Analysis:")
            print(f"  • Non-cached avg: {non_cached_data['duration_ms'].mean():.1f} ms")
            print(f"  • Cached avg: {cached_data['duration_ms'].mean():.1f} ms")
            improvement = non_cached_data['duration_ms'].mean() - cached_data['duration_ms'].mean()
            print(f"  • Performance improvement: {improvement:.1f} ms ({improvement/non_cached_data['duration_ms'].mean()*100:.1f}%)")
    
    plt.show()
    
    return df

def create_scenario_comparison_chart(log_file, output_file='scenario_comparison.svg'):
    """
    シナリオ別の比較チャート
    """
    df = parse_benchmark_log(log_file)
    
    # シナリオ別の統計を計算
    scenario_stats = df.groupby('scenario')['duration_ms'].agg(['mean', 'std', 'count']).reset_index()
    
    plt.figure(figsize=(10, 6))
    
    # 棒グラフで平均を表示、エラーバーで標準偏差を表示
    bars = plt.bar(scenario_stats['scenario'], scenario_stats['mean'], 
                   yerr=scenario_stats['std'], capsize=5, alpha=0.7,
                   color=['#2E86AB', '#F18F01'], edgecolor='black')
    
    # 各棒の上にカウント数を表示
    for i, (bar, count) in enumerate(zip(bars, scenario_stats['count'])):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + scenario_stats['std'].iloc[i] + 10,
                f'n={count}', ha='center', va='bottom', fontweight='bold')
    
    plt.title('Performance Comparison by Scenario', fontsize=16, fontweight='bold')
    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Average Duration (ms)', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, format='svg', dpi=300, bbox_inches='tight')
    plt.show()
    
    return scenario_stats

# 使用例
if __name__ == "__main__":
    print("Creating benchmark duration chart...")
    
    # メインの縦棒グラフ
    df_result = create_duration_bar_chart(sys.argv[1], sys.argv[2])
    
    print("\nCreating scenario comparison chart...")
    
    # シナリオ比較チャート
    scenario_stats = create_scenario_comparison_chart('eval_data_processing.log', 'scenario_comparison.svg')
    
    print("\nBoth charts have been created successfully!")

# 必要なライブラリ
"""
pip install pandas matplotlib numpy
"""
