"""
Rich terminal presentation for discoveries.

This module provides beautiful terminal presentation of exploration results and
discoveries using the existing SparkConsole infrastructure.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from spark.discovery.models import Discovery, DiscoveryType, FeedbackRating, CodeArtifact
from spark.cli.terminal import SparkConsole
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax


class DiscoveryPresenter:
    """Presents discoveries with rich terminal formatting."""
    
    def __init__(self):
        self.console = SparkConsole()
    
    def show_discovery_list(self, discoveries: List[Discovery], title: str = "Recent Discoveries") -> None:
        """Show a list of discoveries in a table format."""
        
        if not discoveries:
            self.console.print_warning("No discoveries found", "Try running some explorations first")
            return
        
        # Create table
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Title", style="bold")
        table.add_column("Type", style="cyan")
        table.add_column("Score", style="green", justify="center", width=8)
        table.add_column("Rating", justify="center", width=8)
        table.add_column("Age", style="dim", justify="right", width=10)
        
        for discovery in discoveries:
            # Format ID (first 8 chars)
            short_id = discovery.id[:8]
            
            # Format title (truncate if too long)
            title = discovery.title[:50] + "..." if len(discovery.title) > 50 else discovery.title
            
            # Format type
            type_name = discovery.discovery_type.value.replace('_', ' ').title()
            
            # Format score
            overall_score = f"{discovery.overall_score():.2f}"
            
            # Format rating
            if discovery.user_rating:
                rating_stars = "⭐" * discovery.user_rating.value
                rating = f"{rating_stars}"
            else:
                rating = "—"
            
            # Format age
            age_days = (datetime.now() - discovery.created_at).days
            if age_days == 0:
                age = "today"
            elif age_days == 1:
                age = "1 day"
            else:
                age = f"{age_days} days"
            
            table.add_row(short_id, title, type_name, overall_score, rating, age)
        
        self.console.console.print(table)
        
        # Show usage hint
        self.console.console.print(f"\n💡 Use [cyan]spark show <id>[/cyan] to view detailed information")
    
    def show_discovery_details(self, discovery: Discovery, show_code: bool = True) -> None:
        """Show detailed information about a specific discovery."""
        
        # Header panel
        header_text = f"[bold]{discovery.title}[/bold]\n"
        header_text += f"[dim]{discovery.discovery_type.value.replace('_', ' ').title()} • Created {self._format_datetime(discovery.created_at)}[/dim]"
        
        header_panel = Panel(
            header_text,
            title=f"🔍 Discovery {discovery.id[:8]}",
            border_style="cyan"
        )
        self.console.console.print(header_panel)
        
        # Description
        if discovery.description:
            desc_panel = Panel(
                discovery.description,
                title="📝 Description",
                border_style="blue"
            )
            self.console.console.print(desc_panel)
        
        # Metrics
        self._show_discovery_metrics(discovery)
        
        # Code artifacts
        if show_code and discovery.exploration_results:
            self._show_code_artifacts(discovery)
        
        # Integration information
        if discovery.integration_ready:
            self._show_integration_info(discovery)
        
        # User feedback
        if discovery.user_rating or discovery.user_feedback:
            self._show_user_feedback(discovery)
        
        # Tags
        if discovery.tags:
            tags_text = " ".join(f"[cyan]#{tag}[/cyan]" for tag in discovery.tags)
            self.console.console.print(f"\n🏷️  {tags_text}")
    
    def show_curation_stats(self, stats: Dict[str, Any]) -> None:
        """Show curation statistics."""
        
        if stats.get('total', 0) == 0:
            self.console.print_warning("No discoveries yet", "Run some explorations to see statistics")
            return
        
        # Overview panel
        overview_text = f"Total Discoveries: [bold]{stats['total']}[/bold]\n"
        overview_text += f"High Confidence (>80%): [green]{stats.get('high_confidence', 0)}[/green]\n"
        overview_text += f"High Impact (>70%): [yellow]{stats.get('high_impact', 0)}[/yellow]\n"
        overview_text += f"Integration Ready: [cyan]{stats.get('integration_ready', 0)}[/cyan]\n"
        overview_text += f"With User Feedback: [magenta]{stats.get('with_feedback', 0)}[/magenta]\n"
        overview_text += f"Recent (7 days): [blue]{stats.get('recent_7_days', 0)}[/blue]"
        
        overview_panel = Panel(
            overview_text,
            title="📊 Discovery Statistics",
            border_style="green"
        )
        self.console.console.print(overview_panel)
        
        # Type distribution
        if 'type_distribution' in stats:
            type_table = Table(title="Discoveries by Type", show_header=True)
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", justify="right", style="bold")
            
            for discovery_type, count in stats['type_distribution'].items():
                type_name = discovery_type.replace('_', ' ').title()
                type_table.add_row(type_name, str(count))
            
            self.console.console.print(type_table)
        
        # Average scores
        if 'avg_confidence' in stats:
            scores_text = f"Average Confidence: [green]{stats['avg_confidence']:.2f}[/green]\n"
            scores_text += f"Average Impact: [yellow]{stats['avg_impact']:.2f}[/yellow]\n"
            scores_text += f"Average Novelty: [cyan]{stats['avg_novelty']:.2f}[/cyan]"
            
            if 'avg_rating' in stats:
                scores_text += f"\nAverage User Rating: [magenta]{stats['avg_rating']:.1f}/5.0[/magenta]"
            
            scores_panel = Panel(
                scores_text,
                title="📈 Quality Metrics",
                border_style="yellow"
            )
            self.console.console.print(scores_panel)
    
    def show_exploration_suggestions(self, suggestions: List[str]) -> None:
        """Show suggested exploration topics."""
        
        if not suggestions:
            self.console.print_info("No specific suggestions available", "Try exploring based on your current project needs")
            return
        
        suggestion_text = ""
        for i, suggestion in enumerate(suggestions, 1):
            suggestion_text += f"{i}. [cyan]{suggestion}[/cyan]\n"
        
        suggestion_panel = Panel(
            suggestion_text.strip(),
            title="💡 Suggested Exploration Topics",
            border_style="magenta"
        )
        self.console.console.print(suggestion_panel)
    
    def _show_discovery_metrics(self, discovery: Discovery) -> None:
        """Show discovery metrics in a formatted layout."""
        
        # Create metrics columns
        confidence_text = f"[green]Confidence[/green]\n[bold]{discovery.confidence_score:.1%}[/bold]"
        impact_text = f"[yellow]Impact[/yellow]\n[bold]{discovery.impact_score:.1%}[/bold]"
        novelty_text = f"[cyan]Novelty[/cyan]\n[bold]{discovery.novelty_score:.1%}[/bold]"
        overall_text = f"[magenta]Overall[/magenta]\n[bold]{discovery.overall_score():.2f}[/bold]"
        
        metrics_columns = Columns([
            Panel(confidence_text, width=15),
            Panel(impact_text, width=15),
            Panel(novelty_text, width=15),
            Panel(overall_text, width=15)
        ], equal=True)
        
        self.console.console.print(Panel(metrics_columns, title="📊 Metrics"))
    
    def _show_code_artifacts(self, discovery: Discovery) -> None:
        """Show code artifacts with syntax highlighting."""
        
        for result in discovery.exploration_results:
            if not result.code_artifacts:
                continue
            
            # Show approach
            approach_panel = Panel(
                f"[bold]{result.approach}[/bold]\n[dim]{result.goal}[/dim]",
                title="🎯 Approach",
                border_style="blue"
            )
            self.console.console.print(approach_panel)
            
            # Show main artifacts
            main_artifacts = [a for a in result.code_artifacts if a.is_main_artifact]
            supporting_artifacts = [a for a in result.code_artifacts if not a.is_main_artifact]
            
            for artifact in main_artifacts:
                self._show_code_artifact(artifact, is_main=True)
            
            if supporting_artifacts:
                self.console.console.print(f"\n[dim]+ {len(supporting_artifacts)} supporting files[/dim]")
    
    def _show_code_artifact(self, artifact: CodeArtifact, is_main: bool = False) -> None:
        """Show a single code artifact with syntax highlighting."""
        
        title = f"📄 {artifact.file_path}"
        if is_main:
            title += " (main)"
        
        # Limit code display to reasonable length
        content = artifact.content
        if len(content) > 1000:
            content = content[:1000] + "\n\n... (truncated)"
        
        try:
            # Use syntax highlighting if possible
            syntax = Syntax(
                content,
                artifact.language,
                theme="monokai",
                line_numbers=True,
                word_wrap=True
            )
            code_panel = Panel(syntax, title=title, border_style="bright_black")
        except Exception:
            # Fallback to plain text
            code_panel = Panel(content, title=title, border_style="bright_black")
        
        self.console.console.print(code_panel)
        
        # Show artifact description
        if artifact.description:
            self.console.console.print(f"[dim]💬 {artifact.description}[/dim]\n")
    
    def _show_integration_info(self, discovery: Discovery) -> None:
        """Show integration information."""
        
        risk_colors = {
            "low": "green",
            "moderate": "yellow", 
            "high": "red"
        }
        risk_color = risk_colors.get(discovery.integration_risk, "yellow")
        
        integration_text = f"[{risk_color}]Risk Level: {discovery.integration_risk.title()}[/{risk_color}]\n\n"
        
        if discovery.integration_instructions:
            integration_text += "[bold]Integration Steps:[/bold]\n"
            for instruction in discovery.integration_instructions:
                integration_text += f"• {instruction}\n"
        
        integration_panel = Panel(
            integration_text.strip(),
            title="🔧 Integration Ready",
            border_style="green"
        )
        self.console.console.print(integration_panel)
    
    def _show_user_feedback(self, discovery: Discovery) -> None:
        """Show user feedback information."""
        
        feedback_text = ""
        
        if discovery.user_rating:
            stars = "⭐" * discovery.user_rating.value
            rating_name = discovery.user_rating.name.title()
            feedback_text += f"[bold]Rating:[/bold] {stars} ({rating_name})\n"
        
        if discovery.user_feedback.strip():
            feedback_text += f"[bold]Feedback:[/bold] {discovery.user_feedback}"
        
        if feedback_text:
            feedback_panel = Panel(
                feedback_text.strip(),
                title="💭 User Feedback",
                border_style="magenta"
            )
            self.console.console.print(feedback_panel)
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago" if minutes > 0 else "just now"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%Y-%m-%d")
    
    def prompt_for_rating(self, discovery: Discovery) -> Optional[tuple[FeedbackRating, str]]:
        """Prompt user for discovery rating (placeholder for now)."""
        
        self.console.console.print(f"\n[bold]Rate this discovery:[/bold] {discovery.title[:50]}")
        self.console.console.print("Rating system will be interactive in the CLI")
        self.console.console.print("For now, use: [cyan]spark rate <discovery-id> <rating> [feedback][/cyan]")
        
        return None
    
    def show_feedback_prompt(self, discovery_id: str) -> None:
        """Show how to provide feedback for a discovery."""
        
        self.console.console.print(Panel(
            f"[bold]Rate this discovery:[/bold]\n\n"
            f"[cyan]spark rate {discovery_id[:8]} 5 \"Excellent implementation!\"[/cyan]\n"
            f"[cyan]spark rate {discovery_id[:8]} 3 \"Good but needs work\"[/cyan]\n"
            f"[cyan]spark rate {discovery_id[:8]} 1[/cyan] (no feedback message)\n\n"
            f"[dim]Ratings: 1=Terrible, 2=Poor, 3=Neutral, 4=Good, 5=Excellent[/dim]",
            title="💭 Provide Feedback",
            border_style="magenta"
        ))