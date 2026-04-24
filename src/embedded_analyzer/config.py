"""
Configuration management - multi-toolchain support via YAML
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional, List
import logging

from .core.models import AppConfig, ToolchainConfig, DEFAULT_SECTIONS

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "embedded-analyzer"


def get_default_config_path() -> Path:
    return DEFAULT_CONFIG_DIR / "config.yaml"


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    p = config_path or get_default_config_path()
    if not p.exists():
        cfg = AppConfig()
        save_config(cfg, config_path)
        return cfg
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return AppConfig.from_dict(data)


def save_config(config: AppConfig, config_path: Optional[Path] = None) -> None:
    p = config_path or get_default_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def add_toolchain(name: str, objdump: str, size: Optional[str] = None,
                  readelf: Optional[str] = None, config_path: Optional[Path] = None) -> AppConfig:
    cfg = load_config(config_path)
    tc = ToolchainConfig(name=name, objdump=objdump, size=size, readelf=readelf)
    existing = [t for t in cfg.toolchains if t.name != name]
    existing.append(tc)
    cfg.toolchains = existing
    if not cfg.current_toolchain:
        cfg.current_toolchain = name
    save_config(cfg, config_path)
    return cfg


def remove_toolchain(name: str, config_path: Optional[Path] = None) -> AppConfig:
    cfg = load_config(config_path)
    cfg.toolchains = [t for t in cfg.toolchains if t.name != name]
    if cfg.current_toolchain == name:
        cfg.current_toolchain = cfg.toolchains[0].name if cfg.toolchains else None
    save_config(cfg, config_path)
    return cfg


def set_current_toolchain(name: str, config_path: Optional[Path] = None) -> AppConfig:
    cfg = load_config(config_path)
    names = [t.name for t in cfg.toolchains]
    if name not in names:
        raise ValueError(f"Toolchain '{name}' not found. Available: {names}")
    cfg.current_toolchain = name
    save_config(cfg, config_path)
    return cfg


def add_section(name: str, config_path: Optional[Path] = None) -> AppConfig:
    cfg = load_config(config_path)
    if name not in cfg.sections:
        cfg.sections.append(name)
        save_config(cfg, config_path)
    return cfg


def remove_section(name: str, config_path: Optional[Path] = None) -> AppConfig:
    cfg = load_config(config_path)
    cfg.sections = [s for s in cfg.sections if s != name]
    save_config(cfg, config_path)
    return cfg