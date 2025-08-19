# -*- coding: utf-8 -*-
"""
File Organization Module for Reel Tracker.

Provides functionality for:
- Automatic file renaming using PERSONA_RELEASE_REELID convention
- Persona-Release folder structure creation
- Safe file copying with comprehensive error handling
- Batch processing capabilities
- Path validation and sanitization
"""

import os
import shutil
import re
import random
import time
from pathlib import Path
from .utils import safe_print


class FileOrganizer:
    """
    Handles file organization and renaming operations for reel content.
    Implements production-grade safety features and error handling.
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
        # File extension mapping for common media types
        self.media_extensions = {
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v',
            '.mp3', '.wav', '.aac', '.m4a', '.wma', '.flac',
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'
        }
    
    def sanitize_filename_component(self, component):
        """Sanitize a component for use in filenames and folder names."""
        if not component:
            return "UNKNOWN"
        
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', str(component))
        
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[\s\-\.\,\;\:\!\@\#\$\%\^\&\*\(\)\+\=\[\]\{\}\|\\`\~]', '_', sanitized)
        
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_{2,}', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it's not empty and not too long
        if not sanitized:
            sanitized = "UNKNOWN"
        
        # Limit length to prevent path issues
        if len(sanitized) > 50:
            sanitized = sanitized[:50].rstrip('_')
        
        return sanitized.upper()
    
    def generate_new_filename(self, persona, release, reel_id, original_filepath):
        """Generate new filename using PERSONA_RELEASE_REELID convention."""
        try:
            # Sanitize components
            persona_clean = self.sanitize_filename_component(persona)
            release_clean = self.sanitize_filename_component(release)
            reel_id_clean = self.sanitize_filename_component(reel_id)
            
            # Get file extension
            original_path = Path(original_filepath)
            file_extension = original_path.suffix.lower()
            
            # Ensure we have a valid extension
            if not file_extension or file_extension not in self.media_extensions:
                file_extension = '.mp4'  # Default fallback
            
            # Generate new filename
            new_filename = f"{persona_clean}_{release_clean}_{reel_id_clean}{file_extension}"
            
            safe_print(f"[FILE_ORG] Generated filename: {new_filename}")
            return new_filename
            
        except Exception as e:
            safe_print(f"[FILE_ORG] Error generating filename: {e}")
            # Fallback filename - use a simpler format
            import random
            fallback_num = random.randint(1000, 9999)
            return f"REEL_{fallback_num}.mp4"
    
    def generate_folder_name(self, persona, release):
        """Generate folder name using PERSONA_RELEASE convention."""
        persona_clean = self.sanitize_filename_component(persona)
        release_clean = self.sanitize_filename_component(release)
        return f"{persona_clean}_{release_clean}"
    
    def randomize_timestamp(self, target_filepath, base_time=None):
        """
        Timestamp function disabled - no longer randomizes file timestamps.
        
        Args:
            target_filepath: Path to the file to modify
            base_time: Base timestamp (defaults to current time)
        """
        # Timestamp randomization has been disabled
        safe_print(f"[FILE_ORG] Timestamp randomization disabled for: {os.path.basename(target_filepath)}")
        return True
    
    def check_duplicate_exists(self, target_filepath, persona, release, reel_id):
        """
        Check if a file with the same PERSONA_RELEASE_REELID pattern already exists.
        
        Args:
            target_filepath: The intended target file path
            persona: Persona component
            release: Release component  
            reel_id: Reel ID component
            
        Returns:
            tuple: (exists: bool, existing_path: str or None, conflict_type: str)
        """
        try:
            target_path = Path(target_filepath)
            target_directory = target_path.parent
            
            if not target_directory.exists():
                return False, None, "no_directory"
            
            # Generate the expected filename pattern (without extension)
            persona_clean = self.sanitize_filename_component(persona)
            release_clean = self.sanitize_filename_component(release)
            reel_id_clean = self.sanitize_filename_component(reel_id)
            expected_pattern = f"{persona_clean}_{release_clean}_{reel_id_clean}"
            
            # Check for any files with the same pattern (any extension)
            for existing_file in target_directory.iterdir():
                if existing_file.is_file():
                    existing_name = existing_file.stem  # filename without extension
                    
                    if existing_name == expected_pattern:
                        if existing_file == target_path:
                            return True, str(existing_file), "exact_match"
                        else:
                            return True, str(existing_file), "pattern_match"
            
            return False, None, "no_conflict"
            
        except Exception as e:
            safe_print(f"[FILE_ORG] Error checking for duplicates: {e}")
            return False, None, "check_error"
    
    def validate_export_folder(self, export_folder):
        """Validate that the export folder exists and is writable."""
        try:
            if not export_folder:
                return False, "Export folder path is empty"
            
            export_path = Path(export_folder)
            
            # Check if path exists
            if not export_path.exists():
                try:
                    export_path.mkdir(parents=True, exist_ok=True)
                    safe_print(f"[FILE_ORG] Created export directory: {export_folder}")
                except Exception as e:
                    return False, f"Cannot create export directory: {e}"
            
            # Check if it's a directory
            if not export_path.is_dir():
                return False, f"Export path is not a directory: {export_folder}"
            
            # Check if writable
            test_file = export_path / "test_write_access.tmp"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                return False, f"Export directory is not writable: {e}"
            
            return True, "Export folder is valid"
            
        except Exception as e:
            return False, f"Error validating export folder: {e}"
    
    def validate_source_file(self, source_filepath):
        """Validate that the source file exists and is readable."""
        try:
            if not source_filepath:
                return False, "Source file path is empty"
            
            source_path = Path(source_filepath)
            
            # Check if file exists
            if not source_path.exists():
                return False, f"Source file does not exist: {source_filepath}"
            
            # Check if it's a file
            if not source_path.is_file():
                return False, f"Source path is not a file: {source_filepath}"
            
            # Check if readable
            try:
                with open(source_path, 'rb') as f:
                    f.read(1)  # Try to read one byte
            except Exception as e:
                return False, f"Source file is not readable: {e}"
            
            return True, "Source file is valid"
            
        except Exception as e:
            return False, f"Error validating source file: {e}"
    
    def organize_single_file(self, reel_data, safe_mode=True, overwrite_protection=True):
        """
        Organize a single file based on reel metadata.
        
        Args:
            reel_data: List containing [reel_id, persona, release, reel_type, filename, caption, filepath]
            safe_mode: If True, copy files instead of moving them
            overwrite_protection: If True, prevent overwriting existing files
            
        Returns:
            tuple: (success: bool, message: str, new_filepath: str or None)
        """
        try:
            # Handle both old format (7 columns) and new format (8 columns with Aspect Ratio)
            if len(reel_data) < 7:
                return False, "Invalid reel data format", None
            
            # Extract data based on column count
            if len(reel_data) == 7:
                # Old format without Aspect Ratio
                reel_id, persona, release, reel_type, filename, caption, source_filepath = reel_data
            else:
                # New format with Aspect Ratio at index 6, FilePath at index 7
                reel_id, persona, release, reel_type, filename, caption, aspect_ratio, source_filepath = reel_data[:8]
            
            # Get export folder from config
            if not self.config_manager:
                return False, "Configuration manager not available", None
            
            settings = self.config_manager.get_file_organization_settings()
            export_folder = settings.get("master_export_folder", "")
            
            # Validate export folder
            valid_export, export_msg = self.validate_export_folder(export_folder)
            if not valid_export:
                return False, f"Export folder validation failed: {export_msg}", None
            
            # Validate source file
            valid_source, source_msg = self.validate_source_file(source_filepath)
            if not valid_source:
                return False, f"Source file validation failed: {source_msg}", None
            
            # Generate new filename
            new_filename = self.generate_new_filename(persona, release, reel_id, source_filepath)
            
            # Generate folder name
            folder_name = self.generate_folder_name(persona, release)
            
            # Create target folder path
            target_folder = Path(export_folder) / folder_name
            target_folder.mkdir(parents=True, exist_ok=True)
            
            # Create full target path
            target_filepath = target_folder / new_filename
            
            # Check for duplicate files with same PERSONA_RELEASE_REELID pattern
            duplicate_exists, existing_path, conflict_type = self.check_duplicate_exists(
                target_filepath, persona, release, reel_id
            )
            
            if duplicate_exists:
                if conflict_type == "exact_match":
                    # Exact same file already exists - skip without error
                    skip_msg = f"Skipped: File already exists with same name: {new_filename}"
                    safe_print(f"[FILE_ORG] {skip_msg}")
                    return "skipped", skip_msg, str(existing_path)
                elif conflict_type == "pattern_match":
                    # Same pattern but different extension - potential duplicate content
                    skip_msg = f"Skipped: Similar file exists: {os.path.basename(existing_path)} (conflicts with {new_filename})"
                    safe_print(f"[FILE_ORG] {skip_msg}")
                    return "skipped", skip_msg, str(existing_path)
            
            # Legacy overwrite protection (for different naming patterns)
            if overwrite_protection and target_filepath.exists():
                # This shouldn't happen with our duplicate detection, but keeping as fallback
                skip_msg = f"Skipped: File exists and overwrite protection enabled: {new_filename}"
                safe_print(f"[FILE_ORG] {skip_msg}")
                return "skipped", skip_msg, str(target_filepath)
            
            # Perform file operation
            if safe_mode:
                # Copy file
                shutil.copy2(source_filepath, target_filepath)
                operation = "copied"
            else:
                # Move file
                shutil.move(source_filepath, target_filepath)
                operation = "moved"
            
            # Apply randomized timestamp for dynamic presentation order
            self.randomize_timestamp(target_filepath)
            
            success_msg = f"Successfully {operation} file to: {target_filepath}"
            safe_print(f"[FILE_ORG] {success_msg}")
            
            return True, success_msg, str(target_filepath)
            
        except Exception as e:
            error_msg = f"Error organizing file: {e}"
            safe_print(f"[FILE_ORG] {error_msg}")
            return False, error_msg, None
    
    def organize_batch(self, reel_data_list, progress_callback=None, csv_update_callback=None):
        """
        Organize multiple files in batch.
        
        Args:
            reel_data_list: List of reel data lists
            progress_callback: Optional callback function for progress updates
            csv_update_callback: Optional callback for CSV updates after successful organization
            
        Returns:
            dict: Results summary with success/failure counts and details
        """
        try:
            if not self.config_manager:
                return {"success": False, "message": "Configuration manager not available"}
            
            settings = self.config_manager.get_file_organization_settings()
            safe_mode = settings.get("safe_testing_mode", True)
            overwrite_protection = settings.get("overwrite_protection", True)
            
            total_files = len(reel_data_list)
            successful = []
            failed = []
            skipped = []
            
            safe_print(f"[FILE_ORG] Starting batch organization of {total_files} files")
            safe_print(f"[FILE_ORG] Safe mode: {safe_mode}, Overwrite protection: {overwrite_protection}")
            
            for i, reel_data in enumerate(reel_data_list):
                try:
                    # Update progress
                    if progress_callback:
                        progress_callback(i + 1, total_files, reel_data)
                    
                    # Organize single file
                    result, message, filepath = self.organize_single_file(
                        reel_data, safe_mode, overwrite_protection
                    )
                    
                    # Get filepath index based on data length (7 for old format, 8 for new with Aspect Ratio)
                    filepath_index = 6 if len(reel_data) == 7 else 7
                    
                    if result == True:  # Success
                        successful.append({
                            "reel_id": reel_data[0],
                            "original_path": reel_data[filepath_index],
                            "new_path": filepath,
                            "message": message
                        })
                        
                        # Trigger CSV update callback if provided
                        if csv_update_callback:
                            new_filename = os.path.basename(filepath)
                            csv_update_callback(reel_data[0], filepath, new_filename)
                    elif result == "skipped":  # Skipped due to duplicate
                        skipped.append({
                            "reel_id": reel_data[0],
                            "original_path": reel_data[filepath_index],
                            "existing_path": filepath,
                            "reason": message
                        })
                    else:  # Failed
                        failed.append({
                            "reel_id": reel_data[0],
                            "original_path": reel_data[filepath_index],
                            "error": message
                        })
                        
                except Exception as e:
                    filepath_index = 6 if len(reel_data) == 7 else 7
                    failed.append({
                        "reel_id": reel_data[0] if len(reel_data) > 0 else "Unknown",
                        "original_path": reel_data[filepath_index] if len(reel_data) > filepath_index else "Unknown",
                        "error": f"Unexpected error: {e}"
                    })
            
            # Summary
            success_count = len(successful)
            skipped_count = len(skipped)
            failure_count = len(failed)
            
            summary = {
                "success": failure_count == 0,
                "total_files": total_files,
                "successful_count": success_count,
                "skipped_count": skipped_count,
                "failed_count": failure_count,
                "successful_files": successful,
                "skipped_files": skipped,
                "failed_files": failed,
                "message": f"Batch complete: {success_count} succeeded, {skipped_count} skipped, {failure_count} failed"
            }
            
            safe_print(f"[FILE_ORG] Batch organization complete: {success_count} succeeded, {skipped_count} skipped, {failure_count} failed")
            
            return summary
            
        except Exception as e:
            error_msg = f"Error in batch organization: {e}"
            safe_print(f"[FILE_ORG] {error_msg}")
            return {"success": False, "message": error_msg}
    
    def preview_organization(self, reel_data_list):
        """
        Preview what the organization would look like without actually moving files.
        
        Args:
            reel_data_list: List of reel data lists
            
        Returns:
            list: Preview information for each file
        """
        try:
            if not self.config_manager:
                return []
            
            settings = self.config_manager.get_file_organization_settings()
            export_folder = settings.get("master_export_folder", "")
            
            preview_data = []
            
            for reel_data in reel_data_list:
                if len(reel_data) < 7:
                    continue
                
                # Extract data based on column count
                if len(reel_data) == 7:
                    # Old format without Aspect Ratio
                    reel_id, persona, release, reel_type, filename, caption, source_filepath = reel_data
                else:
                    # New format with Aspect Ratio at index 6, FilePath at index 7
                    reel_id, persona, release, reel_type, filename, caption, aspect_ratio, source_filepath = reel_data[:8]
                
                # Generate new filename and folder
                new_filename = self.generate_new_filename(persona, release, reel_id, source_filepath)
                folder_name = self.generate_folder_name(persona, release)
                
                # Create preview paths
                target_folder = Path(export_folder) / folder_name if export_folder else Path("NOT_SET") / folder_name
                target_filepath = target_folder / new_filename
                
                # Validate source file
                valid_source, source_msg = self.validate_source_file(source_filepath)
                
                # Check for duplicates
                duplicate_exists, existing_path, conflict_type = self.check_duplicate_exists(
                    target_filepath, persona, release, reel_id
                )
                
                # Determine status and message
                if not valid_source:
                    status = "invalid_source"
                    status_message = source_msg
                elif duplicate_exists:
                    status = "duplicate"
                    if conflict_type == "exact_match":
                        status_message = f"Exact duplicate exists: {os.path.basename(existing_path)}"
                    elif conflict_type == "pattern_match":
                        status_message = f"Similar file exists: {os.path.basename(existing_path)}"
                    else:
                        status_message = "Duplicate detected—this file will be skipped."
                else:
                    status = "ready"
                    status_message = "Ready to organize"
                
                preview_data.append({
                    "reel_id": reel_id,
                    "original_filename": os.path.basename(source_filepath),
                    "original_path": source_filepath,
                    "new_filename": new_filename,
                    "target_folder": str(target_folder),
                    "target_path": str(target_filepath),
                    "valid_source": valid_source,
                    "duplicate_exists": duplicate_exists,
                    "existing_path": existing_path,
                    "conflict_type": conflict_type,
                    "status": status,
                    "status_message": status_message,
                    "folder_exists": target_folder.exists() if export_folder else False
                })
            
            return preview_data
            
        except Exception as e:
            safe_print(f"[FILE_ORG] Error generating preview: {e}")
            return []