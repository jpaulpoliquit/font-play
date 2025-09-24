#!/usr/bin/env python3
"""
 Font Manager - Complete font processing pipeline
Downloads, converts, and organizes all  fonts with proper family mapping.
"""

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection


# Complete font mapping based on  's CSS
FONT_MAPPING = {
    #  GOTHIC FAMILY (4 fonts - the main brand fonts)
    "d3293b264284c7e4-s.p.woff2": {
        "family": "Gothic", 
        "weight": 400, 
        "style": "normal",
        "output_name": "Gothic-Regular",
        "description": "Main text font - Regular"
    },
    "4d47f1cf2188c753-s.p.woff2": {
        "family": "Gothic", 
        "weight": 400, 
        "style": "italic", 
        "output_name": "Gothic-Italic",
        "description": "Main text font - Italic"
    },
    "da0a7633fc8b7288-s.p.woff2": {
        "family": "Gothic", 
        "weight": 700, 
        "style": "normal",
        "output_name": "Gothic-Bold",
        "description": "Main text font - Bold"
    },
    "89358bea2c069d9d-s.p.woff2": {
        "family": "Gothic", 
        "weight": 700, 
        "style": "italic",
        "output_name": "Gothic-BoldItalic",
        "description": "Main text font - Bold Italic"
    },
    
    # BERKELEY MONO FAMILY (2 fonts - monospace coding fonts)
    "c0b22bcfa1a173f2.p.woff2": {
        "family": "Berkeley Mono", 
        "weight": 400, 
        "style": "normal",
        "output_name": "BerkeleyMono-Regular",
        "description": "Code font - Regular"
    },
    "006940878f5e6885.p.woff2": {
        "family": "Berkeley Mono", 
        "weight": 400, 
        "style": "italic",
        "output_name": "BerkeleyMono-Italic",
        "description": "Code font - Italic"
    },
    
    # LATO FAMILY (10 fonts - UI/interface fonts)
    "6ee7df5b3965574d-s.p.woff2": {
        "family": "Lato", 
        "weight": 100, 
        "style": "italic",
        "output_name": "Lato-ThinItalic",
        "description": "UI font - Thin Italic"
    },
    "b5215411e8ce7768-s.p.woff2": {
        "family": "Lato", 
        "weight": 300, 
        "style": "italic",
        "output_name": "Lato-LightItalic",
        "description": "UI font - Light Italic"
    },
    "756f9c755543fe29-s.p.woff2": {
        "family": "Lato", 
        "weight": 400, 
        "style": "italic",
        "output_name": "Lato-Italic",
        "description": "UI font - Regular Italic"
    },
    "25460892714ab800-s.p.woff2": {
        "family": "Lato", 
        "weight": 700, 
        "style": "italic",
        "output_name": "Lato-BoldItalic",
        "description": "UI font - Bold Italic"
    },
    "9364c9a9ce248cb1-s.p.woff2": {
        "family": "Lato", 
        "weight": 900, 
        "style": "italic",
        "output_name": "Lato-BlackItalic",
        "description": "UI font - Black Italic"
    },
    "55c20a7790588da9-s.p.woff2": {
        "family": "Lato", 
        "weight": 100, 
        "style": "normal",
        "output_name": "Lato-Thin",
        "description": "UI font - Thin"
    },
    "155cae559bbd1a77-s.p.woff2": {
        "family": "Lato", 
        "weight": 300, 
        "style": "normal",
        "output_name": "Lato-Light",
        "description": "UI font - Light"
    },
    "4de1fea1a954a5b6-s.p.woff2": {
        "family": "Lato", 
        "weight": 400, 
        "style": "normal",
        "output_name": "Lato-Regular",
        "description": "UI font - Regular"
    },
    "6d664cce900333ee-s.p.woff2": {
        "family": "Lato", 
        "weight": 700, 
        "style": "normal",
        "output_name": "Lato-Bold",
        "description": "UI font - Bold"
    },
    "7ff6869a1704182a-s.p.woff2": {
        "family": "Lato", 
        "weight": 900, 
        "style": "normal",
        "output_name": "Lato-Black",
        "description": "UI font - Black"
    }
}


class FontProcessor:
    """Handles font processing operations."""
    
    def __init__(self, base_url: str, downloads_dir: Path, output_dir: Path, verbose: bool = False):
        self.base_url = base_url
        self.downloads_dir = downloads_dir
        self.output_dir = output_dir
        self.verbose = verbose
        
        # Ensure directories exist
        self.downloads_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        if self.verbose or level in ["ERROR", "SUCCESS"]:
            timestamp = time.strftime("%H:%M:%S")
            prefix = {"INFO": "ℹ️", "ERROR": "❌", "SUCCESS": "✅", "DOWNLOAD": "📥", "CONVERT": "🔄"}
            print(f"[{timestamp}] {prefix.get(level, '•')} {message}")
    
    def download_font(self, filename: str, font_info: Dict) -> Tuple[bool, Optional[Path]]:
        """Download a single font file."""
        url = self.base_url.rstrip('/') + '/marketing-static/_next/static/media/' + filename
        local_path = self.downloads_dir / filename
        
        if local_path.exists():
            self.log(f"Already exists: {filename}")
            return True, local_path
        
        try:
            self.log(f"Downloading: {font_info['description']}", "DOWNLOAD")
            urllib.request.urlretrieve(url, str(local_path))
            return True, local_path
        except urllib.error.URLError as e:
            self.log(f"Failed to download {filename}: {e}", "ERROR")
            return False, None
    
    def download_all_fonts(self, max_workers: int = 4) -> List[Tuple[Path, Dict]]:
        """Download all fonts concurrently."""
        self.log(f"Starting download of {len(FONT_MAPPING)} fonts...")
        
        downloaded_fonts = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_font = {
                executor.submit(self.download_font, filename, font_info): (filename, font_info)
                for filename, font_info in FONT_MAPPING.items()
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_font):
                filename, font_info = future_to_font[future]
                try:
                    success, path = future.result()
                    if success and path:
                        downloaded_fonts.append((path, font_info))
                except Exception as e:
                    self.log(f"Download failed for {filename}: {e}", "ERROR")
        
        self.log(f"Downloaded {len(downloaded_fonts)}/{len(FONT_MAPPING)} fonts", "SUCCESS")
        return downloaded_fonts
    
    def rename_font_family(self, font: TTFont, family_name: str, subfamily: str) -> None:
        """Update font metadata with new family and subfamily names."""
        if 'name' not in font:
            return
        
        name_table = font['name']
        
        for record in name_table.names:
            try:
                if record.nameID == 1:  # Font Family name
                    record.string = family_name.encode('utf-16be') if record.isUnicode() else family_name.encode('latin-1')
                elif record.nameID == 2:  # Font Subfamily name
                    record.string = subfamily.encode('utf-16be') if record.isUnicode() else subfamily.encode('latin-1')
                elif record.nameID == 4:  # Full font name
                    full_name = f"{family_name} {subfamily}"
                    record.string = full_name.encode('utf-16be') if record.isUnicode() else full_name.encode('latin-1')
                elif record.nameID == 6:  # PostScript name
                    ps_name = family_name.replace(' ', '') + '-' + subfamily.replace(' ', '')
                    record.string = ps_name.encode('utf-16be') if record.isUnicode() else ps_name.encode('latin-1')
            except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
                continue
    
    def convert_font(self, font_path: Path, font_info: Dict) -> Optional[Path]:
        """Convert a single WOFF2 font to TTF/OTF with proper naming."""
        try:
            # Load font
            font = TTFont(str(font_path))
            font.flavor = None
            
            # Determine output extension
            ext = ".otf"if "CFF "in font or "CFF2"in font else ".ttf"
            
            # Generate subfamily name
            weight = font_info['weight']
            style = font_info['style']
            
            subfamily_parts = []
            if weight == 100:
                subfamily_parts.append("Thin")
            elif weight == 300:
                subfamily_parts.append("Light")
            elif weight == 700:
                subfamily_parts.append("Bold")
            elif weight == 900:
                subfamily_parts.append("Black")
            
            if style == "italic":
                subfamily_parts.append("Italic")
            
            subfamily = "".join(subfamily_parts) if subfamily_parts else "Regular"
            
            # Update font metadata
            self.rename_font_family(font, font_info['family'], subfamily)
            
            # Create family directory
            family_dir = self.output_dir / font_info['family']
            family_dir.mkdir(exist_ok=True)
            
            # Save converted font
            output_filename = font_info['output_name'] + ext
            output_path = family_dir / output_filename
            
            font.save(str(output_path))
            
            self.log(f"Converted: {font_path.name} -> {font_info['family']}/{output_filename}", "CONVERT")
            return output_path
            
        except Exception as e:
            self.log(f"Error converting {font_path.name}: {e}", "ERROR")
            return None
    
    def convert_all_fonts(self, downloaded_fonts: List[Tuple[Path, Dict]], max_workers: int = 2) -> Dict[str, List[Path]]:
        """Convert all fonts concurrently, organized by family."""
        self.log(f"Converting {len(downloaded_fonts)} fonts...")
        
        converted_by_family = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit conversion tasks
            future_to_font = {
                executor.submit(self.convert_font, font_path, font_info): (font_path, font_info)
                for font_path, font_info in downloaded_fonts
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_font):
                font_path, font_info = future_to_font[future]
                try:
                    converted_path = future.result()
                    if converted_path:
                        family = font_info['family']
                        if family not in converted_by_family:
                            converted_by_family[family] = []
                        converted_by_family[family].append(converted_path)
                except Exception as e:
                    self.log(f"Conversion failed for {font_path.name}: {e}", "ERROR")
        
        return converted_by_family
    
    def create_font_collections(self, converted_by_family: Dict[str, List[Path]]) -> List[Path]:
        """Create TTC collection files for each font family."""
        collections = []
        
        for family_name, font_paths in converted_by_family.items():
            if len(font_paths) < 2:  # Skip single-font families
                continue
            
            try:
                # Load all fonts in family
                family_fonts = []
                for font_path in font_paths:
                    family_fonts.append(TTFont(str(font_path)))
                
                # Create collection
                collection = TTCollection()
                collection.fonts = family_fonts
                
                # Save collection
                family_dir = self.output_dir / family_name
                collection_name = family_name.replace(' ', '') + '.ttc'
                collection_path = family_dir / collection_name
                
                collection.save(str(collection_path))
                collections.append(collection_path)
                
                self.log(f"Created collection: {family_name}/{collection_name} ({len(family_fonts)} fonts)", "SUCCESS")
                
            except Exception as e:
                self.log(f"Failed to create collection for {family_name}: {e}", "ERROR")
        
        return collections
    
    def generate_report(self, converted_by_family: Dict[str, List[Path]], collections: List[Path]) -> None:
        """Generate a comprehensive report of processed fonts."""
        print("\n"+ "="*60)
        print("🎨  FONT PROCESSING COMPLETE")
        print("="*60)
        
        total_fonts = sum(len(fonts) for fonts in converted_by_family.values())
        print(f"📊 SUMMARY:")
        print(f" • Total fonts processed: {total_fonts}")
        print(f" • Font families: {len(converted_by_family)}")
        print(f" • Collections created: {len(collections)}")
        print()
        
        print("📁 FONT FAMILIES:")
        for family_name, font_paths in converted_by_family.items():
            print(f" 📂 {family_name} ({len(font_paths)} fonts)")
            for font_path in sorted(font_paths):
                print(f"   • {font_path.name}")
            
            # Show collection if exists
            family_dir = self.output_dir / family_name
            collection_path = family_dir / f"{family_name.replace(' ', '')}.ttc"
            if collection_path.exists():
                size_mb = collection_path.stat().st_size / 1024 / 1024
                print(f"   📦 {collection_path.name} ({size_mb:.1f} MB)")
            print()
        
        print("🎯 VERIFICATION:")
        _gothic_count = len(converted_by_family.get("Gothic", []))
        berkeley_mono_count = len(converted_by_family.get("Berkeley Mono", []))
        lato_count = len(converted_by_family.get("Lato", []))
        
        def check_count(actual, expected, name):
            status = "✅"if actual == expected else "⚠️"
            return f" {status} {name}: {actual}/{expected} fonts"
        
        print(check_count(_gothic_count, 4, "Gothic"))
        print(check_count(berkeley_mono_count, 2, "Berkeley Mono"))
        print(check_count(lato_count, 10, "Lato"))
        
        print("\n📦 READY FOR INSTALLATION:")
        for collection_path in collections:
            print(f" 🔹 {collection_path}")
        
        print(f"\n📁 All fonts organized in: {self.output_dir}")
        print("\n💡 INSTALLATION TIPS:")
        print(" • Right-click any .ttc file and select 'Install'")
        print(" • Each family will appear as one font with multiple styles")
        print(" • Individual .ttf/.otf files can also be installed separately")


def main():
    parser = argparse.ArgumentParser(
        description="Font Manager - Complete font processing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and process all fonts
  python _font_manager.py
  
  # Custom directories and settings
  python _font_manager.py --output my-fonts --downloads temp --base-url https://.com
  
  # Verbose output with more workers
  python _font_manager.py --verbose --max-workers 8
  
  # Clean previous results
  python _font_manager.py --clean --output my-fonts
        """
    )
    
    parser.add_argument("--base-url", default="https://.com", 
                       help="Base URL for font downloads (default: https://.com)")
    parser.add_argument("--downloads", default="downloads", 
                       help="Directory for WOFF2 downloads (default: downloads)")
    parser.add_argument("--output", default="-fonts", 
                       help="Output directory for organized fonts (default: -fonts)")
    parser.add_argument("--max-workers", type=int, default=4, 
                       help="Maximum concurrent workers (default: 4)")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--clean", action="store_true", 
                       help="Clean output directory before processing")
    parser.add_argument("--skip-download", action="store_true", 
                       help="Skip download phase (use existing files)")
    parser.add_argument("--collections-only", action="store_true", 
                       help="Only create collections from existing fonts")
    
    args = parser.parse_args()
    
    downloads_dir = Path(args.downloads)
    output_dir = Path(args.output)
    
    # Clean output directory if requested
    if args.clean and output_dir.exists():
        print(f"🧹 Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)
    
    # Initialize processor
    processor = FontProcessor(args.base_url, downloads_dir, output_dir, args.verbose)
    
    print("🚀 Starting  Font Manager")
    print(f"📥 Downloads: {downloads_dir}")
    print(f"📁 Output: {output_dir}")
    print(f"🔄 Workers: {args.max_workers}")
    print()
    
    try:
        # Phase 1: Download fonts
        if not args.skip_download and not args.collections_only:
            downloaded_fonts = processor.download_all_fonts(args.max_workers)
            if not downloaded_fonts:
                print("❌ No fonts downloaded. Exiting.")
                return 1
        else:
            # Use existing downloads
            downloaded_fonts = []
            for filename, font_info in FONT_MAPPING.items():
                font_path = downloads_dir / filename
                if font_path.exists():
                    downloaded_fonts.append((font_path, font_info))
            
            if not downloaded_fonts:
                print(f"❌ No existing fonts found in {downloads_dir}. Use --skip-download=false")
                return 1
        
        # Phase 2: Convert fonts
        if not args.collections_only:
            converted_by_family = processor.convert_all_fonts(downloaded_fonts, args.max_workers)
            if not converted_by_family:
                print("❌ No fonts converted. Exiting.")
                return 1
        else:
            # Find existing converted fonts
            converted_by_family = {}
            for family in ["Gothic", "Berkeley Mono", "Lato"]:
                family_dir = output_dir / family
                if family_dir.exists():
                    fonts = list(family_dir.glob("*.[ot]tf"))
                    if fonts:
                        converted_by_family[family] = fonts
        
        # Phase 3: Create collections
        collections = processor.create_font_collections(converted_by_family)
        
        # Phase 4: Generate report
        processor.generate_report(converted_by_family, collections)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
