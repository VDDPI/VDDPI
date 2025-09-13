#!/usr/bin/env python3
"""
run_batch_process_encrypted.py

Read AES-GCM-encrypted JSON files one by one, decrypt, and call main.process_data(person_1).

Requirements:
- Encryption/decryption format matches encdec.py (JSON with base64 iv/ciphertext/tag[/aad]).
- main.py defines: process_data(person_1)

Usage:
  python run_batch_process_encrypted.py \
    <lib_path> <module_name> \
    <input_dir> \
    <key_file> \
    <log_file> \
    --main-path /path/to/dir/with/main.py \
    [--silent]

Arguments:
- lib_path: directory containing a python file to import process_data
- module_name: module name to import process_data
- input_dir: directory with encrypted JSON files (recursively searched)
- key_file: AES key file (HEX text by default)
- log_file: log file to write output
"""

import argparse
import importlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Optional

def setup_logger(module_name: str, log_file: Optional[str] = None, level: str = "INFO"):
    """
    ロガーをセットアップする
    - log_file: 指定すればファイルにも出力
    - level: "DEBUG", "INFO", "WARNING", "ERROR"
    """
    logger = logging.getLogger(module_name)
    if logger.handlers:
        return logger  # 二重登録防止

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # コンソール出力
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # ファイル出力
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(numeric_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def check_condition_phase(condition):
    is_valid_date = check_expiration_date(condition)
    is_valid_location = check_location(condition)
    return is_valid_date, is_valid_location

def check_expiration_date(condition):
    API_CA_CERT = """-----BEGIN CERTIFICATE-----
MIIDSzCCAjMCFDd4rPNHr1Devfmp0NLzGcr+6ggnMA0GCSqGSIb3DQEBCwUAMGIx
CzAJBgNVBAYTAkpQMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRl
cm5ldCBXaWRnaXRzIFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNv
bTAeFw0yNDA5MjcxMDE0MjBaFw0zNDA5MjUxMDE0MjBaMGIxCzAJBgNVBAYTAkpQ
MRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRz
IFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNvbTCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAM4/mSYFhpuHrREzpC64/RbICurPBeWsl7/T
2w21hXtS5z0FjD+sLaPAgr3C1mZkuh5GO/WzqIz9SNa9xMVMEMg+k7K6wIozgZzp
YPQVNBky1TvXQpm20rH+l0vms17ULXbuX26hqQJADARrUOSXdF+wsa8/CHHWqtWa
e06eoN79pqLZmTlRttCUBBMyWYXgEZy1iJczOgsi6u5iLlWj4zvmzUKcQev8BZV1
WC1DhmUgksfclgXLaVemyn35WRgUwsULMR5lB/URPcAjLRIf3n4eHie8mmMKLEez
9eOtvJImuwIWGNyT5cPv+jo9fY6y9lBt+Y6gXStFA5MPjAflIUkCAwEAATANBgkq
hkiG9w0BAQsFAAOCAQEArV2X1bcTzSFY3AtdtkDuUeJGwWlV6lfzyMm9lzS3WJJ3
rDOvQ8Q+G1ilJr4TC+xMIPcHS/XsUxmqPDlguPx9GaWxL/6MNczFsXhTllwBorZF
RHBhv8uT6LgV03xVq/XM+t4RT8SlTYmfz8xjKshFR4jdqz2QFJ6GrH2Xdny0hN3V
nwC3fcDP9wwIKMS5Jl8q9b0y7+uzjtB5qe3kW6cFNlJqDyP0cofH0cqGiRBDBZZC
RpW24O8MGN5wyHW/5P+FZ3UcQ78wS+s4girINinciiIqPayAWJsSLgfOKW8ogZ8P
krEL2VWGrv3IkBKvGUaSVu4rbwxqealC6vid1yi0TA==
-----END CERTIFICATE-----
"""
    CERT_PATH = "./certs/api_ca_cert.pem"
    TRUSTED_TIME_API_URL = "http://registry01.vddpi:8005/time"
    expiration_date_cond = condition["expirationDate"]
    if (expiration_date_cond == ""):
        return True
    with open(CERT_PATH, "w") as f:
        f.write(API_CA_CERT)
    res_time = json.loads(requests.get(TRUSTED_TIME_API_URL, verify=CERT_PATH).text)["datetime"]
    os.remove(CERT_PATH)
    now = datetime.strptime(res_time[:19], "%Y-%m-%dT%H:%M:%S")
    datetime_expiration_date_cond = datetime.strptime(expiration_date_cond, "%Y-%m-%d")
    if (now <= datetime_expiration_date_cond):
        return True
    else:
        return False

def check_location(condition):
    API_CA_CERT = """-----BEGIN CERTIFICATE-----
MIIDSzCCAjMCFDd4rPNHr1Devfmp0NLzGcr+6ggnMA0GCSqGSIb3DQEBCwUAMGIx
CzAJBgNVBAYTAkpQMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRl
cm5ldCBXaWRnaXRzIFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNv
bTAeFw0yNDA5MjcxMDE0MjBaFw0zNDA5MjUxMDE0MjBaMGIxCzAJBgNVBAYTAkpQ
MRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRz
IFB0eSBMdGQxGzAZBgNVBAMMEnJvb3RjYS5leGFtcGxlLmNvbTCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAM4/mSYFhpuHrREzpC64/RbICurPBeWsl7/T
2w21hXtS5z0FjD+sLaPAgr3C1mZkuh5GO/WzqIz9SNa9xMVMEMg+k7K6wIozgZzp
YPQVNBky1TvXQpm20rH+l0vms17ULXbuX26hqQJADARrUOSXdF+wsa8/CHHWqtWa
e06eoN79pqLZmTlRttCUBBMyWYXgEZy1iJczOgsi6u5iLlWj4zvmzUKcQev8BZV1
WC1DhmUgksfclgXLaVemyn35WRgUwsULMR5lB/URPcAjLRIf3n4eHie8mmMKLEez
9eOtvJImuwIWGNyT5cPv+jo9fY6y9lBt+Y6gXStFA5MPjAflIUkCAwEAATANBgkq
hkiG9w0BAQsFAAOCAQEArV2X1bcTzSFY3AtdtkDuUeJGwWlV6lfzyMm9lzS3WJJ3
rDOvQ8Q+G1ilJr4TC+xMIPcHS/XsUxmqPDlguPx9GaWxL/6MNczFsXhTllwBorZF
RHBhv8uT6LgV03xVq/XM+t4RT8SlTYmfz8xjKshFR4jdqz2QFJ6GrH2Xdny0hN3V
nwC3fcDP9wwIKMS5Jl8q9b0y7+uzjtB5qe3kW6cFNlJqDyP0cofH0cqGiRBDBZZC
RpW24O8MGN5wyHW/5P+FZ3UcQ78wS+s4girINinciiIqPayAWJsSLgfOKW8ogZ8P
krEL2VWGrv3IkBKvGUaSVu4rbwxqealC6vid1yi0TA==
-----END CERTIFICATE-----
"""
    CERT_PATH = "./certs/api_ca_cert.pem"
    TRUSTED_GEOLOCATION_API_URL = "http://registry01.vddpi:8005/location"
    location_cond = condition["location"]
    if (location_cond == ""):
        return True
    with open(CERT_PATH, "w") as f:
        f.write(API_CA_CERT)
    loc_info = json.loads(requests.post(TRUSTED_GEOLOCATION_API_URL, verify=CERT_PATH, json={"address": "dummy_ipAddr"}).text)
    os.remove(CERT_PATH)
    if (loc_info["countryCode"] == location_cond):
        return True
    else:
        return False

def import_process_data(lib_path: Path, module_name: str):
    """
    lib_path    : モジュールを探すディレクトリ (例: /root/lib)
    module_name : インポートするモジュール名 (拡張子なし、例: code_eval_01_main)

    戻り値:
        指定モジュール内の process_data 関数
    """
    lib_path = Path(lib_path)
    if not lib_path.exists() or not lib_path.is_dir():
        raise ImportError(f"lib_path not found or not a directory: {lib_path}")

    # sys.path に追加（重複は避ける）
    lib_str = str(lib_path.resolve())
    if lib_str not in sys.path:
        sys.path.insert(0, lib_str)

    try:
        mod: ModuleType = importlib.import_module(module_name)
    except Exception as e:
        raise ImportError(f"Cannot import module '{module_name}' from '{lib_path}': {e}")

    if not hasattr(mod, "process_data"):
        raise AttributeError(f"Module '{module_name}' has no attribute 'process_data'")

    return getattr(mod, "process_data")

def main():
    ap = argparse.ArgumentParser(description="Batch decrypt and run main.process_data over encrypted files.")
    ap.add_argument("lib_path", help="Directory containing the module to import process_data from.")
    ap.add_argument("module_name", help="Module name to import process_data from.")
    ap.add_argument("input_dir", help="Directory containing encrypted JSON files.")
    ap.add_argument("key_file", help="AES key file (HEX by default).")
    ap.add_argument("log_file", help="Log file to write output.")
    ap.add_argument("--silent", action="store_true", help="Print process_data() results to stdout.")
    args = ap.parse_args()

    logger = setup_logger("eval_01", args.log_file, level="INFO")

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"[ERROR] Not found or not a directory: {input_dir}")

    lib_path = Path(args.lib_path).resolve()
    if not (lib_path / f"{args.module_name}.py").exists():
        raise SystemExit(f"[ERROR] {args.module_name}.py not found in: {lib_path}")

    # import decrypt helpers from encdec.py
    try:
        from encdec import load_key_file, decrypt_json_file_to_json
    except Exception as e:
        raise SystemExit("[ERROR] Could not import from encdec.py. Ensure it's on PYTHONPATH or alongside this script. " + str(e))

    # import process_data
    process_data = import_process_data(lib_path, args.module_name)

    total = 0
    ok = 0
    fail = 0

    target_suffix = ".enc.json"

    for p in input_dir.rglob("*"):
        start = datetime.now()
        if p.is_dir():
            continue
        if not str(p).endswith(target_suffix):
            continue
        total += 1
        try:
            # For fairness, the key is loaded each time.
            key = load_key_file(args.key_file)
            if len(key) not in (16, 24, 32):
                logger.warning(f"Key length is {len(key)} bytes; AES typically uses 16/24/32.")

            # Decrypt and parse JSON -> person_1 dict
            person_1 = decrypt_json_file_to_json(p, key)

            # 現在日時から30日後を計算し、YYYY-MM-DD形式の文字列として辞書に保存
            condition["expirationDate"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            # 辞書に「ロケーション」を追加
            condition["location"] = "JP"
            # check condition
            is_valid_date, is_valid_location = check_condition_phase(condition)
            if is_valid_date == False or is_valid_location:
                return False
            # Run
            result = process_data(person_1)
            logger.info(f"{p}")
            if not args.silent:
                try:
                    logger.info(json.dumps({"file": str(p), "result": result}, ensure_ascii=False, indent=2))
                except Exception:
                    logger.info(f"result({p}): {result}")
            ok += 1
        except Exception as e:
            logger.error(f"{p}: {e}")
            fail += 1
        end = datetime.now()
        elapsed_ms = (end - start).total_seconds() * 1000
        logger.info(f"___BENCH___ Data processing without SGX (Start:{start.strftime('%Y-%m-%d %H:%M:%S.%f')}, End:{end.strftime('%Y-%m-%d %H:%M:%S.%f')}, Duration_ms:{elapsed_ms:.3f})")

    logger.info(f"\nDone. files={total}, ok={ok}, failed={fail}")
    return True

if __name__ == "__main__":
    status = main()
    if status == False:
        sys.exit(1)
    sys.exit(0)
