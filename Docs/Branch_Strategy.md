# Branch Strategy for Microservices Migration

**Document Version:** 1.0  
**Date:** October 1, 2025  
**Related Documents:** Architecture_Analysis_2025.md, Microservices_Migration_Plan.md  

---

## 🌳 Git Branch Structure

This document defines the branching strategy for the microservices migration project, ensuring organized development and safe integration.

---

## 📋 Branch Naming Convention

### Main Branches
```
main                    # Production-ready code
├── development         # Integration branch for all features  
└── staging            # Pre-production testing branch
```

### Feature Branches
```
feature/microservices-migration          # Main migration branch
├── foundation/service-registry          # Service discovery implementation
├── foundation/api-gateway              # Central routing service
├── foundation/docker-setup             # Containerization
├── foundation/monitoring               # Logging & health checks
├── services/hardware-service           # Hardware communication layer
├── services/cv-service                # CV measurement service
├── services/dpv-service               # DPV measurement service  
├── services/swv-service               # SWV measurement service
├── services/ca-service                # CA measurement service
├── services/data-service              # Data storage & export
├── frontend/spa-conversion            # Single Page Application
├── testing/integration-tests          # Cross-service testing
├── docs/architecture-updates          # Documentation updates
└── deployment/production-config       # Production deployment
```

### Hotfix Branches
```
hotfix/critical-bug-fix        # Critical production fixes
hotfix/security-patch          # Security vulnerabilities
```

---

## 🔄 Branch Workflow

### 1. Migration Branch Creation
```bash
# Create main migration branch from development
git checkout development
git pull origin development
git checkout -b feature/microservices-migration
git push -u origin feature/microservices-migration

# Set up branch protection rules
# - Require pull request reviews
# - Require status checks to pass
# - Require branches to be up to date
# - Restrict pushes to this branch
```

### 2. Phase-based Development
```bash
# Phase 1: Foundation
git checkout feature/microservices-migration
git checkout -b foundation/service-registry
# Implement service registry
git add .
git commit -m "feat: implement service registry with health checks"
git push -u origin foundation/service-registry

# Create pull request to feature/microservices-migration
# After review and approval, merge
git checkout feature/microservices-migration
git merge foundation/service-registry
git push origin feature/microservices-migration
```

### 3. Service Development
```bash
# Each service in separate branch
git checkout feature/microservices-migration
git checkout -b services/hardware-service

# Implement hardware service
git add .
git commit -m "feat: extract hardware service with WebSocket support"
git push -u origin services/hardware-service

# Pull request → review → merge to feature/microservices-migration
```

### 4. Integration Testing
```bash
# Regular integration with main migration branch
git checkout feature/microservices-migration
git pull origin feature/microservices-migration

# Run integration tests
docker-compose -f docker-compose.dev.yml up -d
npm run test:integration
python -m pytest tests/integration/

# If tests pass, continue development
# If tests fail, fix issues before merging more features
```

---

## 📊 Branch Management Strategy

### Merge Strategy
```yaml
Branch Type: foundation/*
Target: feature/microservices-migration
Strategy: Squash and merge
Required Reviews: 2
Required Checks: 
  - Unit tests pass
  - Code coverage > 80%
  - Docker build successful

Branch Type: services/*
Target: feature/microservices-migration  
Strategy: Merge commit
Required Reviews: 1
Required Checks:
  - Service tests pass
  - API contract tests pass
  - Integration tests pass

Branch Type: feature/microservices-migration
Target: development
Strategy: Merge commit
Required Reviews: 3
Required Checks:
  - All service tests pass
  - Integration tests pass
  - Performance tests pass
  - Security scan pass
```

### Branch Protection Rules
```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "ci/unit-tests",
      "ci/integration-tests", 
      "ci/docker-build",
      "ci/security-scan"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_reviewing_teams": ["h743poten-dev-team"],
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": {
    "users": [],
    "teams": ["h743poten-dev-team"]
  }
}
```

---

## 🚀 Migration Milestones

### Milestone 1: Foundation Complete (Week 8)
```bash
# Merge foundation branches to migration branch
git checkout feature/microservices-migration
git merge foundation/service-registry
git merge foundation/api-gateway  
git merge foundation/docker-setup
git merge foundation/monitoring

# Tag milestone
git tag -a v2.0.0-alpha.1 -m "Foundation infrastructure complete"
git push origin v2.0.0-alpha.1
```

### Milestone 2: Hardware Service (Week 16)
```bash
git merge services/hardware-service
git tag -a v2.0.0-alpha.2 -m "Hardware service extraction complete"
git push origin v2.0.0-alpha.2
```

### Milestone 3: All Services (Week 32)
```bash
git merge services/cv-service
git merge services/dpv-service
git merge services/swv-service
git merge services/ca-service
git merge services/data-service
git tag -a v2.0.0-beta.1 -m "All services extracted"
git push origin v2.0.0-beta.1
```

### Milestone 4: Production Ready (Week 40)
```bash
git merge frontend/spa-conversion
git merge deployment/production-config
git tag -a v2.0.0-rc.1 -m "Release candidate 1"
git push origin v2.0.0-rc.1

# After testing period
git checkout development
git merge feature/microservices-migration
git tag -a v2.0.0 -m "Microservices architecture complete"
git push origin v2.0.0
```

---

## 🔍 Quality Gates

### Pre-merge Checklist
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code coverage ≥ 80%
- [ ] No security vulnerabilities
- [ ] API documentation updated
- [ ] Performance benchmarks met
- [ ] Code review approved

### Automated Checks
```yaml
# .github/workflows/microservices-ci.yml
name: Microservices CI

on:
  pull_request:
    branches: [ feature/microservices-migration ]
  push:
    branches: [ feature/microservices-migration ]

jobs:
  test-foundation:
    if: contains(github.head_ref, 'foundation/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run foundation tests
        run: |
          python -m pytest tests/foundation/
          
  test-services:
    if: contains(github.head_ref, 'services/')
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [hardware, cv, dpv, swv, ca, data]
    steps:
      - uses: actions/checkout@v3
      - name: Test ${{ matrix.service }} service
        run: |
          cd services/${{ matrix.service }}-service
          python -m pytest tests/
          
  integration-test:
    runs-on: ubuntu-latest
    needs: [test-foundation, test-services]
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: |
          docker-compose -f docker-compose.test.yml up -d
          python -m pytest tests/integration/
          docker-compose -f docker-compose.test.yml down
```

---

## 🛡️ Risk Management

### Branch Conflicts
**Risk:** Multiple developers working on related code  
**Mitigation:**
- Regular synchronization with migration branch
- Clear component ownership
- Communication in pull requests

```bash
# Daily sync routine
git checkout feature/microservices-migration
git pull origin feature/microservices-migration
git checkout services/cv-service
git rebase feature/microservices-migration
```

### Failed Migrations
**Risk:** Service extraction breaks existing functionality  
**Mitigation:**
- Feature flags for gradual rollout
- Parallel running of old and new systems  
- Rollback procedures

```python
# Feature flag example
ENABLE_MICROSERVICES = os.getenv('ENABLE_MICROSERVICES', 'false').lower() == 'true'

if ENABLE_MICROSERVICES:
    from services.microservices_handler import MicroservicesHandler
    handler = MicroservicesHandler()
else:
    from services.monolithic_handler import MonolithicHandler  
    handler = MonolithicHandler()
```

### Data Loss
**Risk:** Migration process corrupts or loses data  
**Mitigation:**
- Comprehensive backup procedures
- Database migration scripts with rollback
- Data validation after migration

---

## 📋 Team Assignments

### Foundation Team
- **Lead:** Senior Backend Developer
- **Members:** 2 developers
- **Branches:** foundation/*
- **Duration:** Weeks 1-8

### Services Team  
- **Lead:** Full-stack Developer
- **Members:** 3 developers
- **Branches:** services/*
- **Duration:** Weeks 9-32

### Frontend Team
- **Lead:** Frontend Developer  
- **Members:** 2 developers
- **Branches:** frontend/*
- **Duration:** Weeks 33-40

### DevOps Team
- **Lead:** DevOps Engineer
- **Members:** 1 developer
- **Branches:** deployment/*
- **Duration:** Throughout project

---

## 📝 Branch Commands Quick Reference

### Setup Commands
```bash
# Clone and setup
git clone <repository-url>
cd h743poten-web
git checkout -b feature/microservices-migration

# Create service branch
git checkout feature/microservices-migration
git checkout -b services/cv-service
```

### Development Commands
```bash
# Regular development cycle
git add .
git commit -m "feat: implement CV parameter validation"
git push origin services/cv-service

# Sync with main migration branch
git checkout feature/microservices-migration
git pull origin feature/microservices-migration
git checkout services/cv-service
git rebase feature/microservices-migration
```

### Merge Commands
```bash
# Merge service to migration branch
git checkout feature/microservices-migration
git merge services/cv-service
git push origin feature/microservices-migration

# Delete merged branch
git branch -d services/cv-service
git push origin --delete services/cv-service
```

### Emergency Commands
```bash
# Hotfix from main
git checkout main
git checkout -b hotfix/critical-hardware-bug
# Fix and test
git checkout main
git merge hotfix/critical-hardware-bug
git push origin main

# Apply hotfix to migration branch
git checkout feature/microservices-migration  
git cherry-pick <hotfix-commit-hash>
git push origin feature/microservices-migration
```

---

**Document Status:** ✅ Ready for Implementation  
**Next Review:** October 8, 2025  
**Branch Creation Date:** October 1, 2025