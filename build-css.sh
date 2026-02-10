#!/bin/bash
# Build Tailwind CSS for production
# This script builds the Tailwind CSS file from the input CSS

WATCH=false
MINIFY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --watch)
            WATCH=true
            shift
            ;;
        --minify)
            MINIFY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Detect OS and download appropriate binary
if [ ! -f "tailwindcss" ]; then
    echo "Tailwind CSS CLI not found. Downloading..."
    
    OS=$(uname -s)
    ARCH=$(uname -m)
    
    case "$OS" in
        Linux)
            if [ "$ARCH" = "x86_64" ]; then
                URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64"
            elif [ "$ARCH" = "aarch64" ]; then
                URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-arm64"
            else
                echo "Unsupported architecture: $ARCH"
                exit 1
            fi
            ;;
        Darwin)
            if [ "$ARCH" = "x86_64" ]; then
                URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-x64"
            elif [ "$ARCH" = "arm64" ]; then
                URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64"
            else
                echo "Unsupported architecture: $ARCH"
                exit 1
            fi
            ;;
        *)
            echo "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    curl -sLo tailwindcss "$URL"
    chmod +x tailwindcss
    echo "Download complete!"
fi

# Build command
INPUT_FILE="static/css/tailwind.input.css"
OUTPUT_FILE="static/css/tailwind.output.css"
CONFIG_FILE="tailwind.config.js"

if [ "$WATCH" = true ]; then
    echo "Building Tailwind CSS in watch mode..."
    ./tailwindcss -i "$INPUT_FILE" -o "$OUTPUT_FILE" -c "$CONFIG_FILE" --watch
elif [ "$MINIFY" = true ]; then
    echo "Building Tailwind CSS (minified)..."
    ./tailwindcss -i "$INPUT_FILE" -o "$OUTPUT_FILE" -c "$CONFIG_FILE" --minify
else
    echo "Building Tailwind CSS..."
    ./tailwindcss -i "$INPUT_FILE" -o "$OUTPUT_FILE" -c "$CONFIG_FILE"
fi

echo "Build complete! Output: $OUTPUT_FILE"

