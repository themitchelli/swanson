"""
State management for Swanson Framework.

Handles reading and updating state.json with atomic writes.
Cross-platform compatible.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


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

    def load_next_prd(self, prds_dir: Path = Path("prds")) -> bool:
        """
        Load next PRD from queue.

        Archives current PRD and loads next one from prds/ directory.

        Args:
            prds_dir: Directory containing PRD files.

        Returns:
            True if next PRD loaded, False if queue is empty.
        """
        # Archive current PRD if it exists
        current_prd = self.state.get("current_prd")
        if current_prd:
            archive_dir = prds_dir / "archive"
            archive_dir.mkdir(exist_ok=True)

            current_prd_path = prds_dir / current_prd
            if current_prd_path.exists():
                current_prd_path.rename(archive_dir / current_prd)

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
        with open(next_prd, "r", encoding="utf-8") as f:
            prd_data = json.load(f)

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
