# Deployment Protection Guide

This document explains how we prevent broken code from reaching production.

---

## 🛡️ Protection Layers

### 1. **Local Pre-Commit Hooks** (Optional but Recommended)

Catches issues **before you commit**:
- Code formatting (Black, Prettier)
- Linting (Ruff for Python)
- Secret detection
- Large file checks

**Setup:**
```bash
pip install pre-commit
pre-commit install
```

Now every `git commit` will automatically run checks!

**Skip if urgent** (not recommended):
```bash
git commit --no-verify
```

---

### 2. **GitHub Actions CI** (Automatic)

Runs on **every push and pull request**:

#### Backend Tests:
- ✅ Python linting with Ruff
- ✅ Pytest test suite
- ✅ Code coverage tracking
- ✅ Database integration tests

#### Frontend Tests:
- ✅ TypeScript type checking
- ✅ Next.js build verification
- ✅ ESLint checks

#### Security Scans:
- ✅ Trivy vulnerability scanner
- ✅ TruffleHog secret detection
- ✅ Dependency audit

#### Docker:
- ✅ Docker build verification

**Where to see it:**
- GitHub: Go to your repo → "Actions" tab
- Status checks appear on pull requests
- ❌ Red X = Failed (don't merge!)
- ✅ Green check = Passed (safe to merge)

---

### 3. **Branch Protection Rules** (Recommended Setup)

Prevent direct pushes to `main`:

**How to set up on GitHub:**

1. Go to your repo → Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass
     - Select: `All Checks Passed`
   - ✅ Require branches to be up to date
   - ✅ Do not allow bypassing

**Result:** You can't accidentally push broken code to `main`!

---

### 4. **Development Workflow**

```bash
# 1. Create a feature branch
git checkout -b feature/my-new-feature

# 2. Make changes
# ... edit files ...

# 3. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: add new feature"

# 4. Push to GitHub
git push origin feature/my-new-feature

# 5. Open Pull Request on GitHub
# - CI tests run automatically
# - Review the results
# - Only merge if all checks pass ✅

# 6. Merge to main
# - Use GitHub's "Merge pull request" button
# - Delete feature branch after merge
```

---

## 🚨 What Happens if Tests Fail?

### On GitHub Actions:
1. You'll see a red ❌ on your PR
2. Click "Details" to see what failed
3. Fix the issue locally
4. Push again - CI runs automatically
5. When green ✅, you're safe to merge

### Example Failures:

**Python Import Error:**
```
ModuleNotFoundError: No module named 'app.utils.openai_client'
```
**Fix:** Make sure the file exists and imports are correct

**TypeScript Build Error:**
```
Type 'string | undefined' is not assignable to type 'string'
```
**Fix:** Add proper type checking or null handling

**Secret Detected:**
```
Found API key in commit: sk-proj-abc123...
```
**Fix:** Remove the secret, use environment variables instead

---

## 📊 Running Tests Locally

Before pushing, run tests yourself:

### Backend Tests:
```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend/app
```

### Frontend Build:
```bash
cd frontend

# Type check
npx tsc --noEmit

# Build
npm run build

# Lint
npm run lint
```

---

## 🔐 API Keys in CI

Your CI needs API keys to run tests. Here's how:

### GitHub Secrets (Recommended):

1. Go to repo → Settings → Secrets and variables → Actions
2. Add secrets:
   - `OPENAI_API_KEY` - Your OpenAI key
   - `RESEND_API_KEY` - Your Resend key

3. Reference in workflow:
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Important:**
- Secrets are encrypted and never shown in logs
- Use a separate API key for CI (not your production key)
- Set spending limits on CI keys

---

## 🎯 Quick Reference

### Safe to Merge When:
- ✅ All CI checks pass (green)
- ✅ Code review approved (if required)
- ✅ No conflicts with main branch
- ✅ You've tested locally

### DO NOT Merge If:
- ❌ Tests failing
- ❌ Security vulnerabilities found
- ❌ Build errors
- ❌ Secrets detected in code

---

## 🚀 Deployment Options

### Option 1: Manual Deployment
```bash
# After merge to main:
git checkout main
git pull
docker-compose up -d --build
```

### Option 2: Automated Deployment (Advanced)

Add to `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]  # Only deploy if tests pass

    steps:
      - name: Deploy to server
        # Your deployment script here
```

---

## 📈 Monitoring CI Status

**Check CI status:**
```bash
# See latest workflow runs
gh run list

# View specific run
gh run view <run-id>
```

**GitHub UI:**
- Repo homepage shows latest CI status
- Pull requests show check results
- Actions tab shows all runs

---

## 🎓 Best Practices

1. **Never skip tests** - `--no-verify` should be rare
2. **Fix failing tests immediately** - Don't merge broken code
3. **Keep tests fast** - Slow tests = developers skip them
4. **Test locally first** - Don't use CI as your primary test runner
5. **Use feature branches** - Never push directly to main
6. **Review your own PRs** - Catch obvious mistakes before others see them

---

## 🔄 CI/CD Pipeline Summary

```
Developer → Commit → Pre-commit Hooks → Push → GitHub Actions
                         ↓                            ↓
                   [Optional]                    [Required]
                         ↓                            ↓
                    Fail? Fix it              Pass? → PR Review
                                                      ↓
                                              Merge → Deploy
```

---

## 📞 Troubleshooting

### "CI is too slow"
- Reduce test scope
- Use caching (already configured)
- Run only changed tests

### "Tests pass locally, fail in CI"
- Check Python/Node versions match
- Verify environment variables
- Check for OS-specific code

### "Secret detected but it's not real"
- Add to `.secrets.baseline`
- Use `detect-secrets scan --baseline .secrets.baseline`

---

**Remember:** CI is your friend, not your enemy. It catches bugs before users do! 🐛→✅
