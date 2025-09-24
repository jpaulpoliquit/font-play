# Font Conversion Toolkit

A comprehensive Python toolkit for converting web fonts (WOFF2) to installable desktop fonts with family normalization, organization, and TTC bundling.

## Features
- **Convert** WOFF2 → TTF/OTF with proper metadata
- **Normalize** font family names to unified naming
- **Organize** fonts by family into structured directories
- **Bundle** multiple fonts into single TTC collection files
- **Enhanced** style detection (weights, italics, OpenType features)
- **Automated** processing pipelines with concurrent operations

This toolkit converts static `.woff2` webfonts into installable desktop fonts (`.ttf` or `.otf`). It does not create variable fonts.

## Requirements
- **Python 3.8+** (tested with 3.12)
- **Packages**: `fonttools>=4.54.0`, `brotli>=1.1.0`

### Install Dependencies
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Quick Start

### Option A: Basic Workflow (Step by Step)
```bash
# 1. Place your .woff2 files in fonts/ directory
# 2. Convert to desktop fonts
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/step1-converted

# 3. Normalize to unified family name
python scripts/normalize_font_names.py --src dist/step1-converted --out dist/step2-renamed --family "My Custom Font"

# 4. Create collection file
python scripts/bundle_to_ttc.py --src dist/step2-renamed --out dist/step2-renamed/MyCustomFont.ttc

# 5. Install: Right-click MyCustomFont.ttc → Install
```

### Option B: All-in-One (Advanced)
```bash
# Convert with family renaming and collection in one step
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/unified --force-family "My Custom Font" --create-collection --organize-by-family
```

## Script Documentation

### `convert_woff2_to_ttf.py` - Main Conversion Script

**Purpose**: Convert WOFF2 files to installable TTF/OTF with enhanced metadata detection.

**Basic Usage**:
```bash
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/converted
```

**Advanced Options**:
```bash
# Preview without writing files
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/converted --dry-run

# Rename all fonts to unified family
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/converted --force-family "Gothic Pro"

# Organize by family + create collections
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/converted --organize-by-family --create-collection

# Use original hash filenames instead of metadata names
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/converted --use-hash-names
```

**Parameters**:
- `--src`: Source directory with .woff2 files (default: `fonts`)
- `--out`: Output directory (default: `dist/fonts-installable`)
- `--force-family`: Rename all fonts to this family name
- `--organize-by-family`: Create subdirectories for each font family
- `--create-collection`: Generate .ttc collection files
- `--dry-run`: Preview changes without writing files
- `--overwrite`: Replace existing output files

### `normalize_font_names.py` - Family Name Normalization

**Purpose**: Standardize font names and metadata to a target family name.

**Usage**:
```bash
# Basic normalization
python scripts/normalize_font_names.py --src dist/converted --out dist/normalized --family "Unified Font"

# Preview changes
python scripts/normalize_font_names.py --src dist/converted --out dist/normalized --family "Unified Font" --dry-run
```

**Parameters**:
- `--src`: Source directory with .ttf/.otf files
- `--out`: Output directory for renamed fonts
- `--family`: Target family name (e.g., "Custom Font")
- `--dry-run`: Preview changes without writing files
- `--overwrite`: Replace existing files

### `bundle_to_ttc.py` - TTC Collection Creator

**Purpose**: Bundle multiple font files into a single installable .ttc collection.

**Usage**:
```bash
# Create TTC from TTF files
python scripts/bundle_to_ttc.py --src dist/normalized --out dist/normalized/UnifiedFont.ttc

# Include both TTF and OTF files
python scripts/bundle_to_ttc.py --src dist/normalized --out dist/normalized/UnifiedFont.ttc --include-otf
```

**Parameters**:
- `--src`: Directory containing .ttf/.otf files to bundle
- `--out`: Output .ttc file path
- `--include-otf`: Include .otf files (may cause compatibility issues)
- `--overwrite`: Replace existing .ttc file

### `organize_fonts_by_family.py` - Family Organization

**Purpose**: Organize converted fonts into family-based directory structure.

**Usage**:
```bash
# Organize fonts by detected family names
python scripts/organize_fonts_by_family.py --source dist/converted --output dist/organized

# With collection creation
python scripts/organize_fonts_by_family.py --source dist/converted --output dist/organized --overwrite
```

**Features**:
- Auto-detects font families from metadata
- Creates family subdirectories
- Generates proper filenames
- Creates .ttc collections for each family

### `font_manager.py` - Complete Pipeline (Advanced)

**Purpose**: Full-featured font processing pipeline with download capabilities.

**Usage**:
```bash
# Complete processing pipeline
python scripts/font_manager.py --output my-fonts --verbose

# Skip download phase (use existing files)
python scripts/font_manager.py --output my-fonts --skip-download

# Create collections only
python scripts/font_manager.py --output my-fonts --collections-only
```

## Workflow Examples

### Example 1: Simple Font Family Unification
```bash
# You have: Lato-Regular.woff2, Lato-Bold.woff2, Lato-Italic.woff2
# Goal: Unified "My Brand Font" family

# Step 1: Convert
python scripts/convert_woff2_to_ttf.py --src fonts --out temp/converted

# Step 2: Normalize
python scripts/normalize_font_names.py --src temp/converted --out final/MyBrandFont --family "My Brand Font"

# Step 3: Create collection
python scripts/bundle_to_ttc.py --src final/MyBrandFont --out final/MyBrandFont.ttc

# Result: final/MyBrandFont.ttc (single file, 3 styles)
```

### Example 2: Multiple Font Families
```bash
# You have: Mixed font files from different families
# Goal: Organized by family with collections

python scripts/convert_woff2_to_ttf.py --src fonts --out organized --organize-by-family --create-collection

# Result: 
# organized/FontFamily1/FontFamily1.ttc
# organized/FontFamily2/FontFamily2.ttc
```

### Example 3: Single Unified Family
```bash
# You have: Multiple different font families
# Goal: All fonts as one "Custom Font" family

python scripts/convert_woff2_to_ttf.py --src fonts --out unified --force-family "Custom Font" --create-collection

# Result: unified/CustomFont.ttc (all fonts as one family)
```

## Installation Guide

### Windows Installation
1. **Individual fonts**: Right-click `.ttf`/`.otf` files → "Install" or "Install for all users"
2. **Collection files**: Right-click `.ttc` files → "Install for all users" (recommended)
3. **Batch installation**: Use included `install-fonts.bat` script

### After Installation
- Fonts appear in applications under the specified family name
- Multiple weights/styles available in font style dropdown
- TTC collections provide all variations as one family

## Common Use Cases

| Scenario | Command | Result |
|----------|---------|---------|
| **Basic conversion** | `convert_woff2_to_ttf.py --src fonts --out converted` | Individual TTF/OTF files |
| **Unified family** | `normalize_font_names.py --family "My Font"` | All fonts renamed to "My Font" |
| **Single collection** | `bundle_to_ttc.py --src fonts --out MyFont.ttc` | One .ttc file with all styles |
| **Auto-organize** | `convert_woff2_to_ttf.py --organize-by-family` | Fonts grouped by original families |
| **Preview changes** | Add `--dry-run` to any script | See what would happen without changes |

## Important Legal Notice

**This toolkit was created for personal experimentation and educational purposes.**

### Commercial Use Warning
- **DO NOT** use this tool with copyrighted or commercial fonts without explicit permission
- **ALWAYS** verify that your font license permits:
  - Format conversion (WOFF2 → TTF/OTF)
  - Desktop installation
  - Distribution/sharing (if applicable)
- Many web fonts have licenses that restrict desktop installation
- When in doubt, contact the font foundry or check the license terms

### Recommended Use Cases
- **Allowed**: Personal experiments with your own fonts
- **Allowed**: Open source/libre fonts (OFL, etc.)
- **Allowed**: Fonts where you have explicit conversion rights
- **Not Allowed**: Commercial web fonts without permission
- **Not Allowed**: Fonts with restrictive licenses

**You are responsible for ensuring compliance with all applicable font licenses.**

## Notes
- Creating a true variable font requires source masters or an existing variable font; this tool only converts containers.
- TTC files bundle multiple font faces into a single file for easier installation.
