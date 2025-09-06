#!/bin/bash

# Generate Transfer Calibration Diagrams - Updated Version
# This script generates all diagrams including the new workflow

echo "=== Transfer Calibration Diagram Generation ==="
echo "Starting diagram generation..."

# Change to image directory
cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/image

# Check if graphviz is available
if ! command -v dot &> /dev/null; then
    echo "Error: Graphviz not found. Installing..."
    sudo apt update && sudo apt install -y graphviz
fi

# Generate all diagrams
echo ""
echo "Generating diagrams..."

# 1. Transfer Calibration Concept
if [ -f "transfer_calibration.dot" ]; then
    echo "📊 Generating transfer_calibration diagrams..."
    dot -Tpng transfer_calibration.dot -o transfer_calibration.png
    dot -Tsvg transfer_calibration.dot -o transfer_calibration.svg
    echo "   ✅ transfer_calibration.png"
    echo "   ✅ transfer_calibration.svg"
else
    echo "   ❌ transfer_calibration.dot not found"
fi

# 2. System Architecture
if [ -f "system_architecture.dot" ]; then
    echo "🏗️  Generating system_architecture diagrams..."
    dot -Tpng system_architecture.dot -o system_architecture.png
    dot -Tsvg system_architecture.dot -o system_architecture.svg
    echo "   ✅ system_architecture.png"
    echo "   ✅ system_architecture.svg"
else
    echo "   ❌ system_architecture.dot not found"
fi

# 3. Calibration Workflow
if [ -f "calibration_workflow.dot" ]; then
    echo "⚙️  Generating calibration_workflow diagrams..."
    dot -Tpng calibration_workflow.dot -o calibration_workflow.png
    dot -Tsvg calibration_workflow.dot -o calibration_workflow.svg
    echo "   ✅ calibration_workflow.png"
    echo "   ✅ calibration_workflow.svg"
else
    echo "   ❌ calibration_workflow.dot not found"
fi

# 4. NEW: Transfer Calibration Implementation Workflow
if [ -f "transfer_calibration_workflow.dot" ]; then
    echo "🚀 Generating transfer_calibration_workflow diagrams..."
    dot -Tpng transfer_calibration_workflow.dot -o transfer_calibration_workflow.png
    dot -Tsvg transfer_calibration_workflow.dot -o transfer_calibration_workflow.svg
    dot -Tpdf transfer_calibration_workflow.dot -o transfer_calibration_workflow.pdf
    echo "   ✅ transfer_calibration_workflow.png"
    echo "   ✅ transfer_calibration_workflow.svg"
    echo "   ✅ transfer_calibration_workflow.pdf"
else
    echo "   ❌ transfer_calibration_workflow.dot not found"
fi

echo ""
echo "=== Generation Summary ==="
echo "Generated files:"
ls -la *.png *.svg *.pdf 2>/dev/null | grep -E '\.(png|svg|pdf)$' || echo "No output files found"

echo ""
echo "=== File Sizes ==="
du -h *.png *.svg *.pdf 2>/dev/null | sort -hr || echo "No files to check"

echo ""
echo "✅ Diagram generation completed!"
echo "📁 Location: $(pwd)"
echo ""
echo "🎯 New Implementation Workflow diagram added:"
echo "   - transfer_calibration_workflow.png (for presentations)"
echo "   - transfer_calibration_workflow.svg (for web)"
echo "   - transfer_calibration_workflow.pdf (for documents)"
