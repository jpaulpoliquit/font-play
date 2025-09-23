#!/usr/bin/env python3
"""
Normalize font name tables and filenames to a target family name.

Example:
  python scripts/normalize_font_names.py \
    --src dist/fonts-installable --out dist/CursorGothic --family "Cursor Gothic"

Notes:
  - Works on static TTF/OTF fonts.
  - Updates name IDs: 1, 2, 3, 4, 6 and, if present, 16 and 17.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

from fontTools.ttLib import TTFont


WINDOWS_PLATFORM_ID = 3
WINDOWS_ENC_ID = 1
WINDOWS_LANG_ID = 0x0409  # en-US

MAC_PLATFORM_ID = 1
MAC_ENC_ID = 0
MAC_LANG_ID = 0  # English


def is_italic(font: TTFont) -> bool:
    try:
        # Prefer OS/2 fsSelection bit 0
        fs_sel: int = font["OS/2"].fsSelection
        if fs_sel & 0x01:  # ITALIC
            return True
    except Exception:
        pass
    try:
        # Fallback to head.macStyle bit 1
        mac_style: int = font["head"].macStyle
        if mac_style & 0x02:
            return True
    except Exception:
        pass
    return False


def is_bold(font: TTFont) -> bool:
    try:
        fs_sel: int = font["OS/2"].fsSelection
        if fs_sel & 0x20:  # BOLD
            return True
    except Exception:
        pass
    try:
        # Weight class >= 700 is commonly considered bold
        if getattr(font["OS/2"], "usWeightClass", 400) >= 700:
            return True
    except Exception:
        pass
    return False


def weight_to_name(weight: int) -> str:
    # Map numeric weight to style name
    bins = [
        (100, "Thin"),
        (200, "ExtraLight"),
        (300, "Light"),
        (400, "Regular"),
        (500, "Medium"),
        (600, "SemiBold"),
        (700, "Bold"),
        (800, "ExtraBold"),
        (900, "Black"),
    ]
    if weight <= 100:
        return "Thin"
    if weight >= 900:
        return "Black"
    # Find nearest bin
    closest = min(bins, key=lambda b: abs(b[0] - weight))
    return closest[1]


def derive_style_name(font: TTFont) -> Tuple[str, str]:
    """Return (style_name_human, style_name_ps).

    Example: ("Bold Italic", "BoldItalic")
    """
    try:
        weight = int(getattr(font["OS/2"], "usWeightClass", 400))
    except Exception:
        weight = 400
    italic = is_italic(font)

    # Regular exception: 400 non-italic => "Regular"
    weight_name = weight_to_name(weight)

    human = weight_name if weight_name != "Regular" or italic else "Regular"
    ps = weight_name.replace(" ", "") if weight_name != "Regular" or italic else "Regular"

    if italic:
        human = ("Regular Italic" if human == "Regular" else f"{human} Italic").strip()
        ps = ("Italic" if ps == "Regular" else f"{ps}Italic").strip()

    return human, ps


def set_name(font: TTFont, name_id: int, value: str) -> None:
    name_table = font["name"]
    # Set for Windows and Mac
    name_table.setName(value, name_id, WINDOWS_PLATFORM_ID, WINDOWS_ENC_ID, WINDOWS_LANG_ID)
    name_table.setName(value, name_id, MAC_PLATFORM_ID, MAC_ENC_ID, MAC_LANG_ID)


def determine_output_extension(font: TTFont) -> str:
    if "CFF " in font or "CFF2" in font:
        return ".otf"
    return ".ttf"


def normalize_one_font(src_path: Path, out_dir: Path, family_name: str, overwrite: bool, dry_run: bool, out_filename_override: Optional[str] = None) -> Tuple[bool, str, Optional[Path]]:
    try:
        font = TTFont(str(src_path))
        ext = determine_output_extension(font)

        # Family names
        family_typographic = family_name
        family_menu = family_name

        # Style names
        style_human, style_ps = derive_style_name(font)

        full_name = f"{family_menu} {style_human}".strip()
        ps_family = family_menu.replace(" ", "")
        postscript_name = f"{ps_family}-{style_ps}".replace(" ", "")

        # Update name IDs
        # 1: Font Family name (menu family)
        set_name(font, 1, family_menu)
        # 2: Subfamily (style)
        set_name(font, 2, style_human)
        # 4: Full font name
        set_name(font, 4, full_name)
        # 6: PostScript name
        set_name(font, 6, postscript_name)
        # 16/17: Typographic Family/Subfamily if present
        try:
            set_name(font, 16, family_typographic)
            set_name(font, 17, style_human)
        except Exception:
            pass
        # 3: Unique font identifier (simple, not guaranteed globally unique)
        set_name(font, 3, f"{postscript_name}")

        out_filename = out_filename_override or f"{ps_family}-{style_ps}{ext}"
        out_path = out_dir / out_filename

        if dry_run:
            return True, (
                f"Would write: {out_filename}\n"
                f"  Family: {family_menu}\n  Subfamily: {style_human}\n  Full: {full_name}\n  PS: {postscript_name}"
            ), out_path

        out_dir.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not overwrite:
            return False, f"Skip (exists): {out_path}", out_path

        font.save(str(out_path))
        return True, f"Wrote: {out_filename}", out_path
    except Exception as exc:  # noqa: BLE001
        return False, f"Error: {src_path.name} ({exc})", None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize font names to a target family")
    parser.add_argument("--src", default="dist/fonts-installable", help="Source directory of .ttf/.otf")
    parser.add_argument("--out", default="dist/CursorGothic", help="Output directory for renamed fonts")
    parser.add_argument("--family", default="Cursor Gothic", help="Target family name (menu & typographic)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")

    args = parser.parse_args(argv)
    src_dir = Path(args.src)
    out_dir = Path(args.out)

    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Source directory not found: {src_dir}")
        return 1

    candidates = [
        *sorted(src_dir.glob("*.ttf")),
        *sorted(src_dir.glob("*.otf")),
    ]
    if not candidates:
        print(f"No .ttf/.otf files found in: {src_dir}")
        return 1

    print(f"Found {len(candidates)} font(s) in {src_dir}")
    print(f"Output directory: {out_dir}")
    print(f"Target family: {args.family}")

    successes = 0
    failures = 0
    # Track planned filenames to avoid collisions
    used_filenames: dict[str, int] = {}
    for path in candidates:
        # Precompute intended filename to ensure uniqueness
        font = TTFont(str(path))
        ext = determine_output_extension(font)
        style_human, style_ps = derive_style_name(font)
        ps_family = args.family.replace(" ", "")
        base_filename = f"{ps_family}-{style_ps}{ext}"
        # De-duplicate filenames by appending incremental suffixes
        if base_filename not in used_filenames:
            used_filenames[base_filename] = 1
            out_filename = base_filename
        else:
            used_filenames[base_filename] += 1
            out_filename = f"{ps_family}-{style_ps}-{used_filenames[base_filename]}{ext}"

        # Reopen within normalize call to ensure fresh object state
        ok, msg, _ = normalize_one_font(path, out_dir, args.family, args.overwrite, args.dry_run, out_filename_override=out_filename)
        print(msg)
        if ok:
            successes += 1
        else:
            failures += 1

    print("")
    print(f"Done. Success: {successes}, Failed/Skipped: {failures}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


