# Font Conversion Toolkit

A Python toolkit for converting web fonts (WOFF2) to installable desktop fonts with family normalization and TTC bundling.

## Features
- 🔄 Convert WOFF2 → TTF/OTF
- 🏷️ Normalize font family names (e.g., "Custom Font")
- 📦 Bundle multiple fonts into single TTC files
- ⚡ One-click installation scripts
- 🎯 Automatic weight/style detection

This utility converts static `.woff2` webfonts in `fonts/` into installable desktop fonts (`.ttf` or `.otf`). It does not create variable fonts.

## Requirements
- Python 3.13
- Packages: `fonttools`, `brotli`

Install packages:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Quick Start
1. Place your `.woff2` files in the `fonts/` directory
2. Run the conversion: `python scripts/convert_woff2_to_ttf.py --src fonts --out dist/fonts-installable`
3. Normalize names: `python scripts/normalize_font_names.py --src dist/fonts-installable --out dist/fonts-renamed --family "Custom Font"`
4. Create TTC: `python scripts/bundle_to_ttc.py --src dist/fonts-renamed --out dist/fonts-renamed/CustomFont.ttc`
5. Install: Double-click `install-fonts.bat` or install `CustomFont.ttc` manually

## Convert fonts
Run from the project root:
```bash
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/fonts-installable
```

Dry-run first:
```bash
python scripts/convert_woff2_to_ttf.py --src fonts --out dist/fonts-installable --dry-run
```

Outputs are written to `dist/fonts-installable` using `.ttf` for TrueType or `.otf` for CFF/CFF2 outlines.

## Install fonts (Windows)
- Open `dist/fonts-installable`
- Select the `.ttf`/`.otf` files
- Right‑click → Install (or Install for all users)

## Create TTC collection (single file with all styles)
Bundle TTF files into a single TrueType Collection:
```bash
python scripts/bundle_to_ttc.py --src dist/fonts-renamed --out dist/fonts-renamed/CustomFont.ttc --overwrite
```

Example output: `CustomFont.ttc` contains all TTF styles in one installable file.

## ⚠️ Important Legal Notice

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
- ✅ Personal experiments with your own fonts
- ✅ Open source/libre fonts (OFL, etc.)
- ✅ Fonts where you have explicit conversion rights
- ❌ Commercial web fonts without permission
- ❌ Fonts with restrictive licenses

**You are responsible for ensuring compliance with all applicable font licenses.**

## Notes
- Creating a true variable font requires source masters or an existing variable font; this tool only converts containers.
- TTC files bundle multiple font faces into a single file for easier installation.
