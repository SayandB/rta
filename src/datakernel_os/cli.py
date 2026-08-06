"""Interactive shell for the Rta operating system kernel."""

from __future__ import annotations

import asyncio
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from datakernel_os.core.orchestrator import AgentOrchestrator


class RtaShell:
    """Provide an interactive CLI experience for task translation and execution."""

    def __init__(self) -> None:
        self.console = Console()
        self.orchestrator = AgentOrchestrator()

    def run(self) -> None:
        """Launch the interactive terminal loop."""
        self.console.print(
            Panel(
                "Rta Shell\nType natural language requests to generate PySpark code.",
                title="DataKernel-OS",
                border_style="cyan",
            )
        )

        while True:
            try:
                user_input = Prompt.ask("[bold cyan]rta[/bold cyan]>")
            except KeyboardInterrupt:
                self.console.print("\n[bold yellow]Session interrupted.[/bold yellow]")
                break

            if user_input.strip().lower() in {"exit", "quit"}:
                self.console.print("[bold green]Goodbye.[/bold green]")
                break

            try:
                spark_code = asyncio.run(self.orchestrator.translate_intent_to_spark(user_input))
                self.console.print("[bold green]Generated PySpark:[/bold green]")
                self.console.print(spark_code)
                self.console.print("[bold yellow]Execution simulated via spark_agent template.[/bold yellow]")
            except (RuntimeError, ValueError, TimeoutError) as exc:
                self.console.print(f"[bold red]Error:[/bold red] {exc}")


if __name__ == "__main__":
    RtaShell().run()
