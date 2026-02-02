#!/usr/bin/env python3
"""
Tests for US-002: Add regression test loop

Acceptance Criteria:
1. After story tests pass, loop runs pytest on tests/regression/ directory
2. If regression tests pass, proceed to commit
3. If regression tests fail, attempt one fix with context about which test broke
4. If fix fails, stop with clear error for human intervention
5. Regression failures include story context: 'Story X broke regression test Y'
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
from pathlib import Path

# Import the real module - tests MUST fail until implementation exists
from loop import (
    run_regression_tests,
    execute_story_with_regression,
    attempt_regression_fix,
)


class TestRunRegressionTestsAfterStoryTests:
    """AC1: After story tests pass, loop runs pytest on tests/regression/ directory"""

    def test_run_regression_tests_executes_pytest_on_regression_directory(self):
        """
        GIVEN story tests have passed
        WHEN run_regression_tests is called
        THEN pytest should be executed on tests/regression/ directory
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "All regression tests passed"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Act
            result = run_regression_tests(story_id)

            # Assert
            assert mock_subprocess.called
            call_args = mock_subprocess.call_args[0][0]
            # Should run pytest on tests/regression/
            assert "pytest" in str(call_args)
            assert "tests/regression" in str(call_args)
            assert result is True

    def test_run_regression_tests_returns_true_when_all_pass(self):
        """
        GIVEN regression tests in tests/regression/ directory
        WHEN all regression tests pass
        THEN run_regression_tests should return True
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.subprocess.run') as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 0  # Success
            mock_subprocess.return_value = mock_result

            # Act
            result = run_regression_tests(story_id)

            # Assert
            assert result is True

    def test_run_regression_tests_returns_false_when_tests_fail(self):
        """
        GIVEN regression tests in tests/regression/ directory
        WHEN some regression tests fail
        THEN run_regression_tests should return False
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            mock_result = Mock()
            mock_result.returncode = 1  # Failure
            mock_result.stdout = "FAILED tests/regression/test_something.py::test_feature"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act
            result = run_regression_tests(story_id)

            # Assert
            assert result is False

    def test_run_regression_tests_handles_empty_regression_directory(self):
        """
        GIVEN tests/regression/ directory is empty (no test files)
        WHEN run_regression_tests is called
        THEN it should handle gracefully (pytest returns 5 for no tests collected)
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.subprocess.run') as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 5  # pytest exit code for no tests collected
            mock_result.stdout = "collected 0 items"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Act
            result = run_regression_tests(story_id)

            # Assert
            # Empty regression suite should be treated as passing
            assert result is True


class TestProceedToCommitWhenRegressionTestsPass:
    """AC2: If regression tests pass, proceed to commit"""

    def test_execute_story_with_regression_proceeds_when_both_pass(self):
        """
        GIVEN story tests pass
        AND regression tests pass
        WHEN execute_story_with_regression is called
        THEN it should return success and indicate ready for commit
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests:
            mock_story_tests.return_value = True
            mock_regression_tests.return_value = True

            # Act
            result = execute_story_with_regression(story_id)

            # Assert
            assert result is not None
            assert result['tests_pass'] is True
            assert result['regression_pass'] is True
            assert result['ready_for_commit'] is True
            assert mock_story_tests.called
            assert mock_regression_tests.called

    def test_regression_tests_only_run_after_story_tests_pass(self):
        """
        GIVEN story tests fail
        WHEN execute_story_with_regression is called
        THEN regression tests should NOT be run (no point running them)
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests:
            mock_story_tests.return_value = False

            # Act
            result = execute_story_with_regression(story_id)

            # Assert
            # Regression tests should not be called when story tests fail
            assert not mock_regression_tests.called


class TestAttemptFixOnRegressionFailure:
    """AC3: If regression tests fail, attempt one fix with context about which test broke"""

    def test_attempt_regression_fix_receives_failure_context(self):
        """
        GIVEN regression tests fail
        WHEN attempt_regression_fix is called
        THEN it should receive context including:
        - story_id that caused the break
        - regression test output showing which test failed
        - error type
        """
        # Arrange
        story_id = "US-999"
        test_output = "FAILED tests/regression/test_old_feature.py::test_critical_path"
        error_type = "regression_failure"

        with patch('loop.run_regression_tests') as mock_regression_tests:
            mock_regression_tests.return_value = True  # Fix succeeded

            # Act
            result = attempt_regression_fix(
                story_id=story_id,
                test_output=test_output,
                error_type=error_type
            )

            # Assert - function should accept these parameters
            assert isinstance(result, bool)

    def test_execute_story_attempts_fix_when_regression_fails(self):
        """
        GIVEN story tests pass
        AND regression tests fail
        WHEN execute_story_with_regression is called
        THEN it should automatically attempt one fix
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:
            mock_story_tests.return_value = True
            mock_regression_tests.side_effect = [False, True]  # Fail first, pass after fix
            mock_fix.return_value = True

            # Mock subprocess.run for when execute_story_with_regression gets test output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "FAILED tests/regression/test_something.py::test_feature"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act
            result = execute_story_with_regression(story_id)

            # Assert
            assert mock_fix.called
            # Fix was attempted exactly once
            assert mock_fix.call_count == 1

    def test_fix_succeeds_and_regression_tests_rerun(self):
        """
        GIVEN regression tests fail on first attempt
        WHEN fix is applied
        AND regression tests pass on second attempt
        THEN execution should succeed
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:
            mock_story_tests.return_value = True
            # First call: regression fails, second call (after fix): regression passes
            mock_regression_tests.side_effect = [False, True]
            mock_fix.return_value = True

            # Mock subprocess.run for when execute_story_with_regression gets test output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "FAILED tests/regression/test_something.py::test_feature"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act
            result = execute_story_with_regression(story_id)

            # Assert
            assert result['regression_pass'] is True
            assert result['fix_applied'] is True
            assert result['ready_for_commit'] is True


class TestStopOnRegressionFixFailure:
    """AC4: If fix fails, stop with clear error for human intervention"""

    def test_execute_story_raises_error_when_regression_fix_fails(self):
        """
        GIVEN story tests pass
        AND regression tests fail
        WHEN fix attempt fails to resolve the regression
        THEN RuntimeError should be raised with clear message for human intervention
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:
            mock_story_tests.return_value = True
            mock_regression_tests.return_value = False  # Always fails
            mock_fix.return_value = False  # Fix fails

            # Mock subprocess.run for when execute_story_with_regression gets test output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "FAILED tests/regression/test_something.py::test_feature"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_with_regression(story_id)

            # Error message should mention regression failure and human intervention
            error_msg = str(exc_info.value).lower()
            assert "regression" in error_msg
            assert "human intervention" in error_msg or "manual" in error_msg

    def test_fix_only_attempted_once_before_escalation(self):
        """
        GIVEN regression tests fail
        WHEN fix attempt is made
        THEN only ONE fix attempt should be made before escalating to human
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:
            mock_story_tests.return_value = True
            mock_regression_tests.return_value = False  # Always fails
            mock_fix.return_value = False  # Fix fails

            # Mock subprocess.run for when execute_story_with_regression gets test output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "FAILED tests/regression/test_something.py::test_feature"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act
            try:
                execute_story_with_regression(story_id)
            except RuntimeError:
                pass  # Expected

            # Assert
            # Fix should be attempted exactly once, not multiple times
            assert mock_fix.call_count == 1


class TestRegressionFailureIncludesStoryContext:
    """AC5: Regression failures include story context: 'Story X broke regression test Y'"""

    def test_regression_failure_message_includes_story_id(self):
        """
        GIVEN regression test fails for a story
        WHEN error is raised or logged
        THEN message should include the story ID that caused the break
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression_tests, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:
            mock_story_tests.return_value = True
            mock_regression_tests.return_value = False
            mock_fix.return_value = False

            # Mock subprocess.run for when execute_story_with_regression gets test output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "FAILED tests/regression/test_something.py::test_feature"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_with_regression(story_id)

            # Error should mention the story ID
            error_msg = str(exc_info.value)
            assert story_id in error_msg

    def test_regression_failure_context_includes_which_test_broke(self):
        """
        GIVEN a specific regression test fails
        WHEN attempt_regression_fix is called
        THEN context should include which regression test file failed
        """
        # Arrange
        story_id = "US-999"
        failing_test = "tests/regression/test_BUG-001.py::test_interactive_mode"
        test_output = f"FAILED {failing_test}\nAssertionError: expected True"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            # First call: regression tests fail with output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = test_output
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Act
            with patch('loop.run_story_tests', return_value=True), \
                 patch('loop.attempt_regression_fix', return_value=False) as mock_fix:
                try:
                    execute_story_with_regression(story_id)
                except RuntimeError:
                    pass  # Expected

                # Assert - fix function should be called with test output
                assert mock_fix.called
                call_kwargs = mock_fix.call_args[1] if mock_fix.call_args[1] else {}
                call_args = mock_fix.call_args[0] if mock_fix.call_args[0] else []

                # The test output (with failing test name) should be passed to fix function
                assert any(failing_test in str(arg) or test_output in str(arg)
                          for arg in list(call_args) + list(call_kwargs.values()))

    def test_get_regression_failure_context_formats_message_with_story_and_test(self):
        """
        GIVEN a regression test fails
        WHEN getting failure context
        THEN message should follow format: 'Story X broke regression test Y'
        """
        # Arrange
        story_id = "US-999"
        failing_test = "test_BUG-001.py::test_interactive_mode"

        # This would be a helper function to format error messages
        from loop import get_regression_failure_context

        # Act
        context = get_regression_failure_context(story_id, failing_test)

        # Assert
        assert story_id in context
        assert failing_test in context
        # Should follow the pattern "Story X broke regression test Y"
        assert "broke" in context.lower() or "failed" in context.lower()


class TestNFRPerformance:
    """NFR: Performance - Regression tests should not significantly slow down the loop"""

    def test_regression_tests_timeout_configured(self):
        """
        GIVEN regression test suite
        WHEN running regression tests
        THEN a reasonable timeout should be configured to prevent hanging
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            # Act
            run_regression_tests(story_id)

            # Assert
            # Check that subprocess.run was called with a timeout parameter
            call_kwargs = mock_subprocess.call_args.kwargs
            assert 'timeout' in call_kwargs or mock_subprocess.call_args[1].get('timeout')

    def test_regression_tests_subprocess_args_are_list_not_string(self):
        """
        GIVEN regression test execution
        WHEN subprocess.run is called
        THEN arguments should be passed as a list (not a shell string)
        to prevent command injection attacks

        Note: Parallel execution (pytest-xdist -n flag) is a planned
        enhancement for future performance optimization.
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            # Act
            run_regression_tests(story_id)

            # Assert
            call_args = mock_subprocess.call_args[0][0]
            # Arguments must be a list/tuple for safety (prevents injection)
            assert isinstance(call_args, (list, tuple))
            # Verify the list contains expected pytest command elements
            assert any('pytest' in str(arg) for arg in call_args)


class TestNFRSecurityAndRobustness:
    """NFR: Security - Prevent injection attacks through test paths"""

    def test_regression_test_path_sanitized_to_prevent_injection(self):
        """
        GIVEN potentially malicious story_id with shell metacharacters
        WHEN run_regression_tests is called
        THEN the path should be sanitized to prevent command injection
        """
        # Arrange
        malicious_story_id = "US-001; rm -rf /"

        with patch('loop.subprocess.run') as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            # Act
            try:
                run_regression_tests(malicious_story_id)
            except (ValueError, TypeError, FileNotFoundError):
                pass  # Expected - should reject or sanitize

            # Assert
            if mock_subprocess.called:
                # If it proceeded, ensure the malicious path was sanitized
                call_args = mock_subprocess.call_args[0][0]
                # Should use list format (not string with shell=True)
                assert isinstance(call_args, (list, tuple))
                # Should not have shell=True which would enable injection
                assert not mock_subprocess.call_args.kwargs.get('shell', False)

    def test_subprocess_run_uses_list_args_not_shell_string(self):
        """
        GIVEN regression test execution
        WHEN subprocess.run is called
        THEN it should use list arguments (not shell=True) to prevent injection
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            # Act
            run_regression_tests(story_id)

            # Assert
            call_args = mock_subprocess.call_args[0][0]
            # Should be a list, not a string
            assert isinstance(call_args, (list, tuple))
            # shell should be False or not set
            assert mock_subprocess.call_args.kwargs.get('shell') is not True


class TestNFREdgeCases:
    """NFR: Edge cases and error handling"""

    def test_regression_directory_does_not_exist_yet(self):
        """
        GIVEN tests/regression/ directory doesn't exist yet (new project)
        WHEN run_regression_tests is called
        THEN it should handle gracefully (treat as no regression tests = pass)
        """
        # Arrange
        story_id = "US-999"

        with patch('pathlib.Path.exists', return_value=False):
            # Act
            result = run_regression_tests(story_id)

            # Assert
            # Non-existent regression directory should not block progress
            assert result is True

    def test_regression_tests_with_pytest_collection_errors(self):
        """
        GIVEN regression test files with syntax errors
        WHEN pytest attempts to collect tests
        THEN collection errors should be handled appropriately
        """
        # Arrange
        story_id = "US-999"

        with patch('loop.Path') as mock_path_class, \
             patch('loop.subprocess.run') as mock_subprocess:
            # Mock the regression directory to exist
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__str__.return_value = "tests/regression"
            mock_path_class.return_value = mock_path_instance

            mock_result = Mock()
            mock_result.returncode = 2  # pytest exit code 2 = collection error
            mock_result.stdout = "ERROR collecting tests/regression/test_bad.py"
            mock_result.stderr = "SyntaxError: invalid syntax"
            mock_subprocess.return_value = mock_result

            # Act
            result = run_regression_tests(story_id)

            # Assert
            # Collection errors should be treated as failures
            assert result is False
