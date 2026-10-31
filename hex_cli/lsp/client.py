"""JSON-RPC LSP client over stdio for diagnostics, hover, definition, symbols.

Supports configurable language server commands. Gracefully reports when a
server binary is missing. Does not claim methods that are not implemented.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LSPServerConfig:
    language: str
    command: list[str]
    root: Path
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.language


@dataclass
class Diagnostic:
    path: str
    line: int
    character: int
    severity: int  # 1 error, 2 warning, 3 info, 4 hint
    message: str
    source: str = "lsp"

    @property
    def severity_label(self) -> str:
        return {1: "error", 2: "warning", 3: "info", 4: "hint"}.get(self.severity, "info")


# Sensible defaults — only used if the binary exists
DEFAULT_SERVERS: dict[str, list[str]] = {
    "python": ["pylsp"],
    "typescript": ["typescript-language-server", "--stdio"],
    "javascript": ["typescript-language-server", "--stdio"],
    "json": ["vscode-json-languageserver", "--stdio"],
    "rust": ["rust-analyzer"],
    "go": ["gopls"],
}


class _LSPSession:
    def __init__(self, config: LSPServerConfig):
        self.config = config
        self._proc: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._next_id = 1
        self._reader_thread: threading.Thread | None = None
        self._pending: dict[int, dict[str, Any]] = {}
        self._diagnostics: dict[str, list[Diagnostic]] = {}
        self.initialized = False
        self.last_error: str | None = None

    def start(self) -> bool:
        cmd0 = self.config.command[0]
        if not shutil.which(cmd0) and not Path(cmd0).is_file():
            self.last_error = f"Language server binary not found: {cmd0}"
            return False
        try:
            self._proc = subprocess.Popen(
                self.config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.config.root),
            )
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            root_uri = self.config.root.resolve().as_uri()
            result = self.request(
                "initialize",
                {
                    "processId": os.getpid(),
                    "rootUri": root_uri,
                    "capabilities": {
                        "textDocument": {
                            "hover": {"contentFormat": ["plaintext", "markdown"]},
                            "publishDiagnostics": {},
                            "definition": {},
                            "references": {},
                            "documentSymbol": {},
                        },
                        "workspace": {"symbol": {}},
                    },
                },
                timeout=15.0,
            )
            if result is None:
                self.last_error = self.last_error or "initialize timeout/failed"
                self.stop()
                return False
            self.notify("initialized", {})
            self.initialized = True
            return True
        except Exception as e:
            self.last_error = str(e)
            self.stop()
            return False

    def stop(self) -> None:
        self.initialized = False
        if self._proc and self._proc.poll() is None:
            try:
                self.request("shutdown", None, timeout=3.0)
            except Exception:
                pass
            try:
                self.notify("exit", None)
            except Exception:
                pass
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._proc = None

    def _write(self, msg: dict[str, Any]) -> None:
        if not self._proc or not self._proc.stdin:
            return
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        with self._lock:
            self._proc.stdin.write(header + body)
            self._proc.stdin.flush()

    def request(self, method: str, params: Any, timeout: float = 10.0) -> Any | None:
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        event = threading.Event()
        holder: dict[str, Any] = {}
        self._pending[req_id] = {"event": event, "holder": holder}
        self._write(msg)
        if not event.wait(timeout):
            self._pending.pop(req_id, None)
            self.last_error = f"timeout on {method}"
            return None
        self._pending.pop(req_id, None)
        if "error" in holder:
            self.last_error = str(holder["error"])
            return None
        return holder.get("result")

    def notify(self, method: str, params: Any) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._write(msg)

    def _read_loop(self) -> None:
        assert self._proc and self._proc.stdout
        buf = b""
        while self._proc and self._proc.poll() is None:
            try:
                chunk = self._proc.stdout.read(1)
                if not chunk:
                    break
                buf += chunk
                while b"\r\n\r\n" in buf:
                    header, _, rest = buf.partition(b"\r\n\r\n")
                    length = None
                    for line in header.split(b"\r\n"):
                        if line.lower().startswith(b"content-length:"):
                            length = int(line.split(b":")[1].strip())
                    if length is None:
                        buf = rest
                        break
                    if len(rest) < length:
                        buf = header + b"\r\n\r\n" + rest
                        break
                    body = rest[:length]
                    buf = rest[length:]
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except Exception:
                        continue
                    self._handle_message(data)
            except Exception:
                break

    def _handle_message(self, data: dict[str, Any]) -> None:
        if "id" in data and ("result" in data or "error" in data):
            pending = self._pending.get(data["id"])
            if pending:
                if "error" in data:
                    pending["holder"]["error"] = data["error"]
                else:
                    pending["holder"]["result"] = data.get("result")
                pending["event"].set()
            return
        method = data.get("method")
        if method == "textDocument/publishDiagnostics":
            params = data.get("params") or {}
            uri = params.get("uri", "")
            diags = []
            for d in params.get("diagnostics") or []:
                rng = d.get("range") or {}
                start = rng.get("start") or {}
                diags.append(
                    Diagnostic(
                        path=uri,
                        line=int(start.get("line", 0)) + 1,
                        character=int(start.get("character", 0)),
                        severity=int(d.get("severity", 1)),
                        message=str(d.get("message", "")),
                        source=str(d.get("source") or "lsp"),
                    )
                )
            self._diagnostics[uri] = diags

    def open_document(self, path: Path, language_id: str, text: str) -> None:
        uri = path.resolve().as_uri()
        self.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id,
                    "version": 1,
                    "text": text,
                }
            },
        )

    def hover(self, path: Path, line: int, character: int) -> Any:
        uri = path.resolve().as_uri()
        return self.request(
            "textDocument/hover",
            {
                "textDocument": {"uri": uri},
                "position": {"line": max(0, line - 1), "character": max(0, character)},
            },
        )

    def definition(self, path: Path, line: int, character: int) -> Any:
        uri = path.resolve().as_uri()
        return self.request(
            "textDocument/definition",
            {
                "textDocument": {"uri": uri},
                "position": {"line": max(0, line - 1), "character": max(0, character)},
            },
        )

    def references(self, path: Path, line: int, character: int) -> Any:
        uri = path.resolve().as_uri()
        return self.request(
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": {"line": max(0, line - 1), "character": max(0, character)},
                "context": {"includeDeclaration": True},
            },
        )

    def document_symbols(self, path: Path) -> Any:
        uri = path.resolve().as_uri()
        return self.request(
            "textDocument/documentSymbol",
            {"textDocument": {"uri": uri}},
        )

    def get_diagnostics(self, path: Path | None = None) -> list[Diagnostic]:
        if path is None:
            out: list[Diagnostic] = []
            for diags in self._diagnostics.values():
                out.extend(diags)
            return out
        uri = path.resolve().as_uri()
        return list(self._diagnostics.get(uri, []))


class LSPClient:
    """Manage one or more language server sessions."""

    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        self._sessions: dict[str, _LSPSession] = {}

    def available_defaults(self) -> dict[str, list[str]]:
        found = {}
        for lang, cmd in DEFAULT_SERVERS.items():
            if shutil.which(cmd[0]):
                found[lang] = cmd
        return found

    def start(self, language: str, command: list[str] | None = None) -> dict[str, Any]:
        cmd = command or DEFAULT_SERVERS.get(language)
        if not cmd:
            return {"ok": False, "error": f"No default server for {language}"}
        if language in self._sessions:
            self.stop(language)
        cfg = LSPServerConfig(language=language, command=cmd, root=self.root)
        session = _LSPSession(cfg)
        ok = session.start()
        if ok:
            self._sessions[language] = session
            return {"ok": True, "language": language, "command": cmd}
        return {"ok": False, "error": session.last_error or "start failed", "language": language}

    def stop(self, language: str) -> bool:
        s = self._sessions.pop(language, None)
        if s:
            s.stop()
            return True
        return False

    def stop_all(self) -> None:
        for lang in list(self._sessions):
            self.stop(lang)

    def list_sessions(self) -> list[dict[str, Any]]:
        return [
            {
                "language": lang,
                "initialized": s.initialized,
                "command": s.config.command,
                "error": s.last_error,
            }
            for lang, s in self._sessions.items()
        ]

    def session(self, language: str) -> _LSPSession | None:
        return self._sessions.get(language)
