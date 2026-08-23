from __future__ import annotations

import ast
from pathlib import Path


def test_source_has_no_network_process_or_dynamic_execution_surface() -> None:
    package = Path("src/ctf_payload_studio")
    forbidden_imports = {"socket", "subprocess", "requests", "urllib.request", "http.client"}
    forbidden_calls = {"eval", "exec", "compile", "__import__"}
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name not in forbidden_imports for alias in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert node.module not in forbidden_imports, path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls, path


def test_gui_module_imports_without_starting_event_loop() -> None:
    from ctf_payload_studio.gui import StudioWindow

    assert StudioWindow.__name__ == "StudioWindow"
