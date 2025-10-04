# 📚 H743Poten Research Worktree

## 🎯 Purpose
This is a **Git Worktree** dedicated to research and paper writing, based on the `feature/peak-detection-framework` branch.

## 🔬 What's Here
- **DeepCV Algorithm**: Complete implementation in `validation_data/peak_detection_framework.py`
- **Research Documentation**: Analysis notebooks, papers, and validation data
- **Historical Implementations**: All peak detection algorithms for comparison

## 📂 Key Files

### DeepCV Implementation
```
validation_data/
├── peak_detection_framework.py    # Main: DeepCV + TraditionalCV + HybridCV
├── execute_validation_fixed.py    # Validation runner
├── config.py                       # Configuration
└── README.md                       # Documentation
```

### Classes Available
1. **DeepCVAnalyzer** (Line 236-468)
   - Neural network-based peak detection
   - MLPRegressor with layers (100, 50, 25)
   - Feature extraction pipeline
   - Training data accumulation

2. **TraditionalCVAnalyzer** (Line 75-236)
   - SciPy signal processing
   - Baseline correction
   - Prominence-based detection

3. **HybridCVAnalyzer** (Line 469-584)
   - Combines DeepCV + TraditionalCV
   - Ensemble approach

## 🚀 How to Use

### For Research Analysis
```bash
cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Research

# Run validation
python validation_data/execute_validation_fixed.py

# Analyze DeepCV
jupyter notebook Docs/Algorithm_Analysis_DeepCV.ipynb
```

### For Paper Writing
- All algorithm implementations are here
- Can reference specific commit: `8f4a89b`
- Branch: `feature/peak-detection-framework`

## 🔄 Relationship with Production

### This Worktree (Research)
- Branch: `feature/peak-detection-framework`
- Purpose: Research, analysis, paper writing
- Has: DeepCV, TraditionalCV, HybridCV implementations
- Status: **Read-only for paper reference**

### Main Worktree (Production)
- Branch: `migrate-to-dotnet`
- Purpose: C# migration, production development
- Has: Simplified peak detection for production use
- Status: **Active development**

## 📊 Git Worktree Commands

```bash
# List all worktrees
git worktree list

# Switch to production worktree
cd ../H743Poten-Web

# Cherry-pick commit from production to research
git cherry-pick <commit-hash>

# Create tags for paper versions
git tag -a paper-v1.0 -m "Code snapshot for paper"
```

## ⚠️ Important Notes

1. **Don't modify production code here** - Use main worktree for that
2. **Can commit research findings** - This is your research space
3. **Shared Git history** - Both worktrees use same `.git`
4. **No conflicts** - Each worktree has its own working directory

## 🎓 For Paper Citations

```bibtex
@software{h743poten_deepcv,
  title = {DeepCV Peak Detection Framework},
  author = {H743Poten Research Team},
  year = {2025},
  version = {1.0},
  commit = {8f4a89b},
  branch = {feature/peak-detection-framework},
  file = {validation_data/peak_detection_framework.py}
}
```

## 📝 Next Steps

1. ✅ **Analyze DeepCV implementation** - Ready in this worktree
2. ⏳ **Document TraditionalCV algorithms** - Use production worktree
3. ⏳ **Write methodology section** - Reference both worktrees
4. ⏳ **Generate performance benchmarks** - Run validation scripts

---

**Branch**: `feature/peak-detection-framework` @ commit `8f4a89b`  
**Created**: October 3, 2025  
**Purpose**: Research and academic paper preparation
