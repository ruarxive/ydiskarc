"""Configuration module for ydiskarc."""

from dataclasses import dataclass
from typing import Optional

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

    def __post_init__(self) -> None:
        """Initialize user agent if not provided."""
        if self.user_agent is None:
            self.user_agent = (
                f"ydiskarc/{ydiskarc.__version__} (https://github.com/ruarxive/ydiskarc)"
            )

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
