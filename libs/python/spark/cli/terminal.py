"""
Terminal utilities and Rich formatting foundation for Spark CLI.

This module provides consistent terminal formatting, themes, and utilities
for creating beautiful, accessible command-line interfaces.
"""

from typing import Optional, Union, Dict, Any, List
from pathlib import Path
from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.rule import Rule
from rich.align import Align
from rich.columns import Columns
from rich import box


class SparkTheme:
    """Consistent color theme and styling for Spark CLI."""
    
    # Primary colors
    PRIMARY = "blue"
    SUCCESS = "green" 
    WARNING = "yellow"
    ERROR = "red"
    INFO = "cyan"
    
    # Secondary colors
    DIM = "dim white"
    BRIGHT = "bright_white"
    ACCENT = "magenta"
    
    # Status indicators
    STATUS_READY = "✅"
    STATUS_IN_PROGRESS = "🚧"
    STATUS_PENDING = "⏳"
    STATUS_ERROR = "❌"
    STATUS_WARNING = "⚠️"
    
    # Spark branding
    SPARK_ICON = "🚀"
    LEARN_ICON = "🧠"
    EXPLORE_ICON = "🌙"
    DISCOVER_ICON = "🌅"
    INTEGRATE_ICON = "🔗"


class SparkConsole:
    """Enhanced console with Spark-specific formatting and utilities."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.theme = SparkTheme()
    
    def print_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Print a formatted header with Spark branding."""
        header_text = Text.assemble(
            (f"{self.theme.SPARK_ICON} ", self.theme.PRIMARY),
            (title, "bold white")
        )
        
        if subtitle:
            header_text.append("\n")
            header_text.append(subtitle, style=self.theme.DIM)
        
        panel = Panel(
            Align.center(header_text),
            border_style=self.theme.PRIMARY,
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    def print_status_table(self, items: List[Dict[str, Any]], title: str = "Status") -> None:
        """Print a formatted status table."""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", justify="center", width=8)
        table.add_column("Details", style="white")
        
        for item in items:
            status_icon = item.get("icon", "")
            status_style = item.get("style", "white")
            
            table.add_row(
                item["name"],
                f"[{status_style}]{status_icon}[/{status_style}]",
                item.get("details", "")
            )
        
        self.console.print(table)
    
    def print_discovery_summary(self, discoveries: List[Dict[str, Any]]) -> None:
        """Print a formatted discovery summary."""
        if not discoveries:
            self.console.print("📭 [dim]No discoveries yet. Run 'spark explore' to start exploring![/dim]")
            return
        
        self.console.print(f"✨ [bold]{len(discoveries)} Recent Discoveries[/bold]")
        self.console.print()
        
        for i, discovery in enumerate(discoveries[:5], 1):  # Show top 5
            title = discovery.get("title", "Untitled Discovery")
            description = discovery.get("description", "No description")
            score = discovery.get("score", 0)
            
            # Score color coding
            if score >= 0.8:
                score_style = self.theme.SUCCESS
            elif score >= 0.6:
                score_style = self.theme.WARNING
            else:
                score_style = self.theme.DIM
            
            discovery_text = Text.assemble(
                (f"{i}. ", self.theme.ACCENT),
                (title, "bold white"),
                (f" ({score:.1%})", score_style),
                ("\n   ", ""),
                (description[:80] + "..." if len(description) > 80 else description, self.theme.DIM)
            )
            
            self.console.print(discovery_text)
            self.console.print()
    
    def print_pattern_analysis(self, patterns: Dict[str, Any]) -> None:
        """Print formatted pattern analysis results."""
        if not patterns:
            self.console.print("🔍 [dim]Learning your patterns... Check back soon![/dim]")
            return
        
        # Create columns for different pattern types
        columns = []
        
        # Languages
        if "languages" in patterns:
            lang_table = Table(title="Languages", box=box.ROUNDED)
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Usage", justify="right", style="green")
            
            for lang, usage in patterns["languages"].items():
                lang_table.add_row(lang, f"{usage:.1%}")
            columns.append(lang_table)
        
        # Patterns
        if "coding_patterns" in patterns:
            pattern_table = Table(title="Coding Patterns", box=box.ROUNDED)
            pattern_table.add_column("Pattern", style="magenta")
            pattern_table.add_column("Confidence", justify="right", style="yellow")
            
            for pattern, confidence in patterns["coding_patterns"].items():
                pattern_table.add_row(pattern, f"{confidence:.1%}")
            columns.append(pattern_table)
        
        if columns:
            self.console.print(Columns(columns))
    
    def print_learning_progress(self, progress_data: Dict[str, Any]) -> None:
        """Print learning progress with visual indicators."""
        confidence = progress_data.get("confidence", 0)
        days_learning = progress_data.get("days", 0)
        recent_activity = progress_data.get("recent_activity", {})
        
        # Progress bar representation using text
        bar_length = 20
        filled_length = int(bar_length * confidence)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Confidence color coding
        if confidence >= 0.85:
            confidence_style = self.theme.SUCCESS
            status_text = "Ready for exploration!"
        elif confidence >= 0.6:
            confidence_style = self.theme.WARNING
            status_text = "Building confidence..."
        else:
            confidence_style = self.theme.INFO
            status_text = "Learning your patterns..."
        
        progress_panel = Panel(
            Text.assemble(
                (f"{self.theme.LEARN_ICON} Learning Progress (Day {days_learning})", "bold white"),
                ("\n\n", ""),
                ("Confidence: ", "white"),
                (f"[{confidence_style}]{bar}[/{confidence_style}] {confidence:.1%}", ""),
                ("\n", ""),
                (status_text, confidence_style),
                ("\n\n", ""),
                ("Recent Activity:", "bold white"),
                (f"\n• {recent_activity.get('commits', 0)} commits", self.theme.DIM),
                (f"\n• {recent_activity.get('files_modified', 0)} files modified", self.theme.DIM),
                (f"\n• {recent_activity.get('patterns_detected', 0)} new patterns detected", self.theme.DIM),
            ),
            title="Learning Status",
            border_style=self.theme.PRIMARY
        )
        
        self.console.print(progress_panel)
    
    def print_error(self, message: str, details: Optional[str] = None) -> None:
        """Print formatted error message."""
        error_text = Text.assemble(
            (f"{self.theme.STATUS_ERROR} ", self.theme.ERROR),
            (message, f"bold {self.theme.ERROR}")
        )
        
        if details:
            error_text.append("\n")
            error_text.append(details, style=self.theme.DIM)
        
        self.console.print(error_text)
    
    def print_warning(self, message: str, details: Optional[str] = None) -> None:
        """Print formatted warning message."""
        warning_text = Text.assemble(
            (f"{self.theme.STATUS_WARNING} ", self.theme.WARNING),
            (message, f"bold {self.theme.WARNING}")
        )
        
        if details:
            warning_text.append("\n")
            warning_text.append(details, style=self.theme.DIM)
        
        self.console.print(warning_text)

    def print_info(self, message: str, details: Optional[str] = None) -> None:
        """Print formatted informational message."""
        info_text = Text.assemble(
            (f"{self.theme.SPARK_ICON} ", self.theme.INFO),
            (message, f"bold {self.theme.INFO}")
        )
        if details:
            info_text.append("\n")
            info_text.append(details, style=self.theme.DIM)
        self.console.print(info_text)
    
    def print_success(self, message: str, details: Optional[str] = None) -> None:
        """Print formatted success message."""
        success_text = Text.assemble(
            (f"{self.theme.STATUS_READY} ", self.theme.SUCCESS),
            (message, f"bold {self.theme.SUCCESS}")
        )
        
        if details:
            success_text.append("\n")
            success_text.append(details, style=self.theme.DIM)
        
        self.console.print(success_text)
    
    def create_spinner(self, text: str) -> Progress:
        """Create a spinner for long-running operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{text}[/bold blue]"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        )
    
    def print_code_diff(self, old_code: str, new_code: str, language: str = "python") -> None:
        """Print a formatted code diff."""
        self.console.print(Rule("Before", style=self.theme.ERROR))
        self.console.print(Syntax(old_code, language, theme="monokai", line_numbers=True))
        
        self.console.print(Rule("After", style=self.theme.SUCCESS))
        self.console.print(Syntax(new_code, language, theme="monokai", line_numbers=True))
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Get user confirmation with consistent styling."""
        default_text = "Y/n" if default else "y/N"
        prompt = f"❓ {message} [{default_text}]: "
        
        try:
            response = input(prompt).lower().strip()
            if not response:
                return default
            return response.startswith('y')
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n👋 Cancelled by user")
            return False


# Global console instance for easy access
_spark_console: Optional[SparkConsole] = None

def get_console() -> SparkConsole:
    """Get the global Spark console instance."""
    global _spark_console
    if _spark_console is None:
        _spark_console = SparkConsole()
    return _spark_console
