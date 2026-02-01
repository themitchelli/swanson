#!/usr/bin/env python3
"""
Project initialization script for Swanson Framework.

Creates .swanson/ directory with default templates in target project.
Cross-platform compatible.
"""

import shutil
import sys
from pathlib import Path


def main():
    """Initialize Swanson in a project directory."""
    print("=== Swanson Project Initialization ===\n")

    # Determine swanson framework location
    script_dir = Path(__file__).parent
    templates_dir = script_dir / "templates"

    if not templates_dir.exists():
        print(f"Error: Templates directory not found at {templates_dir}")
        print("Make sure you're running this from the Swanson framework directory.")
        sys.exit(1)

    # Determine target directory
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path.cwd()

    print(f"Initializing Swanson in: {target_dir}\n")

    # Create .swanson directory
    swanson_dir = target_dir / ".swanson"

    if swanson_dir.exists():
        print(f"Warning: {swanson_dir} already exists.")
        response = input("Overwrite? [y/N]: ")
        if response.lower() != "y":
            print("Initialization cancelled.")
            sys.exit(0)
        # Remove existing directory
        shutil.rmtree(swanson_dir)

    swanson_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {swanson_dir}")

    # Copy template files
    template_files = [
        "context-map.md",
        "product-vision.md",
        "standards.md",
        "prd-schema.md",
        "BUILD.md",
    ]

    for template_file in template_files:
        src = templates_dir / template_file
        dst = swanson_dir / template_file

        if src.exists():
            shutil.copy2(src, dst)
            print(f"✓ Copied {template_file}")
        else:
            print(f"✗ Warning: Template {template_file} not found")

    # Create prds directory
    prds_dir = target_dir / "prds"
    prds_dir.mkdir(exist_ok=True)
    print(f"✓ Created {prds_dir}")

    # Create prds/archive directory
    archive_dir = prds_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    print(f"✓ Created {archive_dir}")

    # Create tests directory
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    print(f"✓ Created {tests_dir}")

    # Create .gitkeep files
    (prds_dir / ".gitkeep").touch()
    (tests_dir / ".gitkeep").touch()

    # Create .gitignore entries
    gitignore_path = target_dir / ".gitignore"
    gitignore_entries = [
        "# Swanson Framework",
        "state.json",
        "history.md",
        ".env",
        "config.json",
        "",
    ]

    if gitignore_path.exists():
        # Append to existing .gitignore
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n")
            f.write("\n".join(gitignore_entries))
        print(f"✓ Updated {gitignore_path}")
    else:
        # Create new .gitignore
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("\n".join(gitignore_entries))
        print(f"✓ Created {gitignore_path}")

    # Success message
    print("\n=== Initialization Complete ===\n")
    print("Directory structure:")
    print(f"  {swanson_dir}/")
    print("    ├── context-map.md      (Entry point)")
    print("    ├── product-vision.md   (Strategic direction)")
    print("    ├── standards.md        (Quality expectations)")
    print("    ├── prd-schema.md       (PRD format)")
    print("    └── BUILD.md            (Build spec)")
    print(f"  {prds_dir}/               (PRD queue)")
    print(f"  {tests_dir}/              (Generated tests)")
    print()
    print("Next steps:")
    print("1. Customize .swanson/ templates for your project")
    print("2. Add PRD files to prds/ directory")
    print("3. Run: python /path/to/swanson/src/swanson/loop.py")


if __name__ == "__main__":
    main()
