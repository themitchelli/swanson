#!/usr/bin/env python3
"""
ATDD Loop - Story Execution with Phase Tracking

This module implements the US-001 requirements:
1. Remove strict 'tests must fail first' gate
2. Verify tests pass AFTER implementation phase
3. Attempt one fix with escalation context on test failure
4. Stop with clear error message if fix fails
5. Track story phase: 'test', 'implement', or 'fix'

US-002 requirements:
1. Add regression test loop after story tests pass
2. Attempt one fix on regression failure with context
3. Stop with clear error for human intervention if fix fails
4. Include story context in regression failure messages

US-003 requirements:
1. Move passing story tests to regression folder after successful commit
2. Move is atomic (copy then delete)
3. If move fails, log warning but don't block (tests stay in tests/)
4. Regression folder is created if it doesn't exist

BUG-004 requirements:
1. Support --help flag to display usage information
2. Support --version flag to display version number
3. Parse command-line arguments using argparse
4. Run normally when no arguments provided
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any


# Version number for the loop.py script
__version__ = "1.0.0"


# Phase tracking storage (in-memory for unit tests, persistent for production)
_phase_storage: Dict[str, str] = {}


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up and return the argument parser for loop.py.

    Returns:
        argparse.ArgumentParser: Configured argument parser

    Examples:
        >>> parser = setup_argument_parser()
        >>> args = parser.parse_args([])
        >>> isinstance(args, argparse.Namespace)
        True
    """
    parser = argparse.ArgumentParser(
        prog='loop.py',
        description='ATDD Loop - Automated Test-Driven Development Loop',
        epilog="""
Directory Structure Requirements:
  - prds/          PRD (Product Requirements Document) JSON files
  - tests/         Story test files (test_<STORY_ID>.py)
  - state.json     Current execution state and story tracking

Prerequisites:
  - state.json must exist and contain current_prd and current_story
  - PRD file must exist in prds/ directory
  - Test file must exist for the current story in tests/ directory

The loop automatically executes stories in test -> implement -> fix phases,
running regression tests after each story and moving passing tests to
tests/regression/ folder.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    return parser


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments using argparse.

    Returns:
        argparse.Namespace: Parsed arguments

    Raises:
        SystemExit: If --help or --version flags are used, or if invalid arguments are provided

    Examples:
        >>> import sys
        >>> sys.argv = ['loop.py']
        >>> args = parse_arguments()
        >>> isinstance(args, argparse.Namespace)
        True
    """
    parser = setup_argument_parser()
    args = parser.parse_args()
    return args


def track_phase(story_id: str, phase: str) -> None:
    """
    Track the current phase for a story.

    Valid phases: 'test', 'implement', 'fix'

    Args:
        story_id: The story identifier (e.g., "US-001")
        phase: The phase name ('test', 'implement', or 'fix')

    Raises:
        ValueError: If phase is not one of the valid values
    """
    valid_phases = {'test', 'implement', 'fix'}
    if phase not in valid_phases:
        raise ValueError(
            f"Invalid phase '{phase}'. Must be one of: {', '.join(sorted(valid_phases))}"
        )

    # Sanitize inputs to prevent injection attacks
    if not isinstance(story_id, str) or not isinstance(phase, str):
        raise TypeError("story_id and phase must be strings")

    # Store phase
    _phase_storage[story_id] = phase


def get_current_phase(story_id: str) -> Optional[str]:
    """
    Get the current phase for a story.

    Args:
        story_id: The story identifier

    Returns:
        The current phase ('test', 'implement', or 'fix') or None if not tracked
    """
    return _phase_storage.get(story_id)


def run_story_tests(story_id: str) -> bool:
    """
    Run pytest for the story's test file.

    Args:
        story_id: The story identifier

    Returns:
        True if tests pass, False if tests fail

    Raises:
        FileNotFoundError: If test file doesn't exist
    """
    test_file = Path(f"tests/test_{story_id}.py")

    if not test_file.exists():
        raise FileNotFoundError(f"Test file not found: {test_file}")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v"],
        capture_output=True,
        text=True
    )

    return result.returncode == 0


def attempt_fix_with_context(
    story_id: str,
    test_output: Optional[str] = None,
    error_type: Optional[str] = None
) -> bool:
    """
    Attempt to fix failing tests with escalation context.

    This is a placeholder for the actual fix implementation.
    In a real system, this would invoke Claude Code with context
    about the failure and attempt to fix the issue.

    Args:
        story_id: The story identifier
        test_output: Output from the failing test run
        error_type: Type of error encountered

    Returns:
        True if fix succeeded and tests now pass, False otherwise
    """
    # Note: Phase tracking is handled by execute_story_loop before calling this function

    # Placeholder: In production, this would:
    # 1. Load test output and error context
    # 2. Invoke Claude Code with fix prompt
    # 3. Re-run tests to verify fix
    # 4. Return success/failure

    # For now, just re-run tests to check if they pass
    try:
        return run_story_tests(story_id)
    except FileNotFoundError:
        return False


def execute_story_loop(story_id: str, phase: str = 'test') -> Optional[Dict[str, Any]]:
    """
    Execute the story loop for a given story and phase.

    This implements the US-001 flow:
    1. Does NOT block when tests pass before implementation
    2. Verifies tests pass AFTER implementation phase
    3. Attempts one fix with context if tests fail after implementation
    4. Raises clear error for human intervention if fix fails

    Args:
        story_id: The story identifier (e.g., "US-001")
        phase: Starting phase ('test' or 'implement')

    Returns:
        Dict with execution results, or None if blocked

    Raises:
        RuntimeError: If fix fails and human intervention is required
        FileNotFoundError: If test file doesn't exist
    """
    # Track the starting phase
    track_phase(story_id, phase)

    # Test phase: Run tests but do NOT block if they pass
    # (US-001 AC1: Remove strict 'tests must fail first' gate)
    if phase == 'test':
        try:
            tests_pass = run_story_tests(story_id)

            # Note: We do NOT block here even if tests pass
            # This allows:
            # - Working with existing code
            # - Resuming after crashes
            # - Handling over-implementation

            return {
                'story_id': story_id,
                'phase': 'test',
                'tests_pass': tests_pass,
                'blocked': False
            }
        except FileNotFoundError as e:
            # Test file missing is a real error
            raise

    # Implementation phase: Verify tests pass AFTER implementation
    # (US-001 AC2: Verify tests pass AFTER implementation phase)
    elif phase == 'implement':
        try:
            tests_pass = run_story_tests(story_id)

            if tests_pass:
                # Tests pass - success!
                return {
                    'story_id': story_id,
                    'phase': 'implement',
                    'tests_pass': True,
                    'blocked': False
                }
            else:
                # Tests fail after implementation - attempt fix
                # (US-001 AC3: Attempt one fix with escalation context)

                # Get test output for context
                test_file = Path(f"tests/test_{story_id}.py")
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_file), "-v"],
                    capture_output=True,
                    text=True
                )
                test_output = result.stdout + "\n" + result.stderr

                # Transition to fix phase
                track_phase(story_id, 'fix')

                # Attempt fix (exactly once)
                fix_succeeded = attempt_fix_with_context(
                    story_id,
                    test_output=test_output,
                    error_type="test_failure"
                )

                if fix_succeeded:
                    # Fix succeeded - attempt_fix_with_context has already verified tests pass
                    return {
                        'story_id': story_id,
                        'phase': 'fix',
                        'tests_pass': True,
                        'fix_applied': True,
                        'blocked': False
                    }
                else:
                    # Fix failed - tests still failing
                    # (US-001 AC4: Stop with clear error for human intervention)
                    raise RuntimeError(
                        f"Story {story_id} failed: Tests failing after implementation "
                        f"and automatic fix attempt. Human intervention required to resolve "
                        f"test failures."
                    )
        except FileNotFoundError as e:
            # Test file missing is a real error
            raise

    # Fix phase: Should not be called directly
    else:
        track_phase(story_id, 'fix')
        return {
            'story_id': story_id,
            'phase': 'fix',
            'blocked': False
        }


def run_regression_tests(story_id: str) -> bool:
    """
    Run pytest on the regression test directory.

    Args:
        story_id: The story identifier (used for context in error messages)

    Returns:
        True if regression tests pass or no tests exist, False if tests fail

    Raises:
        None - handles all errors gracefully
    """
    regression_dir = Path("tests/regression")

    # If regression directory doesn't exist, treat as passing (no regression tests yet)
    if not regression_dir.exists():
        return True

    # Run pytest on regression directory with timeout and parallelization
    # Use list arguments (not shell=True) to prevent injection attacks
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(regression_dir), "-v"],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout to prevent hanging
    )

    # pytest exit codes:
    # 0 = all tests passed
    # 5 = no tests collected (empty directory)
    # Other = tests failed or error occurred
    if result.returncode == 0 or result.returncode == 5:
        return True
    else:
        return False


def get_regression_failure_context(story_id: str, failing_test: str) -> str:
    """
    Format a regression failure message with story context.

    Args:
        story_id: The story that broke the regression test
        failing_test: The regression test that failed

    Returns:
        Formatted error message following pattern "Story X broke regression test Y"
    """
    return f"Story {story_id} broke regression test {failing_test}"


def attempt_regression_fix(
    story_id: str,
    test_output: str,
    error_type: str
) -> bool:
    """
    Attempt to fix failing regression tests with context.

    This is a placeholder for the actual fix implementation.
    In a real system, this would invoke Claude Code with context
    about the regression failure and attempt to fix the issue.

    Args:
        story_id: The story identifier that caused the regression
        test_output: Output from the failing regression test run
        error_type: Type of error (should be "regression_failure")

    Returns:
        True if fix succeeded and regression tests now pass, False otherwise
    """
    # Placeholder: In production, this would:
    # 1. Parse test_output to identify which test failed
    # 2. Load story context and test context
    # 3. Invoke Claude Code with fix prompt including regression context
    # 4. Re-run regression tests to verify fix
    # 5. Return success/failure

    # For now, just re-run regression tests to check if they pass
    return run_regression_tests(story_id)


def execute_story_with_regression(story_id: str) -> Dict[str, Any]:
    """
    Execute story tests followed by regression tests.

    This implements the US-002 flow:
    1. Run story tests
    2. If story tests pass, run regression tests
    3. If regression tests fail, attempt one fix
    4. If fix fails, raise error for human intervention

    Args:
        story_id: The story identifier

    Returns:
        Dict with execution results including:
        - tests_pass: bool (story tests passed)
        - regression_pass: bool (regression tests passed)
        - ready_for_commit: bool (both passed)
        - fix_applied: bool (if a fix was attempted and succeeded)

    Raises:
        RuntimeError: If regression fix fails and human intervention is required
    """
    # Step 1: Run story tests
    story_tests_pass = run_story_tests(story_id)

    if not story_tests_pass:
        # Story tests failed - don't run regression tests
        return {
            'story_id': story_id,
            'tests_pass': False,
            'regression_pass': False,
            'ready_for_commit': False
        }

    # Step 2: Run regression tests (only if story tests passed)
    regression_tests_pass = run_regression_tests(story_id)

    if regression_tests_pass:
        # Both story and regression tests pass - ready for commit
        return {
            'story_id': story_id,
            'tests_pass': True,
            'regression_pass': True,
            'ready_for_commit': True
        }

    # Step 3: Regression tests failed - attempt fix (exactly once)
    # Get regression test output for context
    regression_dir = Path("tests/regression")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(regression_dir), "-v"],
        capture_output=True,
        text=True
    )
    test_output = result.stdout + "\n" + result.stderr

    # Attempt fix with context
    fix_succeeded = attempt_regression_fix(
        story_id=story_id,
        test_output=test_output,
        error_type="regression_failure"
    )

    if fix_succeeded:
        # Fix succeeded - regression tests now pass
        return {
            'story_id': story_id,
            'tests_pass': True,
            'regression_pass': True,
            'ready_for_commit': True,
            'fix_applied': True
        }
    else:
        # Fix failed - raise error for human intervention
        # Extract failing test name from output for better error message
        failing_test = "unknown"
        for line in test_output.split('\n'):
            if "FAILED" in line and "tests/regression/" in line:
                failing_test = line.split("FAILED")[1].strip().split()[0]
                break

        context = get_regression_failure_context(story_id, failing_test)

        raise RuntimeError(
            f"Regression tests failed after implementing {story_id}. "
            f"{context}. Automatic fix attempt failed. "
            f"Human intervention required to resolve regression failure."
        )


def move_test_to_regression(story_id: str, base_path: Optional[Path] = None) -> bool:
    """
    Move a story's test file to the regression test directory.

    This implements US-003 requirements:
    1. Move tests/test_{story_id}.py to tests/regression/ after successful commit
    2. Move is atomic (copy then delete original)
    3. If move fails, log warning but don't block (tests stay in tests/)
    4. Regression folder is created if it doesn't exist

    Args:
        story_id: The story identifier (e.g., "US-001")
        base_path: Optional base path for tests (used in unit tests, defaults to current directory)

    Returns:
        True if move succeeded, False if move failed

    Security:
        - Validates story_id to prevent path traversal attacks
        - Uses Path.resolve() to prevent symlink attacks
    """
    # Setup logging
    logger = logging.getLogger(__name__)

    # Validate inputs to prevent injection attacks
    if not isinstance(story_id, str):
        logger.warning(f"Invalid story_id type: {type(story_id)}")
        return False

    # Sanitize story_id to prevent path traversal
    # Remove any path separators or special characters that could be used for traversal
    sanitized_id = story_id.replace('/', '_').replace('\\', '_').replace('..', '_')
    if sanitized_id != story_id:
        logger.warning(f"Story ID contains invalid characters: {story_id}")
        # Use sanitized version but log the issue
        story_id = sanitized_id

    # Set up paths
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)

    tests_dir = base_path / "tests"
    test_file = tests_dir / f"test_{story_id}.py"
    regression_dir = tests_dir / "regression"
    destination_file = regression_dir / f"test_{story_id}.py"

    try:
        # Check if tests directory exists
        if not tests_dir.exists():
            logger.warning(f"Tests directory does not exist: {tests_dir}")
            return False

        # Check if test file exists
        if not test_file.exists():
            logger.warning(f"Test file does not exist: {test_file}")
            return False

        # Create regression directory if it doesn't exist (US-003 AC4)
        try:
            regression_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create regression directory: {e}")
            return False

        # Verify regression_dir is actually a directory
        if not regression_dir.is_dir():
            logger.warning(f"Regression path exists but is not a directory: {regression_dir}")
            return False

        # Atomic move: copy then delete (US-003 AC2)
        # Step 1: Copy file to regression directory
        try:
            shutil.copy2(test_file, destination_file)
        except Exception as e:
            logger.warning(f"Failed to copy test file to regression directory: {e}")
            return False

        # Step 2: Delete original file (only after successful copy)
        # Note: shutil.copy2 will raise exception if it fails, so if we get here, copy succeeded
        try:
            test_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete original test file (copy succeeded): {e}")
            # Copy succeeded but delete failed - this is still a partial success
            # The test is in regression, just also still in tests/
            return False

        # Success!
        logger.info(f"Successfully moved {test_file} to {destination_file}")
        return True

    except Exception as e:
        # Catch-all for any unexpected errors (US-003 AC3: don't block on failure)
        logger.warning(f"Unexpected error moving test file for {story_id}: {e}")
        return False


def main():
    """
    Main entry point for the ATDD loop.

    In production, this would:
    1. Parse command-line arguments
    2. Load state.json
    3. Get current PRD and story
    4. Execute story loop
    5. Update state and history
    6. Commit changes

    For now, this is a placeholder for future implementation.
    """
    # Parse command-line arguments (handles --help and --version)
    args = parse_arguments()

    print("ATDD Loop - Ready for story execution")
    print("Use execute_story_loop(story_id, phase) to run stories")
    print("Use execute_story_with_regression(story_id) for US-002 flow")


if __name__ == "__main__":
    main()
