"""
Project initialization for Swanson Framework.

Copies template files from the package's templates/ directory to a target
project's .swanson/ directory.
"""

import shutil
from importlib import resources
from pathlib import Path
from typing import Optional


# List of template files to copy
TEMPLATE_FILES = [
    "product-vision.md",
    "standards.md",
    "context-map.md",
    "prd-schema.md",
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
