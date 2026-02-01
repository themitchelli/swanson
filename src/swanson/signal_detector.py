"""
Signal detection for Swanson Framework.

Parses Claude Code output for completion signals.
Cross-platform compatible.
"""

import re
from typing import Optional, Tuple


class SignalDetector:
    """Detects completion signals in Claude Code output."""

    # Signal patterns
    TESTS_GENERATED_PATTERN = r"TESTS_GENERATED:\s*(\S+)"
    STORY_DONE_PATTERN = r"STORY_DONE:\s*(\S+)"
    BLOCKED_PATTERN = r"BLOCKED:\s*(.+)"

    def detect_signal(self, output: str) -> Tuple[str, Optional[str]]:
        """
        Parse Claude Code output for completion signals.

        Args:
            output: Claude Code session output

        Returns:
            Tuple of (signal_type, details)

            Signal types:
                - "TESTS_GENERATED" - Test file created (details = story_id)
                - "STORY_DONE" - Implementation complete (details = story_id)
                - "BLOCKED" - Cannot proceed (details = reason)
                - "UNKNOWN" - No signal detected (error state)
        """
        # Check for TESTS_GENERATED
        match = re.search(self.TESTS_GENERATED_PATTERN, output, re.MULTILINE)
        if match:
            story_id = match.group(1)
            return ("TESTS_GENERATED", story_id)

        # Check for STORY_DONE
        match = re.search(self.STORY_DONE_PATTERN, output, re.MULTILINE)
        if match:
            story_id = match.group(1)
            return ("STORY_DONE", story_id)

        # Check for BLOCKED
        match = re.search(self.BLOCKED_PATTERN, output, re.MULTILINE)
        if match:
            reason = match.group(1).strip()
            return ("BLOCKED", reason)

        # No signal detected
        return ("UNKNOWN", None)

    def extract_story_id(self, signal_line: str) -> Optional[str]:
        """
        Extract story ID from signal line.

        Args:
            signal_line: Line like "TESTS_GENERATED: US-002" or "STORY_DONE: US-002"

        Returns:
            Story ID or None if not found
        """
        # Try TESTS_GENERATED pattern
        match = re.search(self.TESTS_GENERATED_PATTERN, signal_line)
        if match:
            return match.group(1)

        # Try STORY_DONE pattern
        match = re.search(self.STORY_DONE_PATTERN, signal_line)
        if match:
            return match.group(1)

        return None

    def is_tests_generated(self, output: str) -> bool:
        """
        Check if output contains TESTS_GENERATED signal.

        Args:
            output: Claude Code session output

        Returns:
            True if TESTS_GENERATED signal found
        """
        signal_type, _ = self.detect_signal(output)
        return signal_type == "TESTS_GENERATED"

    def is_story_done(self, output: str) -> bool:
        """
        Check if output contains STORY_DONE signal.

        Args:
            output: Claude Code session output

        Returns:
            True if STORY_DONE signal found
        """
        signal_type, _ = self.detect_signal(output)
        return signal_type == "STORY_DONE"

    def is_blocked(self, output: str) -> bool:
        """
        Check if output contains BLOCKED signal.

        Args:
            output: Claude Code session output

        Returns:
            True if BLOCKED signal found
        """
        signal_type, _ = self.detect_signal(output)
        return signal_type == "BLOCKED"

    def get_block_reason(self, output: str) -> Optional[str]:
        """
        Extract block reason from output.

        Args:
            output: Claude Code session output

        Returns:
            Block reason or None if not blocked
        """
        signal_type, details = self.detect_signal(output)
        if signal_type == "BLOCKED":
            return details
        return None
