from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__("", id="status-bar", **kwargs)

    def set_status(
        self,
        *,
        state: str = "idle",
        model: str = "",
        session: str = "",
        workspace: str = "",
    ) -> None:
        self.update(
            f" {state}  ·  {model}  ·  {session}  ·  {workspace}  ·  "
            f"ctrl+p palette  ctrl+b sidebar  ctrl+n new  ctrl+c cancel"
        )
