"""Testlerin gerçek ağ veya harici süreç kullanmasını engeller."""

from __future__ import annotations

import socket
import subprocess
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def block_network_and_processes(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    def denied(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("test sırasında ağ veya harici süreç kullanımı yasak")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(subprocess, "run", denied)
    monkeypatch.setattr(subprocess, "call", denied)
    monkeypatch.setattr(subprocess, "check_call", denied)
    monkeypatch.setattr(subprocess, "check_output", denied)
    yield
