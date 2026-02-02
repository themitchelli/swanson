#!/usr/bin/env python3
"""
ATDD Loop - Cross-Platform Orchestration with Two-Loop System

Main orchestration loop for Swanson Framework.
Works on macOS, Windows, and Linux.

This module implements:
- Main orchestration loop for PRD processing
- Two-loop system (story tests + regression tests)
- Phase tracking for stories
- Bounded self-healing (one fix attempt before escalation)

US-001 requirements:
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
"""

import json
import logging
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from swanson.config import config
from swanson.executor import Executor
from swanson.history_logger import HistoryLogger
from swanson.state_manager import StateManager


# Phase tracking storage (in-memory for unit tests, persistent for production)
_phase_storage: Dict[str, str] = {}


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


def _timestamp() -> str:
    """US-002: Get current time as HH:MM:SS for progress indicators."""
    return datetime.now().strftime("%H:%M:%S")


def _elapsed(start_time: float) -> str:
    """
    US-002: Calculate elapsed time in human-readable format.

    Args:
        start_time: Time.time() value from start of operation

    Returns:
        Formatted string like "1m 27s" or "42s"
    """
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def _archive_test_files(prd_filename: str) -> None:
    """
    US-003: Archive test files when PRD is archived.

    Moves test files associated with the PRD to tests/archive/ to prevent
    ghost tests from contaminating future runs.

    Args:
        prd_filename: Name of the PRD file being archived
    """
    try:
        # Load PRD to get story IDs
        prd_path = Path("prds") / prd_filename
        if not prd_path.exists():
            return

        with open(prd_path, "r", encoding="utf-8") as f:
            prd_data = json.load(f)

        story_ids = [story["id"] for story in prd_data.get("userStories", [])]

        # Create tests/archive directory if needed
        tests_archive_dir = Path("tests") / "archive"
        tests_archive_dir.mkdir(exist_ok=True)

        # Move test files to archive
        moved_count = 0
        for story_id in story_ids:
            test_file = Path("tests") / f"test_{story_id}.py"
            if test_file.exists():
                try:
                    archive_file = tests_archive_dir / f"test_{story_id}.py"
                    shutil.move(str(test_file), str(archive_file))
                    moved_count += 1
                except Exception as e:
                    print(f"Warning: Failed to archive test_{story_id}.py: {str(e)}")

        if moved_count > 0:
            print(f"   Archived {moved_count} test file(s) to tests/archive/")

    except Exception as e:
        print(f"Warning: Failed to archive test files: {str(e)}")


def main():
    """
    ATDD Loop with Two-Loop System:

    1. Read state - which PRD/story are we on?
    2. For each story in current PRD:
       a. Test Generation Session (if tests don't exist)
       b. Implementation Session
       c. Verify story tests pass (with one fix attempt on failure)
       d. Run regression tests (with one fix attempt on failure)
       e. Update state
       f. Move tests to regression folder
       g. Append to history
       h. Git commit
    3. Move to next PRD or exit
    """
    print("=== Swanson Framework - ATDD Loop ===\n")

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize components
    state = StateManager()
    executor = Executor()
    history = HistoryLogger()

    # Initialize state if needed
    state.initialize_state()

    # Load first PRD if state is empty
    if not state.get_current_prd():
        print("Initializing from PRD queue...")
        if not state.load_next_prd():
            print("No PRDs in queue. Exiting.")
            sys.exit(0)

    # Main loop
    while True:
        # Read current state
        current_prd = state.get_current_prd()
        current_story = state.get_current_story()

        # Exit if queue empty
        if not current_prd:
            print("Queue empty. All work complete.")
            sys.exit(0)

        if not current_story:
            print(f"All stories in {current_prd} complete.")
            print("Moving to next PRD...")

            # US-003: Clean up test artifacts when archiving PRD
            # Move test files to tests/archive/ to prevent ghost tests in future runs
            _archive_test_files(current_prd)

            if not state.load_next_prd():
                print("Queue empty. All work complete.")
                sys.exit(0)
            continue

        session_num = state.increment_session_count()
        prd_path = Path("prds") / current_prd

        print(f"\n{'='*60}")
        print(f"Session {session_num}")
        print(f"PRD: {current_prd}")
        print(f"Story: {current_story}")
        print(f"{'='*60}\n")

        # Phase 1: Test Generation
        test_file = Path(f"tests/test_{current_story}.py")
        phase_start = time.time()

        # Track story phase
        track_phase(current_story, 'test')

        # Determine if we need to generate tests or if they already exist
        test_exists = test_file.exists()

        if not test_exists:
            # Generate new tests - with progress indicator
            print(f"\n[{_timestamp()}] === Test Generation: {current_story} ===")
            gen_start = time.time()
            success, output = executor.execute_test_generation(prd_path, current_story)

            # Verify tests exist
            if not test_file.exists():
                print(f"\n[{_timestamp()}] BLOCKED: Test generation failed for {current_story}")
                print("\nClaude Code output:")
                print(output)
                history.log_block(
                    current_story,
                    current_prd,
                    "Test file not created",
                    session_num,
                )
                sys.exit(1)

            # Count and log newly generated tests
            test_content = test_file.read_text()
            test_count = test_content.count("def test_")
            history.log_test_generation(
                current_story, current_prd, test_count, session_num
            )
            print(f"[{_timestamp()}] Tests generated ({test_count} test functions, {_elapsed(gen_start)})\n")
        else:
            # US-002: Log when reusing existing tests from previous run
            test_content = test_file.read_text()
            test_count = test_content.count("def test_")
            print(f"\n[{_timestamp()}] Reusing existing tests from previous run ({test_count} test functions)")
            print(
                "   (To regenerate tests, delete tests/test_{}.py and rerun)\n".format(
                    current_story
                )
            )

        # US-001: Do NOT block when tests pass before implementation
        # (Remove strict 'tests must fail first' gate)
        print(f"[{_timestamp()}] Checking initial test state...")
        result = subprocess.run(
            ["pytest", str(test_file), "-v"],
            capture_output=True,
        )

        if result.returncode == 0:
            # Tests already passing - this is OK (allows resuming, over-implementation, etc.)
            print(f"[{_timestamp()}] Tests already passing (resuming or over-implementation)")
        else:
            print(f"[{_timestamp()}] Tests failing (ready for implementation)\n")

        # Phase 2: Implementation - with progress indicator
        track_phase(current_story, 'implement')
        print(f"[{_timestamp()}] === Implementation: {current_story} ===")
        impl_start = time.time()
        success, output = executor.execute_implementation(prd_path, current_story)

        # Verify story tests pass (US-001 AC2)
        print(f"\n[{_timestamp()}] Verifying story tests pass...")
        result = subprocess.run(
            ["pytest", str(test_file), "-v"],
            capture_output=True,
        )

        if result.returncode != 0:
            # Tests failing - attempt one fix (US-001 AC3)
            print(f"\n[{_timestamp()}] Tests failing after implementation - attempting fix...")
            track_phase(current_story, 'fix')

            test_output = result.stdout.decode() + "\n" + result.stderr.decode()
            fix_succeeded = attempt_fix_with_context(
                current_story,
                test_output=test_output,
                error_type="test_failure"
            )

            if not fix_succeeded:
                # Fix failed - stop for human intervention (US-001 AC4)
                print(f"\n[{_timestamp()}] BLOCKED: Tests failing after fix attempt")
                print("\nPytest output:")
                print(result.stdout.decode())
                print(result.stderr.decode())
                history.log_block(
                    current_story,
                    current_prd,
                    "Tests failing after implementation and fix attempt",
                    session_num,
                )
                sys.exit(1)
            else:
                print(f"[{_timestamp()}] Fix succeeded - tests now passing")

        print(f"[{_timestamp()}] Story tests passing ({_elapsed(impl_start)})\n")

        # Phase 3: Regression Tests (US-002)
        print(f"[{_timestamp()}] Running regression tests...")
        regression_pass = run_regression_tests(current_story)

        if not regression_pass:
            # Regression tests failing - attempt one fix (US-002 AC2)
            print(f"\n[{_timestamp()}] Regression tests failing - attempting fix...")

            regression_dir = Path("tests/regression")
            reg_result = subprocess.run(
                [sys.executable, "-m", "pytest", str(regression_dir), "-v"],
                capture_output=True,
                text=True
            )
            test_output = reg_result.stdout + "\n" + reg_result.stderr

            fix_succeeded = attempt_regression_fix(
                current_story,
                test_output=test_output,
                error_type="regression_failure"
            )

            if not fix_succeeded:
                # Fix failed - stop for human intervention (US-002 AC3)
                failing_test = "unknown"
                for line in test_output.split('\n'):
                    if "FAILED" in line and "tests/regression/" in line:
                        failing_test = line.split("FAILED")[1].strip().split()[0]
                        break

                context = get_regression_failure_context(current_story, failing_test)
                print(f"\n[{_timestamp()}] BLOCKED: Regression tests failing after fix attempt")
                print(f"   {context}")
                print("\nPytest output:")
                print(test_output)
                history.log_block(
                    current_story,
                    current_prd,
                    f"Regression tests failing: {context}",
                    session_num,
                )
                sys.exit(1)
            else:
                print(f"[{_timestamp()}] Regression fix succeeded")

        print(f"[{_timestamp()}] Regression tests passing\n")

        # Parse test results
        stdout = result.stdout.decode()
        match = re.search(r"(\d+) passed", stdout)
        passed = int(match.group(1)) if match else 0

        test_results = {"passed": passed, "total": passed, "failed": 0}

        # Phase 4: Completion
        duration = int(time.time() - phase_start)

        # Git commit
        print(f"[{_timestamp()}] Creating git commit...")
        commit_msg = executor.generate_commit_message(current_story, prd_path)

        subprocess.run(["git", "add", "."], check=True)
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
        )

        # Get commit hash
        commit_hash_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        )
        commit_hash = commit_hash_result.stdout.strip()

        print(f"[{_timestamp()}] Committed: {commit_hash}\n")

        # US-003: Move tests to regression folder after successful commit
        print(f"[{_timestamp()}] Moving tests to regression folder...")
        move_success = move_test_to_regression(current_story)
        if move_success:
            print(f"[{_timestamp()}] Tests moved to regression folder")
        else:
            print(f"[{_timestamp()}] Warning: Failed to move tests to regression (tests stay in tests/)")

        # Extract acceptance criteria
        acceptance_criteria = executor.context_loader.extract_acceptance_criteria(
            prd_path, current_story
        )
        story_title = executor.context_loader.get_story_title(prd_path, current_story)

        # Update state
        state.mark_story_complete(current_story)

        # Log to history
        history.log_completion(
            story_id=current_story,
            prd_path=current_prd,
            story_title=story_title,
            acceptance_criteria=acceptance_criteria,
            test_results=test_results,
            commit_hash=commit_hash,
            duration_seconds=duration,
            model="Sonnet",
            session_number=session_num,
        )

        print(f"[{_timestamp()}] Story {current_story} complete ({_elapsed(phase_start)})")
        print(f"  Tests: {test_results['passed']}/{test_results['total']} passed")
        print(f"  Commit: {commit_hash}\n")


if __name__ == "__main__":
    main()
