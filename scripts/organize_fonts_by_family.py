#!/usr/bin/env python3
"""
Organize converted fonts into family-based folders with proper naming.
"""

import argparse
import shutil
import sys
from pathlib import Path
from fontTools.ttLib import TTFont


def get_font_info(font_path: Path):
    """Extract font family and style information."""
    try:
        font = TTFont(str(font_path))
        
        family_name = "Unknown"
        subfamily_name = "Regular"
        
        if 'name' in font:
            name_table = font['name']
            for record in name_table.names:
                try:
                    if record.nameID == 1:  # Font Family name
                        family_name = record.toUnicode()
                    elif record.nameID == 2:  # Font Subfamily name
                        subfamily_name = record.toUnicode()
                except:
                    continue
        
        return family_name, subfamily_name
        
    except Exception as e:
        print(f"Error reading {font_path.name}: {e}")
        return "Unknown", "Regular"


def generate_proper_filename(family: str, subfamily: str, extension: str) -> str:
    """Generate a proper filename based on family and subfamily."""
    # Clean family name
    clean_family = family.replace(" ", "")
    
    # Clean subfamily name
    clean_subfamily = subfamily.replace(" ", "")
    
    if clean_subfamily == "Regular":
        return f"{clean_family}{extension}"
    else:
        return f"{clean_family}-{clean_subfamily}{extension}"


def organize_fonts(source_dir: Path, output_dir: Path, overwrite: bool = False):
    """Organize fonts into family-based folders."""
    
    # Find all font files
    font_extensions = [".ttf", ".otf"]
    font_files = []
    
    for ext in font_extensions:
        font_files.extend(source_dir.glob(f"*{ext}"))
    
    if not font_files:
        print(f"No font files found in {source_dir}")
        return
    
    print(f"Found {len(font_files)} font files")
    print(f"Organizing into: {output_dir}")
    print()
    
    # Group fonts by family
    families = {}
    
    for font_path in font_files:
        family, subfamily = get_font_info(font_path)
        
        if family not in families:
            families[family] = []
        
        families[family].append((font_path, subfamily))
    
    # Create organized structure
    for family, fonts in families.items():
        # Create family directory
        family_dir = output_dir / family
        family_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"=== {family} Family ({len(fonts)} fonts) ===")
        
        for font_path, subfamily in fonts:
            # Generate proper filename
            extension = font_path.suffix
            new_filename = generate_proper_filename(family, subfamily, extension)
            new_path = family_dir / new_filename
            
            # Check if file exists
            if new_path.exists() and not overwrite:
                print(f"Skip (exists): {new_filename}")
                continue
            
            # Copy font file
            try:
                shutil.copy2(font_path, new_path)
                print(f"Organized: {font_path.name} -> {family}/{new_filename}")
            except Exception as e:
                print(f"Error copying {font_path.name}: {e}")
        
        print()
    
    print(f"✅ Organized fonts into {len(families)} family folders")
    
    # Create family-specific collections
    print("\n=== Creating Family Collections ===")
    
    for family, fonts in families.items():
        if len(fonts) > 1:  # Only create collection if multiple fonts
            try:
                from fontTools.ttLib.ttCollection import TTCollection
                
                # Load all fonts in family
                family_fonts = []
                family_dir = output_dir / family
                
                for font_file in family_dir.glob("*.[ot]tf"):
                    try:
                        family_fonts.append(TTFont(str(font_file)))
                    except Exception as e:
                        print(f"Warning: Could not load {font_file.name}: {e}")
                
                if family_fonts:
                    # Create collection
                    collection = TTCollection()
                    collection.fonts = family_fonts
                    
                    collection_name = family.replace(" ", "") + ".ttc"
                    collection_path = family_dir / collection_name
                    
                    collection.save(str(collection_path))
                    print(f"Created collection: {family}/{collection_name} ({len(family_fonts)} fonts)")
                
            except Exception as e:
                print(f"Error creating collection for {family}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Organize fonts by family")
    parser.add_argument("--source", default="-gothic-complete", help="Source directory with fonts")
    parser.add_argument("--output", default="organized-fonts", help="Output directory for organized fonts")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    output_dir = Path(args.output)
    
    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        return 1
    
    organize_fonts(source_dir, output_dir, args.overwrite)
    
    print(f"\n📁 Font families organized in: {output_dir}")
    print("Each family folder contains:")
    print("  • Individual font files with proper names")
    print("  • Family collection (.ttc) file for easy installation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
