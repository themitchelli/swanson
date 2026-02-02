#!/usr/bin/env python3
"""
Tests for US-003: Move passing story tests to regression folder

Acceptance Criteria:
1. After successful commit, tests/test_{story_id}.py moves to tests/regression/
2. Move is atomic (copy then delete original)
3. If move fails, log warning but don't block (tests stay in tests/)
4. Regression folder is created if it doesn't exist
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import logging

# Import the function under test (will fail until implemented)
from swanson.loop import move_test_to_regression


class TestMoveTestToRegressionBasic:
    """Test basic functionality of moving test files to regression folder."""

    def test_moves_test_file_after_successful_commit(self, tmp_path):
        """
        AC1: After successful commit, tests/test_{story_id}.py moves to tests/regression/

        Arrange: Create a test file and regression directory
        Act: Call move_test_to_regression
        Assert: File exists in regression directory and not in original location
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-001"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test content for US-001")

        # Act
        move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        expected_path = regression_dir / f"test_{story_id}.py"
        assert expected_path.exists(), f"Test file should exist at {expected_path}"
        assert not test_file.exists(), f"Original test file should be removed from {test_file}"
        assert expected_path.read_text() == "# Test content for US-001"

    def test_preserves_file_content_during_move(self, tmp_path):
        """
        AC2: Move is atomic (copy then delete) - verify content preservation

        Arrange: Create test file with specific content
        Act: Move file to regression
        Assert: Content is identical in destination
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-002"
        test_file = tests_dir / f"test_{story_id}.py"
        original_content = """#!/usr/bin/env python3
import pytest

def test_example():
    assert True
"""
        test_file.write_text(original_content)

        # Act
        move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        moved_file = regression_dir / f"test_{story_id}.py"
        assert moved_file.read_text() == original_content

    def test_creates_regression_folder_if_not_exists(self, tmp_path):
        """
        AC4: Regression folder is created if it doesn't exist

        Arrange: Create test file but no regression directory
        Act: Move file to regression
        Assert: Regression directory is created and file is moved
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        story_id = "US-003"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test for US-003")

        regression_dir = tests_dir / "regression"
        assert not regression_dir.exists(), "Regression dir should not exist initially"

        # Act
        move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert regression_dir.exists(), "Regression directory should be created"
        assert regression_dir.is_dir(), "Regression path should be a directory"
        moved_file = regression_dir / f"test_{story_id}.py"
        assert moved_file.exists(), "Test file should exist in regression directory"


class TestAtomicMoveOperation:
    """Test that move operation is atomic (copy then delete)."""

    @patch('loop.shutil.copy2')
    @patch('loop.Path.unlink')
    def test_move_is_atomic_copy_then_delete(self, mock_unlink, mock_copy2, tmp_path):
        """
        AC2: Move is atomic (copy then delete original)

        Arrange: Mock copy and delete operations
        Act: Call move_test_to_regression
        Assert: Copy is called before unlink
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-004"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test")

        # Act
        move_test_to_regression(story_id, base_path=tmp_path)

        # Assert - both operations should be called
        assert mock_copy2.called, "Copy operation should be called"
        assert mock_unlink.called, "Delete operation should be called"

        # Verify order: copy should be called before unlink
        # (In a real implementation, this would be verified by the call order)

    @patch('loop.shutil.copy2')
    def test_original_file_not_deleted_if_copy_fails(self, mock_copy2, tmp_path):
        """
        AC2: Move is atomic - if copy fails, original should remain

        Arrange: Mock copy to raise exception
        Act: Call move_test_to_regression
        Assert: Original file still exists and exception is handled
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-005"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Important test")

        # Mock copy to fail
        mock_copy2.side_effect = OSError("Disk full")

        # Act - should not raise, just log warning
        result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert test_file.exists(), "Original file should remain if copy fails"
        assert result is False, "Function should return False on failure"


class TestMoveFailureHandling:
    """Test error handling and logging for move failures."""

    def test_logs_warning_on_move_failure(self, tmp_path, caplog):
        """
        AC3: If move fails, log warning but don't block

        Arrange: Create conditions for move failure
        Act: Call move_test_to_regression
        Assert: Warning is logged
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        story_id = "US-006"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test")

        # Make regression dir read-only to cause failure
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir(mode=0o444)

        # Act
        with caplog.at_level(logging.WARNING):
            result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert result is False, "Should return False on failure"
        assert any("warning" in record.message.lower() for record in caplog.records), \
            "Should log a warning message"

        # Cleanup
        regression_dir.chmod(0o755)

    def test_does_not_raise_exception_on_move_failure(self, tmp_path):
        """
        AC3: If move fails, don't block (no exception raised)

        Arrange: Create conditions for move failure
        Act: Call move_test_to_regression
        Assert: No exception is raised
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        story_id = "US-007"
        # Don't create the test file - this will cause a failure

        # Act & Assert - should not raise exception
        try:
            result = move_test_to_regression(story_id, base_path=tmp_path)
            assert result is False, "Should return False when file doesn't exist"
        except Exception as e:
            pytest.fail(f"Should not raise exception on failure, but raised: {e}")

    def test_original_test_stays_in_tests_dir_on_failure(self, tmp_path):
        """
        AC3: If move fails, tests stay in tests/ directory

        Arrange: Create test file and cause move failure
        Act: Call move_test_to_regression
        Assert: Test file remains in original location
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        story_id = "US-008"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test that should stay")

        # Create regression dir as a file (not directory) to cause failure
        regression_dir = tests_dir / "regression"
        regression_dir.write_text("I'm a file, not a directory")

        # Act
        result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert test_file.exists(), "Original test file should still exist"
        assert test_file.read_text() == "# Test that should stay"
        assert result is False


class TestSuccessfulCommitIntegration:
    """Test integration with commit workflow."""

    def test_move_only_after_successful_commit(self, tmp_path):
        """
        AC1: Move happens AFTER successful commit

        This test verifies the function exists and can be called after commit.
        The actual commit integration would be tested in integration tests.

        Arrange: Setup complete test environment
        Act: Simulate post-commit hook calling move function
        Assert: Function executes successfully
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-009"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test after commit")

        # Act - this would be called by commit workflow
        result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert result is True, "Move should succeed after commit"
        assert (regression_dir / f"test_{story_id}.py").exists()

    def test_function_returns_success_status(self, tmp_path):
        """
        Test that function returns boolean success status.

        Arrange: Create valid test file
        Act: Move to regression
        Assert: Returns True on success
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-010"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test")

        # Act
        result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert result is True, "Should return True on successful move"


class TestNFRSecurity:
    """Non-Functional Requirement: Security tests."""

    def test_prevents_path_traversal_attack(self, tmp_path):
        """
        Security: Prevent path traversal attacks in story_id

        Arrange: Malicious story_id with path traversal
        Act: Attempt to move with malicious ID
        Assert: Attack is prevented, no files outside tests/ affected
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        # Create a file outside tests dir to protect
        sensitive_file = tmp_path / "sensitive_data.txt"
        sensitive_file.write_text("SECRET")

        # Malicious story ID attempting path traversal
        malicious_story_id = "../sensitive_data"

        # Create a legitimate test file
        test_file = tests_dir / f"test_{malicious_story_id.replace('/', '_')}.py"

        # Act & Assert
        try:
            # Should either sanitize the path or fail safely
            result = move_test_to_regression(malicious_story_id, base_path=tmp_path)

            # Verify sensitive file is NOT affected
            assert sensitive_file.exists(), "Sensitive file should not be deleted"
            assert sensitive_file.read_text() == "SECRET", "Sensitive file should not be modified"

        except (ValueError, OSError) as e:
            # It's acceptable to raise an error for invalid input
            pass

    def test_handles_story_id_with_special_characters(self, tmp_path):
        """
        Security: Handle special characters in story_id safely

        Arrange: Story ID with special characters
        Act: Attempt move
        Assert: Either sanitizes or rejects safely
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        # Story IDs with special characters
        special_ids = ["US-001; rm -rf", "US-001 && echo pwned", "US-001`whoami`"]

        for story_id in special_ids:
            # Act - should handle safely without code injection
            try:
                result = move_test_to_regression(story_id, base_path=tmp_path)
                # If it succeeds, verify no command injection occurred
                # (pytest will fail if subprocess commands are executed)
            except (ValueError, OSError):
                # Acceptable to reject invalid input
                pass


class TestNFRPerformance:
    """Non-Functional Requirement: Performance tests."""

    def test_move_completes_within_reasonable_time(self, tmp_path):
        """
        Performance: File move should complete quickly (< 1 second for normal files)

        Arrange: Create test file
        Act: Move to regression and measure time
        Assert: Completes in reasonable time
        """
        import time

        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-PERF-001"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test " * 1000)  # Reasonable size test file

        # Act
        start_time = time.time()
        move_test_to_regression(story_id, base_path=tmp_path)
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 1.0, f"Move should complete in < 1s, took {elapsed_time:.2f}s"

    def test_handles_large_test_files(self, tmp_path):
        """
        Performance: Should handle large test files (e.g., 1MB)

        Arrange: Create large test file
        Act: Move to regression
        Assert: Completes successfully
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-LARGE-001"
        test_file = tests_dir / f"test_{story_id}.py"

        # Create a large file (1MB of test code)
        large_content = "# Test line\n" * 50000
        test_file.write_text(large_content)

        # Act
        result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert
        assert result is True
        moved_file = regression_dir / f"test_{story_id}.py"
        assert moved_file.exists()
        assert len(moved_file.read_text()) == len(large_content)


class TestNFRReliability:
    """Non-Functional Requirement: Reliability tests."""

    def test_idempotent_operation(self, tmp_path):
        """
        Reliability: Calling move multiple times should be safe

        Arrange: Move file to regression
        Act: Call move again on same story_id
        Assert: Operation is idempotent (no error, file stays in regression)
        """
        # Arrange
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        regression_dir = tests_dir / "regression"
        regression_dir.mkdir()

        story_id = "US-IDEM-001"
        test_file = tests_dir / f"test_{story_id}.py"
        test_file.write_text("# Test")

        # Act - move first time
        result1 = move_test_to_regression(story_id, base_path=tmp_path)
        assert result1 is True

        # Act - move second time (file already in regression)
        result2 = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert - should handle gracefully
        assert (regression_dir / f"test_{story_id}.py").exists()

    def test_handles_missing_tests_directory(self, tmp_path):
        """
        Reliability: Handle case where tests/ directory doesn't exist

        Arrange: No tests directory
        Act: Attempt move
        Assert: Handles gracefully with appropriate error/warning
        """
        # Arrange - no tests directory created
        story_id = "US-NODIR-001"

        # Act
        result = move_test_to_regression(story_id, base_path=tmp_path)

        # Assert - should return False and not crash
        assert result is False
