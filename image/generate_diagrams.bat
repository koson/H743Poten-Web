@echo off
REM Generate Images from DOT Files for H743Poten-Web Project
REM Navigate to image directory first

cd /d "D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\image"

echo Current directory: %CD%
echo Generating images from DOT files...

REM Check if dot command exists
where dot >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Graphviz dot command not found!
    echo Please install Graphviz from: https://graphviz.org/download/
    echo And add it to your PATH
    pause
    exit /b 1
)

REM Generate PNG images
if exist transfer_calibration.dot (
    echo Generating transfer_calibration.png...
    dot -Tpng transfer_calibration.dot -o transfer_calibration.png
)

if exist system_architecture.dot (
    echo Generating system_architecture.png...
    dot -Tpng system_architecture.dot -o system_architecture.png
)

if exist calibration_workflow.dot (
    echo Generating calibration_workflow.png...
    dot -Tpng calibration_workflow.dot -o calibration_workflow.png
)

REM Generate SVG images (scalable, good for web)
if exist transfer_calibration.dot (
    echo Generating transfer_calibration.svg...
    dot -Tsvg transfer_calibration.dot -o transfer_calibration.svg
)

if exist system_architecture.dot (
    echo Generating system_architecture.svg...
    dot -Tsvg system_architecture.dot -o system_architecture.svg
)

if exist calibration_workflow.dot (
    echo Generating calibration_workflow.svg...
    dot -Tsvg calibration_workflow.dot -o calibration_workflow.svg
)

REM Generate PDF images (good for documentation)
if exist transfer_calibration.dot (
    echo Generating transfer_calibration.pdf...
    dot -Tpdf transfer_calibration.dot -o transfer_calibration.pdf
)

if exist system_architecture.dot (
    echo Generating system_architecture.pdf...
    dot -Tpdf system_architecture.dot -o system_architecture.pdf
)

if exist calibration_workflow.dot (
    echo Generating calibration_workflow.pdf...
    dot -Tpdf calibration_workflow.dot -o calibration_workflow.pdf
)

echo.
echo All images generated successfully in: %CD%
echo.
echo Generated files:
dir *.png *.svg *.pdf 2>nul

echo.
echo You can now use these images in your documentation, web interface, or presentations.
pause
