#!/usr/bin/env python3
"""
Convert all .woff2 fonts in a source directory into installable TTF/OTF files.

Usage:
  python scripts/convert_woff2_to_ttf.py --src fonts --out dist/fonts-installable

Notes:
  - This does NOT create variable fonts. It only rewraps static WOFF2 to sfnt (TTF/OTF).
  - Ensure your font license permits desktop installation and format conversion.
  - Enhanced to use proper font names based on metadata and detect all style variations.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple, Dict, List

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection


def determine_output_extension(font: TTFont) -> str:
    """Return ".otf" if CFF/CFF2 outlines present; otherwise ".ttf"."""
    if "CFF " in font or "CFF2" in font:
        return ".otf"
    return ".ttf"


def extract_font_metadata(font: TTFont) -> Dict[str, str]:
    """Extract comprehensive font metadata for proper naming."""
    metadata = {
        'family': '',
        'subfamily': '',
        'full_name': '',
        'postscript_name': '',
        'weight': 'Regular',
        'style': 'Regular',
        'features': []
    }
    
    # Extract name table information
    if 'name' in font:
        name_table = font['name']
        for record in name_table.names:
            try:
                text = record.toUnicode()
                if record.nameID == 1:  # Font Family name
                    metadata['family'] = text
                elif record.nameID == 2:  # Font Subfamily name
                    metadata['subfamily'] = text
                elif record.nameID == 4:  # Full font name
                    metadata['full_name'] = text
                elif record.nameID == 6:  # PostScript name
                    metadata['postscript_name'] = text
            except UnicodeDecodeError:
                continue
    
    # Extract weight and style from OS/2 table
    if 'OS/2' in font:
        os2 = font['OS/2']
        weight_class = os2.usWeightClass
        
        # Weight mapping
        weight_names = {
            100: "Thin", 200: "ExtraLight", 250: "UltraLight", 300: "Light",
            350: "SemiLight", 400: "Regular", 500: "Medium", 600: "SemiBold",
            700: "Bold", 800: "ExtraBold", 900: "Black", 950: "ExtraBlack"
        }
        
        # Find closest weight name
        for w in sorted(weight_names.keys()):
            if weight_class <= w:
                metadata['weight'] = weight_names[w]
                break
        else:
            metadata['weight'] = f"W{weight_class}"
        
        # Style flags from OS/2
        selection = os2.fsSelection
        style_parts = []
        
        if selection & 0x01:  # Italic
            style_parts.append("Italic")
        if selection & 0x20:  # Bold (but prefer weight class)
            if metadata['weight'] == 'Regular':
                metadata['weight'] = 'Bold'
        if selection & 0x08:  # Outlined
            style_parts.append("Outlined")
        
        # Combine subfamily and detected styles
        if metadata['subfamily'] and metadata['subfamily'] != 'Regular':
            # Clean up subfamily to extract meaningful style info
            subfamily = metadata['subfamily']
            if 'italic' in subfamily.lower() and 'Italic' not in style_parts:
                style_parts.append("Italic")
            if 'oblique' in subfamily.lower() and 'Oblique' not in style_parts:
                style_parts.append("Oblique")
        
        metadata['style'] = ' '.join(style_parts) if style_parts else 'Regular'
    
    # Extract OpenType features for ligature detection
    features = set()
    if 'GSUB' in font:
        gsub = font['GSUB']
        if hasattr(gsub.table, 'FeatureList') and gsub.table.FeatureList:
            for feature_record in gsub.table.FeatureList.FeatureRecord:
                features.add(feature_record.FeatureTag)
    
    if 'GPOS' in font:
        gpos = font['GPOS']
        if hasattr(gpos.table, 'FeatureList') and gpos.table.FeatureList:
            for feature_record in gpos.table.FeatureList.FeatureRecord:
                features.add(feature_record.FeatureTag)
    
    metadata['features'] = list(features)
    
    return metadata


def generate_output_filename(metadata: Dict[str, str], extension: str, force_family: str = None) -> str:
    """Generate a proper filename based on font metadata."""
    family = force_family or metadata['family'] or 'Unknown'
    
    # Clean family name
    family = re.sub(r'[^\w\s-]', '', family)
    family = re.sub(r'\s+', '', family)  # Remove spaces
    
    # Build style suffix
    style_parts = []
    
    # Add weight if not Regular
    if metadata['weight'] != 'Regular':
        style_parts.append(metadata['weight'])
    
    # Add style modifiers
    if metadata['style'] != 'Regular':
        style_parts.extend(metadata['style'].split())
    
    # Special handling for ligatures and features
    special_features = []
    if 'dlig' in metadata['features']:
        special_features.append('Ligatures')
    if any(f.startswith('ss') for f in metadata['features']):
        stylistic_sets = [f for f in metadata['features'] if f.startswith('ss')]
        if len(stylistic_sets) > 3:  # Many stylistic sets suggest special variant
            special_features.append('Stylistic')
    
    # Combine all parts
    filename_parts = [family]
    if style_parts:
        filename_parts.append('-'.join(style_parts))
    if special_features:
        filename_parts.append('+'.join(special_features))
    
    filename = '-'.join(filename_parts) + extension
    
    # Fallback to PostScript name if family name is too generic or missing
    if not force_family and (not family or family.lower() in ['unknown', 'regular', 'font']):
        ps_name = metadata['postscript_name']
        if ps_name:
            ps_name = re.sub(r'[^\w-]', '', ps_name)
            filename = ps_name + extension
    
    return filename


def rename_font_family(font: TTFont, new_family_name: str) -> None:
    """Rename the font family in the font's name table."""
    if 'name' not in font:
        return
    
    name_table = font['name']
    
    # Update relevant name records
    for record in name_table.names:
        try:
            if record.nameID == 1:  # Font Family name
                record.string = new_family_name.encode('utf-16be') if record.isUnicode() else new_family_name.encode('latin-1')
            elif record.nameID == 4:  # Full font name
                # Extract style from existing full name and combine with new family
                old_full = record.toUnicode()
                # Try to extract style portion (everything after the first space or dash)
                style_part = ""
                for sep in [' ', '-']:
                    if sep in old_full:
                        parts = old_full.split(sep, 1)
                        if len(parts) > 1:
                            style_part = parts[1]
                            break
                
                new_full = new_family_name
                if style_part:
                    new_full += f" {style_part}"
                
                record.string = new_full.encode('utf-16be') if record.isUnicode() else new_full.encode('latin-1')
            elif record.nameID == 6:  # PostScript name
                # Create PostScript name by removing spaces and adding style
                ps_base = new_family_name.replace(' ', '')
                old_ps = record.toUnicode()
                
                # Try to extract style suffix from old PostScript name
                style_suffix = ""
                if '-' in old_ps:
                    style_suffix = old_ps.split('-', 1)[1]
                
                new_ps = ps_base
                if style_suffix:
                    new_ps += f"-{style_suffix}"
                
                record.string = new_ps.encode('utf-16be') if record.isUnicode() else new_ps.encode('latin-1')
        except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
            continue


def convert_single_file(src_path: Path, out_dir: Path, overwrite: bool, use_metadata_names: bool = True, force_family: str = None) -> Tuple[bool, str, Path]:
    """Convert one .woff2 file to TTF/OTF.

    Returns (success, message, output_path).
    """
    try:
        # Load WOFF2; requires brotli to be installed
        font = TTFont(str(src_path))
        # Ensure we save as an unflavored sfnt (TTF/OTF)
        font.flavor = None
        ext = determine_output_extension(font)

        # Extract metadata first for potential family renaming
        metadata = extract_font_metadata(font)
        
        # Rename font family if requested
        if force_family:
            rename_font_family(font, force_family)
            # Update metadata to reflect the new family name
            metadata['family'] = force_family

        if use_metadata_names:
            # Generate proper filename using metadata
            out_filename = generate_output_filename(metadata, ext, force_family)
            
            # Fallback to original name if metadata extraction fails
            if not out_filename or out_filename == ext:
                out_filename = src_path.stem + ext
        else:
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
        
        # Enhanced reporting with metadata
        if use_metadata_names:
            metadata = extract_font_metadata(font)
            family = metadata.get('family', 'Unknown')
            style_info = f"{metadata.get('weight', 'Regular')} {metadata.get('style', 'Regular')}".strip()
            feature_count = len(metadata.get('features', []))
            
            message = f"Converted: {src_path.name} -> {out_filename}"
            message += f" | {family} {style_info}"
            if feature_count > 0:
                message += f" | {feature_count} OpenType features"
            
            return True, message, out_path
        else:
            return True, f"Converted: {src_path.name} -> {out_filename}", out_path
            
    except Exception as exc:  # noqa: BLE001
        return False, f"Error: {src_path.name} ({exc})", out_dir / (src_path.stem + ".ttf")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert WOFF2 fonts to installable TTF/OTF with enhanced style detection")
    parser.add_argument("--src", default="fonts", help="Source directory containing .woff2 files (default: fonts)")
    parser.add_argument("--out", default="dist/fonts-installable", help="Output directory for TTF/OTF (default: dist/fonts-installable)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--dry-run", action="store_true", help="List planned conversions without writing files")
    parser.add_argument("--use-hash-names", action="store_true", help="Use original hash-based filenames instead of metadata-based names")
    parser.add_argument("--organize-by-family", action="store_true", help="Organize output fonts into subdirectories by font family")
    parser.add_argument("--force-family", type=str, help="Rename all fonts to use this family name (e.g., 'Cursor Gothic')")
    parser.add_argument("--create-collection", action="store_true", help="Create a single TTC (TrueType Collection) file containing all fonts")

    args = parser.parse_args(argv)

    src_dir = Path(args.src)
    out_dir = Path(args.out)
    use_metadata_names = not args.use_hash_names

    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Source directory not found: {src_dir}")
        return 1

    woff2_files = sorted(src_dir.glob("*.woff2"))
    if not woff2_files:
        print(f"No .woff2 files found in: {src_dir}")
        return 1

    print(f"Found {len(woff2_files)} .woff2 file(s) in {src_dir}")
    print(f"Output directory: {out_dir}")
    print(f"Naming strategy: {'Metadata-based' if use_metadata_names else 'Hash-based'}")
    if args.force_family:
        print(f"Force family name: {args.force_family}")
    if args.organize_by_family:
        print("Organization: By font family")
    if args.create_collection:
        print("Will create font collection (TTC) file")

    if args.dry_run:
        print("\n=== DRY RUN - No files will be written ===")
        for path in woff2_files:
            try:
                font = TTFont(str(path))
                font.flavor = None
                ext = determine_output_extension(font)
                
                if use_metadata_names:
                    metadata = extract_font_metadata(font)
                    
                    # Apply force family if specified
                    display_family = args.force_family or metadata.get('family', 'Unknown')
                    if args.force_family:
                        metadata['family'] = args.force_family
                    
                    out_filename = generate_output_filename(metadata, ext, args.force_family)
                    if not out_filename or out_filename == ext:
                        out_filename = path.stem + ext
                    
                    style_info = f"{metadata.get('weight', 'Regular')} {metadata.get('style', 'Regular')}".strip()
                    feature_info = ""
                    
                    special_features = []
                    if 'dlig' in metadata.get('features', []):
                        special_features.append('ligatures')
                    if any(f.startswith('ss') for f in metadata.get('features', [])):
                        special_features.append('stylistic sets')
                    if special_features:
                        feature_info = f" (with {', '.join(special_features)})"
                    
                    if args.organize_by_family:
                        out_filename = f"{display_family}/{out_filename}"
                    
                    print(f"Would convert: {path.name} -> {out_filename}")
                    print(f"   Font: {display_family} {style_info}{feature_info}")
                else:
                    out_filename = path.stem + ext
                    print(f"Would convert: {path.name} -> {out_filename}")
                    
            except Exception as exc:  # noqa: BLE001
                print(f"Would fail: {path.name} ({exc})")
        return 0

    # Group fonts by family if requested
    font_groups = {}
    if args.organize_by_family:
        target_family = args.force_family or "Unknown"
        for path in woff2_files:
            try:
                font = TTFont(str(path))
                metadata = extract_font_metadata(font)
                family = args.force_family or metadata.get('family', 'Unknown')
                family = re.sub(r'[^\w\s-]', '', family)
                family = re.sub(r'\s+', '', family) or 'Unknown'
                
                if family not in font_groups:
                    font_groups[family] = []
                font_groups[family].append(path)
            except Exception:
                if target_family not in font_groups:
                    font_groups[target_family] = []
                font_groups[target_family].append(path)
    else:
        font_groups[''] = woff2_files

    success_count = 0
    fail_count = 0
    converted_fonts = []
    
    for family_name, paths in font_groups.items():
        if args.organize_by_family and family_name:
            family_out_dir = out_dir / family_name
            print(f"\n=== Processing {family_name} family ===")
        else:
            family_out_dir = out_dir
            
        for path in paths:
            ok, message, converted_path = convert_single_file(path, family_out_dir, args.overwrite, use_metadata_names, args.force_family)
            print(message)
            if ok:
                success_count += 1
                converted_fonts.append(converted_path)
            else:
                fail_count += 1

    print("")
    print(f"Done. Success: {success_count}, Failed/Skipped: {fail_count}")
    
    if args.organize_by_family:
        print(f"Fonts organized into {len([f for f in font_groups.keys() if f])} families")
    
    # Create font collection if requested
    if args.create_collection and converted_fonts:
        try:
            # Determine collection filename
            collection_name = args.force_family or "FontCollection"
            collection_name = re.sub(r'[^\w\s-]', '', collection_name)
            collection_name = re.sub(r'\s+', '', collection_name)
            collection_path = out_dir / f"{collection_name}.ttc"
            
            print(f"\n=== Creating font collection ===")
            print(f"Collection: {collection_path}")
            print(f"Including {len(converted_fonts)} font(s)")
            
            # Load all converted fonts
            fonts = []
            for font_path in converted_fonts:
                try:
                    fonts.append(TTFont(str(font_path)))
                except Exception as e:
                    print(f"Warning: Could not load {font_path.name} for collection: {e}")
            
            if fonts:
                # Create collection
                collection = TTCollection()
                collection.fonts = fonts
                
                if collection_path.exists() and not args.overwrite:
                    print(f"Collection exists, use --overwrite to replace: {collection_path}")
                else:
                    collection.save(str(collection_path))
                    print(f"Created font collection: {collection_path}")
                    print(f"Size: {collection_path.stat().st_size / 1024 / 1024:.1f} MB")
            else:
                print("No fonts could be loaded for collection")
                
        except Exception as e:
            print(f"Failed to create font collection: {e}")
            return 2
    
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())




