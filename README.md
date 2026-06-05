# Static Resources

This repository contains static resources for blog images with automatic WebP conversion.

## Features

✅ **Automatic Conversion**: Images are automatically converted to WebP format on push
✅ **Directory Preservation**: Maintains the original directory structure
✅ **Smart Updates**: Only converts new or modified images
✅ **Automatic Cleanup**: Removes orphaned WebP files when source images are deleted
✅ **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Activate Git hooks** (choose one based on your environment):

   **For Windows (CMD/PowerShell)**:
   ```bash
   copy scripts\pre-push.bat .git\hooks\pre-push.bat
   ```

   **For Git Bash / Linux / macOS**:
   ```bash
   cp scripts/pre-push.sh .git/hooks/pre-push
   chmod +x .git/hooks/pre-push
   ```

## Usage

### Automatic Conversion (Recommended)

Every time you run `git push`, the pre-push hook will automatically:
1. Convert new or modified images in `blog/images/original` to WebP
2. Save them to `blog/images/webp` with the same directory structure
3. Clean up orphaned WebP files

### Manual Conversion

You can also run the conversion manually:

```bash
npm run convert
```

## Supported Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tif, .tiff)

## Directory Structure

```
blog/images/
├── original/          # Source images (commit this)
│   ├── 2024/
│   │   └── photo.png
│   └── avatar.jpg
└── webp/             # Generated WebP files (auto-generated, don't commit)
    ├── 2024/
    │   └── photo.webp
    └── avatar.webp
```

## Configuration

You can adjust the WebP quality in `scripts/convert-to-webp.js`:

```javascript
const WEBP_QUALITY = 80;  // Default: 80%
```

## How It Works

1. **On push**: Git triggers the pre-push hook
2. **Scanning**: The script scans `blog/images/original` for images
3. **Conversion**: New/updated images are converted to WebP
4. **Cleanup**: Orphaned WebP files (no source) are deleted
5. **Output**: Detailed report shows all operations

## Troubleshooting

### "sharp module not found"
Run `npm install` to install dependencies.

### Hook not running
Make sure the hook file is in `.git/hooks/pre-push` (without .sample extension).

### Images not converting
- Check that images are in `blog/images/original`
- Verify file extensions are supported
- Check the console output for errors

## Requirements

- Node.js (v14 or higher recommended)
- npm
- sharp library (installed via npm install)