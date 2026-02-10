# Build Tailwind CSS for production
# This script builds the Tailwind CSS file from the input CSS

param(
    [switch]$Watch,
    [switch]$Minify
)

# Check if tailwindcss.exe exists
if (-not (Test-Path "tailwindcss.exe")) {
    Write-Host "Tailwind CSS CLI not found. Downloading..."
    $url = "https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe"
    try {
        Invoke-WebRequest -Uri $url -OutFile "tailwindcss.exe" -UseBasicParsing
        Write-Host "Download complete!"
    } catch {
        Write-Error "Failed to download Tailwind CSS CLI. Please download manually from:"
        Write-Error $url
        Write-Error "Save it as 'tailwindcss.exe' in the project root."
        exit 1
    }
}

# Build command
$inputFile = "static/css/tailwind.input.css"
$outputFile = "static/css/tailwind.output.css"
$configFile = "tailwind.config.js"

if ($Watch) {
    Write-Host "Building Tailwind CSS in watch mode..."
    & .\tailwindcss.exe -i $inputFile -o $outputFile -c $configFile --watch
} elseif ($Minify) {
    Write-Host "Building Tailwind CSS (minified)..."
    & .\tailwindcss.exe -i $inputFile -o $outputFile -c $configFile --minify
} else {
    Write-Host "Building Tailwind CSS..."
    & .\tailwindcss.exe -i $inputFile -o $outputFile -c $configFile
}

Write-Host "Build complete! Output: $outputFile"

