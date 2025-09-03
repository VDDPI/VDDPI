import json
import random
import os
import sys
import shutil

# --- 引数処理 ---
if len(sys.argv) < 2:
    print("Usage: python3 make_test_data.py <num_files> [seed]")
    sys.exit(1)

num_files = int(sys.argv[1])  # 生成するファイル数

if len(sys.argv) > 2:
    seed = int(sys.argv[2])
    random.seed(seed)
    print(f"🔧 Using random seed = {seed}")
else:
    print("🔧 No seed specified (random each run)")

# --- 出力先ディレクトリ ---
output_dir = "data/person"
shutil.rmtree(output_dir, ignore_errors=True)
os.makedirs(output_dir, exist_ok=True)

disabilities = [
    "mobility-impairment",
    "invisible-disability",
    "intellectual-disability",
    "hearing-impairment",
    "visual-impairment"
]

# --- データ生成 ---
for i in range(1, num_files + 1):
    age = random.randint(0, 100)
    loc = random.randint(0, 300)

    # 確率で disability の数を決める (70%で0個, 残り30%で1〜2個)
    r = random.random()
    if r < 0.7:
        k = 0
    else:
        k = random.randint(1, 2)

    selected_disabilities = random.sample(disabilities, k)

    record = {
        "dataType": "personal",
        "id": i,
        "age": age,
        "loc": loc,
        "disability": selected_disabilities
    }

    filename = os.path.join(output_dir, f"personal-{i:03}.json")
    with open(filename, "w") as f:
        json.dump(record, f, indent=4)

print(f"✅ {num_files} JSON files have been generated in the '{output_dir}' directory.")
