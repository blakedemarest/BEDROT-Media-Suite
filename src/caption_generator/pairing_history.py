# -*- coding: utf-8 -*-
"""
Pairing History Module for Caption Generator.

SQLite-based persistent storage for audio file to SRT pairings.
Enables auto-detection of previously generated subtitles when audio files
are dropped into the Caption Generator.
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any


class PairingHistory:
    """
    Manages persistent history of audio file to subtitle pairings.

    Uses SQLite for storage with support for:
    - Path-based matching (primary)
    - Content hash matching (for moved/renamed files)
    - Source tracking (auto_transcribed vs user_provided)
    """

    def __init__(self, db_path: str):
        """
        Initialize the pairing history database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """Ensure the directory for the database file exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_database(self):
        """Initialize database schema if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Audio files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_hash TEXT,
                    file_size INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # SRT/VTT files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS srt_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audio_id INTEGER NOT NULL,
                    srt_path TEXT,
                    vtt_path TEXT,
                    source TEXT NOT NULL DEFAULT 'auto_transcribed',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audio_id) REFERENCES audio_files(id) ON DELETE CASCADE
                )
            """)

            # Active pairings table (one SRT per audio at a time)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pairings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audio_id INTEGER NOT NULL UNIQUE,
                    srt_id INTEGER NOT NULL,
                    paired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audio_id) REFERENCES audio_files(id) ON DELETE CASCADE,
                    FOREIGN KEY (srt_id) REFERENCES srt_files(id) ON DELETE CASCADE
                )
            """)

            # Indexes for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_path ON audio_files(file_path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_hash ON audio_files(file_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audio_name ON audio_files(file_name)
            """)

            conn.commit()

    def _calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> Optional[str]:
        """
        Calculate MD5 hash of a file for content-based matching.

        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read at a time

        Returns:
            MD5 hash string or None if file cannot be read
        """
        if not os.path.exists(file_path):
            return None

        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return None

    def _get_or_create_audio(self, audio_path: str) -> int:
        """
        Get existing audio file record or create new one.

        Args:
            audio_path: Full path to audio file

        Returns:
            Audio file ID
        """
        audio_path = os.path.normpath(audio_path)
        file_name = os.path.basename(audio_path)
        file_hash = self._calculate_file_hash(audio_path)
        file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Try to find by exact path first
            cursor.execute(
                "SELECT id FROM audio_files WHERE file_path = ?",
                (audio_path,)
            )
            result = cursor.fetchone()

            if result:
                return result[0]

            # Try to find by hash if available
            if file_hash:
                cursor.execute(
                    "SELECT id FROM audio_files WHERE file_hash = ?",
                    (file_hash,)
                )
                result = cursor.fetchone()
                if result:
                    # Update path for the existing record
                    cursor.execute(
                        "UPDATE audio_files SET file_path = ? WHERE id = ?",
                        (audio_path, result[0])
                    )
                    conn.commit()
                    return result[0]

            # Create new record
            cursor.execute(
                """INSERT INTO audio_files (file_path, file_name, file_hash, file_size)
                   VALUES (?, ?, ?, ?)""",
                (audio_path, file_name, file_hash, file_size)
            )
            conn.commit()
            return cursor.lastrowid

    def find_pairing(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Find existing SRT pairing for an audio file.

        Matching strategy:
        1. Exact path match
        2. Content hash match (for moved/renamed files)
        3. Filename + size match (fallback)

        Args:
            audio_path: Full path to audio file

        Returns:
            Dict with pairing info or None if not found:
            {
                'audio_id': int,
                'srt_id': int,
                'srt_path': str,
                'source': str,  # 'auto_transcribed' or 'user_provided'
                'paired_at': str
            }
        """
        audio_path = os.path.normpath(audio_path)
        file_name = os.path.basename(audio_path)
        file_hash = self._calculate_file_hash(audio_path)
        file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else None

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Strategy 1: Exact path match
            cursor.execute("""
                SELECT a.id as audio_id, s.id as srt_id, s.srt_path, s.vtt_path,
                       s.source, p.paired_at
                FROM audio_files a
                JOIN pairings p ON a.id = p.audio_id
                JOIN srt_files s ON p.srt_id = s.id
                WHERE a.file_path = ?
            """, (audio_path,))
            result = cursor.fetchone()

            if result:
                return dict(result)

            # Strategy 2: Hash match
            if file_hash:
                cursor.execute("""
                    SELECT a.id as audio_id, s.id as srt_id, s.srt_path, s.vtt_path,
                           s.source, p.paired_at
                    FROM audio_files a
                    JOIN pairings p ON a.id = p.audio_id
                    JOIN srt_files s ON p.srt_id = s.id
                    WHERE a.file_hash = ?
                """, (file_hash,))
                result = cursor.fetchone()

                if result:
                    return dict(result)

            # Strategy 3: Filename + size match
            if file_size:
                cursor.execute("""
                    SELECT a.id as audio_id, s.id as srt_id, s.srt_path, s.vtt_path,
                           s.source, p.paired_at
                    FROM audio_files a
                    JOIN pairings p ON a.id = p.audio_id
                    JOIN srt_files s ON p.srt_id = s.id
                    WHERE a.file_name = ? AND a.file_size = ?
                """, (file_name, file_size))
                result = cursor.fetchone()

                if result:
                    return dict(result)

        return None

    def add_pairing(self, audio_path: str, srt_path: str,
                    source: str = 'auto_transcribed') -> int:
        """
        Add a new audio-to-SRT pairing.

        If a pairing already exists for this audio, it will be replaced.

        Args:
            audio_path: Full path to audio file
            srt_path: Full path to SRT file
            source: 'auto_transcribed' or 'user_provided'

        Returns:
            Pairing ID
        """
        audio_path = os.path.normpath(audio_path)
        srt_path = os.path.normpath(srt_path)

        audio_id = self._get_or_create_audio(audio_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create SRT file record (vtt_path kept as NULL for backwards compatibility)
            cursor.execute(
                """INSERT INTO srt_files (audio_id, srt_path, vtt_path, source)
                   VALUES (?, ?, NULL, ?)""",
                (audio_id, srt_path, source)
            )
            srt_id = cursor.lastrowid

            # Remove existing pairing if any
            cursor.execute(
                "DELETE FROM pairings WHERE audio_id = ?",
                (audio_id,)
            )

            # Create new pairing
            cursor.execute(
                """INSERT INTO pairings (audio_id, srt_id)
                   VALUES (?, ?)""",
                (audio_id, srt_id)
            )
            pairing_id = cursor.lastrowid

            conn.commit()
            return pairing_id

    def update_pairing(self, audio_path: str, srt_path: str,
                       source: str = 'user_provided') -> bool:
        """
        Update an existing pairing with a new SRT file.

        Args:
            audio_path: Full path to audio file
            srt_path: Full path to new SRT file
            source: 'auto_transcribed' or 'user_provided'

        Returns:
            True if updated, False if no existing pairing found
        """
        audio_path = os.path.normpath(audio_path)

        existing = self.find_pairing(audio_path)
        if not existing:
            return False

        # Add new pairing (this will replace the old one)
        self.add_pairing(audio_path, srt_path, source)
        return True

    def delete_pairing(self, audio_path: str) -> bool:
        """
        Remove pairing for an audio file.

        Does not delete the actual SRT/VTT files.

        Args:
            audio_path: Full path to audio file

        Returns:
            True if deleted, False if not found
        """
        audio_path = os.path.normpath(audio_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Find audio ID
            cursor.execute(
                "SELECT id FROM audio_files WHERE file_path = ?",
                (audio_path,)
            )
            result = cursor.fetchone()

            if not result:
                return False

            audio_id = result[0]

            # Delete pairing
            cursor.execute(
                "DELETE FROM pairings WHERE audio_id = ?",
                (audio_id,)
            )

            conn.commit()
            return cursor.rowcount > 0

    def get_all_pairings(self) -> List[Dict[str, Any]]:
        """
        Get all stored pairings.

        Returns:
            List of pairing dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT a.id as audio_id, a.file_path as audio_path, a.file_name,
                       s.id as srt_id, s.srt_path, s.vtt_path, s.source,
                       p.paired_at
                FROM audio_files a
                JOIN pairings p ON a.id = p.audio_id
                JOIN srt_files s ON p.srt_id = s.id
                ORDER BY p.paired_at DESC
            """)

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_pairings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get most recent pairings.

        Args:
            limit: Maximum number of pairings to return

        Returns:
            List of pairing dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT a.id as audio_id, a.file_path as audio_path, a.file_name,
                       s.id as srt_id, s.srt_path, s.vtt_path, s.source,
                       p.paired_at
                FROM audio_files a
                JOIN pairings p ON a.id = p.audio_id
                JOIN srt_files s ON p.srt_id = s.id
                ORDER BY p.paired_at DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def verify_pairing_files_exist(self, audio_path: str) -> Dict[str, bool]:
        """
        Check if the SRT file in a pairing still exists.

        Args:
            audio_path: Full path to audio file

        Returns:
            Dict with 'srt_exists' boolean,
            or empty dict if no pairing found
        """
        pairing = self.find_pairing(audio_path)
        if not pairing:
            return {}

        result = {
            'srt_exists': False
        }

        if pairing.get('srt_path'):
            result['srt_exists'] = os.path.exists(pairing['srt_path'])

        return result

    def cleanup_orphaned_records(self) -> int:
        """
        Remove pairings where the SRT file no longer exists.

        Returns:
            Number of records cleaned up
        """
        cleaned = 0
        pairings = self.get_all_pairings()

        for pairing in pairings:
            srt_path = pairing.get('srt_path')
            if srt_path and not os.path.exists(srt_path):
                self.delete_pairing(pairing['audio_path'])
                cleaned += 1

        return cleaned


# Singleton instance management
_history_instance: Optional[PairingHistory] = None


def get_pairing_history(db_path: Optional[str] = None) -> PairingHistory:
    """
    Get the singleton PairingHistory instance.

    Args:
        db_path: Optional path to database. If not provided, uses default.

    Returns:
        PairingHistory instance
    """
    global _history_instance

    if _history_instance is None:
        if db_path is None:
            # Default path relative to this file's location
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(module_dir, 'config', 'caption_generator_history.db')

        _history_instance = PairingHistory(db_path)

    return _history_instance
