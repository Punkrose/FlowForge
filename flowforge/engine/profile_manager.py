"""
ProfileManager - Browser profile management with file-based locking.

Profiles are directories on disk that store persistent browser state
(cookies, localStorage, etc.).  The manager supports listing, creating,
deleting, and lock-guarding profiles so that only one task uses a profile
at a time.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from flowforge.models.task import ProfileInfo

logger = logging.getLogger(__name__)

DEFAULT_PROFILES_DIR = Path.home() / ".flowforge" / "profiles"


class ProfileManager:
    """Manage browser profiles with filesystem-backed locking.

    Parameters
    ----------
    profiles_dir : Path, optional
        Root directory for all profiles. Defaults to ``~/.flowforge/profiles/``.
    """

    def __init__(self, profiles_dir: Optional[Path] = None) -> None:
        self._dir = profiles_dir or DEFAULT_PROFILES_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Listing & lookup
    # ------------------------------------------------------------------

    def list_profiles(self) -> list[ProfileInfo]:
        """Return metadata for every profile in the profiles directory."""
        profiles: list[ProfileInfo] = []
        for entry in sorted(self._dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                profiles.append(self._build_info(entry))
        return profiles

    def get_profile(self, name: str) -> Optional[ProfileInfo]:
        """Return profile info for *name*, or ``None`` if it doesn't exist."""
        path = self._dir / name
        if not path.is_dir():
            return None
        return self._build_info(path)

    # ------------------------------------------------------------------
    # Creation & deletion
    # ------------------------------------------------------------------

    def create_profile(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> ProfileInfo:
        """Create a new empty profile.

        Parameters
        ----------
        name : str
            Profile name (must not already exist).
        description : str, optional
            Human-readable description.

        Returns
        -------
        ProfileInfo
            The newly created profile metadata.

        Raises
        ------
        FileExistsError
            If a profile with the given name already exists.
        ValueError
            If the name contains invalid characters.
        """
        self._validate_name(name)
        path = self._dir / name
        if path.exists():
            raise FileExistsError(f"Profile '{name}' already exists at {path}")

        path.mkdir(parents=True)

        meta = {
            "name": name,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": None,
        }
        (path / "profile.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        logger.info("Created profile '%s' at %s", name, path)
        return self._build_info(path)

    def delete_profile(self, name: str) -> bool:
        """Delete a profile and all its data.

        Returns False if the profile is currently locked.
        """
        path = self._dir / name
        if not path.is_dir():
            logger.warning("Profile '%s' does not exist", name)
            return False

        if self.check_lock(name):
            logger.warning("Cannot delete locked profile '%s'", name)
            return False

        shutil.rmtree(path)
        logger.info("Deleted profile '%s'", name)
        return True

    # ------------------------------------------------------------------
    # Locking
    # ------------------------------------------------------------------

    def check_lock(self, name: str) -> bool:
        """Return True if the profile is currently locked."""
        lock_file = self._dir / name / ".lock"
        return lock_file.exists()

    def acquire(self, name: str, task_id: str = "") -> bool:
        """Attempt to acquire an exclusive lock on the profile.

        Returns True if the lock was acquired, False if already locked.
        """
        lock_file = self._dir / name / ".lock"
        if lock_file.exists():
            # Check for stale lock (older than 30 minutes)
            try:
                age = time.time() - lock_file.stat().st_mtime
                if age > 1800:
                    logger.warning(
                        "Removing stale lock for profile '%s' (age: %.0fs)", name, age
                    )
                    lock_file.unlink()
                else:
                    return False
            except OSError:
                return False

        lock_data = {
            "task_id": task_id,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
        }
        lock_file.write_text(json.dumps(lock_data), encoding="utf-8")
        logger.info("Acquired lock on profile '%s' for task %s", name, task_id)
        return True

    def release(self, name: str) -> None:
        """Release the lock on a profile."""
        lock_file = self._dir / name / ".lock"
        if lock_file.exists():
            lock_file.unlink()
            logger.info("Released lock on profile '%s'", name)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_info(self, path: Path) -> ProfileInfo:
        """Construct a ProfileInfo from a profile directory."""
        lock_file = path / ".lock"
        is_locked = lock_file.exists()
        locked_by: Optional[str] = None
        if is_locked:
            try:
                lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
                locked_by = lock_data.get("task_id")
            except (json.JSONDecodeError, OSError):
                locked_by = "unknown"

        description: Optional[str] = None
        created_at: Optional[datetime] = None
        last_used_at: Optional[datetime] = None
        meta_file = path / "profile.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                description = meta.get("description")
                if meta.get("created_at"):
                    created_at = datetime.fromisoformat(meta["created_at"])
                if meta.get("last_used_at"):
                    last_used_at = datetime.fromisoformat(meta["last_used_at"])
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        return ProfileInfo(
            name=path.name,
            description=description,
            path=str(path),
            is_locked=is_locked,
            locked_by=locked_by,
            created_at=created_at,
            last_used_at=last_used_at,
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Raise ValueError if the profile name is invalid."""
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError(
                f"Invalid profile name '{name}'. "
                "Use only alphanumeric characters, hyphens, and underscores."
            )
