# Convert WOFF2 to installable fonts

This utility converts static `.woff2` webfonts in `fonts/` into installable desktop fonts (`.ttf` or `.otf`). It does not create variable fonts.

## Requirements
- Python 3.13
- Packages: `fonttools`, `brotli`

Install packages:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

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
python scripts/bundle_to_ttc.py --src dist/CursorGothic --out dist/CursorGothic/CursorGothic.ttc --overwrite
```

Example output: `CursorGothic.ttc` contains all TTF styles in one installable file.

## Notes
- Ensure your license permits format conversion and desktop installation.
- Creating a true variable font requires source masters or an existing variable font; this tool only converts containers.
- TTC files bundle multiple font faces into a single file for easier installation.
