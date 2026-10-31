"""Modular Language Server Protocol client foundation."""

from hex_cli.lsp.client import LSPClient, LSPServerConfig, Diagnostic as LSPDiagnostic

__all__ = ["LSPClient", "LSPServerConfig", "LSPDiagnostic"]
