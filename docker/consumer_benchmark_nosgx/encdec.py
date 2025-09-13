#!/usr/bin/env python3
"""
run_encrypt_aesgcm_dir.py

Encrypt or decrypt files in a directory using AES-GCM (JSON format only).

JSON ciphertext format (UTF-8, Base64 fields):
{
  "iv": "BASE64...",
  "ciphertext": "BASE64...",
  "tag": "BASE64...",
  "aad": "BASE64..."   # optional (present only if provided at encryption)
}

Public API (import to use in other scripts):
- generate_key(size_bytes=32) -> bytes
- save_key_file(path, key, hex_mode=True) -> None
- load_key_file(key_file, hex_mode=True) -> bytes
- encrypt_file_to_json_file(in_path, out_path, key, aad: bytes|None = None) -> None
- encrypt_dir(in_dir, out_dir, key, aad: bytes|None = None, ext='enc.json', include_hidden=False, overwrite=False) -> dict
- decrypt_json_file(enc_file, key, aad_override: bytes|None = None) -> bytes
- decrypt_json_file_to_json(enc_file, key, aad_override: bytes|None = None) -> Any
- decrypt_dir(in_dir, out_dir, key, aad_override: bytes|None = None, ext='enc.json', include_hidden=False, overwrite=False) -> dict

CLI:
  # Encrypt directory -> JSON ciphertexts (mirror structure)
  python run_encrypt_aesgcm_dir.py --mode encrypt \
      --in-dir ./plain_dir --out-dir ./enc_dir \
      --gen-key-file ./secret.key                # default: HEX save
      # or: --key-file ./secret.key              # default: HEX load
      --ext enc.json \
      [--gen-key-raw] [--key-raw]                # raw bytes save/load if specified
      [--aad 'dataset=v1'] [--include-hidden] [--overwrite]

  # Decrypt directory of JSON ciphertexts -> plaintexts
  python run_encrypt_aesgcm_dir.py --mode decrypt \
      --in-dir ./enc_dir --out-dir ./plain_out \
      --key-file ./secret.key                    # default: HEX load
      --ext enc.json \
      [--key-raw] [--aad 'dataset=v1'] [--include-hidden] [--overwrite]

Notes:
  * Requires: pip install cryptography
  * Keys: 16/24/32 bytes (AES-128/192/256).
  * Default behavior: generate/save **HEX**; load keys as **HEX** unless --key-raw is given.
"""

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Optional, Tuple, Union, Dict

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as e:
    print("[ERROR] 'cryptography' is required. Install with: pip install cryptography", file=sys.stderr)
    raise

import secrets

PathLike = Union[str, Path]


# ---------- Helpers (public) ----------

def generate_key(size_bytes: int = 32) -> bytes:
    """Generate a random AES key (16/24/32 bytes)."""
    if size_bytes not in (16, 24, 32):
        raise ValueError("Key size must be one of 16, 24, 32 bytes.")
    return secrets.token_bytes(size_bytes)


def save_key_file(path: PathLike, key: bytes, hex_mode: bool = True) -> None:
    """Save AES key to file (HEX text by default; raw bytes when hex_mode=False)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if hex_mode:
        p.write_text(key.hex() + "\n", encoding="utf-8")
    else:
        p.write_bytes(key)


def load_key_file(key_file: PathLike, hex_mode: bool = True) -> bytes:
    """
    Load AES key bytes from file.
    - When hex_mode=True (default): interpret file as HEX text (whitespace stripped).
    - When hex_mode=False: read raw bytes.
    """
    p = Path(key_file)
    data = p.read_bytes()
    if hex_mode:
        return bytes.fromhex(data.decode("utf-8").strip())
    return data


def encrypt_file_to_json_file(in_path: PathLike, out_path: PathLike, key: bytes, aad: Optional[bytes] = None) -> None:
    """Encrypt a single file and write JSON ciphertext."""
    in_p = Path(in_path)
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    pt = in_p.read_bytes()
    iv, ct, tag = _encrypt_bytes(key, pt, aad)
    _write_json_cipher(out_p, iv, ct, tag, aad)


def encrypt_dir(in_dir: PathLike, out_dir: PathLike, key: bytes, aad: Optional[bytes] = None,
                ext: str = "enc.json", include_hidden: bool = False, overwrite: bool = False) -> Dict[str, int]:
    """Encrypt all files under in_dir into out_dir, appending .{ext} to filenames. Returns counters."""
    in_root = Path(in_dir).resolve()
    out_root = Path(out_dir).resolve()
    counters = {"ok": 0, "skipped": 0, "failed": 0}

    for p in in_root.rglob("*"):
        if p.is_dir():
            continue
        if not include_hidden and any(part.startswith(".") for part in p.relative_to(in_root).parts):
            counters["skipped"] += 1
            continue

        rel = p.relative_to(in_root)
        out_p = (out_root / rel).with_suffix((out_root / rel).suffix + f".{ext}")

        if out_p.exists() and not overwrite:
            print(f"[SKIP] Exists: {out_p}")
            counters["skipped"] += 1
            continue

        try:
            encrypt_file_to_json_file(p, out_p, key, aad=aad)
            print(f"[OK] {p} -> {out_p}")
            counters["ok"] += 1
        except Exception as e:
            print(f"[ERROR] Encrypt {p} failed: {e}", file=sys.stderr)
            counters["failed"] += 1

    return counters


def decrypt_json_file(enc_file: PathLike, key: bytes, aad_override: Optional[bytes] = None) -> bytes:
    """Decrypt a JSON ciphertext file (bytes payload)."""
    obj = json.loads(Path(enc_file).read_text(encoding="utf-8"))
    return _decrypt_json_obj(obj, key, aad_override=aad_override)


def decrypt_json_file_to_json(enc_file: PathLike, key: bytes, aad_override: Optional[bytes] = None) -> Any:
    """Decrypt a JSON ciphertext file and parse plaintext as JSON."""
    pt = decrypt_json_file(enc_file, key, aad_override=aad_override)
    return json.loads(pt.decode("utf-8"))


def decrypt_dir(in_dir: PathLike, out_dir: PathLike, key: bytes, aad_override: Optional[bytes] = None,
                ext: str = "enc.json", include_hidden: bool = False, overwrite: bool = False) -> Dict[str, int]:
    """
    Decrypt all *.{ext} files under in_dir into out_dir, removing the trailing .{ext}.
    If filename does not end with .{ext}, falls back to appending '.dec' to name.
    Returns counters.
    """
    in_root = Path(in_dir).resolve()
    out_root = Path(out_dir).resolve()
    counters = {"ok": 0, "skipped": 0, "failed": 0}

    for p in in_root.rglob("*"):
        if p.is_dir():
            continue
        if not include_hidden and any(part.startswith(".") for part in p.relative_to(in_root).parts):
            counters["skipped"] += 1
            continue

        rel = p.relative_to(in_root)
        out_rel = _strip_suffix_once(rel, f".{ext}") if str(rel).endswith(f".{ext}") else rel.with_suffix(rel.suffix + ".dec")
        out_p = out_root / out_rel

        if out_p.exists() and not overwrite:
            print(f"[SKIP] Exists: {out_p}")
            counters["skipped"] += 1
            continue

        try:
            pt = decrypt_json_file(p, key, aad_override=aad_override)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_bytes(pt)
            print(f"[OK] {p} -> {out_p}")
            counters["ok"] += 1
        except Exception as e:
            print(f"[ERROR] Decrypt {p} failed: {e}", file=sys.stderr)
            counters["failed"] += 1

    return counters


# ---------- Internal helpers ----------

def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s)


def _encrypt_bytes(key: bytes, data: bytes, aad: Optional[bytes]) -> Tuple[bytes, bytes, bytes]:
    iv = secrets.token_bytes(12)  # 96-bit IV
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(iv, data, aad)  # returns ciphertext||tag
    tag = ct_with_tag[-16:]
    ct = ct_with_tag[:-16]
    return iv, ct, tag


def _write_json_cipher(out_path: Path, iv: bytes, ct: bytes, tag: bytes, aad: Optional[bytes]) -> None:
    obj = {
        "iv": _b64e(iv),
        "ciphertext": _b64e(ct),
        "tag": _b64e(tag),
    }
    if aad is not None:
        obj["aad"] = _b64e(aad)
    out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _decrypt_json_obj(obj: dict, key: bytes, aad_override: Optional[bytes]) -> bytes:
    try:
        iv = _b64d(obj["iv"])
        ct = _b64d(obj["ciphertext"])
        tag = _b64d(obj["tag"])
    except KeyError as e:
        raise ValueError(f"Missing field in JSON ciphertext: {e}") from e

    aad = aad_override
    if aad is None and "aad" in obj and obj["aad"] is not None:
        aad = _b64d(obj["aad"])

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ct + tag, aad)


def _strip_suffix_once(rel_path: Path, suffix: str) -> Path:
    """Remove one occurrence of suffix from a relative path's name (rightmost)."""
    s = str(rel_path)
    if s.endswith(suffix):
        s = s[: -len(suffix)]
    return Path(s)


# ---------- CLI ----------

def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="AES-GCM encrypt/decrypt an entire directory (JSON format).")
    ap.add_argument("mode", help="Operation mode.")

    ap.add_argument("--in-dir", required=True, help="Input directory.")
    ap.add_argument("--out-dir", required=True, help="Output directory.")
    # Key input / generation
    ap.add_argument("--key-file", help="AES key file (HEX by default).")
    ap.add_argument("--key-raw", action="store_true", help="Interpret key file as raw bytes instead of HEX.")
    ap.add_argument("--gen-key-file", help="Generate a new AES key and save to this path (encrypt mode only).")
    ap.add_argument("--gen-key-size", type=int, choices=[16, 24, 32], default=16,
                    help="Generated key size in bytes (16/24/32). Default: 16 (AES-128).")
    ap.add_argument("--gen-key-raw", action="store_true",
                    help="When generating a key, save as raw bytes instead of HEX (default is HEX).")
    # AAD / filenames
    ap.add_argument("--aad", help="Optional AAD string. Encrypt: embedded. Decrypt: override.")
    ap.add_argument("--ext", default="enc.json", help="Encryption output extension to append / decryption suffix to strip (default: enc.json).")
    ap.add_argument("--include-hidden", action="store_true", help="Process dotfiles (.gitignore etc.).")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    return ap.parse_args()


def main():
    args = _parse_args()

    # --- Key handling ---
    key: Optional[bytes] = None

    if args.mode == "encrypt":
        if args.gen_key_file:
            # Generate a new key and save it; use it for this run.
            key = generate_key(args.gen_key_size)
            # Default is HEX save, unless --gen-key-raw is given
            save_key_file(args.gen_key_file, key, hex_mode=not args.gen_key_raw)
            mode_str = "raw bytes" if args.gen_key_raw else "HEX"
            print(f"[INFO] Generated new key ({len(key)} bytes, saved as {mode_str}) -> {args.gen_key_file}")
            if args.key_file and Path(args.key_file).resolve() != Path(args.gen_key_file).resolve():
                print("[WARN] --key-file is ignored because --gen-key-file is provided.", file=sys.stderr)
        elif args.key_file:
            key = load_key_file(args.key_file, hex_mode=not args.key_raw)
        else:
            print("[ERROR] In encrypt mode, specify either --gen-key-file to generate a key or --key-file to load one.", file=sys.stderr)
            sys.exit(2)
    else:
        # decrypt mode requires a key file (cannot generate)
        if not args.key_file:
            print("[ERROR] In decrypt mode, --key-file is required.", file=sys.stderr)
            sys.exit(2)
        key = load_key_file(args.key_file, hex_mode=not args.key_raw)

    if key is None:
        print("[ERROR] Failed to obtain AES key.", file=sys.stderr)
        sys.exit(2)
    if len(key) not in (16, 24, 32):
        print(f"[WARN] Key length is {len(key)} bytes; AES keys are typically 16/24/32 bytes.", file=sys.stderr)

    aad_bytes = args.aad.encode("utf-8") if args.aad else None

    if args.mode == "encrypt":
        counters = encrypt_dir(args.in_dir, args.out_dir, key, aad=aad_bytes,
                               ext=args.ext, include_hidden=args.include_hidden, overwrite=args.overwrite)
        print(f"\nEncrypt done. ok={counters['ok']}, skipped={counters['skipped']}, failed={counters['failed']}")
    else:
        counters = decrypt_dir(args.in_dir, args.out_dir, key, aad_override=aad_bytes,
                               ext=args.ext, include_hidden=args.include_hidden, overwrite=args.overwrite)
        print(f"\nDecrypt done. ok={counters['ok']}, skipped={counters['skipped']}, failed={counters['failed']}")


if __name__ == "__main__":
    main()
