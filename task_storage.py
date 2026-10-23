"""
task_storage.py - JSON Persistence Engine for Academic Tasks.
Supports FR-7, NFR-2 (Data integrity), and NFR-3 (Reliability / Persistence).
"""

import os
import json
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class StorageError(Exception):
    """Raised when reading from or writing to task storage fails."""
    pass


class JsonTaskStorage:
    """
    Thread-safe, atomic JSON file storage for academic tasks.
    
    Guarantees:
    - Atomicity: Uses a temporary file and atomic rename (os.replace) so 
      crashes/interruptions never result in half-written or corrupted files (NFR-2).
    - Persistence: All successfully saved tasks remain available after application restart (NFR-3).
    - Concurrency Safety: Threading locks ensure mutual exclusion during file I/O.
    - Fault Tolerance: Corrupt files are backed up to a .corrupted snapshot rather than silently discarded.
    """

    def __init__(self, file_path: str = "data/tasks.json"):
        self.file_path = Path(file_path).resolve()
        self._lock = threading.RLock()
        self._ensure_storage_ready()

    def _ensure_storage_ready(self) -> None:
        """Ensures the directory exists and the JSON storage file is initialized."""
        with self._lock:
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                if not self.file_path.exists():
                    initial_state = {
                        "metadata": {
                            "created_at": datetime.now().isoformat(),
                            "version": "1.0",
                            "next_id": 1
                        },
                        "tasks": []
                    }
                    self._atomic_write(initial_state)
            except Exception as e:
                raise StorageError(f"Failed to initialize storage at '{self.file_path}': {e}") from e

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """
        Writes data to a temporary file in the same directory, then atomically replaces
        the target file. This prevents partial writes and corruption (NFR-2).
        """
        temp_path = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is flushed to physical disk
            
            # Atomic replacement on Windows and POSIX
            os.replace(temp_path, self.file_path)
        except Exception as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise StorageError(f"Failed to atomically persist tasks to disk: {e}") from e

    def load_raw_data(self) -> Dict[str, Any]:
        """
        Reads and parses the JSON storage file.
        Recovers gracefully if file is missing, and creates a backup if corrupted.
        """
        with self._lock:
            if not self.file_path.exists():
                self._ensure_storage_ready()

            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        # Empty file recovery
                        initial_state = {"metadata": {"next_id": 1}, "tasks": []}
                        self._atomic_write(initial_state)
                        return initial_state
                    data = json.loads(content)
                    if not isinstance(data, dict) or "tasks" not in data:
                        raise ValueError("Invalid schema: Root element must contain 'tasks' array.")
                    return data
            except (json.JSONDecodeError, ValueError) as err:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                corrupt_backup = self.file_path.with_name(f"{self.file_path.stem}.corrupt_{timestamp}.json")
                try:
                    shutil.copy2(self.file_path, corrupt_backup)
                except Exception:
                    pass
                raise StorageError(
                    f"Corrupted task storage file detected at '{self.file_path}'. "
                    f"A backup was saved to '{corrupt_backup}'. Details: {err}"
                ) from err
            except OSError as os_err:
                raise StorageError(f"I/O error reading task storage file: {os_err}") from os_err

    def save_raw_data(self, data: Dict[str, Any]) -> None:
        """Atomically saves the raw data structure under lock."""
        with self._lock:
            self._atomic_write(data)
