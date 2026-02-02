#!/usr/bin/env python3
"""
Test Suite for BUG-004: Add --help flag support to loop.py

Tests verify that loop.py properly handles command-line arguments including
--help and --version flags using argparse.

These tests MUST fail initially because the implementation doesn't exist yet.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import functions that will be added to loop.py for argument parsing
# These imports will FAIL until the implementation is added
from loop import parse_arguments, setup_argument_parser


class TestArgumentParsing:
    """Test argument parsing functionality (AC1)"""

    def test_parse_arguments_uses_argparse(self):
        """
        AC1: loop.py uses argparse to parse command-line arguments

        Verify that parse_arguments function exists and uses argparse.ArgumentParser
        """
        # Arrange
        test_args = []

        # Act
        parser = setup_argument_parser()

        # Assert
        assert parser is not None
        assert hasattr(parser, 'parse_args')
        # Verify it's an ArgumentParser instance
        import argparse
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parse_arguments_returns_namespace(self):
        """
        AC1: parse_arguments returns argparse Namespace object

        Verify that parsing empty args returns a valid Namespace
        """
        # Arrange
        test_args = []

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            args = parse_arguments()

        # Assert
        import argparse
        assert isinstance(args, argparse.Namespace)


class TestHelpFlag:
    """Test --help flag functionality (AC2)"""

    def test_help_flag_displays_usage_and_exits(self):
        """
        AC2: python loop.py --help displays usage information and exits

        Verify that --help flag displays usage information and exits with code 0
        """
        # Arrange
        test_args = ['--help']

        # Act & Assert
        with patch('sys.argv', ['loop.py'] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

    def test_help_flag_short_form_works(self):
        """
        AC2: python loop.py -h displays usage information and exits

        Verify that -h short form also works
        """
        # Arrange
        test_args = ['-h']

        # Act & Assert
        with patch('sys.argv', ['loop.py'] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

    def test_help_text_contains_usage_information(self, capsys):
        """
        AC2: Help text contains usage information

        Verify that help output includes the program name and basic usage
        """
        # Arrange
        test_args = ['--help']

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            try:
                parse_arguments()
            except SystemExit:
                pass

        # Assert
        captured = capsys.readouterr()
        help_output = captured.out
        assert 'usage:' in help_output.lower() or 'Usage:' in help_output


class TestVersionFlag:
    """Test --version flag functionality (AC3)"""

    def test_version_flag_displays_version_and_exits(self):
        """
        AC3: python loop.py --version displays version number and exits

        Verify that --version flag displays version and exits with code 0
        """
        # Arrange
        test_args = ['--version']

        # Act & Assert
        with patch('sys.argv', ['loop.py'] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

    def test_version_output_contains_version_number(self, capsys):
        """
        AC3: Version output contains a version number

        Verify that version output includes a semantic version number
        """
        # Arrange
        test_args = ['--version']

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            try:
                parse_arguments()
            except SystemExit:
                pass

        # Assert
        captured = capsys.readouterr()
        version_output = captured.out
        # Should contain a version number (e.g., 1.0.0, 0.1.0, etc.)
        import re
        version_pattern = r'\d+\.\d+\.\d+'
        assert re.search(version_pattern, version_output) is not None


class TestHelpTextContent:
    """Test help text content and formatting (AC4)"""

    def test_help_explains_directory_structure(self, capsys):
        """
        AC4: Help text explains required directory structure

        Verify that help text mentions required directories (prds/, tests/, etc.)
        """
        # Arrange
        test_args = ['--help']

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            try:
                parse_arguments()
            except SystemExit:
                pass

        # Assert
        captured = capsys.readouterr()
        help_output = captured.out.lower()

        # Should mention key directories
        assert 'prds' in help_output or 'tests' in help_output or 'directory' in help_output

    def test_help_explains_prerequisites(self, capsys):
        """
        AC4: Help text explains prerequisites

        Verify that help text mentions required files like state.json or PRD files
        """
        # Arrange
        test_args = ['--help']

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            try:
                parse_arguments()
            except SystemExit:
                pass

        # Assert
        captured = capsys.readouterr()
        help_output = captured.out.lower()

        # Should mention prerequisites
        assert any(keyword in help_output for keyword in ['state.json', 'prd', 'prerequisite', 'require'])

    def test_help_text_is_readable_and_formatted(self, capsys):
        """
        AC4: Help text is readable and properly formatted

        Verify help text contains sections and is not just a wall of text
        """
        # Arrange
        test_args = ['--help']

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            try:
                parse_arguments()
            except SystemExit:
                pass

        # Assert
        captured = capsys.readouterr()
        help_output = captured.out

        # Should have multiple lines
        lines = help_output.strip().split('\n')
        assert len(lines) >= 5  # At least 5 lines of help text

        # Should not be too long (readable)
        assert len(lines) <= 50  # Reasonable upper limit


class TestNormalOperation:
    """Test normal operation without arguments (AC5)"""

    def test_loop_runs_normally_without_arguments(self):
        """
        AC5: Loop runs normally when no arguments provided

        Verify that parse_arguments succeeds with no args and returns valid namespace
        """
        # Arrange
        test_args = []

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            args = parse_arguments()

        # Assert
        import argparse
        assert isinstance(args, argparse.Namespace)
        # Should not raise SystemExit

    def test_main_function_accepts_parsed_args(self):
        """
        AC5: main() function can accept parsed arguments

        Verify that main() can be called with parsed arguments without crashing
        """
        # Arrange
        test_args = []

        # Act
        with patch('sys.argv', ['loop.py'] + test_args):
            args = parse_arguments()

        # Assert - main should be able to handle these args
        # We're just verifying the args object is valid
        assert hasattr(args, '__dict__')

    def test_no_arguments_does_not_exit(self):
        """
        AC5: Providing no arguments does not cause premature exit

        Verify that parse_arguments without args doesn't exit the program
        """
        # Arrange
        test_args = []

        # Act - should NOT raise SystemExit
        with patch('sys.argv', ['loop.py'] + test_args):
            args = parse_arguments()

        # Assert - if we get here, no SystemExit was raised
        assert args is not None


class TestSecurityAndRobustness:
    """NFR: Security and robustness tests"""

    def test_invalid_arguments_exit_with_error(self):
        """
        NFR: Invalid arguments cause graceful error exit

        Verify that invalid args exit with non-zero code
        """
        # Arrange
        test_args = ['--invalid-flag-that-does-not-exist']

        # Act & Assert
        with patch('sys.argv', ['loop.py'] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

        # Should exit with non-zero code (error)
        assert exc_info.value.code != 0

    def test_argument_parser_has_prog_name(self):
        """
        NFR: ArgumentParser has proper program name set

        Verify that the parser has prog name set for better error messages
        """
        # Arrange & Act
        parser = setup_argument_parser()

        # Assert
        assert parser.prog is not None
        assert 'loop' in parser.prog.lower()

    def test_multiple_help_calls_are_idempotent(self):
        """
        NFR: Calling --help multiple times produces same result

        Verify that help behavior is consistent
        """
        # Arrange
        test_args = ['--help']

        # Act - call twice
        for _ in range(2):
            with patch('sys.argv', ['loop.py'] + test_args):
                try:
                    parse_arguments()
                except SystemExit as e:
                    assert e.code == 0


class TestPerformance:
    """NFR: Performance tests"""

    def test_argument_parsing_is_fast(self):
        """
        NFR: Argument parsing completes quickly

        Verify that parsing args doesn't take excessive time (< 100ms)
        """
        import time

        # Arrange
        test_args = []

        # Act
        start_time = time.time()
        with patch('sys.argv', ['loop.py'] + test_args):
            for _ in range(100):  # Run 100 times
                args = parse_arguments()
        end_time = time.time()

        # Assert - 100 iterations should complete in < 100ms
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms < 100  # Less than 100ms for 100 iterations

    def test_help_generation_is_fast(self):
        """
        NFR: Help text generation is fast

        Verify that --help completes quickly (< 50ms)
        """
        import time

        # Arrange
        test_args = ['--help']

        # Act
        start_time = time.time()
        with patch('sys.argv', ['loop.py'] + test_args):
            try:
                parse_arguments()
            except SystemExit:
                pass
        end_time = time.time()

        # Assert - should complete in < 50ms
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms < 50
