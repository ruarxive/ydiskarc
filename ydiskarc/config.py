"""Configuration module for ydiskarc."""

import os
from dataclasses import dataclass, field
from typing import Optional, Union

import ydiskarc


@dataclass
class Config:
    """Configuration settings for ydiskarc."""

    api_base_url: str = "https://cloud-api.yandex.net/v1/disk"
    api_resources: str = "/public/resources"
    api_download: str = "/public/resources/download"
    chunk_size: int = 32 * 1024  # 32KB chunks
    timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 1.0
    user_agent: Optional[str] = None  # Auto-generated if None
    verify: Optional[Union[bool, str]] = field(default=None)
    """TLS verification mode passed to ``requests``. ``None`` (default) means
    use the system trust store (``True``). Set to a path string to point at a
    custom CA bundle, or ``False`` to disable verification (not recommended)."""
    pool_maxsize: int = 10
    """``HTTPAdapter`` connection pool size. Should be at least the value of
    ``--parallel`` for parallel downloads to avoid TCP connection sharing."""

    def __post_init__(self) -> None:
        """Initialize user agent and resolve TLS verification overrides."""
        if self.user_agent is None:
            self.user_agent = (
                f"ydiskarc/{ydiskarc.__version__} (https://github.com/ruarxive/ydiskarc)"
            )
        # Env-var override: YDISKARC_TLS_VERIFY takes precedence over the
        # dataclass default but is itself overridden by an explicit value
        # passed to the constructor.
        env_value = os.environ.get("YDISKARC_TLS_VERIFY")
        if env_value is not None and self.verify is None:
            env_value = env_value.strip()
            if env_value == "" or env_value == "0" or env_value.lower() == "false":
                self.verify = False
            elif env_value == "1" or env_value.lower() == "true":
                self.verify = True
            else:
                # Treat as a path to a CA bundle.
                self.verify = env_value

    @property
    def api_resources_url(self) -> str:
        """Get full API resources URL."""
        return f"{self.api_base_url}{self.api_resources}"

    @property
    def api_download_url(self) -> str:
        """Get full API download URL."""
        return f"{self.api_base_url}{self.api_download}"


# Global configuration instance
config = Config()
