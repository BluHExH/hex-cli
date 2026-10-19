"""Tests for path safety and permission logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from hex_cli.config import AppConfig, PermissionConfig
from hex_cli.permissions import ActionType, PermissionManager, PermissionRequest


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n")
    return tmp_path


@pytest.fixture
def perms(project: Path) -> PermissionManager:
    cfg = AppConfig(permissions=PermissionConfig(
        read_files="allow",
        create_files="ask",
        modify_files="ask",
        run_commands="ask",
    ))
    return PermissionManager(cfg, project, ask_fn=lambda r: True)


def test_resolve_safe_relative(perms: PermissionManager, project: Path):
    p = perms.resolve_safe_path("src/main.py")
    assert p == (project / "src" / "main.py").resolve()


def test_reject_parent_traversal(perms: PermissionManager):
    with pytest.raises(PermissionError):
        perms.resolve_safe_path("../outside.txt")


def test_reject_absolute_outside(perms: PermissionManager, tmp_path: Path):
    outside = tmp_path.parent / "escape.txt"
    with pytest.raises(PermissionError):
        perms.resolve_safe_path(str(outside))


def test_reject_nested_traversal(perms: PermissionManager):
    with pytest.raises(PermissionError):
        perms.resolve_safe_path("src/../../etc/passwd")


def test_symlink_escape(project: Path, tmp_path: Path):
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret")
    link = project / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    cfg = AppConfig()
    pm = PermissionManager(cfg, project, ask_fn=lambda r: True)
    with pytest.raises(PermissionError):
        pm.resolve_safe_path("link.txt")


def test_permission_deny_mode(project: Path):
    cfg = AppConfig(permissions=PermissionConfig(run_commands="deny"))
    pm = PermissionManager(cfg, project, ask_fn=lambda r: True)
    result = pm.check(ActionType.RUN_COMMAND, "run ls", detail="ls")
    assert result.allowed is False


def test_permission_ask_rejected(project: Path):
    cfg = AppConfig(permissions=PermissionConfig(create_files="ask"))
    pm = PermissionManager(cfg, project, ask_fn=lambda r: False)
    result = pm.check(ActionType.CREATE_FILE, "create x", path="x.py")
    assert result.allowed is False
    assert "rejected" in result.reason


def test_permission_ask_approved(project: Path):
    cfg = AppConfig(permissions=PermissionConfig(create_files="ask"))
    pm = PermissionManager(cfg, project, ask_fn=lambda r: True)
    result = pm.check(ActionType.CREATE_FILE, "create x", path="x.py")
    assert result.allowed is True


def test_high_impact_detection(project: Path):
    cfg = AppConfig()
    pm = PermissionManager(cfg, project, ask_fn=lambda r: False)
    assert pm.is_high_impact_command("rm -rf /tmp/foo")
    assert pm.is_high_impact_command("git push origin main")
    assert not pm.is_high_impact_command("pytest -q")
    assert not pm.is_high_impact_command("python -m compileall .")


def test_is_path_safe(perms: PermissionManager):
    assert perms.is_path_safe("src/main.py") is True
    assert perms.is_path_safe("../etc/passwd") is False
