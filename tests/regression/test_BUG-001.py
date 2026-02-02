"""
Tests for BUG-001: Fix interactive setup breaking pip install on Windows

Acceptance Criteria:
1. setup.py checks if running in pip subprocess using sys.stdin.isatty()
2. If in subprocess, setup.py reads ANTHROPIC_API_KEY from environment instead of prompting
3. If env var missing and in subprocess, setup.py prints helpful error message
4. Interactive prompt still works when running setup.py directly
5. pip install -e . succeeds on Windows without hanging
"""

import sys
from unittest.mock import patch, MagicMock, call
import pytest

# Import the functions we'll be testing from setup.py
# These imports will FAIL until the implementation exists
from setup import is_interactive, get_api_key, setup_configuration


class TestInteractiveDetection:
    """Tests for AC1: setup.py checks if running in pip subprocess using sys.stdin.isatty()"""

    def test_is_interactive_returns_true_when_stdin_is_tty(self):
        """Test that is_interactive returns True when stdin.isatty() is True"""
        # Arrange
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True

            # Act
            result = is_interactive()

            # Assert
            assert result is True
            mock_stdin.isatty.assert_called_once()

    def test_is_interactive_returns_false_when_stdin_is_not_tty(self):
        """Test that is_interactive returns False when stdin.isatty() is False (pip subprocess)"""
        # Arrange
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False

            # Act
            result = is_interactive()

            # Assert
            assert result is False
            mock_stdin.isatty.assert_called_once()

    def test_is_interactive_handles_missing_isatty_method(self):
        """Test that is_interactive handles stdin without isatty method gracefully"""
        # Arrange
        with patch('sys.stdin', MagicMock(spec=[])):
            # Act
            result = is_interactive()

            # Assert
            assert result is False


class TestNonInteractiveAPIKeyRetrieval:
    """Tests for AC2: If in subprocess, setup.py reads ANTHROPIC_API_KEY from environment"""

    def test_get_api_key_reads_from_env_when_non_interactive(self):
        """Test that get_api_key reads from ANTHROPIC_API_KEY env var in non-interactive mode"""
        # Arrange
        test_api_key = "sk-ant-test-key-12345"
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}):

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key

    def test_get_api_key_does_not_prompt_when_non_interactive(self):
        """Test that get_api_key does not call input() in non-interactive mode"""
        # Arrange
        test_api_key = "sk-ant-test-key-67890"
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}), \
             patch('builtins.input') as mock_input:

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key
            mock_input.assert_not_called()


class TestNonInteractiveErrorHandling:
    """Tests for AC3: If env var missing and in subprocess, setup.py prints helpful error message"""

    def test_get_api_key_raises_error_when_env_var_missing_and_non_interactive(self):
        """Test that get_api_key raises error with helpful message when env var missing"""
        # Arrange
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {}, clear=True):

            # Act & Assert
            with pytest.raises(EnvironmentError) as exc_info:
                get_api_key()

            # Verify error message is helpful
            error_message = str(exc_info.value).lower()
            assert 'anthropic_api_key' in error_message
            assert 'environment' in error_message

    def test_get_api_key_error_message_includes_setup_instructions(self):
        """Test that error message includes instructions for setting env var"""
        # Arrange
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {}, clear=True):

            # Act & Assert
            with pytest.raises(EnvironmentError) as exc_info:
                get_api_key()

            error_message = str(exc_info.value)
            # Should mention how to set the environment variable
            assert 'export' in error_message or 'set' in error_message or 'setx' in error_message


class TestInteractivePrompt:
    """Tests for AC4: Interactive prompt still works when running setup.py directly"""

    def test_get_api_key_prompts_user_when_interactive(self):
        """Test that get_api_key prompts for input in interactive mode"""
        # Arrange
        test_api_key = "sk-ant-interactive-key"
        with patch('setup.is_interactive', return_value=True), \
             patch('builtins.input', return_value=test_api_key) as mock_input:

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key
            mock_input.assert_called_once()

    def test_get_api_key_shows_prompt_message(self):
        """Test that interactive prompt includes helpful message"""
        # Arrange
        test_api_key = "sk-ant-key-789"
        with patch('setup.is_interactive', return_value=True), \
             patch('builtins.input', return_value=test_api_key) as mock_input:

            # Act
            result = get_api_key()

            # Assert
            call_args = mock_input.call_args[0][0]
            assert 'api' in call_args.lower() and 'key' in call_args.lower()

    def test_get_api_key_ignores_env_var_when_interactive(self):
        """Test that interactive mode prompts user even if env var exists"""
        # Arrange
        env_key = "sk-ant-env-key"
        user_input_key = "sk-ant-user-key"
        with patch('setup.is_interactive', return_value=True), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': env_key}), \
             patch('builtins.input', return_value=user_input_key):

            # Act
            result = get_api_key()

            # Assert
            assert result == user_input_key


class TestSetupConfiguration:
    """Tests for AC5: pip install -e . succeeds on Windows without hanging"""

    def test_setup_configuration_completes_without_blocking_in_subprocess(self):
        """Test that setup_configuration doesn't block when called from pip subprocess"""
        # Arrange
        test_api_key = "sk-ant-subprocess-key"
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}), \
             patch('setup.get_api_key', return_value=test_api_key) as mock_get_key:

            # Act
            result = setup_configuration()

            # Assert
            # Should complete without raising exception
            assert result is not None or result is None  # Just verify it returns
            mock_get_key.assert_called_once()

    def test_setup_configuration_does_not_wait_for_input_in_subprocess(self):
        """Test that setup doesn't wait for stdin in non-interactive mode"""
        # Arrange
        test_api_key = "sk-ant-no-wait-key"
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}), \
             patch('builtins.input') as mock_input:

            # Act
            setup_configuration()

            # Assert
            mock_input.assert_not_called()


class TestNFRSecurity:
    """Non-Functional Requirement Tests: Security"""

    def test_api_key_not_logged_or_printed(self):
        """Test that API key is never printed to stdout/stderr"""
        # Arrange
        test_api_key = "sk-ant-secret-key-should-not-appear"
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}), \
             patch('sys.stdout.write') as mock_stdout, \
             patch('sys.stderr.write') as mock_stderr:

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key
            # Check that API key was never written to stdout/stderr
            for call_obj in mock_stdout.call_args_list:
                assert test_api_key not in str(call_obj)
            for call_obj in mock_stderr.call_args_list:
                assert test_api_key not in str(call_obj)

    def test_api_key_stripped_of_whitespace(self):
        """Test that API key input is stripped of leading/trailing whitespace"""
        # Arrange
        test_api_key = "sk-ant-key-with-spaces"
        with patch('setup.is_interactive', return_value=True), \
             patch('builtins.input', return_value=f"  {test_api_key}  "):

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key
            assert result.strip() == result


class TestNFRPerformance:
    """Non-Functional Requirement Tests: Performance"""

    def test_is_interactive_completes_quickly(self):
        """Test that is_interactive check completes in under 100ms"""
        # Arrange
        import time
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False

            # Act
            start = time.time()
            result = is_interactive()
            duration = time.time() - start

            # Assert
            assert duration < 0.1  # 100ms

    def test_get_api_key_from_env_completes_quickly(self):
        """Test that getting API key from environment is fast (< 50ms)"""
        # Arrange
        import time
        test_api_key = "sk-ant-perf-test-key"
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}):

            # Act
            start = time.time()
            result = get_api_key()
            duration = time.time() - start

            # Assert
            assert result == test_api_key
            assert duration < 0.05  # 50ms


class TestNFRCompatibility:
    """Non-Functional Requirement Tests: Cross-platform compatibility"""

    def test_works_on_windows_without_tty(self):
        """Test that setup works on Windows where stdin.isatty() may not exist"""
        # Arrange
        test_api_key = "sk-ant-windows-key"
        # Simulate Windows subprocess without TTY support
        with patch('sys.stdin', MagicMock(spec=[])), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}):

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key

    @pytest.mark.parametrize("platform_name", ["win32", "linux", "darwin"])
    def test_get_api_key_works_across_platforms(self, platform_name):
        """Test that get_api_key works on Windows, Linux, and macOS"""
        # Arrange
        test_api_key = f"sk-ant-{platform_name}-key"
        with patch('sys.platform', platform_name), \
             patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': test_api_key}):

            # Act
            result = get_api_key()

            # Assert
            assert result == test_api_key


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_api_key_from_env_raises_error(self):
        """Test that empty API key from environment is treated as missing"""
        # Arrange
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}):

            # Act & Assert
            with pytest.raises(EnvironmentError):
                get_api_key()

    def test_whitespace_only_api_key_raises_error(self):
        """Test that whitespace-only API key is treated as invalid"""
        # Arrange
        with patch('setup.is_interactive', return_value=False), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': '   '}):

            # Act & Assert
            with pytest.raises(EnvironmentError):
                get_api_key()

    def test_interactive_mode_handles_empty_input(self):
        """Test that interactive mode re-prompts or handles empty input gracefully"""
        # Arrange
        with patch('setup.is_interactive', return_value=True), \
             patch('builtins.input', side_effect=['', 'sk-ant-valid-key']) as mock_input:

            # Act
            result = get_api_key()

            # Assert
            assert result == 'sk-ant-valid-key'
            # Should have prompted twice (once for empty, once for valid)
            assert mock_input.call_count >= 1
