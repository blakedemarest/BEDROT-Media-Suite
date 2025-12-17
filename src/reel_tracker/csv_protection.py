# -*- coding: utf-8 -*-
"""
CSV Protection Manager for Reel Tracker.

Provides enhanced CSV protection with file locking, data validation,
and auto-save debouncing to prevent CSV corruption.
"""

from __future__ import annotations

import os
import sys
import threading

import pandas as pd

# File locking imports with fallback
try:
    import fcntl  # For file locking on Unix-like systems
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import msvcrt  # For file locking on Windows
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

from .utils import safe_print


class CSVProtectionManager:
    """
    Enhanced CSV protection manager with file locking, data validation, and auto-save debouncing.
    Prevents CSV corruption by ensuring atomic writes and validating data before saving.
    """

    def __init__(self, csv_path=None):
        self.csv_path = csv_path
        self.lock = threading.Lock()
        self.last_save_time = 0
        self.debounce_delay = 0.1  # 100ms debounce - much faster saves
        self.save_timer = None
        self.pending_save = False

    def lock_file(self, file_handle):
        """Cross-platform file locking with fallback."""
        try:
            if sys.platform == "win32" and HAS_MSVCRT:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            elif HAS_FCNTL:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            else:
                # File locking not available, proceed without locking
                safe_print("[WARNING] File locking not available on this system")
                return True
        except (OSError, IOError):
            return False

    def unlock_file(self, file_handle):
        """Cross-platform file unlocking with fallback."""
        try:
            if sys.platform == "win32" and HAS_MSVCRT:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            elif HAS_FCNTL:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except (OSError, IOError):
            pass

    def validate_data(self, data, columns):
        """
        Validate data before saving to prevent empty or corrupted CSV writes.
        """
        if not data:
            return False, "Data is empty"

        if not columns:
            return False, "Columns are empty"

        if len(data) == 0:
            return False, "No rows to save"

        # Check if all rows have the correct number of columns
        expected_cols = len(columns)
        for i, row in enumerate(data):
            if len(row) != expected_cols:
                return False, f"Row {i} has {len(row)} columns, expected {expected_cols}"

        # Additional validation: ensure at least one row has meaningful data
        has_meaningful_data = False
        for row in data:
            if any(str(cell).strip() for cell in row):
                has_meaningful_data = True
                break

        if not has_meaningful_data:
            return False, "All rows appear to be empty"

        return True, "Data validation passed"

    def safe_csv_write(self, data, columns, csv_path, backup_manager=None):
        """
        Safely write CSV with file locking, validation, and backup protection.
        NEVER destructively overwrites without backup.
        """
        with self.lock:
            # CRITICAL: Ensure we're using the correct path
            # The single source of truth is E:\VIDEOS\RELEASE CONTENT\bedrot-reel-tracker.csv
            expected_path = "E:/VIDEOS/RELEASE CONTENT/bedrot-reel-tracker.csv"
            if csv_path.replace("\\", "/") != expected_path:
                safe_print(f"[WARNING] Attempting to save to non-standard path: {csv_path}")
                safe_print(f"[WARNING] Expected: {expected_path}")

            # Validate data first
            is_valid, validation_msg = self.validate_data(data, columns)
            if not is_valid:
                safe_print(f"[ERROR] CSV Write Blocked: {validation_msg}")
                return False, f"Data validation failed: {validation_msg}"

            # MANDATORY: Create backup before ANY write operation
            if os.path.exists(csv_path):
                if backup_manager:
                    try:
                        backup_path = backup_manager.create_pre_save_backup()
                        if backup_path:
                            safe_print(f"[BACKUP] Created before save: {backup_path}")
                        else:
                            safe_print(f"[ERROR] Backup creation returned None - aborting save")
                            return False, "Could not create backup - save aborted for safety"
                    except Exception as e:
                        safe_print(f"[ERROR] Backup creation failed: {e}")
                        return False, f"Backup creation failed - save aborted for safety: {e}"
                else:
                    safe_print(f"[WARNING] No backup manager available - creating emergency backup")
                    try:
                        import shutil
                        from datetime import datetime
                        emergency_backup = csv_path + f".emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        shutil.copy2(csv_path, emergency_backup)
                        safe_print(f"[BACKUP] Emergency backup created: {emergency_backup}")
                    except Exception as e:
                        safe_print(f"[ERROR] Emergency backup failed: {e}")
                        return False, f"Could not create emergency backup - save aborted: {e}"

            # Write CSV with file locking
            temp_path = csv_path + ".tmp"
            try:
                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)

                # Write to temporary file first
                # Try multiple encoding options for maximum compatibility
                encoding_options = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
                write_success = False
                last_error = None

                for encoding in encoding_options:
                    try:
                        with open(temp_path, 'w', newline='', encoding=encoding) as temp_file:
                            if not self.lock_file(temp_file):
                                continue  # Try next encoding

                            try:
                                df.to_csv(temp_file, index=False)
                                temp_file.flush()
                                os.fsync(temp_file.fileno())  # Force write to disk
                                write_success = True
                                safe_print(f"[SUCCESS] Wrote CSV with {encoding} encoding")
                                break
                            finally:
                                self.unlock_file(temp_file)
                    except Exception as e:
                        last_error = e
                        safe_print(f"[WARNING] Failed with {encoding} encoding: {e}")
                        continue

                if not write_success:
                    raise Exception(f"Could not write CSV with any encoding. Last error: {last_error}")

                # Verify temp file exists and has content
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    raise Exception("Temp file is missing or empty after write")

                # Atomic move from temp to final location
                if os.path.exists(csv_path):
                    os.replace(temp_path, csv_path)
                else:
                    os.rename(temp_path, csv_path)

                safe_print(f"[SUCCESS] CSV safely written: {len(data)} rows to {csv_path}")
                return True, f"Successfully saved {len(data)} rows"

            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                safe_print(f"[ERROR] CSV write failed: {e}")
                return False, f"Write operation failed: {e}"

    def debounced_save(self, data, columns, csv_path, backup_manager=None, callback=None):
        """
        Debounced save to prevent multiple rapid saves from corrupting the file.
        """
        def perform_save():
            success, message = self.safe_csv_write(data, columns, csv_path, backup_manager)
            if callback:
                callback(success, message)
            self.pending_save = False

        # Cancel any pending save
        if self.save_timer:
            self.save_timer.cancel()

        # Mark as pending and schedule new save
        self.pending_save = True
        self.save_timer = threading.Timer(self.debounce_delay, perform_save)
        self.save_timer.start()

    def immediate_save(self, data, columns, csv_path, backup_manager=None):
        """
        Perform an immediate synchronous save without debouncing.
        Used for critical operations like app exit or file organization.
        """
        # Cancel any pending debounced save first
        if self.save_timer:
            self.save_timer.cancel()
            self.save_timer = None
        self.pending_save = False

        # Perform immediate save
        success, message = self.safe_csv_write(data, columns, csv_path, backup_manager)
        return success, message
