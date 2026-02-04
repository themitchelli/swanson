"""
Architectural smoke tests - these protect Swanson's core identity.
If these fail, something fundamental was deleted or broken.
DO NOT delete or modify without explicit human approval.
"""
import pytest


class TestSwansonArchitecture:
    """Verify core orchestration components exist."""

    def test_executor_class_exists(self):
        """Executor class must exist - it's the orchestration core."""
        from swanson.executor import Executor
        assert Executor is not None

    def test_executor_has_test_generation(self):
        """Test generation capability must exist."""
        from swanson.executor import Executor
        executor = Executor()
        assert hasattr(executor, 'execute_test_generation')
        assert callable(executor.execute_test_generation)

    def test_executor_has_implementation(self):
        """Implementation capability must exist."""
        from swanson.executor import Executor
        executor = Executor()
        assert hasattr(executor, 'execute_implementation')
        assert callable(executor.execute_implementation)

    def test_executor_has_test_prompt_generator(self):
        """Test generation prompt method must exist."""
        from swanson.executor import Executor
        executor = Executor()
        assert hasattr(executor, '_create_test_generation_prompt')

    def test_executor_has_implementation_prompt_generator(self):
        """Implementation prompt method must exist."""
        from swanson.executor import Executor
        executor = Executor()
        assert hasattr(executor, '_create_implementation_prompt')
