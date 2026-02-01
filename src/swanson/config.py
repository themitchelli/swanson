"""
Configuration management for Swanson Framework.

Cross-platform compatible. Authentication is delegated to Claude Code,
which handles API keys and OAuth automatically.
"""

from pathlib import Path
from typing import Optional


class Config:
    """Configuration manager for Swanson Framework."""

    def __init__(self):
        """Initialize configuration."""
        self.model: str = "sonnet"
        self.project_root: Path = Path.cwd()

    def validate(self) -> None:
        """
        Validate configuration.

        Note: Authentication is handled by Claude Code itself.
        It uses OAuth (Keychain/Credential Manager) or ANTHROPIC_API_KEY.
        Swanson does not manage API keys.
        """
        # No validation needed - Claude Code handles its own auth
        pass

    def get_swanson_dir(self) -> Optional[Path]:
        """
        Get .swanson directory path if it exists.

        Returns:
            Path to .swanson directory or None if not initialized.
        """
        swanson_dir = self.project_root / ".swanson"
        return swanson_dir if swanson_dir.exists() else None


# Global configuration instance
config = Config()
