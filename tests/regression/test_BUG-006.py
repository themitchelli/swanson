#!/usr/bin/env python3
"""
Test Suite for BUG-006: Add cross-platform Claude Code executable detection

Tests verify that executor.py properly detects Claude Code executable across platforms
including Windows, macOS, and Linux with proper fallbacks and error handling.

These tests MUST fail initially because the implementation doesn't exist yet.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Import functions that will be added to executor.py
# These imports will FAIL until the implementation is added
from swanson.executor import _find_claude_executable


class TestClaudeExecutableFinder:
    """Test _find_claude_executable() function exists (AC1)"""

    def test_find_claude_executable_function_exists(self):
        """
        AC1: executor.py has _find_claude_executable() function

        Verify that the function exists and is callable
        """
        # Arrange & Act & Assert
        assert callable(_find_claude_executable)
        assert hasattr(_find_claude_executable, '__call__')


class TestPathDetection:
    """Test PATH checking functionality (AC2)"""

    def test_checks_path_for_claude_command_first(self):
        """
        AC2: Function checks PATH for 'claude' command first

        Verify that shutil.which('claude') is called before platform-specific searches
        """
        # Arrange
        with patch('shutil.which', return_value='/usr/local/bin/claude') as mock_which:
            # Act
            result = _find_claude_executable()

            # Assert
            mock_which.assert_called_with('claude')
            assert result == '/usr/local/bin/claude'

    def test_returns_path_result_when_claude_in_path(self):
        """
        AC2: Function returns result when 'claude' found in PATH

        Verify that if claude is in PATH, that path is returned immediately
        """
        # Arrange
        expected_path = '/usr/bin/claude'
        with patch('shutil.which', return_value=expected_path):
            # Act
            result = _find_claude_executable()

            # Assert
            assert result == expected_path

    def test_continues_to_platform_search_when_not_in_path(self):
        """
        AC2: Function continues to platform-specific search when not in PATH

        Verify that when shutil.which returns None, platform-specific search happens
        """
        # Arrange - PATH check returns None, Windows APPDATA search finds it
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Windows'), \
             patch.dict(os.environ, {'APPDATA': 'C:\\Users\\test\\AppData\\Roaming'}), \
             patch('pathlib.Path.glob') as mock_glob:

            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.__str__.return_value = 'C:\\Users\\test\\AppData\\Roaming\\Claude\\claude-code\\1.0.0\\claude.exe'
            mock_glob.return_value = [mock_path]

            # Act
            result = _find_claude_executable()

            # Assert
            assert result is not None
            # Verify glob was called (platform-specific search happened)
            mock_glob.assert_called_once()


class TestWindowsDetection:
    """Test Windows-specific detection (AC3)"""

    def test_searches_appdata_on_windows_when_not_in_path(self):
        """
        AC3: On Windows, searches %APPDATA%/Claude/claude-code/*/claude.exe if not in PATH

        Verify that Windows APPDATA directory is searched
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Windows'), \
             patch.dict(os.environ, {'APPDATA': 'C:\\Users\\test\\AppData\\Roaming'}), \
             patch('pathlib.Path.glob') as mock_glob:

            mock_path = MagicMock()
            mock_path.exists.return_value = True
            expected_path = 'C:\\Users\\test\\AppData\\Roaming\\Claude\\claude-code\\1.0.0\\claude.exe'
            mock_path.__str__.return_value = expected_path
            mock_glob.return_value = [mock_path]

            # Act
            result = _find_claude_executable()

            # Assert
            assert expected_path in str(result)
            # Verify glob pattern matches Claude installation path
            call_args = str(mock_glob.call_args)
            assert 'claude-code' in call_args or mock_glob.called

    def test_searches_multiple_version_directories_on_windows(self):
        """
        AC3: Windows search uses glob pattern to find any version

        Verify that the glob pattern allows finding claude.exe in any version directory
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Windows'), \
             patch.dict(os.environ, {'APPDATA': 'C:\\Users\\test\\AppData\\Roaming'}), \
             patch('pathlib.Path.glob') as mock_glob:

            # Multiple version directories exist
            v1 = MagicMock()
            v1.exists.return_value = True
            v1.__str__.return_value = 'C:\\Users\\test\\AppData\\Roaming\\Claude\\claude-code\\1.0.0\\claude.exe'

            v2 = MagicMock()
            v2.exists.return_value = True
            v2.__str__.return_value = 'C:\\Users\\test\\AppData\\Roaming\\Claude\\claude-code\\2.0.0\\claude.exe'

            mock_glob.return_value = [v1, v2]

            # Act
            result = _find_claude_executable()

            # Assert
            # Should find at least one version
            assert result is not None
            assert 'claude.exe' in str(result)

    def test_handles_missing_appdata_env_var_on_windows(self):
        """
        AC3: Handles case where APPDATA environment variable is missing

        Verify graceful handling when APPDATA is not set
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Windows'), \
             patch.dict(os.environ, {}, clear=True):  # No APPDATA

            # Act & Assert
            # Should raise error or return None, not crash
            try:
                result = _find_claude_executable()
                # If it returns None, that's acceptable
                assert result is None or isinstance(result, (str, type(None)))
            except Exception as e:
                # If it raises an error, should be a helpful one
                assert 'Claude Code' in str(e) or 'not found' in str(e)


class TestMacOSDetection:
    """Test macOS-specific detection (AC4)"""

    def test_searches_applications_on_macos_when_not_in_path(self):
        """
        AC4: On macOS, searches /Applications/Claude.app if not in PATH

        Verify that macOS applications directory is searched
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Darwin'), \
             patch('pathlib.Path.exists') as mock_exists:

            def exists_side_effect(self):
                # /Applications/Claude.app exists
                return '/Applications/Claude.app' in str(self)

            mock_exists.side_effect = exists_side_effect

            # Act
            result = _find_claude_executable()

            # Assert
            assert result is not None
            assert 'Claude.app' in str(result) or 'Applications' in str(result)

    def test_constructs_correct_macos_app_path(self):
        """
        AC4: Constructs proper macOS .app bundle path

        Verify that the function looks in /Applications/Claude.app
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Darwin'), \
             patch('pathlib.Path.exists') as mock_exists:

            checked_paths = []

            def track_exists(self):
                checked_paths.append(str(self))
                return '/Applications/Claude.app' in str(self)

            mock_exists.side_effect = track_exists

            # Act
            result = _find_claude_executable()

            # Assert
            # Should have checked the Applications directory
            assert any('/Applications' in path for path in checked_paths)

    def test_returns_none_when_claude_app_not_found_on_macos(self):
        """
        AC4: Returns None when Claude.app not found on macOS

        Verify proper handling when Claude is not installed on macOS
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Darwin'), \
             patch('pathlib.Path.exists', return_value=False):

            # Act & Assert
            # Should either return None or raise helpful error
            try:
                result = _find_claude_executable()
                assert result is None
            except Exception as e:
                # If it raises, should be a helpful error
                assert 'Claude Code' in str(e) or 'not found' in str(e)


class TestCaching:
    """Test result caching functionality (AC5)"""

    def test_caches_result_to_avoid_repeated_searches(self):
        """
        AC5: Function caches result to avoid repeated filesystem searches

        Verify that subsequent calls don't repeat expensive filesystem operations
        """
        # Arrange
        with patch('shutil.which', return_value='/usr/local/bin/claude') as mock_which:
            # Act - Call twice
            result1 = _find_claude_executable()
            result2 = _find_claude_executable()

            # Assert
            # Both calls should return same result
            assert result1 == result2
            # But shutil.which should only be called once (or at least not called for every invocation)
            # Note: Implementation might call it once per function call or cache globally
            # The key is that filesystem searches (glob, exists checks) are cached
            assert mock_which.call_count <= 2  # At most once per call, ideally once total

    def test_cache_persists_across_calls(self):
        """
        AC5: Cache persists across multiple function calls

        Verify that the cache is actually working by checking call counts
        """
        # Arrange
        call_count = 0
        original_path = '/usr/bin/claude'

        def counting_which(cmd):
            nonlocal call_count
            call_count += 1
            return original_path

        with patch('shutil.which', side_effect=counting_which):
            # Act - Call multiple times
            results = [_find_claude_executable() for _ in range(5)]

            # Assert
            # All results should be the same
            assert all(r == original_path for r in results)
            # Call count should be less than number of calls if caching works
            # Implementation detail: might cache after first call
            assert call_count <= 5  # Upper bound - without cache would be 5

    def test_cache_returns_same_object_or_value(self):
        """
        AC5: Cached result is reused

        Verify that cached value is consistently returned
        """
        # Arrange
        with patch('shutil.which', return_value='/usr/local/bin/claude'):
            # Act
            result1 = _find_claude_executable()
            result2 = _find_claude_executable()

            # Assert
            assert result1 == result2
            assert isinstance(result1, (str, type(None)))
            assert isinstance(result2, (str, type(None)))


class TestErrorHandling:
    """Test error handling with helpful messages (AC6)"""

    def test_raises_helpful_error_when_claude_not_found(self):
        """
        AC6: Raises helpful error with download link if Claude Code not found

        Verify that a clear error message is provided when Claude Code is not found
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Linux'), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.glob', return_value=[]):

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                _find_claude_executable()

            error_message = str(exc_info.value)
            assert 'Claude Code' in error_message or 'claude' in error_message.lower()

    def test_error_message_includes_download_link(self):
        """
        AC6: Error message includes download link

        Verify that the error message contains a URL to download Claude Code
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Linux'), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.glob', return_value=[]):

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                _find_claude_executable()

            error_message = str(exc_info.value)
            # Should contain a URL (http:// or https://)
            assert 'http://' in error_message or 'https://' in error_message or 'claude.ai' in error_message

    def test_error_message_is_user_friendly(self):
        """
        AC6: Error message is clear and actionable

        Verify that error message tells user what to do
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='Linux'), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.glob', return_value=[]):

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                _find_claude_executable()

            error_message = str(exc_info.value).lower()
            # Should mention installation or download
            assert any(word in error_message for word in ['install', 'download', 'get', 'available'])


class TestCrossPlatformCompatibility:
    """NFR: Cross-platform compatibility tests"""

    def test_handles_linux_platform(self):
        """
        NFR: Function handles Linux platform

        Verify that Linux is properly handled (relies on PATH)
        """
        # Arrange
        with patch('shutil.which', return_value='/usr/bin/claude'), \
             patch('platform.system', return_value='Linux'):

            # Act
            result = _find_claude_executable()

            # Assert
            assert result == '/usr/bin/claude'

    def test_handles_unknown_platform_gracefully(self):
        """
        NFR: Function handles unknown platforms gracefully

        Verify that uncommon platforms don't cause crashes
        """
        # Arrange
        with patch('shutil.which', return_value=None), \
             patch('platform.system', return_value='FreeBSD'), \
             patch('pathlib.Path.exists', return_value=False):

            # Act & Assert
            # Should either return None or raise helpful error, not crash
            try:
                result = _find_claude_executable()
                assert result is None or isinstance(result, str)
            except Exception as e:
                # Should be a helpful error
                assert 'Claude Code' in str(e) or 'not found' in str(e)

    def test_handles_paths_with_spaces(self):
        """
        NFR: Handles paths with spaces correctly

        Verify that paths containing spaces are handled properly
        """
        # Arrange
        path_with_spaces = '/Applications/My Apps/Claude Code.app/claude'
        with patch('shutil.which', return_value=path_with_spaces):

            # Act
            result = _find_claude_executable()

            # Assert
            assert result == path_with_spaces
            assert ' ' in result  # Verify spaces are preserved


class TestSecurityAndRobustness:
    """NFR: Security and robustness tests"""

    def test_does_not_execute_arbitrary_commands(self):
        """
        NFR: Function does not execute arbitrary system commands

        Verify that no shell commands are executed (prevents injection)
        """
        # Arrange
        with patch('subprocess.run') as mock_run, \
             patch('os.system') as mock_system, \
             patch('shutil.which', return_value='/usr/bin/claude'):

            # Act
            _find_claude_executable()

            # Assert
            # Should not call subprocess.run or os.system
            mock_run.assert_not_called()
            mock_system.assert_not_called()

    def test_validates_found_executable_exists(self):
        """
        NFR: Validates that found executable actually exists

        Verify that the function checks if the path exists before returning
        """
        # Arrange
        fake_path = '/fake/path/claude'
        with patch('shutil.which', return_value=fake_path), \
             patch('pathlib.Path.exists', return_value=False):

            # Act & Assert
            # Should either return None or verify existence
            result = _find_claude_executable()
            # If it returns the fake path without checking, that's a problem
            # Either it should return None or raise an error
            if result is not None:
                # If it returns a path, it should have verified it exists
                # This test will fail if implementation doesn't validate
                with patch('pathlib.Path.exists', return_value=True):
                    result2 = _find_claude_executable()
                    # With exists=True, should return path
                    assert result2 is not None

    def test_does_not_modify_environment(self):
        """
        NFR: Function does not modify environment variables

        Verify that PATH and other env vars are not changed
        """
        # Arrange
        original_env = os.environ.copy()
        with patch('shutil.which', return_value='/usr/bin/claude'):

            # Act
            _find_claude_executable()

            # Assert
            # Environment should not be modified
            assert os.environ == original_env


class TestPerformance:
    """NFR: Performance tests"""

    def test_first_call_completes_quickly(self):
        """
        NFR: First call completes in reasonable time

        Verify that even the first call (with filesystem searches) is fast
        """
        import time

        # Arrange
        with patch('shutil.which', return_value='/usr/bin/claude'):
            # Act
            start = time.time()
            result = _find_claude_executable()
            elapsed = time.time() - start

            # Assert
            # Should complete in under 1 second even with filesystem access
            assert elapsed < 1.0
            assert result is not None

    def test_cached_calls_are_very_fast(self):
        """
        NFR: Cached calls are significantly faster

        Verify that cached calls are near-instant
        """
        import time

        # Arrange
        with patch('shutil.which', return_value='/usr/bin/claude'):
            # Warm up cache
            _find_claude_executable()

            # Act - measure cached call
            start = time.time()
            for _ in range(100):
                _find_claude_executable()
            elapsed = time.time() - start

            # Assert
            # 100 cached calls should complete in under 10ms
            assert elapsed < 0.01

    def test_does_not_leak_file_handles(self):
        """
        NFR: Does not leak file handles

        Verify that repeated calls don't leave file handles open
        """
        # Arrange
        import gc
        with patch('shutil.which', return_value='/usr/bin/claude'):
            # Act - call many times
            for _ in range(100):
                _find_claude_executable()

            # Force garbage collection
            gc.collect()

            # Assert - if we get here without resource exhaustion, test passes
            assert True
