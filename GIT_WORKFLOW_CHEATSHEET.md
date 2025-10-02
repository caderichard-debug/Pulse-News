# Git Workflow Cheat Sheet

## 🚀 Quick Reference for Safe Git Workflow

---

## The Safe Way (Recommended!)

### 1. Create Feature Branch

```bash
git checkout -b feature/my-fix
# or
git checkout -b fix/bug-name
# or
git checkout -b docs/update-readme
```

### 2. Make Changes

```bash
# Edit files...
# Test locally first!
```

### 3. Commit Changes

```bash
git add .
git commit -m "Fix: description of what you fixed"
```

### 4. Push to Branch (NOT main!)

```bash
git push -u origin feature/my-fix
```

**This triggers CI but doesn't affect main!** ✅

### 5. Create Pull Request

```bash
# Option A: GitHub CLI
gh pr create --title "Fix: my fix" --body "Description of changes"

# Option B: GitHub Web
# Go to your repo → "Pull requests" → "New pull request"
```

### 6. Wait for CI

All tests run automatically on your branch. Check status:

```bash
gh pr checks
# or view on GitHub PR page
```

### 7. Merge When Green

```bash
# Via CLI
gh pr merge --squash

# Or click "Merge pull request" on GitHub
```

### 8. Cleanup

```bash
git checkout main
git pull
git branch -d feature/my-fix  # Delete local branch
```

---

## Branch Naming Conventions

```bash
feature/  - New features
fix/      - Bug fixes
docs/     - Documentation
test/     - Test improvements
refactor/ - Code refactoring
chore/    - Maintenance tasks
```

Examples:
```bash
git checkout -b feature/email-notifications
git checkout -b fix/login-error
git checkout -b docs/api-documentation
git checkout -b test/add-unit-tests
```

---

## Common Commands

### See Current Branch

```bash
git branch
# or
git status
```

### Switch Branches

```bash
git checkout main
git checkout feature/my-branch
```

### See All Branches

```bash
git branch -a           # All branches
git branch -r           # Remote branches only
```

### Pull Latest Changes

```bash
git checkout main
git pull origin main
```

### Update Feature Branch with Latest Main

```bash
git checkout feature/my-branch
git merge main
# or
git rebase main
```

### Delete Branch

```bash
git branch -d feature/my-branch  # Local only
git push origin --delete feature/my-branch  # Remote
```

---

## Test Before Pushing

```bash
# Frontend
cd frontend
npm run build
npm run lint

# Backend
docker exec news_backend pytest /app/tests/ -v

# Full stack
docker-compose up -d --build
```

---

## Emergency: Undo Last Commit

```bash
# Keep changes, undo commit
git reset --soft HEAD~1

# Discard changes, undo commit
git reset --hard HEAD~1

# Already pushed? Revert instead
git revert HEAD
git push
```

---

## View Changes

```bash
git status              # Files changed
git diff                # Unstaged changes
git diff --staged       # Staged changes
git log --oneline       # Commit history
```

---

## Stash Changes (Save for Later)

```bash
# Save current work
git stash

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{0}
```

---

## GitHub CLI Quick Reference

```bash
# Install
brew install gh

# Login
gh auth login

# Create PR
gh pr create

# List PRs
gh pr list

# View PR
gh pr view

# Check CI status
gh pr checks

# Merge PR
gh pr merge --squash

# Close PR
gh pr close
```

---

## Complete Workflow Example

```bash
# 1. Start new feature
git checkout main
git pull
git checkout -b feature/new-feature

# 2. Work on feature
# ... make changes ...

# 3. Test locally
cd frontend && npm run build && cd ..
docker-compose up -d --build
docker exec news_backend pytest /app/tests/ -v

# 4. Commit
git add .
git commit -m "Add new feature"

# 5. Push to branch
git push -u origin feature/new-feature

# 6. Create PR and wait for CI
gh pr create --title "Add new feature"
gh pr checks

# 7. Merge when green
gh pr merge --squash

# 8. Cleanup
git checkout main
git pull
git branch -d feature/new-feature
```

---

## Commit Message Format

### Good Commit Messages

```
Fix: Resolve login authentication bug
Add: Email notification feature
Update: Improve error handling in API
Docs: Add API documentation
Test: Add unit tests for auth module
Refactor: Simplify user validation logic
```

### Bad Commit Messages

```
fixed stuff
update
changes
wip
.
```

### Format

```
<Type>: <Short description>

<Optional longer description>

<Optional issue reference>
```

Example:
```
Fix: Resolve CORS error in production

Updated CORS middleware to allow credentials
and handle preflight requests correctly.

Fixes #123
```

---

## Working with Forks

If you forked the repository:

```bash
# Add upstream remote
git remote add upstream https://github.com/original/repo.git

# Fetch upstream changes
git fetch upstream

# Merge upstream main into your main
git checkout main
git merge upstream/main
git push origin main
```

---

## Tips & Best Practices

1. **Never work directly on main** - Always use feature branches
2. **Pull before push** - Keep your branch up to date
3. **Test locally first** - Don't rely only on CI
4. **Write clear commit messages** - Your future self will thank you
5. **Keep commits atomic** - One logical change per commit
6. **Review your own PR** - Check the diff before requesting review
7. **Use draft PRs** - For work in progress
8. **Delete merged branches** - Keep your repo clean

---

## Help!

### I pushed to main by accident!

```bash
# If not pushed to GitHub yet
git reset --hard origin/main

# If already pushed and main is protected
# You're safe! The push will be rejected.

# If already pushed and main is NOT protected
# Create a PR to revert
git revert HEAD
git push
```

### I committed to wrong branch!

```bash
# Save the commit
git log  # Copy the commit hash

# Switch to correct branch
git checkout correct-branch

# Cherry-pick the commit
git cherry-pick <commit-hash>

# Go back to wrong branch and undo
git checkout wrong-branch
git reset --hard HEAD~1
```

### My branch is behind main!

```bash
git checkout feature/my-branch
git merge main
# Resolve any conflicts
git push
```

---

## Quick Links

- [Full Testing Guide](TESTING_CI_LOCALLY.md)
- [CI Fixes Summary](CI_FIXES_SUMMARY.md)
- [Email Testing](QUICK_EMAIL_TEST.md)

---

## Summary

✅ **Always use feature branches**
✅ **Test locally before pushing**
✅ **Use pull requests**
✅ **Wait for CI to pass**
✅ **Merge when green**
✅ **Keep main clean**

Your main branch should **always** be deployable! 🎯
