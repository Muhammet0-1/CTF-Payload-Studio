"""Üretilen wheel ve sdist içeriğini kurulum yapmadan doğrular."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path


def main() -> int:
    wheels = list(Path("dist").glob("ctf_payload_studio-*.whl"))
    sdists = list(Path("dist").glob("ctf_payload_studio-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("tam olarak bir wheel ve bir sdist bekleniyordu")

    with zipfile.ZipFile(wheels[0]) as archive:
        wheel_names = set(archive.namelist())
        bad = archive.testzip()
    if bad is not None:
        raise SystemExit(f"wheel ZIP bütünlüğü bozuk: {bad}")
    required_wheel = {
        "ctf_payload_studio/__init__.py",
        "ctf_payload_studio/analyzer.py",
        "ctf_payload_studio/cli.py",
        "ctf_payload_studio/gui.py",
        "ctf_payload_studio/pipeline.py",
        "ctf_payload_studio/py.typed",
    }
    if not required_wheel.issubset(wheel_names):
        raise SystemExit("wheel gerekli paket dosyalarını içermiyor")

    with tarfile.open(sdists[0], "r:gz") as archive:
        sdist_names = archive.getnames()
    required_sdist = (
        "/tests/conftest.py",
        "/tests/test_analyzer.py",
        "/README.md",
        "/LICENSE",
        "/studio.py",
    )
    for suffix in required_sdist:
        if not any(name.endswith(suffix) for name in sdist_names):
            raise SystemExit(f"sdist içinde eksik: {suffix}")
    print("Paket artefaktları doğrulandı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
