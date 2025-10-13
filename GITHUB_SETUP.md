# 📋 GitHub Setup Guide

This guide walks you through pushing your EV Charging Simulation project to GitHub.

## 🎯 Quick Setup (Automated)

### Option 1: Using the Setup Script (Easiest)

1. **Make the script executable:**
   ```bash
   cd /tmp/ev-charging-simulation
   chmod +x git-setup.sh
   ```

2. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `ev-charging-simulation`
   - Description: `Distributed EV charging management system with Python, Docker, Kafka`
   - Keep it Public or Private (your choice)
   - **DO NOT** initialize with README, .gitignore, or license
   - Click "Create repository"

3. **Run the setup script:**
   ```bash
   ./git-setup.sh https://github.com/YOUR-USERNAME/ev-charging-simulation.git
   ```
   
   Replace `YOUR-USERNAME` with your GitHub username.

4. **Done!** Your code is now on GitHub.

---

## 🔧 Manual Setup (Step by Step)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Fill in the details:
   - **Repository name:** `ev-charging-simulation`
   - **Description:** `Distributed EV charging management system with Python, Docker, Kafka, and TCP sockets`
   - **Visibility:** Public (or Private if you prefer)
   - **DO NOT** check "Initialize this repository with a README"
3. Click **"Create repository"**

### Step 2: Initialize Git Locally

```bash
cd /tmp/ev-charging-simulation

# Initialize git repository
git init

# Configure your identity (if not already done)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Add Files to Git

```bash
# Add all files
git add .

# Check what will be committed
git status

# Commit the files
git commit -m "Initial commit - EV Charging Simulation"
```

### Step 4: Connect to GitHub

```bash
# Add GitHub repository as remote
git remote add origin https://github.com/YOUR-USERNAME/ev-charging-simulation.git

# Verify remote was added
git remote -v
```

Replace `YOUR-USERNAME` with your actual GitHub username.

### Step 5: Push to GitHub

```bash
# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## 🔐 Authentication Options

### Option A: HTTPS with Personal Access Token (Recommended)

1. **Generate a token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a name: `EV Charging Simulation`
   - Select scopes: `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **Use token when pushing:**
   ```bash
   git push -u origin main
   # Username: YOUR-USERNAME
   # Password: YOUR-TOKEN (paste the token, not your password)
   ```

3. **Cache credentials** (so you don't have to enter token every time):
   ```bash
   git config --global credential.helper cache
   # Or for longer persistence:
   git config --global credential.helper 'cache --timeout=3600'
   ```

### Option B: SSH Keys (Advanced)

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   # Press Enter to accept default location
   # Enter a passphrase (optional but recommended)
   ```

2. **Add SSH key to GitHub:**
   ```bash
   # Copy your public key
   cat ~/.ssh/id_ed25519.pub
   ```
   
   - Go to GitHub Settings → SSH and GPG keys → New SSH key
   - Paste your public key
   - Click "Add SSH key"

3. **Use SSH URL:**
   ```bash
   git remote set-url origin git@github.com:YOUR-USERNAME/ev-charging-simulation.git
   git push -u origin main
   ```

---

## 🐛 Troubleshooting

### Problem: "Repository already exists" or "non-fast-forward" error

**Solution:** Force push (⚠️ Use with caution - overwrites remote)
```bash
git push -u origin main --force
```

### Problem: "Authentication failed"

**Solutions:**
1. Make sure you're using a Personal Access Token, not your password
2. Generate a new token with correct permissions
3. Clear cached credentials:
   ```bash
   git credential-cache exit
   ```

### Problem: "Permission denied (publickey)"

**Solutions:**
1. Check SSH key is added to GitHub
2. Test SSH connection:
   ```bash
   ssh -T git@github.com
   ```
3. Use HTTPS instead of SSH

### Problem: Git not configured

**Solution:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## ✅ Verification

After pushing, verify your repository:

1. **Visit your repository:**
   ```
   https://github.com/YOUR-USERNAME/ev-charging-simulation
   ```

2. **Check that all files are there:**
   - README.md should display on the homepage
   - All folders (evcharging, docker, etc.) should be visible
   - Check the file count (should be 40+ files)

3. **View README:**
   - The README should be rendered with formatting
   - Images and badges should display correctly

---

## 🎨 Enhance Your GitHub Repository

### Add Topics

1. Go to your repository on GitHub
2. Click the ⚙️ icon next to "About"
3. Add topics:
   - `python`
   - `kafka`
   - `docker`
   - `electric-vehicles`
   - `charging-station`
   - `distributed-systems`
   - `fastapi`
   - `asyncio`

### Add Description

In the "About" section, add:
```
Distributed EV charging management system with Python, Kafka, Docker, and real-time telemetry dashboard
```

### Enable GitHub Pages (Optional)

If you want to host documentation:
1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, folder: /docs (if you create a docs folder)

### Add License

```bash
# Create LICENSE file
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

git add LICENSE
git commit -m "Add MIT License"
git push
```

---

## 🚀 Next Steps After Pushing

1. **Share your repository:**
   - Copy the URL: `https://github.com/YOUR-USERNAME/ev-charging-simulation`
   - Share with your team or on social media

2. **Set up GitHub Actions** (optional):
   - Add CI/CD workflows
   - Automated testing on push
   - Docker image builds

3. **Enable GitHub Discussions** (optional):
   - Repository Settings → Features → Discussions

4. **Create branches for development:**
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```

5. **Invite collaborators:**
   - Repository Settings → Collaborators → Add people

---

## 📝 Git Cheat Sheet

### Common Commands

```bash
# Check status
git status

# View changes
git diff

# Add specific files
git add file1.py file2.py

# Commit changes
git commit -m "Your message"

# Push changes
git push

# Pull changes from remote
git pull

# View commit history
git log --oneline --graph

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Merge branch
git merge feature-name

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD
```

---

## 🎉 Success!

Your EV Charging Simulation is now on GitHub! 

**Repository URL:** `https://github.com/YOUR-USERNAME/ev-charging-simulation`

Don't forget to:
- ⭐ Star your own repository
- 📝 Add a good description
- 🏷️ Add relevant topics
- 📄 Ensure README displays correctly
- 🔗 Share with others!

---

**Questions?** Check the [README.md](README.md) or [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for more details.
