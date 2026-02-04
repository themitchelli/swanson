"""
CLI interface for Swanson Framework.

Provides 'swanson init' and 'swanson run' commands.
"""

import argparse
import sys
from pathlib import Path

from swanson.init_project import copy_templates, TEMPLATE_FILES


def cmd_init(args: argparse.Namespace) -> int:
    """
    Initialize a new Swanson project.

    Copies template files to target directory's .swanson/ folder.
    """
    # Determine target directory
    if args.directory:
        target_dir = Path(args.directory).resolve()
    else:
        target_dir = Path.cwd()

    # Create .swanson subdirectory
    swanson_dir = target_dir / ".swanson"

    print(f"Initializing Swanson project in: {target_dir}")
    print(f"Creating .swanson/ directory...")

    try:
        success = copy_templates(swanson_dir)

        if success:
            print(f"\n✓ Successfully initialized project")
            print(f"✓ Copied {len(TEMPLATE_FILES)} template files to {swanson_dir}/:")
            for filename in TEMPLATE_FILES:
                print(f"  - {filename}")
            print("\nNext steps:")
            print("1. Review and customize template files in .swanson/")
            print("2. Create PRD files in prds/")
            print("3. Run: swanson run")
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


def cmd_run(args: argparse.Namespace) -> int:
    """
    Run the ATDD loop.

    Executes test generation and implementation sessions.
    """
    print("Starting Swanson ATDD loop...")
    print("(ATDD loop not yet implemented in CLI - use loop.py directly)")
    # TODO: Import and call the loop module
    return 0


def main() -> int:
    """Main entry point for swanson CLI."""
    parser = argparse.ArgumentParser(
        prog="swanson",
        description="Swanson Framework - Autonomous Development Engine",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    # init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new Swanson project",
        description="Copy template files to target directory's .swanson/ folder.",
    )
    init_parser.add_argument(
        "directory",
        nargs="?",
        help="Target directory (default: current directory)",
    )
    init_parser.set_defaults(func=cmd_init)

    # run subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Run the ATDD loop",
        description="Execute test generation and implementation sessions.",
    )
    run_parser.set_defaults(func=cmd_run)

    # Parse and execute
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
