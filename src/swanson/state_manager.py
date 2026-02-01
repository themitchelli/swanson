"""
State management for Swanson Framework.

Handles reading and updating state.json with atomic writes.
Cross-platform compatible.
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class StateManager:
    """Manages execution state in state.json."""

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            state_file: Path to state.json (defaults to ./state.json)
        """
        self.state_file = state_file or Path("state.json")
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """
        Load state from state.json.

        Returns:
            State dictionary or default state if file doesn't exist.
        """
        if not self.state_file.exists():
            return {
                "current_prd": None,
                "current_story": None,
                "completed_stories": [],
                "remaining_stories": [],
                "last_updated": None,
                "session_count": 0,
            }

        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_state(self) -> None:
        """
        Save state to state.json atomically.

        Uses temp file + rename for atomic writes.
        """
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Write to temp file in same directory as state_file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.state_file.parent, suffix=".json"
        )
        temp_path = Path(temp_path)

        try:
            with open(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)

            # Atomic rename
            temp_path.replace(self.state_file)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def initialize_state(self) -> None:
        """Create state.json if it doesn't exist."""
        if not self.state_file.exists():
            self._save_state()

    def get_current_prd(self) -> Optional[str]:
        """
        Get current PRD filename.

        Returns:
            PRD filename or None if queue is empty.
        """
        return self.state.get("current_prd")

    def get_current_story(self) -> Optional[str]:
        """
        Get current story ID.

        Returns:
            Story ID or None if no current story.
        """
        return self.state.get("current_story")

    def get_remaining_stories(self) -> List[str]:
        """
        Get list of remaining story IDs.

        Returns:
            List of story IDs not yet completed.
        """
        return self.state.get("remaining_stories", [])

    def get_completed_stories(self) -> List[str]:
        """
        Get list of completed story IDs.

        Returns:
            List of story IDs that are complete.
        """
        return self.state.get("completed_stories", [])

    def increment_session_count(self) -> int:
        """
        Increment and return session count.

        Returns:
            Updated session count.
        """
        self.state["session_count"] = self.state.get("session_count", 0) + 1
        self._save_state()
        return self.state["session_count"]

    def mark_story_complete(self, story_id: str) -> None:
        """
        Mark a story as complete.

        Moves story from remaining to completed.
        If no remaining stories, clears current_story.

        Args:
            story_id: Story ID to mark complete.
        """
        remaining = self.state.get("remaining_stories", [])
        completed = self.state.get("completed_stories", [])

        if story_id in remaining:
            remaining.remove(story_id)

        if story_id not in completed:
            completed.append(story_id)

        self.state["remaining_stories"] = remaining
        self.state["completed_stories"] = completed

        # Update current_story to next remaining or None
        if remaining:
            self.state["current_story"] = remaining[0]
        else:
            self.state["current_story"] = None

        self._save_state()

    def _verify_state_integrity(self) -> Tuple[bool, str]:
        """
        Verify that state.json has valid structure.

        Returns:
            Tuple of (is_valid, error_message)
            is_valid: True if state is valid
            error_message: Description of any issues found
        """
        try:
            # Check required fields exist
            if "current_prd" not in self.state:
                return False, "Missing 'current_prd' field"
            if "remaining_stories" not in self.state:
                return False, "Missing 'remaining_stories' field"
            if "completed_stories" not in self.state:
                return False, "Missing 'completed_stories' field"

            # Check field types
            if not isinstance(self.state.get("remaining_stories"), list):
                return False, "'remaining_stories' is not a list"
            if not isinstance(self.state.get("completed_stories"), list):
                return False, "'completed_stories' is not a list"

            return True, ""
        except Exception as e:
            return False, f"State validation error: {str(e)}"

    def _verify_completion(self, prd_path: Path) -> Tuple[bool, str]:
        """
        Verify that PRD has all stories completed.

        Checks:
        1. remaining_stories list is empty
        2. All stories from PRD are in completed_stories

        Args:
            prd_path: Path to the PRD file

        Returns:
            Tuple of (is_complete, error_message)
            is_complete: True if all stories are complete
            error_message: Description of any issues found
        """
        try:
            # Check remaining_stories is empty
            remaining = self.state.get("remaining_stories", [])
            if remaining:
                return False, f"PRD has {len(remaining)} incomplete stories: {remaining}"

            # Load PRD to verify all stories are in completed list
            if not prd_path.exists():
                return False, f"PRD file not found: {prd_path}"

            with open(prd_path, "r", encoding="utf-8") as f:
                prd_data = json.load(f)

            prd_stories = [story["id"] for story in prd_data.get("userStories", [])]
            completed = self.state.get("completed_stories", [])

            # Verify all PRD stories are completed
            for story_id in prd_stories:
                if story_id not in completed:
                    return (
                        False,
                        f"Story {story_id} not in completed_stories",
                    )

            return True, ""
        except json.JSONDecodeError as e:
            return False, f"PRD file is not valid JSON: {str(e)}"
        except Exception as e:
            return False, f"Completion verification error: {str(e)}"

    def _archive_prd_atomic(
        self, prd_path: Path, archive_dir: Path
    ) -> Tuple[bool, str]:
        """
        Archive PRD file atomically with backup and rollback.

        Steps:
        1. Verify archive directory is writable
        2. Copy PRD to archive (backup)
        3. Verify copy succeeded
        4. Delete original only after verification
        5. Rollback on any failure

        Args:
            prd_path: Source PRD file path
            archive_dir: Destination archive directory

        Returns:
            Tuple of (success, error_message)
            success: True if archiving succeeded
            error_message: Description of any errors
        """
        try:
            # Verify source exists
            if not prd_path.exists():
                return False, f"Source PRD not found: {prd_path}"

            # Verify archive directory exists and is writable
            try:
                archive_dir.mkdir(exist_ok=True)
            except Exception as e:
                return False, f"Cannot create archive directory: {str(e)}"

            # Verify archive directory is writable
            if not os.access(archive_dir, os.W_OK):
                return False, f"Archive directory is not writable: {archive_dir}"

            archive_path = archive_dir / prd_path.name

            # Copy to archive first (don't move yet)
            try:
                shutil.copy2(prd_path, archive_path)
            except Exception as e:
                return False, f"Failed to copy to archive: {str(e)}"

            # Verify copy succeeded
            if not archive_path.exists():
                return False, "Archive copy verification failed"

            # Verify copy is identical
            try:
                source_size = prd_path.stat().st_size
                archive_size = archive_path.stat().st_size
                if source_size != archive_size:
                    archive_path.unlink()  # Rollback
                    return (
                        False,
                        f"Archive copy size mismatch: {source_size} != {archive_size}",
                    )
            except Exception as e:
                archive_path.unlink()  # Rollback
                return False, f"Archive verification failed: {str(e)}"

            # Only delete original after successful copy verification
            try:
                prd_path.unlink()
            except Exception as e:
                # Rollback: delete the archive copy
                try:
                    archive_path.unlink()
                except Exception:
                    pass
                return False, f"Failed to delete original after archiving: {str(e)}"

            return True, ""
        except Exception as e:
            return False, f"Atomic archive operation failed: {str(e)}"

    def load_next_prd(self, prds_dir: Path = Path("prds")) -> bool:
        """
        Load next PRD from queue.

        Archives current PRD (with safety checks) and loads next one from prds/ directory.

        Safety checks before archiving:
        1. Verify state.json integrity
        2. Verify all stories in current PRD are completed
        3. Archive atomically with backup and rollback

        Args:
            prds_dir: Directory containing PRD files.

        Returns:
            True if next PRD loaded, False if queue is empty.
        """
        # US-001: Verify state integrity before archiving
        current_prd = self.state.get("current_prd")
        if current_prd:
            # Verify state.json structure
            is_valid, validation_error = self._verify_state_integrity()
            if not is_valid:
                logger.warning(f"Skipping archive: {validation_error}")
                # Don't archive if state is corrupted
            else:
                # US-001: Verify all stories are completed
                current_prd_path = prds_dir / current_prd
                is_complete, completion_error = self._verify_completion(current_prd_path)

                if not is_complete:
                    logger.warning(
                        f"Cannot archive {current_prd}: {completion_error}. "
                        "PRD has incomplete stories. Skipping archive to preserve work."
                    )
                    # Don't archive incomplete PRDs
                else:
                    # US-002: Archive atomically with backup and rollback
                    archive_dir = prds_dir / "archive"
                    success, archive_error = self._archive_prd_atomic(
                        current_prd_path, archive_dir
                    )

                    if not success:
                        logger.warning(f"Failed to archive {current_prd}: {archive_error}")
                        # Continue loading next PRD even if archiving failed
                    else:
                        logger.info(f"Successfully archived {current_prd}")

        # Find next PRD (sorted by filename)
        prd_files = sorted(prds_dir.glob("*.json"))

        if not prd_files:
            # Queue empty
            self.state["current_prd"] = None
            self.state["current_story"] = None
            self.state["remaining_stories"] = []
            self._save_state()
            return False

        # Load next PRD
        next_prd = prd_files[0]
        try:
            with open(next_prd, "r", encoding="utf-8") as f:
                prd_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to load PRD {next_prd.name}: invalid JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to load PRD {next_prd.name}: {str(e)}")
            return False

        # Extract story IDs
        story_ids = [story["id"] for story in prd_data.get("userStories", [])]

        self.state["current_prd"] = next_prd.name
        self.state["current_story"] = story_ids[0] if story_ids else None
        self.state["remaining_stories"] = story_ids
        self.state["completed_stories"] = []

        self._save_state()
        return True

    def initialize_from_prd(
        self, prd_filename: str, prds_dir: Path = Path("prds")
    ) -> None:
        """
        Initialize state from a specific PRD file.

        Args:
            prd_filename: Name of PRD file to load.
            prds_dir: Directory containing PRD files.
        """
        prd_path = prds_dir / prd_filename

        if not prd_path.exists():
            raise FileNotFoundError(f"PRD not found: {prd_path}")

        with open(prd_path, "r", encoding="utf-8") as f:
            prd_data = json.load(f)

        # Extract story IDs
        story_ids = [story["id"] for story in prd_data.get("userStories", [])]

        self.state["current_prd"] = prd_filename
        self.state["current_story"] = story_ids[0] if story_ids else None
        self.state["remaining_stories"] = story_ids
        self.state["completed_stories"] = []

        self._save_state()
