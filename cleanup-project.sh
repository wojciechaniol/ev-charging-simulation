#!/bin/bash
# Project Cleanup Script
# This script removes unnecessary, empty, and duplicate files
# Review the deletions below before running this script

set -e

echo "=========================================="
echo "🧹 EV Charging Simulation - Project Cleanup"
echo "=========================================="
echo ""

# Create backup directory
BACKUP_DIR=".cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Backup directory created: $BACKUP_DIR"
echo ""

# Function to safely remove files
safe_remove() {
    local file=$1
    local reason=$2
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "🗑️  Removing: $file"
        echo "   Reason: $reason"
        mv "$file" "$BACKUP_DIR/"
    fi
}

echo "Starting cleanup..."
echo ""

# ========== EMPTY FILES ==========
echo "1️⃣  Removing empty files..."
safe_remove "PROJECT_SUMMARY.md" "Empty file (0 bytes)"

# ========== OLD/UNUSED DIRECTORIES ==========
echo ""
echo "2️⃣  Removing unused directories..."
safe_remove "charging_station" "Old unused directory (all files empty)"
safe_remove "shared" "Old unused directory (all files empty)"

# ========== TEMPORARY DOCKER COMPOSE FILES ==========
echo ""
echo "3️⃣  Removing temporary docker-compose files..."
safe_remove "docker-compose.cp-11.yml" "Temporary file from add-cp.sh script"
safe_remove "docker-compose.driver-frank.yml" "Temporary file from add-driver.sh script"

# ========== DUPLICATE/REDUNDANT DOCUMENTATION ==========
echo ""
echo "4️⃣  Removing duplicate and status documentation..."

# Status/validation files (replaced by README.md)
safe_remove "AUTONOMOUS_OPERATION_VALIDATION.md" "Status doc - info in README.md"
safe_remove "AUTONOMOUS_SYSTEM_READY.md" "Status doc - info in README.md"
safe_remove "CONFIGURATION_COMPLETE.md" "Status doc - info in README.md"
safe_remove "DOCUMENTATION_UPDATE_COMPLETE.md" "Status doc - obsolete"
safe_remove "INCIDENT_FREE_STARTUP.md" "Status doc - info in README.md"
safe_remove "LAB_DEPLOYMENT_READY.md" "Status doc - replaced by MULTI_MACHINE_DEPLOYMENT_ANALYSIS.md"

# Summary files (replaced by comprehensive guides)
safe_remove "DEPLOYMENT_SUMMARY.md" "Summary - use DEPLOYMENT_GUIDE.md instead"
safe_remove "FIXES_SUMMARY.md" "Old fixes summary - obsolete"
safe_remove "LATEST_FIXES.md" "Old fixes summary - obsolete"
safe_remove "STATUS_LOGIC_DOCUMENTATION_SUMMARY.md" "Summary - use CP_STATUS_LOGIC.md instead"
safe_remove "TCP_FRAMING_DOCUMENTATION_SUMMARY.md" "Summary - use TCP_FRAMING_PROTOCOL.md instead"
safe_remove "RECOVERY_SCALABILITY_UPDATE_SUMMARY.md" "Summary - use RECOVERY_SCALABILITY_GUIDE.md instead"
safe_remove "DRIVER_DASHBOARD_COMPLETE.md" "Summary - use DRIVER_DASHBOARD_API.md instead"

# Duplicate content (already in other files)
safe_remove "AUTONOMOUS_OPERATION.md" "Duplicate - covered in README.md and FAULT_TOLERANCE.md"
safe_remove "GITHUB_SETUP.md" "Setup completed - instructions in README.md"
safe_remove "PUSH_TO_GITHUB.md" "One-time task - completed"

# Old deployment files (replaced by new scripts)
safe_remove "deploy.sh" "Replaced by deploy-machine1.sh"
safe_remove "git-setup.sh" "Setup completed - obsolete"

# ========== ALTERNATE DOCKER COMPOSE FILES ==========
echo ""
echo "5️⃣  Removing alternate docker-compose configurations..."
safe_remove "docker-compose.extended.yml" "Alternate config - use docker-compose.yml instead"
safe_remove "docker-compose.minimal.yml" "Alternate config - use docker-compose.yml instead"

echo ""
echo "=========================================="
echo "✅ Cleanup Complete!"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "   Backup location: $BACKUP_DIR"
echo "   Files moved: $(ls -1 $BACKUP_DIR | wc -l)"
echo ""
echo "🔄 To restore files:"
echo "   mv $BACKUP_DIR/* ."
echo ""
echo "🗑️  To permanently delete backup:"
echo "   rm -rf $BACKUP_DIR"
echo ""
echo "📋 Kept important files:"
echo "   ✅ README.md (main documentation)"
echo "   ✅ QUICKSTART.md (quick start guide)"
echo "   ✅ DEPLOYMENT_GUIDE.md (deployment instructions)"
echo "   ✅ MULTI_MACHINE_DEPLOYMENT_ANALYSIS.md (multi-machine setup)"
echo "   ✅ DYNAMIC_DEPLOYMENT.md (dynamic scaling guide)"
echo "   ✅ FAULT_TOLERANCE.md (fault tolerance documentation)"
echo "   ✅ FAULT_TOLERANCE_GUIDE.md (fault tolerance guide)"
echo "   ✅ FAULT_TOLERANCE_QUICKREF.md (quick reference)"
echo "   ✅ RECOVERY_SCALABILITY_GUIDE.md (recovery & scaling)"
echo "   ✅ CP_STATUS_LOGIC.md (CP status logic)"
echo "   ✅ CP_STATUS_QUICKREF_CARD.md (quick reference)"
echo "   ✅ TCP_FRAMING_PROTOCOL.md (TCP protocol docs)"
echo "   ✅ DRIVER_DASHBOARD_API.md (driver API docs)"
echo "   ✅ QUICK_REFERENCE.md (system quick reference)"
echo "   ✅ docker-compose.yml (main compose file)"
echo "   ✅ docker/docker-compose.remote-kafka.yml (remote kafka)"
echo "   ✅ All deployment scripts (add-cp.sh, etc.)"
echo "   ✅ evcharging/ (main application code)"
echo ""
