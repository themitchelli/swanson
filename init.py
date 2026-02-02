#!/usr/bin/env python3
"""
Project initialization script for Swanson Framework.

This script copies template files from the templates/ directory to a target
project's .swanson/ directory, setting up the configuration and documentation
needed for autonomous development sessions.

Usage:
    python init.py [target_directory]

If no target directory is specified, uses the current directory.
"""

import sys
import shutil
from pathlib import Path
from typing import Optional


# List of template files to copy
TEMPLATE_FILES = [
    "product-vision.md",
    "standards.md",
    "context-map.md",
    "prd-schema.md",
]


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

    # Determine templates directory (relative to this script)
    script_dir = Path(__file__).parent.resolve()
    templates_dir = script_dir / "templates"

    # Validate templates directory exists
    if not templates_dir.exists():
        raise FileNotFoundError(
            f"Templates directory not found: {templates_dir}. "
            "Please ensure the templates/ directory exists in the framework installation."
        )

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


def main():
    """Main entry point for init.py script."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path.cwd()

    # Display what we're doing
    print(f"Initializing Swanson project in: {target_dir}")

    try:
        # Copy templates
        success = copy_templates(target_dir)

        if success:
            print(f"\n✓ Successfully initialized project")
            print(f"✓ Copied {len(TEMPLATE_FILES)} template files to {target_dir}/:")
            for filename in TEMPLATE_FILES:
                print(f"  - {filename}")
            print("\nNext steps:")
            print("1. Review and customize template files")
            print("2. Create PRD files in prds/")
            print("3. Run: python loop.py")
            return 0
        else:
            print("\n✗ Initialization failed")
            return 1

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
