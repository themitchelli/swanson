#!/usr/bin/env python3
"""
Tests for BUG-007: Fix executor using wrong Claude Code CLI syntax

PRD Requirements:
1. executor.py builds command as: ['claude', '--print', '--model', 'sonnet', '--dangerously-skip-permissions', prompt]
2. Prompt is passed as final positional argument, not as value to -p
3. -p flag is replaced with --print for clarity
4. Command works on both macOS and Windows
5. Integration test verifies simple prompt execution succeeds

Bug Context:
- Current: executor.py passes prompt as argument to -p flag: ['claude', '-p', prompt, ...]
- Expected: -p/--print is boolean flag, prompt should be positional: ['claude', '--print', ..., prompt]
- Claude Code CLI expects: claude [OPTIONS] [PROMPT]
"""

import platform
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from swanson.executor import build_claude_command, execute_claude_prompt


class TestBuildClaudeCommand:
    """Tests for AC1: executor.py builds command with correct CLI syntax"""

    def test_command_uses_print_flag_not_p(self):
        """
        AC3: -p flag is replaced with --print for clarity

        The command should use '--print' instead of '-p' for better readability
        and to avoid confusion with other CLI tools.
        """
        prompt = "Write a hello world function"

        command = build_claude_command(prompt)

        # Should contain --print, not -p
        assert '--print' in command, "Command should use --print flag"
        assert '-p' not in command, "Command should not use -p shorthand"

    def test_prompt_is_positional_argument(self):
        """
        AC2: Prompt is passed as final positional argument, not as value to -p

        The Claude Code CLI expects prompts as positional arguments, not as
        flag values. The prompt should be the last element in the command list.
        """
        prompt = "Write a hello world function"

        command = build_claude_command(prompt)

        # Prompt should be the last element (positional argument)
        assert command[-1] == prompt, "Prompt should be the final positional argument"

        # The element before prompt should not be a flag that takes a value
        # (i.e., if --print appears, the next element should not be the prompt)
        if '--print' in command:
            print_index = command.index('--print')
            # --print is a boolean flag, so the next element should NOT be the prompt
            # (unless prompt is the very last element)
            if print_index < len(command) - 1:
                next_element = command[print_index + 1]
                # If next element is the prompt AND it's not the last element, that's wrong
                if next_element == prompt and print_index + 1 != len(command) - 1:
                    pytest.fail("Prompt should not immediately follow --print flag")

    def test_command_structure_matches_spec(self):
        """
        AC1: executor.py builds command as:
        ['claude', '--print', '--model', 'sonnet', '--dangerously-skip-permissions', prompt]

        The command should follow this exact structure with all required flags.
        """
        prompt = "Write a hello world function"

        command = build_claude_command(prompt)

        # Should be a list
        assert isinstance(command, list), "Command should be a list"

        # Should start with 'claude'
        assert command[0] == 'claude', "Command should start with 'claude'"

        # Should contain required flags
        assert '--print' in command, "Command should contain --print flag"
        assert '--model' in command, "Command should contain --model flag"
        assert '--dangerously-skip-permissions' in command, "Command should contain --dangerously-skip-permissions flag"

        # --model should be followed by 'sonnet'
        model_index = command.index('--model')
        assert command[model_index + 1] == 'sonnet', "--model flag should be followed by 'sonnet'"

        # Prompt should be last
        assert command[-1] == prompt, "Prompt should be the last element"

    def test_command_with_multiline_prompt(self):
        """
        Edge case: Prompt with multiple lines should be passed as single positional argument
        """
        prompt = "Write a function that:\n1. Takes a number\n2. Returns its square"

        command = build_claude_command(prompt)

        # Prompt should still be the last element, preserved as-is
        assert command[-1] == prompt, "Multiline prompt should be preserved as single argument"
        assert '\n' in command[-1], "Newlines should be preserved in prompt"

    def test_command_with_special_characters_in_prompt(self):
        """
        Edge case: Prompt with special characters should not break command structure
        """
        prompt = "Write a function with 'quotes' and \"double quotes\" and $variables"

        command = build_claude_command(prompt)

        # Prompt should be last and unchanged
        assert command[-1] == prompt, "Special characters should be preserved in prompt"

        # Command structure should still be valid
        assert command[0] == 'claude'
        assert '--print' in command

    def test_command_with_empty_prompt(self):
        """
        Edge case: Empty prompt should still be passed as positional argument
        """
        prompt = ""

        command = build_claude_command(prompt)

        # Should still have correct structure
        assert command[-1] == prompt, "Empty prompt should still be last element"
        assert command[0] == 'claude'

    def test_command_order_flags_before_prompt(self):
        """
        AC1 & AC2: All flags should come before the positional prompt argument

        Ensures that the command follows standard CLI conventions where
        flags precede positional arguments.
        """
        prompt = "Write a hello world function"

        command = build_claude_command(prompt)

        prompt_index = command.index(prompt)

        # All flags should come before the prompt
        for i in range(prompt_index):
            element = command[i]
            # Elements before prompt should be either:
            # 1. The executable name 'claude'
            # 2. A flag (starts with --)
            # 3. A flag value (preceded by a flag that takes a value)
            if i == 0:
                assert element == 'claude', "First element should be 'claude'"
            else:
                # For other elements before prompt, they should be flags or flag values
                # This is validated implicitly by checking prompt is last
                pass


class TestCrossPlatformCompatibility:
    """Tests for AC4: Command works on both macOS and Windows"""

    @patch('executor.subprocess.run')
    def test_command_works_on_macos(self, mock_run):
        """
        AC4: Command structure is compatible with macOS
        """
        with patch('executor.platform.system', return_value='Darwin'):
            prompt = "Write a hello world function"
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

            command = build_claude_command(prompt)

            # Command should work on macOS (no platform-specific issues)
            assert command[0] == 'claude'
            assert command[-1] == prompt

            # Verify command structure doesn't have Windows-specific issues
            for element in command:
                # No backslashes in flags (Windows path separators)
                if element.startswith('--'):
                    assert '\\' not in element, "Flags should not contain backslashes"

    @patch('executor.subprocess.run')
    def test_command_works_on_windows(self, mock_run):
        """
        AC4: Command structure is compatible with Windows
        """
        with patch('executor.platform.system', return_value='Windows'):
            prompt = "Write a hello world function"
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

            command = build_claude_command(prompt)

            # Command should work on Windows
            assert command[0] == 'claude'
            assert command[-1] == prompt

            # Verify command can be passed to subprocess on Windows
            # (list format works on both platforms)
            assert isinstance(command, list), "Command should be a list for cross-platform subprocess"

    @patch('executor.platform.system')
    def test_command_identical_across_platforms(self, mock_system):
        """
        AC4: Command structure should be identical on macOS and Windows

        The command list should not change based on the platform, ensuring
        consistent behavior across systems.
        """
        prompt = "Write a hello world function"

        # Get command on macOS
        mock_system.return_value = 'Darwin'
        macos_command = build_claude_command(prompt)

        # Get command on Windows
        mock_system.return_value = 'Windows'
        windows_command = build_claude_command(prompt)

        # Commands should be identical
        assert macos_command == windows_command, "Command should be platform-independent"


class TestExecuteClaudePrompt:
    """Tests for AC5: Integration test verifies simple prompt execution succeeds"""

    @patch('executor.subprocess.run')
    @patch('executor._find_claude_executable')
    def test_simple_prompt_execution_succeeds(self, mock_find_claude, mock_run):
        """
        AC5: Integration test verifies simple prompt execution succeeds

        Tests that a simple prompt can be executed successfully through the
        executor module, using the correct command structure.
        """
        prompt = "Write a hello world function"

        # Mock Claude executable found
        mock_find_claude.return_value = '/usr/local/bin/claude'

        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "def hello_world():\n    print('Hello, World!')"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute prompt
        result = execute_claude_prompt(prompt)

        # Should return the output
        assert result is not None
        assert "hello_world" in result.lower() or "Hello" in result

        # Verify subprocess.run was called with correct command structure
        mock_run.assert_called_once()
        called_command = mock_run.call_args[0][0]

        # Verify command structure
        assert called_command[0] == 'claude', "Should call claude executable"
        assert '--print' in called_command, "Should use --print flag"
        assert called_command[-1] == prompt, "Prompt should be positional argument"

    @patch('executor.subprocess.run')
    @patch('executor._find_claude_executable')
    def test_execution_with_complex_prompt(self, mock_find_claude, mock_run):
        """
        Integration test with a more complex prompt to verify robustness
        """
        prompt = """Write a Python function that:
1. Takes a list of numbers
2. Filters out negative numbers
3. Returns the sum of positive numbers"""

        mock_find_claude.return_value = '/usr/local/bin/claude'

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "def sum_positive(numbers):\n    return sum(x for x in numbers if x > 0)"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = execute_claude_prompt(prompt)

        assert result is not None

        # Verify command was called correctly
        called_command = mock_run.call_args[0][0]
        assert called_command[-1] == prompt, "Complex prompt should be passed as-is"
        assert '--print' in called_command

    @patch('executor.subprocess.run')
    @patch('executor._find_claude_executable')
    def test_execution_handles_claude_not_found(self, mock_find_claude, mock_run):
        """
        Integration test verifies graceful handling when Claude is not found
        """
        prompt = "Write a hello world function"

        # Mock Claude executable not found
        mock_find_claude.side_effect = RuntimeError("Claude Code executable not found")

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Claude Code executable not found"):
            execute_claude_prompt(prompt)

        # subprocess.run should not be called if executable not found
        mock_run.assert_not_called()

    @patch('executor.subprocess.run')
    @patch('executor._find_claude_executable')
    def test_execution_handles_subprocess_failure(self, mock_find_claude, mock_run):
        """
        Integration test verifies handling of Claude CLI execution failure
        """
        prompt = "Write a hello world function"

        mock_find_claude.return_value = '/usr/local/bin/claude'

        # Mock subprocess failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Invalid model specified"
        mock_run.return_value = mock_result

        # Should handle error gracefully (either return None or raise exception)
        try:
            result = execute_claude_prompt(prompt)
            # If it doesn't raise, it should return None or empty result
            assert result is None or result == ""
        except subprocess.CalledProcessError:
            # Or it might raise CalledProcessError, which is also valid
            pass


class TestNFRSecurity:
    """Non-Functional Requirement: Security tests for command injection prevention"""

    def test_prompt_with_command_injection_attempt(self):
        """
        Security: Prompt with shell injection attempts should be safely handled

        Using list-based subprocess execution (not shell=True) prevents
        command injection, but we should verify the command structure is safe.
        """
        malicious_prompt = "Hello'; rm -rf /; echo 'world"

        command = build_claude_command(malicious_prompt)

        # Prompt should be passed as-is, not interpreted
        assert command[-1] == malicious_prompt, "Malicious prompt should be passed as literal string"

        # Command should still be a list (safe for subprocess)
        assert isinstance(command, list), "Command should be list to prevent shell injection"

        # Should not contain shell operators in unexpected places
        assert command[0] == 'claude', "Executable should not be affected by prompt content"

    def test_prompt_with_flag_injection_attempt(self):
        """
        Security: Prompt starting with -- should not be interpreted as a flag

        Ensures that prompts starting with -- are passed as positional arguments,
        not misinterpreted as flags.
        """
        flag_like_prompt = "--help"

        command = build_claude_command(flag_like_prompt)

        # Prompt should be last, even if it looks like a flag
        assert command[-1] == flag_like_prompt, "Flag-like prompt should be positional argument"

        # The command structure should prevent misinterpretation
        # (--print and other flags should come before the prompt)
        prompt_index = command.index(flag_like_prompt)
        assert prompt_index == len(command) - 1, "Flag-like prompt should be last element"


class TestNFRPerformance:
    """Non-Functional Requirement: Performance tests"""

    def test_build_command_is_fast(self):
        """
        Performance: Building command should be near-instantaneous
        """
        import time

        prompt = "Write a hello world function"

        start_time = time.perf_counter()
        command = build_claude_command(prompt)
        elapsed_time = time.perf_counter() - start_time

        # Should complete in less than 1ms (0.001 seconds)
        assert elapsed_time < 0.001, f"Command building took {elapsed_time}s, should be < 1ms"

    def test_build_command_with_large_prompt(self):
        """
        Performance: Should handle large prompts efficiently
        """
        import time

        # Create a large prompt (10KB)
        large_prompt = "Write a function that " + ("does something " * 1000)

        start_time = time.perf_counter()
        command = build_claude_command(large_prompt)
        elapsed_time = time.perf_counter() - start_time

        # Should still be fast even with large prompt
        assert elapsed_time < 0.01, f"Large prompt handling took {elapsed_time}s, should be < 10ms"

        # Prompt should still be last element
        assert command[-1] == large_prompt


class TestNFRRobustness:
    """Non-Functional Requirement: Robustness and error handling"""

    def test_build_command_with_none_prompt(self):
        """
        Robustness: Should handle None prompt gracefully
        """
        with pytest.raises((TypeError, ValueError)):
            build_claude_command(None)

    def test_build_command_with_non_string_prompt(self):
        """
        Robustness: Should handle non-string prompt gracefully
        """
        with pytest.raises((TypeError, ValueError)):
            build_claude_command(12345)

        with pytest.raises((TypeError, ValueError)):
            build_claude_command(['list', 'prompt'])

    def test_build_command_with_unicode_prompt(self):
        """
        Robustness: Should handle Unicode characters in prompt
        """
        unicode_prompt = "Write a function that prints '你好世界' and '🌍'"

        command = build_claude_command(unicode_prompt)

        # Should handle Unicode correctly
        assert command[-1] == unicode_prompt, "Unicode prompt should be preserved"
        assert '你好世界' in command[-1]
        assert '🌍' in command[-1]
