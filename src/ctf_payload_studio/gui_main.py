"""İsteğe bağlı PyQt5 arayüzünün giriş noktası."""


def main() -> int:
    try:
        from ctf_payload_studio.gui import run_gui
    except ImportError as exc:
        raise SystemExit("GUI için 'pip install .[gui]' çalıştırın.") from exc
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
