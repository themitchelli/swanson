"""
Configuration management for Swanson Framework.

Loads API key from .env or config.json.
Cross-platform compatible.
"""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration manager for Swanson Framework."""

    def __init__(self):
        """Initialize configuration from environment or config files."""
        self.api_key: Optional[str] = None
        self.model: str = "sonnet"
        self.project_root: Path = Path.cwd()

        self._load()

    def _is_valid_api_key(self, key: Optional[str]) -> bool:
        """Check if API key has valid format (not necessarily valid with API)."""
        if not key:
            return False
        # Anthropic API keys start with sk-ant- and are typically 100+ chars
        return key.startswith("sk-ant-") and len(key) >= 90

    def _load(self) -> None:
        """
        Load configuration in priority order:
        1. .env file (project-specific takes priority)
        2. config.json file
        3. Environment variable (ANTHROPIC_API_KEY) - fallback

        Project-specific config (.env) is preferred because it allows
        different projects to use different API keys.
        """
        # Try .env file first (project-specific)
        env_path = self.project_root / ".env"
        if env_path.exists():
            self._load_env_file(env_path)
            if self._is_valid_api_key(self.api_key):
                return

        # Try config.json
        config_path = self.project_root / "config.json"
        if config_path.exists():
            self._load_config_json(config_path)
            if self._is_valid_api_key(self.api_key):
                return

        # Fall back to environment variable (always check, even if files exist but had no valid key)
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            # Strip whitespace/newlines that may have been accidentally added
            cleaned_key = env_key.replace("\n", "").replace(" ", "").strip()
            if self._is_valid_api_key(cleaned_key):
                self.api_key = cleaned_key
                return

        # Also try user-level config in ~/.swanson/config.json
        user_config = Path.home() / ".swanson" / "config.json"
        if user_config.exists():
            self._load_config_json(user_config)

    def _load_env_file(self, env_path: Path) -> None:
        """Load API key from .env file."""
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == "ANTHROPIC_API_KEY":
                        self.api_key = value
                        return

    def _load_config_json(self, config_path: Path) -> None:
        """Load configuration from config.json."""
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.api_key = data.get("anthropic_api_key")
            self.model = data.get("model", "sonnet")

    def validate(self) -> None:
        """
        Validate configuration.

        Note: API key is optional - Claude Code can use OAuth authentication.
        This validation now only warns about invalid key format if one is provided.
        """
        # API key is optional - Claude Code can authenticate via OAuth
        # Only validate format if a key is explicitly provided
        pass

        if not self.api_key.startswith("sk-ant-"):
            raise ValueError(
                "Invalid API key format. Anthropic API keys start with 'sk-ant-'."
            )

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
