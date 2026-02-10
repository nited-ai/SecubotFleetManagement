# Tailwind CSS Setup Guide

This project uses Tailwind CSS v3.4.1 for local, offline-capable CSS generation.

> **Note:** This project uses Tailwind CSS v3, which uses `tailwind.config.js` for configuration.
> Custom colors are defined in `tailwind.config.js` in the `theme.extend.colors` section.

## Quick Start

### Windows

1. Run the build script (it will auto-download Tailwind CLI if needed):
   ```powershell
   .\build-css.ps1
   ```

2. For development with auto-rebuild on file changes:
   ```powershell
   .\build-css.ps1 -Watch
   ```

3. For production (minified):
   ```powershell
   .\build-css.ps1 -Minify
   ```

### Linux/macOS

1. Make the script executable:
   ```bash
   chmod +x build-css.sh
   ```

2. Run the build script:
   ```bash
   ./build-css.sh
   ```

3. For development with auto-rebuild:
   ```bash
   ./build-css.sh --watch
   ```

4. For production (minified):
   ```bash
   ./build-css.sh --minify
   ```

## Manual Installation

If the automatic download fails, manually download the Tailwind CSS standalone CLI:

### Windows
Download from: https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe
Save as: `tailwindcss.exe` in the project root

### Linux (x64)
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
mv tailwindcss-linux-x64 tailwindcss
chmod +x tailwindcss
```

### macOS (Apple Silicon)
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
mv tailwindcss-macos-arm64 tailwindcss
chmod +x tailwindcss
```

### macOS (Intel)
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-x64
mv tailwindcss-macos-x64 tailwindcss
chmod +x tailwindcss
```

## File Structure

```
unitree_webrtc_connect/
├── tailwind.config.js           # Tailwind configuration with custom colors
├── static/
│   └── css/
│       ├── tailwind.input.css   # Input file with @tailwind directives
│       ├── tailwind.output.css  # Generated CSS (DO NOT EDIT)
│       └── custom.css           # Additional custom styles
├── templates/
│   └── *.html                   # HTML templates (scanned for classes)
├── build-css.ps1                # Windows build script
└── build-css.sh                 # Linux/macOS build script
```

## Custom Colors

The following custom Unitree colors are defined in `tailwind.config.js`:

- `unitree-primary`: #00E8DA (Teal/Cyan)
- `unitree-secondary`: #00B8AD (Darker Teal)
- `unitree-dark`: #1e1e1e (Dark background)
- `unitree-dark-lighter`: #2d2d2d (Lighter dark)
- `unitree-success`: #10b981 (Green)
- `unitree-warning`: #f59e0b (Orange)
- `unitree-danger`: #ef4444 (Red)
- `unitree-info`: #3b82f6 (Blue)

These are defined in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        'unitree-primary': '#00E8DA',
        'unitree-secondary': '#00B8AD',
        // ... etc
      }
    }
  }
}
```

Usage example:
```html
<div class="bg-unitree-primary text-unitree-dark">
  Hello Unitree!
</div>
```

## Development Workflow

1. Edit HTML templates in `templates/`
2. Run `build-css.ps1 -Watch` (Windows) or `./build-css.sh --watch` (Linux/macOS)
3. Tailwind will automatically rebuild CSS when you save changes
4. Refresh your browser to see changes

## Production Build

Before deploying, build minified CSS:

**Windows:**
```powershell
.\build-css.ps1 -Minify
```

**Linux/macOS:**
```bash
./build-css.sh --minify
```

This generates a smaller `static/css/tailwind.output.css` file optimized for production.

## Troubleshooting

### "tailwindcss.exe is not recognized"
- Make sure you're in the project root directory
- Run the build script which will auto-download the CLI

### "Permission denied" (Linux/macOS)
```bash
chmod +x tailwindcss
chmod +x build-css.sh
```

### CSS not updating
- Make sure you're running the build script
- Check that `tailwind.output.css` was generated
- Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)

### Offline usage
Once you've downloaded `tailwindcss.exe` (or `tailwindcss` on Linux/macOS) and built the CSS, the application works completely offline. No internet connection is required.

