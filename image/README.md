# H743Poten-Web Image Assets

This folder contains diagram source files and generated images for the H743 Potentiostat project.

## DOT Files (Source)

- `transfer_calibration.dot` - Transfer calibration concept diagram
- `system_architecture.dot` - Overall system architecture
- `calibration_workflow.dot` - Step-by-step calibration process

## Generated Images

Run `generate_diagrams.bat` (Windows) to create:
- PNG files (web/screen display)
- SVG files (scalable vector graphics)
- PDF files (documentation/printing)

## Requirements

- [Graphviz](https://graphviz.org/download/) must be installed and in your PATH

## Usage

### Windows:
```cmd
cd "D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\image"
generate_diagrams.bat
```

### Manual generation:
```cmd
dot -Tpng transfer_calibration.dot -o transfer_calibration.png
dot -Tsvg system_architecture.dot -o system_architecture.svg
dot -Tpdf calibration_workflow.dot -o calibration_workflow.pdf
```

## Integration

These images can be used in:
- Web interface (`../templates/` HTML files)
- Documentation (Jupyter notebooks, README files)
- Presentations and reports
- Technical documentation

## Customization

Edit the `.dot` files to modify:
- Colors: Change `fillcolor` and `color` attributes
- Layout: Modify `rankdir` (TB=top-bottom, LR=left-right)
- Fonts: Adjust `fontname` and `fontsize`
- Shapes: Change `shape` attribute (box, ellipse, diamond, etc.)

## File Organization

```
image/
├── *.dot           # Source diagram files
├── *.png           # Raster images (web display)
├── *.svg           # Vector images (scalable)
├── *.pdf           # Print-ready documents
├── generate_diagrams.bat
└── README.md       # This file
```
