from __future__ import annotations

import sys
import types

import pytest

from redbot_orm.common import get_piccolo_command


def test_get_piccolo_command_prefers_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "redbot_orm.common.find_piccolo_executable",
        lambda: "C:/fake/piccolo",
    )

    assert get_piccolo_command() == ["C:/fake/piccolo"]


def test_get_piccolo_command_falls_back_to_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise() -> str:
        raise FileNotFoundError("missing")

    monkeypatch.setattr("redbot_orm.common.find_piccolo_executable", _raise)
    monkeypatch.setattr(
        "redbot_orm.common.importlib.util.find_spec",
        lambda _: types.SimpleNamespace(name="piccolo"),
    )

    assert get_piccolo_command() == [sys.executable, "-m", "piccolo.main"]


def test_get_piccolo_command_raises_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise() -> str:
        raise FileNotFoundError("missing")

    monkeypatch.setattr("redbot_orm.common.find_piccolo_executable", _raise)
    monkeypatch.setattr("redbot_orm.common.importlib.util.find_spec", lambda _: None)

    with pytest.raises(FileNotFoundError):
        get_piccolo_command()
