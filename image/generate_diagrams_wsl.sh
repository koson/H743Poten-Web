#!/bin/bash

# Generate Images from DOT Files for H743Poten-Web Project
# WSL Version

# Convert Windows path to WSL path
IMAGE_DIR="/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/image"

echo "Navigating to image directory..."
cd "$IMAGE_DIR" || {
    echo "Error: Cannot navigate to $IMAGE_DIR"
    echo "Please check if the path exists"
    exit 1
}

echo "Current directory: $(pwd)"
echo "Generating images from DOT files..."

# Check if dot command exists
if ! command -v dot &> /dev/null; then
    echo "Error: Graphviz dot command not found!"
    echo "Please install Graphviz in WSL:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install graphviz"
    exit 1
fi

echo "Graphviz version: $(dot -V 2>&1)"

# Function to generate image if dot file exists
generate_image() {
    local dotfile="$1"
    local format="$2"
    local extension="$3"
    
    if [ -f "$dotfile" ]; then
        local output="${dotfile%.*}.$extension"
        echo "Generating $output..."
        if dot -T$format "$dotfile" -o "$output"; then
            echo "  ✓ Success: $output"
        else
            echo "  ✗ Failed: $output"
        fi
    else
        echo "  ⚠ File not found: $dotfile"
    fi
}

echo
echo "=== Generating PNG images (for web/screen display) ==="
generate_image "transfer_calibration.dot" "png" "png"
generate_image "system_architecture.dot" "png" "png"
generate_image "calibration_workflow.dot" "png" "png"

echo
echo "=== Generating SVG images (scalable vector graphics) ==="
generate_image "transfer_calibration.dot" "svg" "svg"
generate_image "system_architecture.dot" "svg" "svg"
generate_image "calibration_workflow.dot" "svg" "svg"

echo
echo "=== Generating PDF images (for documentation/printing) ==="
generate_image "transfer_calibration.dot" "pdf" "pdf"
generate_image "system_architecture.dot" "pdf" "pdf"
generate_image "calibration_workflow.dot" "pdf" "pdf"

echo
echo "=== Generation Complete ==="
echo "Generated files in: $(pwd)"
echo
echo "File listing:"
ls -la *.png *.svg *.pdf 2>/dev/null | grep -E '\.(png|svg|pdf)$' || echo "No generated files found"

echo
echo "You can now use these images in your documentation, web interface, or presentations."
