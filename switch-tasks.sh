#!/bin/bash

# Script to switch tasks.json based on platform
# Usage: ./switch-tasks.sh [windows|pi]

PLATFORM=$1
VSCODE_DIR=".vscode"

if [ -z "$PLATFORM" ]; then
    echo "Usage: $0 [windows|pi]"
    echo "Current platform tasks:"
    if [ -f "$VSCODE_DIR/tasks.json" ]; then
        echo "✅ tasks.json exists"
    else
        echo "❌ No tasks.json found"
    fi
    exit 1
fi

case $PLATFORM in
    "windows")
        if [ -f "$VSCODE_DIR/tasks-windows.json" ]; then
            cp "$VSCODE_DIR/tasks-windows.json" "$VSCODE_DIR/tasks.json"
            echo "✅ Switched to Windows tasks"
        else
            echo "❌ tasks-windows.json not found"
            exit 1
        fi
        ;;
    "pi")
        if [ -f "$VSCODE_DIR/tasks-raspberry-pi.json" ]; then
            cp "$VSCODE_DIR/tasks-raspberry-pi.json" "$VSCODE_DIR/tasks.json"
            echo "✅ Switched to Raspberry Pi tasks"
        else
            echo "❌ tasks-raspberry-pi.json not found"
            exit 1
        fi
        ;;
    *)
        echo "❌ Unknown platform: $PLATFORM"
        echo "Use 'windows' or 'pi'"
        exit 1
        ;;
esac
