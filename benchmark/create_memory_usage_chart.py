import pandas as pd
import matplotlib.pyplot as plt
import re
import sys
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

def parse_memory_to_mib(mem_str):
    """
    MemUsageの文字列から分子の値をMiB単位で抽出する関数
    例: "1.5GiB / 8GiB" -> 1536.0 (MiB)
    例: "512MiB / 4GiB" -> 512.0 (MiB)
    """
    if pd.isna(mem_str) or mem_str == '':
        return None
    
    # 分子部分を抽出（"/" より前の部分）
    numerator = mem_str.split('/')[0].strip()
    
    # 数値と単位を抽出
    match = re.match(r'([0-9.]+)\s*([A-Za-z]+)', numerator)
    if not match:
        return None
    
    value = float(match.group(1))
    unit = match.group(2).upper()
    
    # 全ての単位をMiBに変換
    if unit in ['GIB', 'GB', 'G']:
        return value * 1024  # GiB to MiB
    elif unit in ['MIB', 'MB', 'M']:
        return value  # Already in MiB
    elif unit in ['KIB', 'KB', 'K']:
        return value / 1024  # KiB to MiB
    elif unit in ['B', 'BYTES']:
        return value / (1024 * 1024)  # Bytes to MiB
    else:
        return value

def create_memory_chart_mib(csv_file, output_file='memory_usage_mib.svg'):
    """
    Container statsからMemUsageの折れ線グラフを作成（MiB単位）
    複数コンテナがある場合は全て表示
    """
    
    # CSVファイルを読み込み
    df = pd.read_csv(csv_file)
    
    print("=== Data Loading ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print("\nFirst few MemUsage values:")
    print(df['MemUsage'].head())
    
    # MemUsageから分子の値をMiB単位で抽出
    df['Memory_MiB'] = df['MemUsage'].apply(parse_memory_to_mib)
    
    # Timestampを日時形式に変換
    try:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        timestamp_is_datetime = True
    except:
        print("Warning: Could not parse Timestamp as datetime, using as-is")
        timestamp_is_datetime = False
    
    # NaN値を除去
    df_clean = df.dropna(subset=['Memory_MiB'])
    
    print(f"\n=== After Processing ===")
    print(f"Valid data points: {len(df_clean)}")
    print(f"Memory usage range: {df_clean['Memory_MiB'].min():.1f} - {df_clean['Memory_MiB'].max():.1f} MiB")
    
    # コンテナの種類を確認
    if 'Container' in df_clean.columns:
        containers = df_clean['Container'].unique()
        print(f"Containers found: {list(containers)}")
    else:
        containers = ['Unknown']
        print("No Container column found, treating as single container")
    
    # グラフの作成
    plt.figure(figsize=(14, 8))
    
    # 複数コンテナの場合は色を分ける
    if len(containers) > 1:
        colors = plt.cm.Set1(np.linspace(0, 1, len(containers)))
        
        for i, container in enumerate(containers):
            container_data = df_clean[df_clean['Container'] == container]
            
            plt.plot(container_data['Timestamp'], container_data['Memory_MiB'], 
                     marker='o', linewidth=2, markersize=6, 
                     color=colors[i], markerfacecolor='white', 
                     markeredgewidth=2, markeredgecolor=colors[i],
                     label=f'{container}', alpha=0.8)
            
            # 各コンテナの平均線
            mean_memory = container_data['Memory_MiB'].mean()
            plt.axhline(y=mean_memory, color=colors[i], linestyle='--', alpha=0.5)
    else:
        # 単一コンテナの場合
        plt.plot(df_clean['Timestamp'], df_clean['Memory_MiB'], 
                 marker='o', linewidth=2, markersize=6, 
                 color='#2E86AB', markerfacecolor='white', 
                 markeredgewidth=2, markeredgecolor='#2E86AB',
                 label='Memory Usage')
        
        # 平均線を追加
        mean_memory = df_clean['Memory_MiB'].mean()
        plt.axhline(y=mean_memory, color='red', linestyle='--', alpha=0.7,
                    label=f'Average: {mean_memory:.1f} MiB')
    
    # グラフの装飾
    plt.title('Container Memory Usage Over Time', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Timestamp', fontsize=12)
    plt.ylabel('Memory Usage (MiB)', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(framealpha=0.9)
    
    # X軸の表示を改善
    if timestamp_is_datetime:
        # データ数に応じて適切な間隔で表示（最大8個）
        total_points = len(df_clean)
        if total_points > 8:
            step = total_points // 7  # 約8個になるように
            indices = list(range(0, total_points, step))
            if indices[-1] != total_points - 1:  # 最後のポイントを含める
                indices.append(total_points - 1)
        else:
            indices = list(range(total_points))
        
        # 選択したインデックスのタイムスタンプを表示
        selected_times = [df_clean.iloc[i]['Timestamp'] for i in indices]
        plt.gca().set_xticks(selected_times)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # 横向きに表示（回転なし）
        plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=0, ha='center')
    else:
        # 非日時データの場合も間隔を調整
        total_points = len(df_clean)
        if total_points > 8:
            step = total_points // 7
            indices = list(range(0, total_points, step))
            if indices[-1] != total_points - 1:
                indices.append(total_points - 1)
            
            # 選択したラベルのみ表示
            all_labels = [str(x) for x in df_clean['Timestamp']]
            selected_labels = [all_labels[i] for i in indices]
            selected_positions = [df_clean.iloc[i]['Timestamp'] for i in indices]
            
            plt.xticks(selected_positions, selected_labels, rotation=0, ha='center')
    
    # レイアウト調整
    plt.tight_layout()
    
    # SVG形式で保存
    plt.savefig(output_file, format='svg', dpi=300, bbox_inches='tight')
    
    # 詳細統計を出力
    print("\n" + "="*50)
    print("MEMORY USAGE ANALYSIS (MiB UNITS)")
    print("="*50)
    
    if len(containers) > 1:
        for container in containers:
            container_data = df_clean[df_clean['Container'] == container]
            print(f"\nContainer: {container}")
            print(f"  • Data points: {len(container_data)}")
            print(f"  • Minimum: {container_data['Memory_MiB'].min():.1f} MiB")
            print(f"  • Maximum: {container_data['Memory_MiB'].max():.1f} MiB")
            print(f"  • Average: {container_data['Memory_MiB'].mean():.1f} MiB")
            print(f"  • Standard deviation: {container_data['Memory_MiB'].std():.1f} MiB")
            
            if len(container_data) > 1:
                memory_trend = container_data['Memory_MiB'].iloc[-1] - container_data['Memory_MiB'].iloc[0]
                trend_text = 'increasing' if memory_trend > 0 else 'decreasing' if memory_trend < 0 else 'stable'
                print(f"  • Overall trend: {memory_trend:+.1f} MiB ({trend_text})")
    else:
        container_name = containers[0] if 'Container' in df_clean.columns else 'Unknown'
        print(f"Container: {container_name}")
        if timestamp_is_datetime:
            print(f"Time period: {df_clean['Timestamp'].iloc[0]} to {df_clean['Timestamp'].iloc[-1]}")
        print(f"Memory usage statistics (MiB):")
        print(f"  • Minimum: {df_clean['Memory_MiB'].min():.1f} MiB")
        print(f"  • Maximum: {df_clean['Memory_MiB'].max():.1f} MiB")
        print(f"  • Average: {df_clean['Memory_MiB'].mean():.1f} MiB")
        print(f"  • Standard deviation: {df_clean['Memory_MiB'].std():.1f} MiB")
        
        # メモリ使用量の変化を分析
        if len(df_clean) > 1:
            memory_trend = df_clean['Memory_MiB'].iloc[-1] - df_clean['Memory_MiB'].iloc[0]
            trend_text = 'increasing' if memory_trend > 0 else 'decreasing' if memory_trend < 0 else 'stable'
            print(f"  • Overall trend: {memory_trend:+.1f} MiB ({trend_text})")
    
    plt.show()
    
    return df_clean

# テスト用の関数
def test_memory_parsing():
    """メモリ解析のテスト"""
    test_cases = [
        "1.5GiB / 8GiB",     # -> 1536.0 MiB
        "512MiB / 4GiB",     # -> 512.0 MiB
        "2048KiB / 16GiB",   # -> 2.0 MiB
        "1073741824B / 8GiB" # -> 1024.0 MiB
    ]
    
    print("=== Memory Parsing Test ===")
    for test in test_cases:
        result = parse_memory_to_mib(test)
        print(f"{test:20} -> {result:.1f} MiB")

if __name__ == "__main__":
    # メモリ解析のテスト
    test_memory_parsing()
    
    print("\n" + "="*50)
    print("CREATING GRAPH...")
    print("="*50)
    
    # グラフ作成
    df_result = create_memory_chart_mib(sys.argv[1], sys.argv[2])

# 使用方法の例：
# python this_script.py
