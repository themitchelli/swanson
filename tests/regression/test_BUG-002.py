#!/usr/bin/env python3
"""
Test suite for BUG-002: Fix init.py treating --help as directory name

Tests that setup.py properly parses command-line arguments using argparse
instead of treating flags like --help as directory names.

All tests import from the REAL setup.py module and will FAIL until the
feature is implemented.
"""

import sys
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import from the REAL module - these will fail if implementation doesn't exist
from setup import main, parse_arguments, setup_configuration


class TestArgumentParsing:
    """Tests for command-line argument parsing functionality."""

    def test_parse_arguments_function_exists(self):
        """
        Acceptance Criteria 1: init.py uses argparse to parse command-line arguments

        Verify that a parse_arguments function exists that uses argparse.
        This test will FAIL until the function is implemented.
        """
        # Arrange & Act
        # The import above will fail if parse_arguments doesn't exist

        # Assert - function should exist and be callable
        assert callable(parse_arguments), "parse_arguments should be a callable function"

    def test_parse_arguments_with_directory(self):
        """
        Acceptance Criteria 4: python init.py <directory> initializes the specified directory

        Verify that parse_arguments correctly parses a directory argument.
        This test will FAIL until argparse is implemented.
        """
        # Arrange
        test_dir = "/path/to/project"

        # Act
        args = parse_arguments([test_dir])

        # Assert
        assert hasattr(args, 'directory'), "Arguments should have a 'directory' attribute"
        assert args.directory == test_dir, f"Directory should be '{test_dir}'"

    def test_parse_arguments_without_arguments_defaults_to_current_dir(self):
        """
        Acceptance Criteria 5: python init.py without arguments initializes current directory

        Verify that parse_arguments defaults to current directory when no arguments provided.
        This test will FAIL until argparse is implemented.
        """
        # Arrange & Act
        args = parse_arguments([])

        # Assert
        assert hasattr(args, 'directory'), "Arguments should have a 'directory' attribute"
        assert args.directory == '.' or args.directory is None, \
            "Directory should default to current directory (. or None)"

    def test_parse_arguments_handles_help_flag(self):
        """
        Acceptance Criteria 2: python init.py --help displays usage information

        Verify that --help flag is parsed correctly and triggers help display.
        This test will FAIL until argparse is implemented.
        """
        # Arrange
        # argparse exits with SystemExit when --help is used

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments(['--help'])

        # argparse exits with code 0 for --help
        assert exc_info.value.code == 0, "--help should exit with code 0"

    def test_parse_arguments_handles_version_flag(self):
        """
        Acceptance Criteria 3: python init.py --version displays version number

        Verify that --version flag is parsed correctly and triggers version display.
        This test will FAIL until argparse is implemented.
        """
        # Arrange
        # argparse exits with SystemExit when --version is used

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments(['--version'])

        # argparse exits with code 0 for --version
        assert exc_info.value.code == 0, "--version should exit with code 0"


class TestMainFunctionIntegration:
    """Integration tests for main() function with argument parsing."""

    def test_main_function_exists(self):
        """
        Verify that a main() function exists that can be called as entry point.
        This test will FAIL until the function is implemented.
        """
        # Arrange & Act
        # The import above will fail if main doesn't exist

        # Assert
        assert callable(main), "main should be a callable function"

    @patch('os.chdir')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('setup.setup_configuration')
    @patch('setup.parse_arguments')
    def test_main_calls_parse_arguments(self, mock_parse, mock_setup, mock_exists, mock_makedirs, mock_chdir):
        """
        Verify that main() function calls parse_arguments with sys.argv.
        This test will FAIL until main() is implemented to use parse_arguments.
        """
        # Arrange
        mock_args = MagicMock()
        mock_args.directory = 'test_dir'
        mock_parse.return_value = mock_args
        mock_exists.return_value = True

        # Act
        main(['setup.py', 'test_dir'])

        # Assert
        mock_parse.assert_called_once()
        call_args = mock_parse.call_args[0][0]
        assert 'test_dir' in call_args, "parse_arguments should be called with directory argument"

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['setup.py', '--help'])
    def test_main_with_help_displays_usage(self, mock_stdout):
        """
        Acceptance Criteria 2: python init.py --help displays usage information

        Integration test verifying that running with --help shows usage.
        This test will FAIL until argparse integration is complete.
        """
        # Arrange & Act
        with pytest.raises(SystemExit) as exc_info:
            main(['setup.py', '--help'])

        # Assert
        assert exc_info.value.code == 0, "--help should exit successfully"

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['setup.py', '--version'])
    def test_main_with_version_displays_version(self, mock_stdout):
        """
        Acceptance Criteria 3: python init.py --version displays version number

        Integration test verifying that running with --version shows version.
        This test will FAIL until argparse integration is complete.
        """
        # Arrange & Act
        with pytest.raises(SystemExit) as exc_info:
            main(['setup.py', '--version'])

        # Assert
        assert exc_info.value.code == 0, "--version should exit successfully"

    @patch('setup.setup_configuration')
    @patch('setup.parse_arguments')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.chdir')
    def test_main_with_directory_changes_to_directory(self, mock_chdir, mock_exists, mock_makedirs, mock_parse, mock_setup):
        """
        Acceptance Criteria 4: python init.py <directory> initializes the specified directory

        Verify that providing a directory argument causes setup to work in that directory.
        This test will FAIL until directory argument handling is implemented.
        """
        # Arrange
        test_dir = "/path/to/project"
        mock_args = MagicMock()
        mock_args.directory = test_dir
        mock_parse.return_value = mock_args
        mock_exists.return_value = True  # Directory exists

        # Act
        main(['setup.py', test_dir])

        # Assert
        mock_chdir.assert_called_once_with(test_dir)
        mock_setup.assert_called_once()

    @patch('setup.setup_configuration')
    @patch('setup.parse_arguments')
    @patch('os.chdir')
    def test_main_without_arguments_uses_current_directory(self, mock_chdir, mock_parse, mock_setup):
        """
        Acceptance Criteria 5: python init.py without arguments initializes current directory

        Verify that running without arguments works in current directory.
        This test will FAIL until default directory handling is implemented.
        """
        # Arrange
        mock_args = MagicMock()
        mock_args.directory = '.'  # or None
        mock_parse.return_value = mock_args

        # Act
        main(['setup.py'])

        # Assert
        # Should not change directory if using current directory
        if mock_args.directory == '.':
            mock_chdir.assert_not_called()
        mock_setup.assert_called_once()


class TestNonFunctionalRequirements:
    """Non-functional requirement tests for security, performance, and robustness."""

    def test_help_flag_not_treated_as_directory(self):
        """
        Security/Correctness: Verify --help is NOT treated as a directory name.

        This is the core bug being fixed - ensure --help doesn't attempt
        to create a directory or initialize a folder named "--help".
        """
        # Arrange
        with patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:

            # Act
            with pytest.raises(SystemExit):
                parse_arguments(['--help'])

            # Assert
            mock_exists.assert_not_called()
            mock_makedirs.assert_not_called()

    def test_version_flag_not_treated_as_directory(self):
        """
        Security/Correctness: Verify --version is NOT treated as a directory name.

        Similar to --help, ensure --version doesn't attempt filesystem operations.
        """
        # Arrange
        with patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:

            # Act
            with pytest.raises(SystemExit):
                parse_arguments(['--version'])

            # Assert
            mock_exists.assert_not_called()
            mock_makedirs.assert_not_called()

    def test_argument_parsing_performance(self):
        """
        Performance: Verify argument parsing completes quickly.

        Argument parsing should be near-instantaneous (< 100ms).
        """
        # Arrange
        import time

        # Act
        start_time = time.time()
        try:
            parse_arguments(['--help'])
        except SystemExit:
            pass
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 0.1, f"Argument parsing took {elapsed_time}s, should be < 0.1s"

    def test_parse_arguments_handles_invalid_input_gracefully(self):
        """
        Robustness: Verify invalid arguments are handled gracefully.

        Invalid arguments should raise SystemExit with non-zero code, not crash.
        """
        # Arrange
        invalid_args = ['--nonexistent-flag']

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments(invalid_args)

        # Should exit with non-zero code for invalid arguments
        assert exc_info.value.code != 0, "Invalid arguments should exit with non-zero code"

    def test_help_output_contains_usage_information(self):
        """
        Usability: Verify --help output contains helpful usage information.

        Help text should include program description and available options.
        """
        # Arrange
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:

            # Act
            try:
                parse_arguments(['--help'])
            except SystemExit:
                pass

            # Assert
            help_output = mock_stdout.getvalue()
            assert 'usage:' in help_output.lower() or 'Usage:' in help_output, \
                "Help should contain usage information"

    def test_version_output_contains_version_number(self):
        """
        Usability: Verify --version output contains actual version number.

        Version output should display a semantic version number.
        """
        # Arrange
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:

            # Act
            try:
                parse_arguments(['--version'])
            except SystemExit:
                pass

            # Assert
            version_output = mock_stdout.getvalue()
            # Should contain something that looks like a version (digits and dots)
            assert any(char.isdigit() for char in version_output), \
                "Version output should contain version number"

    @patch('setup.parse_arguments')
    def test_main_handles_keyboard_interrupt(self, mock_parse):
        """
        Robustness: Verify main() handles Ctrl+C gracefully.

        Should exit cleanly without stack trace when user interrupts.
        """
        # Arrange
        mock_parse.side_effect = KeyboardInterrupt()

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            main(['setup.py'])

        # Should exit with non-zero code but handle gracefully
        assert exc_info.value.code != 0, "Keyboard interrupt should exit with non-zero code"

    def test_directory_argument_accepts_absolute_paths(self):
        """
        Robustness: Verify absolute paths work correctly.

        Should accept both relative and absolute directory paths.
        """
        # Arrange
        absolute_path = "/usr/local/project"

        # Act
        args = parse_arguments([absolute_path])

        # Assert
        assert args.directory == absolute_path, "Should accept absolute paths"

    def test_directory_argument_accepts_relative_paths(self):
        """
        Robustness: Verify relative paths work correctly.

        Should accept relative paths like ./project or ../other.
        """
        # Arrange
        relative_path = "./my-project"

        # Act
        args = parse_arguments([relative_path])

        # Assert
        assert args.directory == relative_path, "Should accept relative paths"

    def test_directory_with_spaces_handled_correctly(self):
        """
        Robustness: Verify directory names with spaces are handled.

        Should correctly parse paths like "My Project" or "C:\\Program Files\\project".
        """
        # Arrange
        dir_with_spaces = "My Project Folder"

        # Act
        args = parse_arguments([dir_with_spaces])

        # Assert
        assert args.directory == dir_with_spaces, \
            "Should handle directory names with spaces"
