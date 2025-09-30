#!/bin/bash

# Create a simple app icon using ImageMagick (if available)
if command -v convert &> /dev/null; then
    # Create a simple 64x64 icon with chemistry theme
    convert -size 64x64 xc:blue \
        -fill white -pointsize 20 -gravity center \
        -annotate +0+0 'H743' \
        -fill yellow -pointsize 12 -gravity south \
        -annotate +0+5 'Poten' \
        /home/koson/H743Poten-Desktop/app_icon.png
    echo "✅ App icon created"
else
    # Create a placeholder icon file
    echo "⚠️  ImageMagick not found, creating placeholder icon"
    touch /home/koson/H743Poten-Desktop/app_icon.png
fi
