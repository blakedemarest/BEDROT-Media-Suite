#!/usr/bin/env python3
"""
AUTOMATIC BACKUP MANAGER FOR REEL TRACKER
Prevents data loss by creating timestamped backups before any save operation.
"""

import os
import shutil
import datetime
from pathlib import Path
from .utils import safe_print

class BackupManager:
    """Manages automatic backups of the reel tracker CSV."""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.backup_dir = os.path.join(os.path.dirname(csv_path), "backups")
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist."""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, reason="manual"):
        """Create a timestamped backup of the CSV file."""
        if not os.path.exists(self.csv_path):
            return None
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"REEL_TRACKER_BACKUP_{timestamp}_{reason.upper()}.csv"
        backup_path = os.path.join(self.backup_dir, filename)
        
        try:
            shutil.copy2(self.csv_path, backup_path)
            safe_print(f"[BACKUP] Created: {backup_path}")
            return backup_path
        except Exception as e:
            safe_print(f"[BACKUP ERROR] Failed: {e}")
            return None
    
    def create_pre_save_backup(self):
        """Create backup before any save operation."""
        return self.create_backup("pre_save")
    
    def create_pre_clear_backup(self):
        """Create backup before clearing data (CRITICAL!)."""
        return self.create_backup("pre_clear_CRITICAL")
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove backups older than specified days."""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        
        for backup_file in os.listdir(self.backup_dir):
            if backup_file.startswith("REEL_TRACKER_BACKUP_") or backup_file.startswith("bedrot-reel-tracker_backup_"):
                backup_path = os.path.join(self.backup_dir, backup_file)
                if os.path.getmtime(backup_path) < cutoff_time.timestamp():
                    try:
                        os.remove(backup_path)
                        safe_print(f"[CLEANUP] Removed old backup: {backup_file}")
                    except Exception as e:
                        safe_print(f"[CLEANUP ERROR] Failed to remove {backup_file}: {e}")
    
    def list_backups(self):
        """List all available backups."""
        if not os.path.exists(self.backup_dir):
            return []
        
        backups = []
        for backup_file in os.listdir(self.backup_dir):
            if backup_file.startswith("REEL_TRACKER_BACKUP_") or backup_file.startswith("bedrot-reel-tracker_backup_"):
                backup_path = os.path.join(self.backup_dir, backup_file)
                stat = os.stat(backup_path)
                backups.append({
                    'name': backup_file,
                    'path': backup_path,
                    'size': stat.st_size,
                    'modified': datetime.datetime.fromtimestamp(stat.st_mtime)
                })
        
        return sorted(backups, key=lambda x: x['modified'], reverse=True)

def safe_csv_save(csv_path, dataframe, backup_manager=None):
    """Safely save CSV with automatic backup."""
    if backup_manager:
        backup_manager.create_pre_save_backup()
    
    try:
        dataframe.to_csv(csv_path, index=False)
        print(f"✅ CSV saved successfully: {csv_path}")
        return True
    except Exception as e:
        print(f"❌ CSV save failed: {e}")
        return False

if __name__ == "__main__":
    # Test the backup system
    csv_path = "E:/VIDEOS/RELEASE CONTENT/bedrot-reel-tracker.csv"
    backup_mgr = BackupManager(csv_path)
    
    print("🔧 Testing backup system with new REEL_ format...")
    backup_mgr.create_backup("test")
    
    print("\n📋 Available backups:")
    for backup in backup_mgr.list_backups():
        print(f"  {backup['name']} - {backup['size']} bytes - {backup['modified']}") 