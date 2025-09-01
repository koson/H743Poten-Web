#!/bin/bash

# 🛠️ Repository Problem Fixer
# Fixes common Git repository issues for cross-platform compatibility

echo "🔧 H743 Potentiostat Repository Problem Fixer"
echo "============================================"

# Function to remove problematic directories
remove_problematic_dirs() {
    echo "🗑️  Removing problematic directories..."
    
    # Remove D: directory variants (Windows drive letter conflicts)
    if [ -d "D:" ]; then
        rm -rf "D:"
        echo "   ✅ Removed D: directory"
    fi
    
    if [ -d "D" ]; then
        rm -rf "D"
        echo "   ✅ Removed D directory"
    fi
    
    # Remove other problematic paths
    if [ -d "C:" ]; then
        rm -rf "C:"
        echo "   ✅ Removed C: directory"
    fi
    
    # Remove Windows temporary files
    find . -name "Thumbs.db" -delete 2>/dev/null && echo "   ✅ Removed Thumbs.db files"
    find . -name ".DS_Store" -delete 2>/dev/null && echo "   ✅ Removed .DS_Store files"
    find . -name "*.tmp" -delete 2>/dev/null && echo "   ✅ Removed .tmp files"
}

# Function to clean Git cache
clean_git_cache() {
    echo "🧹 Cleaning Git cache..."
    
    # Remove cached entries for problematic files
    git rm --cached "D:" 2>/dev/null && echo "   ✅ Removed D: from Git cache"
    git rm --cached "D" 2>/dev/null && echo "   ✅ Removed D from Git cache"
    git rm --cached "C:" 2>/dev/null && echo "   ✅ Removed C: from Git cache"
    
    # Clean untracked files
    git clean -fd -e .env -e .venv -e venv 2>/dev/null
    echo "   ✅ Cleaned untracked files"
}

# Function to fix .gitignore
fix_gitignore() {
    echo "📝 Checking .gitignore..."
    
    # Check if .gitignore has absolute paths
    if grep -q "D:/" .gitignore 2>/dev/null; then
        echo "   ⚠️  Found absolute paths in .gitignore"
        echo "   🔧 Please run: git checkout HEAD -- .gitignore"
        echo "   📝 Or manually remove absolute paths from .gitignore"
    else
        echo "   ✅ .gitignore looks good"
    fi
}

# Function to check repository health
check_repo_health() {
    echo "🏥 Repository Health Check..."
    
    # Check for large files
    large_files=$(find . -type f -size +10M 2>/dev/null | grep -v .git | head -5)
    if [ -n "$large_files" ]; then
        echo "   ⚠️  Large files found:"
        echo "$large_files" | sed 's/^/      /'
    else
        echo "   ✅ No large files found"
    fi
    
    # Check for binary files in Git
    binary_count=$(git ls-files | xargs file | grep -c "binary" 2>/dev/null || echo "0")
    echo "   📊 Binary files in Git: $binary_count"
    
    # Check repository size
    repo_size=$(du -sh .git 2>/dev/null | cut -f1)
    echo "   📏 Repository size: $repo_size"
}

# Main execution
echo ""
echo "🚀 Starting repository cleanup..."
echo ""

# Step 1: Remove problematic directories
remove_problematic_dirs
echo ""

# Step 2: Clean Git cache
clean_git_cache
echo ""

# Step 3: Fix .gitignore
fix_gitignore
echo ""

# Step 4: Health check
check_repo_health
echo ""

# Final recommendations
echo "📋 RECOMMENDATIONS:"
echo "=================="
echo "1. 🔄 Run: git add . && git commit -m 'Fix: Remove problematic directories'"
echo "2. 🌐 Test pull/push on different machines"
echo "3. 🛡️  Keep .gitignore updated with proper ignore patterns"
echo "4. 🚫 Avoid creating directories with drive letters (C:, D:, etc.)"
echo "5. 💾 Use relative paths only in .gitignore"
echo ""

# Success message
echo "✅ Repository cleanup completed!"
echo "🍓 Ready for cross-platform Git operations"
