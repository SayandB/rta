"""Interactive shell for the Rta operating system kernel."""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from datakernel_os.agents.spark_agent import SparkExecutionAgent, create_kernel_from_env
from datakernel_os.core.orchestrator import AgentOrchestrator

load_dotenv()


class RtaShell:
    """Provide an interactive CLI experience for task translation and execution."""

    def __init__(self) -> None:
        self.console = Console()
        self.orchestrator = AgentOrchestrator()
        self.kernel = create_kernel_from_env()
        self.agent = SparkExecutionAgent(kernel=self.kernel)

    async def process_command(self, user_input: str) -> None:
        """Translate intent, validate AST, and execute the resulting Spark snippet."""
        self.console.print("[bold yellow]Synthesizing PySpark execution plan...[/bold yellow]")
        spark_code = await self.orchestrator.translate_intent_to_spark(user_input)

        self.console.print("[bold green]Generated PySpark Code:[/bold green]")
        self.console.print(spark_code)

        input_path = os.getenv("SAMPLE_INPUT_PATH", "s3://datakernel-lakehouse/raw/data.csv")
        output_path = os.getenv("SAMPLE_OUTPUT_PATH", "s3://datakernel-lakehouse/output/processed")

        self.console.print("[bold yellow]Submitting workload to Spark execution agent...[/bold yellow]")
        result_path = await self.agent.submit_with_retry_async(
            generated_code=spark_code,
            input_path=input_path,
            output_path=output_path,
            orchestrator=self.orchestrator,
            objective=user_input,
        )
        self.console.print(f"[bold green]Job executed successfully. Output written to:[/bold green] {result_path}")

    def run(self) -> None:
        """Launch the interactive terminal loop."""
        self.console.print(
            Panel(
                "Rta Shell (ऋत)\nType natural language requests to execute lakehouse transformations.",
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

            if not user_input.strip():
                continue

            try:
                asyncio.run(self.process_command(user_input))
            except Exception as exc:  # pylint: disable=broad-except
                self.console.print(f"[bold red]Kernel Execution Error:[/bold red] {exc}")


if __name__ == "__main__":
    RtaShell().run()
