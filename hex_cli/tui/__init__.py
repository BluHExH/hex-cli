"""HEX Textual TUI package."""

def run_tui(*args, **kwargs):
    from hex_cli.tui.app import run_tui as _run
    return _run(*args, **kwargs)

__all__ = ["run_tui"]
