"""
Context loading for Swanson Framework.

Loads relevant documents for each Claude Code session type.
Cross-platform compatible.
"""

import json
from pathlib import Path
from typing import List, Optional


class ContextLoader:
    """Loads context documents for different session types."""

    def __init__(self, swanson_dir: Optional[Path] = None):
        """
        Initialize context loader.

        Args:
            swanson_dir: Path to .swanson directory (defaults to ./.swanson)
        """
        self.swanson_dir = swanson_dir or Path(".swanson")
        self.state_file = Path("state.json")

    def load_test_generation_context(self, prd_path: Path, story_id: str) -> str:
        """
        Load context for test generation session.

        Includes:
        - state.json
        - PRD content
        - prd-schema.md (for AC structure)
        - standards.md (Testing Standards section only)

        Args:
            prd_path: Path to PRD file
            story_id: Story ID to generate tests for

        Returns:
            Concatenated context string
        """
        context_parts = []

        # 1. State
        if self.state_file.exists():
            context_parts.append("=== CURRENT STATE (state.json) ===\n")
            context_parts.append(self.state_file.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 2. PRD
        if prd_path.exists():
            context_parts.append(f"=== PRD ({prd_path.name}) ===\n")
            context_parts.append(prd_path.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 3. PRD Schema
        schema_path = self.swanson_dir / "prd-schema.md"
        if schema_path.exists():
            context_parts.append("=== PRD SCHEMA (prd-schema.md) ===\n")
            context_parts.append(schema_path.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 4. Testing Standards (extract testing section only)
        standards_path = self.swanson_dir / "standards.md"
        if standards_path.exists():
            context_parts.append("=== TESTING STANDARDS (standards.md) ===\n")
            testing_section = self._extract_testing_section(standards_path)
            context_parts.append(testing_section)
            context_parts.append("\n\n")

        # 5. Story-specific instructions
        context_parts.append(f"=== CURRENT STORY ===\n")
        context_parts.append(f"Story ID: {story_id}\n\n")

        return "".join(context_parts)

    def load_implementation_context(self, prd_path: Path, story_id: str) -> str:
        """
        Load context for implementation session.

        Includes:
        - state.json
        - PRD content
        - Generated tests for this story
        - standards.md (full document)
        - Existing source files (if any)

        Args:
            prd_path: Path to PRD file
            story_id: Story ID to implement

        Returns:
            Concatenated context string
        """
        context_parts = []

        # 1. State
        if self.state_file.exists():
            context_parts.append("=== CURRENT STATE (state.json) ===\n")
            context_parts.append(self.state_file.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 2. PRD
        if prd_path.exists():
            context_parts.append(f"=== PRD ({prd_path.name}) ===\n")
            context_parts.append(prd_path.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 3. Generated Tests
        test_file = Path(f"tests/test_{story_id}.py")
        if test_file.exists():
            context_parts.append(f"=== GENERATED TESTS (test_{story_id}.py) ===\n")
            context_parts.append(test_file.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 4. Full Standards
        standards_path = self.swanson_dir / "standards.md"
        if standards_path.exists():
            context_parts.append("=== STANDARDS (standards.md) ===\n")
            context_parts.append(standards_path.read_text(encoding="utf-8"))
            context_parts.append("\n\n")

        # 5. Existing Source Files
        src_dir = Path("src")
        if src_dir.exists():
            context_parts.append("=== EXISTING SOURCE FILES ===\n")
            # Include Python files in src/ (excluding swanson framework itself)
            for py_file in src_dir.rglob("*.py"):
                # Skip swanson framework files
                if "swanson" not in py_file.parts:
                    context_parts.append(f"\n--- {py_file} ---\n")
                    context_parts.append(py_file.read_text(encoding="utf-8"))
                    context_parts.append("\n")
            context_parts.append("\n")

        # 6. Story-specific instructions
        context_parts.append(f"=== CURRENT STORY ===\n")
        context_parts.append(f"Story ID: {story_id}\n\n")

        return "".join(context_parts)

    def extract_acceptance_criteria(self, prd_path: Path, story_id: str) -> List[str]:
        """
        Extract acceptance criteria for a specific story from PRD.

        Args:
            prd_path: Path to PRD file
            story_id: Story ID to extract AC for

        Returns:
            List of acceptance criteria strings
        """
        if not prd_path.exists():
            return []

        with open(prd_path, "r", encoding="utf-8") as f:
            prd_data = json.load(f)

        # Find the story
        for story in prd_data.get("userStories", []):
            if story.get("id") == story_id:
                return story.get("acceptanceCriteria", [])

        return []

    def get_story_title(self, prd_path: Path, story_id: str) -> str:
        """
        Get story title from PRD.

        Args:
            prd_path: Path to PRD file
            story_id: Story ID

        Returns:
            Story title or empty string if not found
        """
        if not prd_path.exists():
            return ""

        with open(prd_path, "r", encoding="utf-8") as f:
            prd_data = json.load(f)

        # Find the story
        for story in prd_data.get("userStories", []):
            if story.get("id") == story_id:
                return story.get("title", "")

        return ""

    def _extract_testing_section(self, standards_path: Path) -> str:
        """
        Extract testing-related sections from standards.md.

        Args:
            standards_path: Path to standards.md

        Returns:
            Testing sections as string
        """
        content = standards_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        testing_lines = []
        in_testing_section = False
        header_level = 0

        for line in lines:
            # Detect testing-related headers
            if line.startswith("#"):
                current_level = len(line) - len(line.lstrip("#"))
                if "test" in line.lower():
                    in_testing_section = True
                    header_level = current_level
                    testing_lines.append(line)
                elif in_testing_section and current_level <= header_level:
                    # Exited testing section
                    in_testing_section = False
                elif in_testing_section:
                    testing_lines.append(line)
            elif in_testing_section:
                testing_lines.append(line)

        return "\n".join(testing_lines) if testing_lines else content
