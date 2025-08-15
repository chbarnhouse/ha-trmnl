#!/bin/bash

# TRMNL Integration Repository Setup Script
# This script helps set up the initial GitHub repository

echo "🚀 TRMNL Integration Repository Setup"
echo "====================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "custom_components/trmnl" ]; then
    echo "❌ Please run this script from the root directory of your integration files."
    exit 1
fi

echo "✅ Git is installed"
echo "✅ Integration files found"
echo ""

# Get repository name
REPO_NAME="ha-trmnl"
GITHUB_USERNAME="chbarnhouse"
REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME"

echo "Repository Details:"
echo "  Name: $REPO_NAME"
echo "  Username: $GITHUB_USERNAME"
echo "  URL: $REPO_URL"
echo ""

# Check if directory is already a git repository
if [ -d ".git" ]; then
    echo "⚠️  This directory is already a git repository."
    read -p "Do you want to continue and set up the remote? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
else
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: TRMNL Integration for Home Assistant"

# Add remote origin
echo "🔗 Adding remote origin..."
git remote add origin $REPO_URL

# Set main branch
echo "🌿 Setting main branch..."
git branch -M main

echo ""
echo "✅ Repository setup complete!"
echo ""
echo "Next steps:"
echo "1. Create the repository on GitHub: $REPO_URL"
echo "2. Push your code: git push -u origin main"
echo "3. Create a release tag: git tag -a v1.0.0 -m 'Initial release'"
echo "4. Push the tag: git push origin v1.0.0"
echo ""
echo "For detailed instructions, see SETUP_GUIDE.md"
echo ""
echo "🎉 Your TRMNL integration is ready to be published!"
