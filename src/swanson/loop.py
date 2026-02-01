#!/usr/bin/env python3
"""
ATDD Loop - Cross-Platform Orchestration

Main orchestration loop for Swanson Framework.
Works on macOS, Windows, and Linux.
"""

import subprocess
import sys
import time
from pathlib import Path

from swanson.config import config
from swanson.executor import Executor
from swanson.history_logger import HistoryLogger
from swanson.state_manager import StateManager


def main():
    """
    ATDD Loop:
    1. Read state - which PRD/story are we on?
    2. For each story in current PRD:
       a. Test Generation Session (if tests don't exist)
       b. Verify tests fail (expected state)
       c. Implementation Session
       d. Verify tests pass (required for completion)
       e. Update state
       f. Append to history
       g. Git commit
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
            print("✓ Queue empty. All work complete.")
            sys.exit(0)

        if not current_story:
            print(f"✓ All stories in {current_prd} complete.")
            print("Moving to next PRD...")
            if not state.load_next_prd():
                print("✓ Queue empty. All work complete.")
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
        start_time = time.time()

        if not test_file.exists():
            print(f"=== Test Generation: {current_story} ===")
            success, output = executor.execute_test_generation(prd_path, current_story)

            # Verify tests exist
            if not test_file.exists():
                print(f"\n❌ BLOCKED: Test generation failed for {current_story}")
                print("\nClaude Code output:")
                print(output)
                history.log_block(
                    current_story,
                    current_prd,
                    "Test file not created",
                    session_num,
                )
                sys.exit(1)

            # Verify tests fail (feature doesn't exist yet)
            print("\nVerifying tests fail (expected state)...")
            result = subprocess.run(
                ["pytest", str(test_file), "-v"],
                capture_output=True,
            )

            if result.returncode == 0:
                print(
                    f"\n❌ BLOCKED: Tests passing before implementation (should fail)"
                )
                print("\nThis means tests are stubbed or feature already exists.")
                print(result.stdout.decode())
                history.log_block(
                    current_story,
                    current_prd,
                    "Tests passing before implementation",
                    session_num,
                )
                sys.exit(1)

            print("✓ Tests generated and failing as expected\n")

            # Log test generation
            # Count test functions in file
            test_content = test_file.read_text()
            test_count = test_content.count("def test_")
            history.log_test_generation(
                current_story, current_prd, test_count, session_num
            )

        # Phase 2: Implementation
        print(f"=== Implementation: {current_story} ===")
        success, output = executor.execute_implementation(prd_path, current_story)

        # Verify tests pass
        print("\nVerifying tests pass...")
        result = subprocess.run(
            ["pytest", str(test_file), "-v"],
            capture_output=True,
        )

        if result.returncode != 0:
            print(f"\n❌ BLOCKED: Tests failing after implementation")
            print("\nPytest output:")
            print(result.stdout.decode())
            print(result.stderr.decode())
            history.log_block(
                current_story,
                current_prd,
                "Tests failing after implementation",
                session_num,
            )
            sys.exit(1)

        print("✓ Tests passing\n")

        # Parse test results
        stdout = result.stdout.decode()
        # Extract test counts (e.g., "5 passed in 0.12s")
        import re

        match = re.search(r"(\d+) passed", stdout)
        passed = int(match.group(1)) if match else 0

        test_results = {"passed": passed, "total": passed, "failed": 0}

        # Phase 3: Completion
        duration = int(time.time() - start_time)

        # Git commit
        print("Creating git commit...")
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

        print(f"✓ Committed: {commit_hash}\n")

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

        print(f"✓ Story {current_story} complete")
        print(f"  Duration: {duration // 60} minutes")
        print(f"  Tests: {test_results['passed']}/{test_results['total']} passed")
        print(f"  Commit: {commit_hash}")


if __name__ == "__main__":
    main()
