#!/usr/bin/env python3
"""
Convert all .woff2 fonts in a source directory into installable TTF/OTF files.

Usage:
  python scripts/convert_woff2_to_ttf.py --src fonts --out dist/fonts-installable

Notes:
  - This does NOT create variable fonts. It only rewraps static WOFF2 to sfnt (TTF/OTF).
  - Ensure your font license permits desktop installation and format conversion.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

from fontTools.ttLib import TTFont


def determine_output_extension(font: TTFont) -> str:
    """Return ".otf" if CFF/CFF2 outlines present; otherwise ".ttf"."""
    if "CFF " in font or "CFF2" in font:
        return ".otf"
    return ".ttf"


def convert_single_file(src_path: Path, out_dir: Path, overwrite: bool) -> Tuple[bool, str, Path]:
    """Convert one .woff2 file to TTF/OTF.

    Returns (success, message, output_path).
    """
    try:
        # Load WOFF2; requires brotli to be installed
        font = TTFont(str(src_path))
        # Ensure we save as an unflavored sfnt (TTF/OTF)
        font.flavor = None
        ext = determine_output_extension(font)

        out_filename = src_path.stem + ext
        out_path = out_dir / out_filename

        if out_path.exists() and not overwrite:
            return (
                False,
                f"Skip (exists): {out_path}",
                out_path,
            )

        out_dir.mkdir(parents=True, exist_ok=True)
        font.save(str(out_path))
        return True, f"Converted: {src_path.name} -> {out_filename}", out_path
    except Exception as exc:  # noqa: BLE001
        return False, f"Error: {src_path.name} ({exc})", out_dir / (src_path.stem + ".ttf")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert WOFF2 fonts to installable TTF/OTF")
    parser.add_argument("--src", default="fonts", help="Source directory containing .woff2 files (default: fonts)")
    parser.add_argument("--out", default="dist/fonts-installable", help="Output directory for TTF/OTF (default: dist/fonts-installable)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--dry-run", action="store_true", help="List planned conversions without writing files")

    args = parser.parse_args(argv)

    src_dir = Path(args.src)
    out_dir = Path(args.out)

    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Source directory not found: {src_dir}")
        return 1

    woff2_files = sorted(src_dir.glob("*.woff2"))
    if not woff2_files:
        print(f"No .woff2 files found in: {src_dir}")
        return 1

    print(f"Found {len(woff2_files)} .woff2 file(s) in {src_dir}")
    print(f"Output directory: {out_dir}")

    if args.dry_run:
        for path in woff2_files:
            try:
                font = TTFont(str(path))
                font.flavor = None
                ext = determine_output_extension(font)
                print(f"Would convert: {path.name} -> {path.stem + ext}")
            except Exception as exc:  # noqa: BLE001
                print(f"Would fail: {path.name} ({exc})")
        return 0

    success_count = 0
    fail_count = 0
    for path in woff2_files:
        ok, message, _ = convert_single_file(path, out_dir, args.overwrite)
        print(message)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    print("")
    print(f"Done. Success: {success_count}, Failed/Skipped: {fail_count}")
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


