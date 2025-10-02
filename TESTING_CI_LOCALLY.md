# Testing CI Flow Locally

This guide shows you how to test your CI pipeline locally before pushing to GitHub, and how to use the PR workflow safely.

---

## Option 1: Test CI Locally with `act`

### Install `act` (GitHub Actions locally)

```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (with Chocolatey)
choco install act-cli
```

### Run CI Locally

```bash
# Test all jobs
act

# Test specific job
act -j backend-tests
act -j frontend-tests
act -j docker-build

# Test on push event
act push

# Test on pull request event
act pull_request
```

### Run with secrets

```bash
# Create .secrets file
cat > .secrets << EOF
OPENAI_API_KEY=sk-proj-your-key-here
EOF

# Run with secrets
act --secret-file .secrets
```

**Note**: `act` uses Docker, so it's close to real GitHub Actions but not 100% identical.

---

## Option 2: Test Individual CI Steps Locally

### Backend Tests

```bash
# Activate virtual environment (or use Docker)
cd backend

# Install dependencies
pip install -r ../requirements.txt
pip install pytest pytest-cov

# Run tests
export DATABASE_URL=postgresql://postgres:password@localhost:5432/news_db
export SECRET_KEY=test-secret-key
pytest tests/ -v --cov=app --cov-report=xml

# Lint
pip install ruff
ruff check . --select E,F,W
```

### Frontend Tests

```bash
cd frontend

# Install dependencies
npm ci

# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build
```

### Docker Build

```bash
# Test backend Docker build
docker build -f dockerfile -t pulse-backend:test .

# Test full compose stack
docker-compose build
docker-compose up -d
docker-compose ps
docker-compose down
```

### Security Scans

```bash
# Install Trivy
brew install aquasecurity/trivy/trivy  # macOS
# or download from https://github.com/aquasecurity/trivy/releases

# Run vulnerability scan
trivy fs .

# Scan specific directories
trivy fs backend/ --severity CRITICAL,HIGH
trivy fs frontend/ --severity CRITICAL,HIGH

# Scan Docker image
trivy image pulse-backend:latest
```

---

## Option 3: Use Git Branches + Pull Requests (Recommended!)

This is the **safest** way to test CI before merging to main.

### Step 1: Create a Feature Branch

```bash
# Create and switch to new branch
git checkout -b feature/fix-ci-errors

# Or separate commands
git branch feature/fix-ci-errors
git checkout feature/fix-ci-errors
```

### Step 2: Make Your Changes

```bash
# Make changes to code
# Edit files...

# Stage changes
git add .

# Commit
git commit -m "Fix CI/CD errors and configure Resend"
```

### Step 3: Push to Branch (NOT main!)

```bash
# Push to your feature branch
git push origin feature/fix-ci-errors

# If first time pushing this branch
git push -u origin feature/fix-ci-errors
```

**This triggers CI but doesn't affect main!** ✅

### Step 4: Create Pull Request

#### Via GitHub CLI

```bash
# Install GitHub CLI
brew install gh  # macOS
# or download from https://cli.github.com/

# Login
gh auth login

# Create PR
gh pr create --title "Fix CI/CD errors" --body "
## Changes
- Fixed TypeScript/ESLint errors
- Configured Resend test domain
- Fixed GitHub Actions workflow

## Testing
- ✅ All tests passing (32/32)
- ✅ Frontend builds successfully
- ✅ Docker build working
"

# View PR status
gh pr status

# Check CI status
gh pr checks
```

#### Via GitHub Web UI

1. Go to your repository on GitHub
2. Click **"Pull requests"** tab
3. Click **"New pull request"**
4. Select:
   - **Base**: `main` (what you're merging INTO)
   - **Compare**: `feature/fix-ci-errors` (your branch)
5. Click **"Create pull request"**
6. Fill in title and description
7. Click **"Create pull request"**

### Step 5: Wait for CI to Run

GitHub Actions will automatically:
1. ✅ Run backend tests
2. ✅ Run frontend build
3. ✅ Run security scans
4. ✅ Test Docker build

You can see results in the PR under **"Checks"** tab.

### Step 6: Merge When Green

Once all checks pass:

```bash
# Merge via CLI
gh pr merge --squash  # Squash commits
gh pr merge --merge   # Regular merge
gh pr merge --rebase  # Rebase

# Or use GitHub web UI
# Click "Merge pull request" button
```

---

## Option 4: Draft Pull Requests

Create a **draft PR** to run CI without making it ready for review:

```bash
# Create draft PR
gh pr create --draft --title "WIP: Testing CI fixes"

# When ready, mark as ready for review
gh pr ready
```

Or on GitHub web UI:
1. When creating PR, click dropdown on **"Create pull request"**
2. Select **"Create draft pull request"**

---

## Option 5: Protected Main Branch (Best Practice!)

Prevent direct pushes to main:

### Via GitHub Web UI

1. Go to **Settings** → **Branches**
2. Click **"Add rule"**
3. Branch name pattern: `main`
4. Check:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
   - ✅ **Require branches to be up to date before merging**
5. Select required checks:
   - ✅ `backend-tests`
   - ✅ `frontend-tests`
   - ✅ `docker-build`
6. Click **"Create"**

Now you **can't** push directly to main - must use PRs! ✅

---

## Complete Local Testing Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-changes

# 2. Make changes
# ... edit files ...

# 3. Test locally BEFORE committing
cd frontend && npm run build && cd ..  # Test frontend
docker-compose up -d --build           # Test full stack
docker exec news_backend pytest /app/tests/ -v  # Test backend

# 4. If tests pass locally, commit
git add .
git commit -m "My changes"

# 5. Push to branch (triggers CI on GitHub)
git push -u origin feature/my-changes

# 6. Create PR
gh pr create --title "My changes"

# 7. Wait for CI to pass on GitHub
gh pr checks

# 8. If CI passes, merge
gh pr merge --squash

# 9. Delete branch
git checkout main
git pull
git branch -d feature/my-changes
```

---

## Quick Reference

### Test Everything Locally

```bash
# Backend
docker exec news_backend pytest /app/tests/ -v

# Frontend
cd frontend && npm run build

# Docker
docker-compose build

# Full stack
docker-compose up -d
```

### Safe Push Workflow

```bash
# SAFE: Push to branch (doesn't affect main)
git checkout -b feature/my-fix
git push origin feature/my-fix

# UNSAFE: Push directly to main (skip this!)
# git push origin main  ❌ Don't do this!
```

### PR Workflow

```bash
# Create branch → Push → PR → Wait for CI → Merge
git checkout -b feature/fix
git push -u origin feature/fix
gh pr create
gh pr checks  # Wait for green ✅
gh pr merge --squash
```

---

## Best Practices

1. **Always use feature branches** - Never work directly on `main`
2. **Test locally first** - Catch issues before pushing
3. **Use PRs** - Let CI validate before merging
4. **Protect main branch** - Require PR + passing CI
5. **Use draft PRs** - Run CI without requesting review

---

## Troubleshooting

### `act` not working?

```bash
# Use smaller Docker image
act -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Skip Docker
act --container-architecture linux/amd64
```

### CI passes locally but fails on GitHub?

Common causes:
- Different Node/Python versions
- Missing environment variables
- Different file paths (case sensitivity)
- Cache issues

Solution: Check versions match:
```yaml
# .github/workflows/ci.yml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'  # Match your local version
```

### Can't push to main?

Good! That means branch protection is working. Use a PR instead:
```bash
git checkout -b feature/my-fix
git push origin feature/my-fix
gh pr create
```

---

## Summary

**Safest Workflow**:
1. ✅ Test locally first
2. ✅ Push to feature branch
3. ✅ Create PR
4. ✅ Let CI run on GitHub
5. ✅ Merge when green
6. ✅ Never push directly to main

This way, your main branch is **always** in a working state! 🎯

---

## ⚠️ Known Issues with `act`

### Port Conflicts

If you get "port is already allocated" errors:

```bash
# Stop local Docker Compose first
docker-compose down

# Then run act
act -j frontend-tests  # Works without DB
act -j docker-build    # Works independently

# Backend tests need PostgreSQL on port 5432
# Will conflict if your local DB is running
act -j backend-tests   # May fail locally

# Restart local services after testing
docker-compose up -d
```

**Recommendation**: Use `act` only for frontend and Docker tests. Use GitHub Actions for full integration tests.


### Security Scan Issues

Security scans (Trivy, TruffleHog) may fail with `act` due to missing tokens:

```bash
# Skip security scans when testing locally
act --job frontend-tests
act --job backend-tests
act --job docker-build

# Don't run: act --job security-scan
```

Security scans will run properly on GitHub Actions - no local testing needed.

