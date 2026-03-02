import asyncio
import json
from pathlib import Path
from pydantic import BaseModel


class ScopedConfig(BaseModel):
    command_priority: int = 10

    groups_enabled: list[str] = []
    ban_user: list[str] = []

    image_url_list: list[str] = [
        "https://t.alcy.cc/moe/",
        "https://t.alcy.cc/ycy/",
        # "https://t.alcy.cc/ai/",
        "https://t.alcy.cc/ys/",
    ]

    fool_mode: bool = False
    fool_rp: dict[str, int] = {}


class Config(BaseModel):
    jrrp_next: ScopedConfig


class LocalConfig:
    def __init__(self, path: str | Path, default: ScopedConfig) -> None:
        self.path: str | Path = path
        self.config: dict = {}
        self.load(default=default)

    def load(
        self, filename: Path | str | None = None, default: ScopedConfig | None = None
    ) -> None:
        path: str | Path = self.path
        if filename:
            path = filename
        try:
            with open(path) as f:
                self.config: dict = json.load(f)
        except Exception as e:
            print(f"WARN: {e}, fallback to default config")
            self.config = dict((default if default else ScopedConfig).__dict__.items())
            self.dump()

    def dump(self, filename: Path | str | None = None) -> None:
        path: str | Path = self.path
        if filename:
            path = filename
        with open(path, "w") as f:
            json.dump(self.config, f)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value
        self.dump()
