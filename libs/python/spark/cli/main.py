"""
Spark CLI main entry point and command routing system.

This module provides the primary command-line interface for Spark, implementing
the terminal-native experience for AI-powered coding exploration.
"""

import sys
import asyncio
import argparse
from typing import List, Optional, Dict, Any
from pathlib import Path

# Rich terminal formatting
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint

# Defer command imports to setup for better resilience

# Core Spark modules
try:
    from spark.core.config import SparkConfig
    from spark.core.initialization import initialize_spark
except ImportError:
    # Graceful fallback during development
    SparkConfig = None
    initialize_spark = None


class SparkCLI:
    """
    Main CLI class implementing the Spark command interface.
    
    Provides terminal-native commands following the Learn → Explore → Discover → Integrate workflow.
    """
    
    def __init__(self):
        self.console = Console()
        self.config = None
        self.commands = {}
        self._setup_commands()
    
    def _setup_commands(self) -> None:
        """Setup command registry with per-command import isolation."""
        # Import each command independently so one failure doesn't block others
        try:
            from spark.cli.commands.status import StatusCommand  # type: ignore
            self.commands['status'] = StatusCommand()
        except Exception:
            pass
        try:
            from spark.cli.commands.learn import LearnCommand  # type: ignore
            self.commands['learn'] = LearnCommand()
        except Exception:
            pass
        try:
            from spark.cli.commands.explore import ExploreCommand  # type: ignore
            self.commands['explore'] = ExploreCommand()
        except Exception:
            pass
        try:
            from spark.cli.commands.morning import MorningCommand  # type: ignore
            self.commands['morning'] = MorningCommand()
        except Exception:
            pass
        try:
            from spark.cli.commands.show import ShowCommand  # type: ignore
            self.commands['show'] = ShowCommand()
        except Exception:
            pass
        try:
            from spark.cli.commands.rate import RateCommand  # type: ignore
            self.commands['rate'] = RateCommand()
        except Exception:
            pass
        
        # Add built-in commands
        self.commands['help'] = self._help_command
        self.commands['version'] = self._version_command
    
    async def _initialize_if_needed(self) -> bool:
        """Initialize Spark on first run if needed."""
        try:
            if SparkConfig and initialize_spark:
                self.config = SparkConfig()
                if not self.config.is_initialized():
                    self.console.print("🚀 [bold blue]Welcome to Spark![/bold blue] Let's learn your coding rhythm.")
                    self.console.print()
                    
                    success = await initialize_spark(self.config, self.console)
                    if success:
                        self.console.print("✅ [green]Spark initialized successfully![/green]")
                        self.console.print("💡 Use [cyan]'spark learn'[/cyan] to manage learning or [cyan]'spark status'[/cyan] to check progress.")
                        return True
                    else:
                        self.console.print("❌ [red]Failed to initialize Spark[/red]")
                        return False
                else:
                    self.config.load()
                    return True
            else:
                # Development mode - show placeholder
                self._show_development_status()
                return True
        except Exception as e:
            self.console.print(f"❌ [red]Initialization error: {e}[/red]")
            return False
    
    def _show_development_status(self) -> None:
        """Show development status when core modules aren't available yet."""
        panel = Panel(
            Text.assemble(
                ("🚧 ", "bold yellow"),
                ("Spark Development Mode", "bold white"),
                ("\n\n", ""),
                ("• CLI Framework: ", ""), ("✅ Ready", "green"),
                ("\n• Configuration: ", ""), ("🚧 In Progress", "yellow"),
                ("\n• Learning Engine: ", ""), ("⏳ Pending", "dim white"),
                ("\n• Exploration Engine: ", ""), ("⏳ Pending", "dim white"),
                ("\n• Discovery System: ", ""), ("⏳ Pending", "dim white"),
                ("\n\n", ""),
                ("Run 'spark --help' for available commands.", "dim white"),
            ),
            title="Spark Status",
            border_style="blue"
        )
        self.console.print(panel)
    
    async def run(self, args: List[str]) -> int:
        """Main entry point for CLI execution."""
        if not args or args[0] in ['', 'status']:
            # Default command - show status and auto-initialize
            await self._initialize_if_needed()
            if 'status' in self.commands:
                return await self.commands['status'].execute([])
            else:
                self._show_development_status()
                return 0
        
        command_name = args[0]
        command_args = args[1:] if len(args) > 1 else []
        
        # Handle built-in commands
        if command_name == 'help':
            return self._help_command(command_args)
        elif command_name == 'version':
            return self._version_command(command_args)
        
        # Handle main commands
        if command_name in self.commands:
            await self._initialize_if_needed()
            if hasattr(self.commands[command_name], 'execute'):
                return await self.commands[command_name].execute(command_args)
            else:
                return self.commands[command_name](command_args)
        else:
            self.console.print(f"❌ [red]Unknown command: {command_name}[/red]")
            self._help_command([])
            return 1
    
    def _help_command(self, args: List[str]) -> int:
        """Display help information."""
        if args and args[0] in self.commands:
            # Command-specific help
            command = self.commands[args[0]]
            if hasattr(command, 'help'):
                command.help()
                return 0
        
        # General help
        help_table = Table(title="Spark Commands", show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan", width=15)
        help_table.add_column("Description", style="white")
        help_table.add_column("Status", justify="center", width=8)
        
        commands_info = [
            ("spark", "Show status and auto-initialize on first run", "✅"),
            ("spark learn", "Start/stop background learning from git and files", "🚧"),
            ("spark status", "Display learning progress and detected patterns", "🚧"),
            ("spark explore", "Plan and schedule autonomous exploration", "🚧"),
            ("spark morning", "Browse overnight discoveries", "⏳"),
            ("spark show", "Browse historical discoveries and patterns", "✅"),
            ("spark rate", "Rate and provide feedback for discoveries", "✅"),
            ("spark help", "Show this help message", "✅"),
            ("spark version", "Show version information", "✅"),
        ]
        
        for cmd, desc, status in commands_info:
            help_table.add_row(cmd, desc, status)
        
        self.console.print()
        self.console.print(help_table)
        self.console.print()
        self.console.print("💡 [dim]Use 'spark help <command>' for command-specific help[/dim]")
        return 0
    
    def _version_command(self, args: List[str]) -> int:
        """Display version information."""
        from spark import __version__
        version_panel = Panel(
            Text.assemble(
                ("Spark ", "bold blue"),
                (f"v{__version__}", "green"),
                ("\n", ""),
                ("AI Coding Platform", "white"),
                ("\n\n", ""),
                ("🧠 Learn your coding patterns", "dim white"),
                ("\n🚀 Autonomous exploration", "dim white"),
                ("\n🌅 Curated discoveries", "dim white"),
                ("\n🔗 Safe integration", "dim white"),
            ),
            title="Version Info",
            border_style="blue"
        )
        self.console.print(version_panel)
        return 0


def main() -> int:
    """Main CLI entry point."""
    try:
        cli = SparkCLI()
        args = sys.argv[1:]  # Remove script name
        return asyncio.run(cli.run(args))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        console = Console()
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
