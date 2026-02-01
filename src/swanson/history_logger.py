"""
History logging for Swanson Framework.

Appends to history.md with completion and block entries.
Cross-platform compatible.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class HistoryLogger:
    """Manages append-only history.md audit trail."""

    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize history logger.

        Args:
            history_file: Path to history.md (defaults to ./history.md)
        """
        self.history_file = history_file or Path("history.md")
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create history.md with header if it doesn't exist."""
        if not self.history_file.exists():
            with open(self.history_file, "w", encoding="utf-8") as f:
                f.write("# Swanson Framework - Execution History\n\n")
                f.write(
                    "This file is an append-only audit trail. Never read during execution.\n\n"
                )
                f.write("---\n\n")

    def log_completion(
        self,
        story_id: str,
        prd_path: str,
        story_title: str,
        acceptance_criteria: List[str],
        test_results: Dict,
        commit_hash: str,
        duration_seconds: int,
        model: str = "Sonnet",
        session_number: int = 0,
    ) -> None:
        """
        Append completion entry to history.md.

        Args:
            story_id: Story ID (e.g., "US-002")
            prd_path: Path to PRD file
            story_title: Title of the story
            acceptance_criteria: List of AC that were met
            test_results: Dict with test execution results
            commit_hash: Git commit hash
            duration_seconds: Time taken in seconds
            model: Model used (default: "Sonnet")
            session_number: Session count
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        duration_min = duration_seconds // 60

        entry = f"## {timestamp} - Story {story_id} Complete\n\n"
        entry += f"- **PRD:** {prd_path}\n"
        entry += f"- **Story:** {story_id} - {story_title}\n"
        entry += f"- **Duration:** {duration_min} minutes\n"
        entry += f"- **Tests:** {test_results.get('passed', 0)}/{test_results.get('total', 0)} passed\n"
        entry += f"- **Commit:** {commit_hash}\n"
        entry += f"- **Model:** {model}\n"
        entry += f"- **Session:** {session_number}\n\n"

        if acceptance_criteria:
            entry += "### Acceptance Criteria Met\n"
            for ac in acceptance_criteria:
                entry += f"- [x] {ac}\n"
            entry += "\n"

        entry += "---\n\n"

        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_block(
        self, story_id: str, prd_path: str, reason: str, session_number: int = 0
    ) -> None:
        """
        Append block entry to history.md.

        Args:
            story_id: Story ID that was blocked
            prd_path: Path to PRD file
            reason: Reason for blocking
            session_number: Session count
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        entry = f"## {timestamp} - Story {story_id} BLOCKED\n\n"
        entry += f"- **PRD:** {prd_path}\n"
        entry += f"- **Story:** {story_id}\n"
        entry += f"- **Session:** {session_number}\n"
        entry += f"- **Reason:** {reason}\n\n"
        entry += "---\n\n"

        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_test_generation(
        self, story_id: str, prd_path: str, test_count: int, session_number: int = 0
    ) -> None:
        """
        Append test generation entry to history.md.

        Args:
            story_id: Story ID
            prd_path: Path to PRD file
            test_count: Number of tests generated
            session_number: Session count
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        entry = f"## {timestamp} - Tests Generated for {story_id}\n\n"
        entry += f"- **PRD:** {prd_path}\n"
        entry += f"- **Story:** {story_id}\n"
        entry += f"- **Tests Generated:** {test_count}\n"
        entry += f"- **Session:** {session_number}\n\n"
        entry += "---\n\n"

        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(entry)
