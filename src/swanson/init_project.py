"""
Project initialization for Swanson Framework.

Copies template files from the package's templates/ directory to a target
project's .swanson/ directory and creates the full project structure.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# List of template files to copy
TEMPLATE_FILES = [
    "product-vision.md",
    "standards.md",
    "context-map.md",
    "prd-schema.md",
]

# Directories to create
PROJECT_DIRS = [
    "prds",
    "prds/archive",
    "tests",
    "tests/regression",
]


def get_templates_dir() -> Path:
    """
    Get the path to the templates directory within the installed package.

    Returns:
        Path to templates directory

    Raises:
        FileNotFoundError: If templates directory not found
    """
    # Try to find templates relative to this file (for editable installs)
    module_dir = Path(__file__).parent.resolve()
    templates_dir = module_dir / "templates"

    if templates_dir.exists():
        return templates_dir

    # Try parent directory (for flat structure during development)
    parent_templates = module_dir.parent.parent / "templates"
    if parent_templates.exists():
        return parent_templates

    # Try the original swanson-dogfood location
    dogfood_templates = module_dir.parent.parent.parent / "templates"
    if dogfood_templates.exists():
        return dogfood_templates

    raise FileNotFoundError(
        f"Templates directory not found. Searched:\n"
        f"  - {templates_dir}\n"
        f"  - {parent_templates}\n"
        f"  - {dogfood_templates}\n"
        "Please ensure templates/ directory exists."
    )


def copy_templates(target_dir: Optional[Path] = None) -> bool:
    """
    Copy all template files to target directory.

    Args:
        target_dir: Directory where template files should be copied.
                   If None, uses current directory.

    Returns:
        True if successful, False if failed.

    Raises:
        FileNotFoundError: If templates directory doesn't exist.
        RuntimeError: If template files are missing or copy fails.
    """
    # Default to current directory if not specified
    if target_dir is None:
        target_dir = Path.cwd()
    else:
        target_dir = Path(target_dir)

    # Resolve to absolute path
    target_dir = target_dir.resolve()

    # Get templates directory
    templates_dir = get_templates_dir()

    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy each template file
    copied_count = 0
    for filename in TEMPLATE_FILES:
        source_file = templates_dir / filename
        target_file = target_dir / filename

        # Check source exists
        if not source_file.exists():
            raise RuntimeError(
                f"Template file missing: {filename}. "
                f"Expected at: {source_file}"
            )

        # Copy file
        try:
            shutil.copy2(source_file, target_file)
            copied_count += 1
        except Exception as e:
            raise RuntimeError(
                f"Failed to copy {filename}: {e}"
            ) from e

    # Verify all files were copied
    if copied_count != len(TEMPLATE_FILES):
        return False

    return True


def create_project_structure(project_dir: Optional[Path] = None) -> bool:
    """
    Create the full Swanson project structure.

    Creates:
    - prds/ directory for PRD files
    - prds/archive/ for completed PRDs
    - tests/ directory (if not exists)
    - tests/regression/ for passing tests
    - state.json initial state file

    Args:
        project_dir: Root directory of the project.
                    If None, uses current directory.

    Returns:
        True if successful, False if failed.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    project_dir = project_dir.resolve()

    # Create directories
    for dir_path in PROJECT_DIRS:
        full_path = project_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

    # Create initial state.json if it doesn't exist
    state_file = project_dir / "state.json"
    if not state_file.exists():
        initial_state = {
            "current_prd": None,
            "current_story": None,
            "completed_stories": [],
            "remaining_stories": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "session_count": 0,
        }
        state_file.write_text(
            json.dumps(initial_state, indent=2),
            encoding="utf-8"
        )

    # Create initial history.md if it doesn't exist
    history_file = project_dir / "history.md"
    if not history_file.exists():
        history_content = """# Swanson Framework - Execution History

This file is an append-only audit trail. Never read during execution.

---

"""
        history_file.write_text(history_content, encoding="utf-8")

    return True


def init_project(project_dir: Optional[Path] = None) -> bool:
    """
    Initialize a complete Swanson project.

    This is the main entry point that:
    1. Creates .swanson/ with template files
    2. Creates prds/, tests/, and other directories
    3. Creates initial state.json

    Args:
        project_dir: Root directory of the project.
                    If None, uses current directory.

    Returns:
        True if successful, False if failed.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    project_dir = project_dir.resolve()

    # Create .swanson/ with templates
    swanson_dir = project_dir / ".swanson"
    if not copy_templates(swanson_dir):
        return False

    # Create project structure
    if not create_project_structure(project_dir):
        return False

    return True
