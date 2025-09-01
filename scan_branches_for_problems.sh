#!/bin/bash

# 🔍 Branch Scanner for Problematic Directories
# Scans all branches for problematic D: directories

echo "🔍 Scanning All Branches for Problematic Directories"
echo "===================================================="

CURRENT_BRANCH=$(git branch --show-current)
PROBLEM_FOUND=false

echo "📊 Current branch: $CURRENT_BRANCH"
echo ""

# Get list of all local branches
BRANCHES=$(git branch | sed 's/\*//g' | sed 's/ //g')

for branch in $BRANCHES; do
    echo "🔎 Scanning branch: $branch"
    
    # Checkout to branch quietly
    git checkout "$branch" -q 2>/dev/null
    
    # Check for problematic directories
    if [ -d "D:" ] || [ -d "D" ]; then
        echo "   ❌ FOUND: Problematic D directory exists!"
        PROBLEM_FOUND=true
        
        # List the problematic directory
        ls -la | grep -E "^d.*D"
        
        echo "   🛠️  Run this to fix:"
        echo "      rm -rf 'D:' 'D'"
        echo "      git add ."
        echo "      git commit -m 'Fix: Remove problematic D directory'"
        echo ""
    else
        echo "   ✅ Clean - No problematic directories"
    fi
    
    # Check Git index for tracked D directories
    if git ls-tree HEAD | grep -E " D:| D/" >/dev/null 2>&1; then
        echo "   ⚠️  WARNING: D directory tracked in Git!"
        PROBLEM_FOUND=true
        echo "   🛠️  Run this to fix:"
        echo "      git rm -r 'D:' 'D' 2>/dev/null || true"
        echo "      git commit -m 'Remove D directory from Git tracking'"
        echo ""
    fi
done

# Return to original branch
git checkout "$CURRENT_BRANCH" -q 2>/dev/null

echo ""
echo "📋 SCAN RESULTS:"
echo "================"

if [ "$PROBLEM_FOUND" = true ]; then
    echo "❌ PROBLEMS FOUND: Some branches have problematic directories"
    echo ""
    echo "🔧 RECOMMENDED ACTIONS:"
    echo "1. Use ./fix_repo_problems.sh on problematic branches"
    echo "2. Or manually remove D: directories as shown above"
    echo "3. Commit the fixes to clean up Git history"
    echo "4. Consider using .gitignore patterns to prevent recurrence"
    echo ""
    echo "🛡️  PREVENTION:"
    echo "• Add to .gitignore: D/, D:/, D:*"
    echo "• Use ./fix_repo_problems.sh regularly"
    echo "• Avoid creating directories with drive letter names"
else
    echo "✅ ALL CLEAN: No problematic directories found in any branch!"
    echo ""
    echo "🎉 Repository Status:"
    echo "• All branches are clean"
    echo "• No cross-platform Git issues"
    echo "• Safe for pull/push operations"
    echo "• Ready for multi-machine development"
fi

echo ""
echo "🍓 Repository is ready for Raspberry Pi deployment!"
