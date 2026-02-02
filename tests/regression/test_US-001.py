#!/usr/bin/env python3
"""
Tests for US-001: Remove strict 'tests must fail first' gate

Acceptance Criteria:
1. loop.py does NOT block when tests pass before implementation
2. loop.py verifies tests pass AFTER implementation phase
3. If tests fail after implementation, attempt one fix with escalation context
4. If fix fails, stop with clear error message for human intervention
5. State tracks whether story is in 'test', 'implement', or 'fix' phase
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Import the real module - tests MUST fail until implementation exists
from loop import (
    execute_story_loop,
    run_story_tests,
    track_phase,
    get_current_phase,
    attempt_fix_with_context,
)


class TestNoBlockOnPassingTestsBeforeImplementation:
    """AC1: loop.py does NOT block when tests pass before implementation"""

    def test_loop_continues_when_tests_pass_before_implementation(self):
        """
        GIVEN tests that pass before implementation starts
        WHEN execute_story_loop is called
        THEN the loop should NOT raise an error or block
        AND should proceed to implementation phase
        """
        # Arrange
        story_id = "US-999"
        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True  # Tests pass before implementation

            # Act & Assert
            # Should NOT raise any exception
            result = execute_story_loop(story_id, phase='test')

            # Verify it didn't block and allowed continuation
            assert result is not None
            assert mock_run_tests.called

    def test_loop_handles_existing_code_with_passing_tests(self):
        """
        GIVEN existing code where tests already pass
        WHEN execute_story_loop is called for that story
        THEN loop should handle gracefully without blocking
        """
        # Arrange
        story_id = "US-EXISTING"
        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True

            # Act - should not raise exception
            execute_story_loop(story_id, phase='test')

            # Assert - verify it handled the scenario
            assert mock_run_tests.called

    def test_loop_handles_resume_after_crash_with_passing_tests(self):
        """
        GIVEN a story that was partially implemented before crash
        AND tests now pass after resuming
        WHEN execute_story_loop is called
        THEN loop should NOT block on "tests must fail first" logic
        """
        # Arrange
        story_id = "US-RESUME"
        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True  # Tests pass after crash/resume

            # Act - should not block
            result = execute_story_loop(story_id, phase='test')

            # Assert
            assert result is not None


class TestVerifyTestsPassAfterImplementation:
    """AC2: loop.py verifies tests pass AFTER implementation phase"""

    def test_loop_runs_tests_after_implementation_phase(self):
        """
        GIVEN implementation phase has completed
        WHEN loop transitions from 'implement' to verification
        THEN run_story_tests should be called to verify tests pass
        """
        # Arrange
        story_id = "US-123"
        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.get_current_phase') as mock_get_phase:

            mock_get_phase.return_value = 'implement'
            mock_run_tests.return_value = True

            # Act
            execute_story_loop(story_id, phase='implement')

            # Assert - verify tests are run after implementation
            mock_run_tests.assert_called()

    def test_loop_validates_test_success_after_implementation(self):
        """
        GIVEN implementation phase completed
        AND tests are run
        WHEN tests return passing status
        THEN loop should validate and accept the success
        """
        # Arrange
        story_id = "US-456"
        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True

            # Act
            result = execute_story_loop(story_id, phase='implement')

            # Assert - should complete successfully
            assert result is not None
            mock_run_tests.assert_called_with(story_id)

    def test_loop_fails_when_tests_fail_after_implementation(self):
        """
        GIVEN implementation phase completed
        WHEN tests are run and FAIL
        THEN loop should detect the failure and trigger fix attempt
        """
        # Arrange
        story_id = "US-FAIL"
        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False  # Tests fail
            mock_fix.return_value = True  # Fix succeeds

            # Act
            execute_story_loop(story_id, phase='implement')

            # Assert - fix should be attempted
            mock_fix.assert_called_once()


class TestSingleFixAttemptWithEscalation:
    """AC3: If tests fail after implementation, attempt one fix with escalation context"""

    def test_loop_attempts_fix_exactly_once_on_test_failure(self):
        """
        GIVEN tests fail after implementation
        WHEN fix attempt is triggered
        THEN attempt_fix_with_context should be called EXACTLY once
        AND should not retry multiple times
        """
        # Arrange
        story_id = "US-FIX"
        test_output = "AssertionError: expected 5 but got 3"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.side_effect = [False, True]  # Fail then pass after fix
            mock_fix.return_value = True

            # Act
            execute_story_loop(story_id, phase='implement')

            # Assert - fix called exactly once
            assert mock_fix.call_count == 1

    def test_fix_attempt_receives_escalation_context(self):
        """
        GIVEN tests fail after implementation
        WHEN attempt_fix_with_context is called
        THEN it should receive: story_id, test_output, error_type
        """
        # Arrange
        story_id = "US-CONTEXT"
        test_output = "TypeError: unsupported operand type"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = True

            # Act
            execute_story_loop(story_id, phase='implement')

            # Assert - verify context is passed
            call_args = mock_fix.call_args
            assert call_args is not None
            assert story_id in str(call_args)

    def test_fix_transitions_to_fix_phase_in_state(self):
        """
        GIVEN tests fail after implementation
        WHEN fix is attempted
        THEN state should track phase as 'fix'
        """
        # Arrange
        story_id = "US-PHASE"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix, \
             patch('loop.track_phase') as mock_track:

            mock_run_tests.return_value = False
            mock_fix.return_value = True

            # Act
            execute_story_loop(story_id, phase='implement')

            # Assert - verify phase tracking
            # Check if 'fix' phase was tracked
            phase_calls = [call[0][1] for call in mock_track.call_args_list if len(call[0]) > 1]
            assert 'fix' in phase_calls


class TestStopOnFixFailure:
    """AC4: If fix fails, stop with clear error message for human intervention"""

    def test_loop_stops_with_error_when_fix_fails(self):
        """
        GIVEN tests fail after implementation
        AND fix attempt also fails
        WHEN execute_story_loop completes fix attempt
        THEN should raise clear error for human intervention
        """
        # Arrange
        story_id = "US-STOP"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False  # Tests fail
            mock_fix.return_value = False  # Fix also fails

            # Act & Assert - should raise exception with clear message
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            # Verify error message mentions human intervention
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in ['human', 'intervention', 'manual', 'failed'])

    def test_error_message_includes_story_context(self):
        """
        GIVEN fix fails
        WHEN error is raised
        THEN error message should include story_id for context
        """
        # Arrange
        story_id = "US-CONTEXT-ERR"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            # Verify story_id in error
            assert story_id in str(exc_info.value)

    def test_loop_does_not_continue_after_failed_fix(self):
        """
        GIVEN fix attempt fails
        WHEN error is raised
        THEN loop should NOT attempt to continue to next phase
        """
        # Arrange
        story_id = "US-NO-CONTINUE"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix, \
             patch('loop.track_phase') as mock_track:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act
            try:
                execute_story_loop(story_id, phase='implement')
            except RuntimeError:
                pass

            # Assert - should not have tracked any phase after 'fix'
            phase_calls = [call[0][1] for call in mock_track.call_args_list if len(call[0]) > 1]
            # After fix fails, should not proceed to any other phase
            if 'fix' in phase_calls:
                fix_index = len(phase_calls) - 1 - phase_calls[::-1].index('fix')
                # No phases should be tracked after fix
                assert len(phase_calls) == fix_index + 1 or phase_calls[-1] == 'fix'


class TestPhaseStateTracking:
    """AC5: State tracks whether story is in 'test', 'implement', or 'fix' phase"""

    def test_track_phase_records_test_phase(self):
        """
        GIVEN story enters test phase
        WHEN track_phase is called
        THEN state should record phase as 'test'
        """
        # Arrange
        story_id = "US-TRACK-TEST"

        # Act
        track_phase(story_id, 'test')

        # Assert
        current_phase = get_current_phase(story_id)
        assert current_phase == 'test'

    def test_track_phase_records_implement_phase(self):
        """
        GIVEN story enters implement phase
        WHEN track_phase is called
        THEN state should record phase as 'implement'
        """
        # Arrange
        story_id = "US-TRACK-IMPL"

        # Act
        track_phase(story_id, 'implement')

        # Assert
        current_phase = get_current_phase(story_id)
        assert current_phase == 'implement'

    def test_track_phase_records_fix_phase(self):
        """
        GIVEN story enters fix phase
        WHEN track_phase is called
        THEN state should record phase as 'fix'
        """
        # Arrange
        story_id = "US-TRACK-FIX"

        # Act
        track_phase(story_id, 'fix')

        # Assert
        current_phase = get_current_phase(story_id)
        assert current_phase == 'fix'

    def test_phase_transitions_are_tracked_in_order(self):
        """
        GIVEN story progresses through phases
        WHEN phases transition: test -> implement -> fix
        THEN get_current_phase should always return the latest phase
        """
        # Arrange
        story_id = "US-TRANSITIONS"

        # Act & Assert
        track_phase(story_id, 'test')
        assert get_current_phase(story_id) == 'test'

        track_phase(story_id, 'implement')
        assert get_current_phase(story_id) == 'implement'

        track_phase(story_id, 'fix')
        assert get_current_phase(story_id) == 'fix'

    def test_get_current_phase_returns_none_for_new_story(self):
        """
        GIVEN a story that has not been tracked yet
        WHEN get_current_phase is called
        THEN should return None or raise appropriate exception
        """
        # Arrange
        story_id = "US-NEVER-TRACKED"

        # Act
        result = get_current_phase(story_id)

        # Assert - new story should have no phase or None
        assert result is None or result == ''


class TestNFR_Performance:
    """Non-Functional Requirement: Performance tests"""

    def test_execute_story_loop_completes_within_reasonable_time(self):
        """
        GIVEN a story with passing tests
        WHEN execute_story_loop runs
        THEN should complete within 5 seconds (excluding actual test execution)
        """
        import time

        # Arrange
        story_id = "US-PERF"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.return_value = True

            # Act
            start = time.time()
            execute_story_loop(story_id, phase='test')
            duration = time.time() - start

            # Assert - loop overhead should be minimal
            assert duration < 5.0, f"Loop took {duration}s, should be < 5s"

    def test_phase_tracking_is_efficient(self):
        """
        GIVEN rapid phase transitions
        WHEN track_phase is called many times
        THEN operations should complete quickly without performance degradation
        """
        import time

        # Arrange
        story_id = "US-PERF-TRACK"

        # Act
        start = time.time()
        for i in range(100):
            track_phase(f"{story_id}-{i}", 'test')
        duration = time.time() - start

        # Assert - 100 tracking operations should be fast
        assert duration < 1.0, f"100 track_phase calls took {duration}s, should be < 1s"


class TestNFR_Security:
    """Non-Functional Requirement: Security tests"""

    def test_loop_does_not_expose_sensitive_data_in_errors(self):
        """
        GIVEN test failure with potential sensitive data
        WHEN error is raised for human intervention
        THEN error message should not include raw test output that might contain secrets
        """
        # Arrange
        story_id = "US-SEC"

        with patch('loop.run_story_tests') as mock_run_tests, \
             patch('loop.attempt_fix_with_context') as mock_fix:

            mock_run_tests.return_value = False
            mock_fix.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                execute_story_loop(story_id, phase='implement')

            error_msg = str(exc_info.value)
            # Should not contain patterns that look like API keys or secrets
            assert 'sk-' not in error_msg  # Example: OpenAI key pattern
            assert 'password' not in error_msg.lower()

    def test_phase_tracking_prevents_injection_attacks(self):
        """
        GIVEN malicious input in story_id or phase
        WHEN track_phase is called
        THEN should handle safely without command injection
        """
        # Arrange - attempt various injection patterns
        malicious_inputs = [
            "US-001; rm -rf /",
            "US-001' OR '1'='1",
            "US-001`whoami`",
            "US-001$(cat /etc/passwd)",
        ]

        # Act & Assert - should not execute injected commands
        for malicious_id in malicious_inputs:
            try:
                track_phase(malicious_id, 'test')
                # If it doesn't raise, verify it stored safely
                phase = get_current_phase(malicious_id)
                assert phase == 'test'
            except (ValueError, TypeError):
                # Expected to reject malicious input
                pass


class TestNFR_Reliability:
    """Non-Functional Requirement: Reliability tests"""

    def test_loop_handles_missing_story_gracefully(self):
        """
        GIVEN a story_id that doesn't exist
        WHEN execute_story_loop is called
        THEN should raise clear error rather than crash
        """
        # Arrange
        story_id = "US-NONEXISTENT"

        with patch('loop.run_story_tests') as mock_run_tests:
            mock_run_tests.side_effect = FileNotFoundError("Test file not found")

            # Act & Assert - should handle gracefully
            with pytest.raises((FileNotFoundError, RuntimeError)):
                execute_story_loop(story_id, phase='test')

    def test_loop_recovers_from_invalid_phase_transitions(self):
        """
        GIVEN an invalid phase transition
        WHEN track_phase is called with invalid phase
        THEN should raise ValueError with clear message
        """
        # Arrange
        story_id = "US-INVALID"
        invalid_phase = "invalid_phase_name"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            track_phase(story_id, invalid_phase)

        assert 'phase' in str(exc_info.value).lower()
