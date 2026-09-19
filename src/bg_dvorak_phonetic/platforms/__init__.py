"""Static, lazy adapter registry: importing shared code loads no native adapter."""

from importlib import import_module

from bg_dvorak_phonetic.platforms.base import PlatformAdapter

ADAPTERS = {"linux": "LinuxAdapter", "macos": "MacOSAdapter"}


def get_adapter(platform_id: str) -> PlatformAdapter:
    """Load only the explicitly supported adapter; reject other operating systems."""
    if platform_id not in ADAPTERS:
        raise ValueError(f"Unsupported platform: {platform_id}")
    module = import_module(f"bg_dvorak_phonetic.platforms.{platform_id}")
    adapter: PlatformAdapter = getattr(module, ADAPTERS[platform_id])()
    return adapter
