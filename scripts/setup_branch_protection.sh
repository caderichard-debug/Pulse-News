#!/bin/bash
# Script to set up branch protection for main branch using GitHub CLI

set -e

echo "🔒 Setting up branch protection for main branch"
echo "================================================"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo ""
    echo "Install it with:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   See https://github.com/cli/cli#installation"
    echo "  Windows: See https://github.com/cli/cli#installation"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "🔐 Not authenticated with GitHub. Logging in..."
    gh auth login
fi

echo "✅ GitHub CLI is authenticated"
echo ""

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📦 Repository: $REPO"
echo ""

# Confirm
read -p "Do you want to protect the 'main' branch? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🔧 Configuring branch protection..."
echo ""

# Note: GitHub CLI doesn't have direct branch protection commands yet
# We'll provide instructions for the web UI

cat << 'EOF'
📋 Branch Protection Setup Instructions:

Since GitHub CLI doesn't fully support branch protection rules yet,
please follow these steps in the GitHub web UI:

1. Go to your repository on GitHub:
   https://github.com/$REPO

2. Click "Settings" tab (top right)

3. Click "Branches" in left sidebar

4. Under "Branch protection rules", click "Add rule"

5. Configure the rule:

   Branch name pattern: main

   ✅ Check these options:

   - [x] Require a pull request before merging
       - [x] Require approvals: 0 (or 1 if you want review)
       - [x] Dismiss stale pull request approvals

   - [x] Require status checks to pass before merging
       - [x] Require branches to be up to date before merging
       - Search and add these required checks:
           • backend-tests
           • frontend-tests
           • docker-build

   - [x] Require conversation resolution before merging

   - [x] Include administrators (optional but recommended)

6. Click "Create" or "Save changes"

✅ Done! Now you must use pull requests to merge to main.

EOF

echo ""
echo "📖 Alternative: Quick Setup via Web"
echo ""
echo "Visit: https://github.com/$REPO/settings/branches"
echo ""

# Create a development branch if it doesn't exist
if ! git show-ref --quiet refs/heads/develop; then
    read -p "Create 'develop' branch for active development? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout -b develop
        git push -u origin develop
        echo "✅ Created 'develop' branch"
        echo ""
        echo "💡 Recommended workflow:"
        echo "   main    - Production-ready code (protected)"
        echo "   develop - Active development (optional protection)"
        echo "   feature/* - Feature branches (merge to develop)"
        echo ""
    fi
fi

echo "🎯 Summary:"
echo "  • Set up branch protection via GitHub web UI"
echo "  • Use pull requests for all changes to main"
echo "  • Create feature branches for new work"
echo ""
echo "See TESTING_CI_LOCALLY.md for complete workflow guide!"
