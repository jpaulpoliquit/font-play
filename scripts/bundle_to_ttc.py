#!/usr/bin/env python3
"""
Bundle multiple TTF/OTF fonts into a single OpenType Collection (.ttc).

Note: Some environments and tools may not support mixing CFF (.otf) and TrueType (.ttf)
in a single collection. By default, this tool bundles only TTFs. Use --include-otf to
attempt to include OTFs as well.

Usage:
  python scripts/bundle_to_ttc.py \
    --src dist/CursorGothic --out dist/CursorGothic/CursorGothic.ttc [--include-otf]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        pass


def load_fonts(paths: List[Path]) -> list[TTFont]:
    fonts: list[TTFont] = []
    for p in paths:
        fonts.append(TTFont(str(p)))
    return fonts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bundle fonts into a TTC")
    parser.add_argument("--src", default="dist/CursorGothic", help="Directory containing .ttf/.otf to bundle")
    parser.add_argument("--out", default="dist/CursorGothic/CursorGothic.ttc", help="Output .ttc path")
    parser.add_argument("--include-otf", action="store_true", help="Attempt to include .otf (CFF) faces as well")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .ttc")

    args = parser.parse_args(argv)
    src_dir = Path(args.src)
    out_path = Path(args.out)

    if not src_dir.exists() or not src_dir.is_dir():
        safe_print(f"Source directory not found: {src_dir}")
        return 1

    ttf_paths = sorted(src_dir.glob("*.ttf"))
    otf_paths = sorted(src_dir.glob("*.otf")) if args.include_otf else []

    if not ttf_paths and not otf_paths:
        safe_print(f"No fonts found in: {src_dir}")
        return 1

    candidates = [*ttf_paths, *otf_paths]
    safe_print(f"Bundling {len(candidates)} font(s) into: {out_path}")

    if out_path.exists() and not args.overwrite:
        safe_print(f"Output exists, use --overwrite to replace: {out_path}")
        return 1

    fonts = load_fonts(candidates)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Create a new empty collection and assign fonts
    tc = TTCollection()
    tc.fonts = fonts
    tc.save(str(out_path))
    safe_print("Wrote TTC:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


