"""
Executor for Swanson Framework.

Invokes Claude Code sessions with proper context and prompts.
Cross-platform compatible.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from swanson.config import config
from swanson.context_loader import ContextLoader
from swanson.signal_detector import SignalDetector


class Executor:
    """Executes Claude Code sessions for test generation and implementation."""

    def __init__(self):
        """Initialize executor."""
        self.context_loader = ContextLoader()
        self.signal_detector = SignalDetector()

    def execute_test_generation(
        self, prd_path: Path, story_id: str
    ) -> tuple[bool, str]:
        """
        Run test generation session.

        Args:
            prd_path: Path to PRD file
            story_id: Story ID to generate tests for

        Returns:
            Tuple of (success, output)
            success is True if TESTS_GENERATED signal detected
        """
        # Load context
        context = self.context_loader.load_test_generation_context(prd_path, story_id)

        # Create prompt
        prompt = self._create_test_generation_prompt(story_id, context)

        # Execute Claude Code
        output = self._execute_claude_code(prompt)

        # Detect signal
        signal_type, details = self.signal_detector.detect_signal(output)

        if signal_type == "TESTS_GENERATED":
            return (True, output)
        elif signal_type == "BLOCKED":
            return (False, output)
        else:
            return (False, output)

    def execute_implementation(
        self, prd_path: Path, story_id: str
    ) -> tuple[bool, str]:
        """
        Run implementation session.

        Args:
            prd_path: Path to PRD file
            story_id: Story ID to implement

        Returns:
            Tuple of (success, output)
            success is True if STORY_DONE signal detected
        """
        # Load context
        context = self.context_loader.load_implementation_context(prd_path, story_id)

        # Create prompt
        prompt = self._create_implementation_prompt(story_id, context)

        # Execute Claude Code
        output = self._execute_claude_code(prompt)

        # Detect signal
        signal_type, details = self.signal_detector.detect_signal(output)

        if signal_type == "STORY_DONE":
            return (True, output)
        elif signal_type == "BLOCKED":
            return (False, output)
        else:
            return (False, output)

    def generate_commit_message(
        self, story_id: str, prd_path: Optional[Path] = None
    ) -> str:
        """
        Generate conventional commit message for completed story.

        Args:
            story_id: Story ID that was completed
            prd_path: Optional path to PRD for extracting story title

        Returns:
            Commit message in format: <type>: <description> (<story-id>)
        """
        story_title = "completed story"

        if prd_path and prd_path.exists():
            story_title = self.context_loader.get_story_title(prd_path, story_id)

        # Determine commit type from story ID prefix
        commit_type = "feat"  # Default
        if story_id.startswith("BUG"):
            commit_type = "fix"
        elif story_id.startswith("REFACTOR"):
            commit_type = "refactor"
        elif story_id.startswith("DOC"):
            commit_type = "docs"

        # Clean title for commit message
        title_lower = story_title.lower() if story_title else "completed story"

        return f"{commit_type}: {title_lower} ({story_id})"

    def _create_test_generation_prompt(self, story_id: str, context: str) -> str:
        """
        Create prompt for test generation session.

        Args:
            story_id: Story ID
            context: Loaded context string

        Returns:
            Formatted prompt string
        """
        return f"""You are in Test Generation mode.

Context loaded:
{context}

Your task:
1. Read the acceptance criteria for story {story_id}
2. Generate pytest tests in tests/test_{story_id}.py
3. One test per acceptance criterion (minimum)
4. Follow AAA pattern (Arrange, Act, Assert)
5. Include NFR tests (performance, security, etc.)
6. Do NOT implement any features
7. Do NOT stub tests - all tests must have real assertions

When complete, output exactly:
TESTS_GENERATED: {story_id}

If you cannot proceed, output:
BLOCKED: <reason>
"""

    def _create_implementation_prompt(self, story_id: str, context: str) -> str:
        """
        Create prompt for implementation session.

        Args:
            story_id: Story ID
            context: Loaded context string

        Returns:
            Formatted prompt string
        """
        return f"""You are in Implementation mode.

Context loaded:
{context}

Your task:
1. Read the failing tests in tests/test_{story_id}.py
2. Implement features to make ALL tests pass
3. Follow ALL standards in standards.md
4. Write clean, documented code
5. Handle errors gracefully
6. Do NOT modify tests to make them pass

Run pytest tests/test_{story_id}.py to verify.

When all tests pass, output exactly:
STORY_DONE: {story_id}

If you cannot proceed, output:
BLOCKED: <reason>
"""

    def _execute_claude_code(self, prompt: str) -> str:
        """
        Execute Claude Code with given prompt.

        Args:
            prompt: Prompt text to send to Claude Code

        Returns:
            Claude Code output as string
        """
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(prompt)
            prompt_file = Path(f.name)

        try:
            # Execute claude with prompt in non-interactive mode
            # Using --model sonnet as specified in BUILD.md
            # -p: pass prompt directly
            # --print: non-interactive output mode
            # --dangerously-skip-permissions: allow file writes for autonomous operation
            # Pass API key from Swanson config to ensure correct key is used
            env = os.environ.copy()
            env["ANTHROPIC_API_KEY"] = config.api_key
            result = subprocess.run(
                [
                    "claude",
                    "-p", prompt,
                    "--model", "sonnet",
                    "--print",
                    "--dangerously-skip-permissions",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )

            # Return combined stdout and stderr
            return result.stdout + result.stderr

        finally:
            # Clean up temp file
            if prompt_file.exists():
                prompt_file.unlink()
