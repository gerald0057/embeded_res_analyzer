"""Tests for config module."""
import tempfile
from pathlib import Path
from embedded_analyzer.config import (
    load_config,
    save_config,
    add_toolchain,
    remove_toolchain,
    set_current_toolchain,
)
from embedded_analyzer.core.models import AppConfig, ToolchainConfig


def test_load_save_config(tmp_path):
    cfg_path = tmp_path / "test_config.yaml"
    cfg = AppConfig(
        current_toolchain="test",
        toolchains=[ToolchainConfig(name="test", objdump="/usr/bin/objdump")],
    )
    save_config(cfg, cfg_path)
    loaded = load_config(cfg_path)
    assert loaded.current_toolchain == "test"
    assert len(loaded.toolchains) == 1
    assert loaded.toolchains[0].name == "test"


def test_add_toolchain(tmp_path):
    cfg_path = tmp_path / "test_config.yaml"
    cfg = add_toolchain("riscv", "/opt/bin/objdump", config_path=cfg_path)
    assert len(cfg.toolchains) == 1
    assert cfg.toolchains[0].name == "riscv"
    assert cfg.current_toolchain == "riscv"


def test_add_multiple_toolchains(tmp_path):
    cfg_path = tmp_path / "test_config.yaml"
    add_toolchain("riscv", "/opt/bin/riscv-objdump", config_path=cfg_path)
    cfg = add_toolchain("arm", "/opt/bin/arm-objdump", config_path=cfg_path)
    assert len(cfg.toolchains) == 2


def test_remove_toolchain(tmp_path):
    cfg_path = tmp_path / "test_config.yaml"
    add_toolchain("riscv", "/opt/bin/riscv-objdump", config_path=cfg_path)
    add_toolchain("arm", "/opt/bin/arm-objdump", config_path=cfg_path)
    cfg = remove_toolchain("riscv", config_path=cfg_path)
    assert len(cfg.toolchains) == 1
    assert cfg.toolchains[0].name == "arm"


def test_set_current_toolchain(tmp_path):
    cfg_path = tmp_path / "test_config.yaml"
    add_toolchain("riscv", "/opt/bin/riscv-objdump", config_path=cfg_path)
    add_toolchain("arm", "/opt/bin/arm-objdump", config_path=cfg_path)
    cfg = set_current_toolchain("arm", config_path=cfg_path)
    assert cfg.current_toolchain == "arm"


def test_set_invalid_toolchain(tmp_path):
    cfg_path = tmp_path / "test_config.yaml"
    add_toolchain("riscv", "/opt/bin/riscv-objdump", config_path=cfg_path)
    try:
        set_current_toolchain("nonexistent", config_path=cfg_path)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass