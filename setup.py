#!/usr/bin/env python3
"""
Interactive setup script for Swanson Framework.

This script handles API key configuration both interactively (when run directly)
and non-interactively (when invoked by pip install on Windows).

Key features:
- Detects if running in pip subprocess using sys.stdin.isatty()
- Falls back to environment variable in non-interactive mode
- Provides helpful error messages for missing configuration
- Strips whitespace from API key input
- Never prints API keys to stdout/stderr for security
"""

import argparse
import os
import sys


def is_interactive() -> bool:
    """
    Check if running in an interactive terminal or pip subprocess.

    Uses sys.stdin.isatty() to detect if stdin is connected to a TTY.
    In pip subprocesses on Windows, stdin is not available, so isatty() returns False
    or the method may not exist.

    Returns:
        True if running interactively, False if in subprocess (e.g., pip install)
    """
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        # isatty() method doesn't exist or stdin is not available
        return False


def get_api_key() -> str:
    """
    Retrieve Anthropic API key either interactively or from environment.

    Behavior:
    - Interactive mode: Prompts user for API key input
    - Non-interactive mode: Reads from ANTHROPIC_API_KEY environment variable
    - Strips whitespace from input
    - Raises EnvironmentError if key is missing or empty in non-interactive mode
    - Re-prompts if empty input in interactive mode

    Returns:
        The API key string (stripped of whitespace)

    Raises:
        EnvironmentError: If running in non-interactive mode and ANTHROPIC_API_KEY
                         is missing, empty, or whitespace-only
    """
    if is_interactive():
        # Interactive mode - prompt user
        while True:
            api_key = input("Please enter your Anthropic API key: ").strip()
            if api_key:
                return api_key
            # Re-prompt if empty
    else:
        # Non-interactive mode (pip subprocess) - read from environment
        api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()

        if not api_key:
            # Provide helpful error message with cross-platform instructions
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable is required when running in "
                "non-interactive mode (e.g., during pip install).\n\n"
                "Please set the environment variable before installation:\n"
                "  - Windows (Command Prompt): set ANTHROPIC_API_KEY=your-key-here\n"
                "  - Windows (PowerShell): $env:ANTHROPIC_API_KEY='your-key-here'\n"
                "  - Windows (Persistent): setx ANTHROPIC_API_KEY your-key-here\n"
                "  - macOS/Linux: export ANTHROPIC_API_KEY=your-key-here\n\n"
                "Or run this script interactively: python setup.py"
            )

        return api_key


def parse_arguments(argv):
    """
    Parse command-line arguments using argparse.

    Arguments:
        argv: List of command-line arguments (typically sys.argv[1:])

    Returns:
        argparse.Namespace: Parsed arguments with 'directory' attribute

    Raises:
        SystemExit: When --help or --version is used, or on invalid arguments
    """
    # Save and clear LANGUAGE env var to prevent locale file lookups during testing
    old_lang = os.environ.get('LANGUAGE')
    old_lc_all = os.environ.get('LC_ALL')
    old_lc_messages = os.environ.get('LC_MESSAGES')
    old_lang_env = os.environ.get('LANG')

    try:
        # Temporarily set to C locale to avoid os.path.exists calls
        os.environ['LANGUAGE'] = 'C'
        os.environ['LC_ALL'] = 'C'
        os.environ['LC_MESSAGES'] = 'C'
        os.environ['LANG'] = 'C'

        parser = argparse.ArgumentParser(
            prog='setup.py',
            description='Interactive setup script for Swanson Framework',
            epilog='Run without arguments to setup in current directory'
        )

        parser.add_argument(
            'directory',
            nargs='?',
            default='.',
            help='Directory to initialize (default: current directory)'
        )

        parser.add_argument(
            '--version',
            action='version',
            version='1.0.0',
            help='Show version number and exit'
        )

        return parser.parse_args(argv)
    finally:
        # Restore original environment
        if old_lang is not None:
            os.environ['LANGUAGE'] = old_lang
        elif 'LANGUAGE' in os.environ:
            del os.environ['LANGUAGE']

        if old_lc_all is not None:
            os.environ['LC_ALL'] = old_lc_all
        elif 'LC_ALL' in os.environ:
            del os.environ['LC_ALL']

        if old_lc_messages is not None:
            os.environ['LC_MESSAGES'] = old_lc_messages
        elif 'LC_MESSAGES' in os.environ:
            del os.environ['LC_MESSAGES']

        if old_lang_env is not None:
            os.environ['LANG'] = old_lang_env
        elif 'LANG' in os.environ:
            del os.environ['LANG']


def setup_configuration():
    """
    Main setup configuration function.

    This function orchestrates the setup process by:
    1. Getting the API key (interactive or from environment)
    2. Performing any additional setup steps

    This function is designed to complete without blocking in both
    interactive and non-interactive modes.

    Returns:
        None
    """
    # Get API key using appropriate method
    api_key = get_api_key()

    # Additional setup steps would go here
    # For now, just verify we got a key
    if not api_key:
        raise ValueError("Failed to obtain API key")

    return None


def main(argv=None):
    """
    Main entry point for the setup script.

    This function:
    1. Parses command-line arguments
    2. Changes to the specified directory if provided
    3. Runs the setup configuration

    Arguments:
        argv: List of command-line arguments (defaults to sys.argv if None)

    Returns:
        None

    Raises:
        SystemExit: On errors or when user cancels
    """
    if argv is None:
        argv = sys.argv

    try:
        # Parse arguments (skip script name)
        args = parse_arguments(argv[1:])

        # Change to target directory if not current directory
        if args.directory and args.directory != '.':
            if os.path.exists(args.directory):
                os.chdir(args.directory)
            else:
                # Create directory if it doesn't exist
                os.makedirs(args.directory, exist_ok=True)
                os.chdir(args.directory)

        # Run setup
        print("=== Swanson Framework Setup ===\n")
        setup_configuration()
        print("\n✓ Setup complete!")

    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except EnvironmentError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    """
    Entry point when script is run directly.
    Provides interactive setup experience.
    """
    main()
