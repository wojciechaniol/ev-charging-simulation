#!/bin/bash
# Script to initialize Git repository and push to GitHub
# Usage: ./git-setup.sh <your-github-repo-url>

set -e

echo "🚀 EV Charging Simulation - Git Setup"
echo "========================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if repository URL is provided
if [ -z "$1" ]; then
    echo "❌ Please provide your GitHub repository URL"
    echo ""
    echo "Usage: ./git-setup.sh <your-github-repo-url>"
    echo ""
    echo "Example:"
    echo "  ./git-setup.sh https://github.com/username/ev-charging-simulation.git"
    echo "  ./git-setup.sh git@github.com:username/ev-charging-simulation.git"
    echo ""
    exit 1
fi

REPO_URL="$1"

echo "📦 Repository URL: $REPO_URL"
echo ""

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "⚠️  .gitignore not found. Creating default .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Environment
.env
.env.local

# Logs
*.log

# Docker
docker-compose.override.yml

# Database
*.db
*.sqlite
*.sqlite3

# Kafka data
kafka-data/
EOF
fi

# Add all files
echo ""
echo "📦 Adding files to Git..."
git add .

# Show status
echo ""
echo "📊 Git status:"
git status --short

# Commit
echo ""
read -p "Enter commit message (default: 'Initial commit - EV Charging Simulation'): " COMMIT_MSG
COMMIT_MSG=${COMMIT_MSG:-"Initial commit - EV Charging Simulation"}

echo ""
echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"
echo "✅ Changes committed"

# Check if remote already exists
if git remote | grep -q "^origin$"; then
    echo ""
    echo "⚠️  Remote 'origin' already exists. Removing it..."
    git remote remove origin
fi

# Add remote
echo ""
echo "🔗 Adding remote repository..."
git remote add origin "$REPO_URL"
echo "✅ Remote 'origin' added"

# Determine default branch name
DEFAULT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")
if [ "$DEFAULT_BRANCH" != "main" ] && [ "$DEFAULT_BRANCH" != "master" ]; then
    echo ""
    echo "🔄 Renaming branch to 'main'..."
    git branch -M main
    DEFAULT_BRANCH="main"
fi

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
echo "   Branch: $DEFAULT_BRANCH"
echo "   Remote: $REPO_URL"
echo ""

# Attempt to push
if git push -u origin "$DEFAULT_BRANCH" 2>&1; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎉 Your repository is now available at:"
    echo "   $REPO_URL"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Visit your repository on GitHub"
    echo "   2. Add a description and topics"
    echo "   3. Enable GitHub Actions (if desired)"
    echo "   4. Share with your team!"
else
    echo ""
    echo "⚠️  Push failed. This might happen if:"
    echo "   - The repository already has content"
    echo "   - You don't have permission"
    echo "   - Authentication failed"
    echo ""
    echo "💡 Try these solutions:"
    echo ""
    echo "1. If repository exists with content, use force push:"
    echo "   git push -u origin $DEFAULT_BRANCH --force"
    echo ""
    echo "2. If authentication failed, configure Git:"
    echo "   git config --global user.name \"Your Name\""
    echo "   git config --global user.email \"your.email@example.com\""
    echo ""
    echo "3. For SSH authentication issues:"
    echo "   ssh-keygen -t ed25519 -C \"your.email@example.com\""
    echo "   cat ~/.ssh/id_ed25519.pub  # Add this to GitHub Settings > SSH Keys"
    echo ""
    echo "4. For HTTPS authentication, use a Personal Access Token:"
    echo "   GitHub Settings > Developer settings > Personal access tokens"
    echo ""
    exit 1
fi

# Display repository info
echo ""
echo "📊 Repository Information:"
echo "   Local branch: $DEFAULT_BRANCH"
echo "   Remote: origin"
echo "   URL: $REPO_URL"
echo ""
echo "🔧 Useful Git commands:"
echo "   git status              - Check status"
echo "   git log --oneline       - View commit history"
echo "   git remote -v           - View remotes"
echo "   git push                - Push changes"
echo "   git pull                - Pull changes"
echo ""
echo "✨ Setup complete!"
