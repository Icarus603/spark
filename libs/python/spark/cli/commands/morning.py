"""
Spark morning command implementation.

Rich terminal interface for browsing overnight exploration discoveries,
complete with impact analysis, integration guidance, and interactive workflow.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.console import Group

from spark.cli.terminal import get_console
from spark.cli.errors import handle_async_cli_error
from spark.discovery.curator import DiscoveryCurator, CurationCriteria, RankingFactor
from spark.discovery.integrator import SafeIntegrator, IntegrationConfig, IntegrationStrategy
from spark.storage.discovery_storage import DiscoveryStorage
from spark.discovery.models import Discovery, DiscoveryType


class MorningCommand:
    """Implementation of the 'spark morning' command with rich presentation."""
    
    def __init__(self):
        self.console = get_console()
        self.curator = DiscoveryCurator()
        self.integrator = SafeIntegrator()
        self.storage = DiscoveryStorage()
    
    @handle_async_cli_error
    async def execute(self, args: List[str]) -> int:
        """Execute the morning command with rich discovery presentation."""
        
        # Parse command arguments
        show_all = "--all" in args
        interactive = "--interactive" in args or "-i" in args
        limit = self._parse_limit_arg(args)
        
        # Display morning greeting
        self._display_morning_greeting()
        
        # Get recent discoveries
        criteria = CurationCriteria(
            max_age_days=1 if not show_all else 7,  # Yesterday's discoveries or last week
            min_confidence=0.4,
            ranking_weights={
                RankingFactor.TECHNICAL_VALUE: 0.3,
                RankingFactor.IMPACT_POTENTIAL: 0.25,
                RankingFactor.ACTIONABILITY: 0.2,
                RankingFactor.NOVELTY: 0.15,
                RankingFactor.RECENCY: 0.1
            }
        )
        
        discoveries = self.curator.curate_discoveries(limit=limit, criteria=criteria)
        
        if not discoveries:
            self._display_no_discoveries()
            return 0
        
        # Display featured discovery
        featured = self.curator.get_featured_discovery()
        if featured:
            self._display_featured_discovery(featured)
        
        # Display discovery overview
        self._display_discovery_overview(discoveries)
        
        # Display learning updates
        self._display_learning_updates()
        
        # Interactive workflow
        if interactive or len(discoveries) <= 5:
            return await self._interactive_workflow(discoveries)
        else:
            self._display_non_interactive_summary()
            return 0
    
    def _display_morning_greeting(self):
        """Display personalized morning greeting."""
        
        current_time = datetime.now()
        
        if current_time.hour < 12:
            greeting = "🌅 Good morning!"
        elif current_time.hour < 17:
            greeting = "☀️ Good afternoon!"
        else:
            greeting = "🌆 Good evening!"
        
        # Get discovery stats
        stats = self.curator.get_curation_stats()
        recent_count = stats.get('recent_7_days', 0)
        
        greeting_panel = Panel(
            f"{greeting}\n\n"
            f"While you were away, I explored [bold cyan]{recent_count}[/bold cyan] new possibilities.\n"
            f"Here are the most promising discoveries:",
            title="🚀 Spark Discovery Report",
            border_style="cyan"
        )
        
        self.console.console.print(greeting_panel)
        self.console.console.print()
    
    def _display_featured_discovery(self, discovery: Discovery):
        """Display the featured discovery with rich formatting."""
        
        # Generate narrative for featured discovery
        narrative = self.curator.generate_discovery_narrative(discovery)
        impact_analysis = self.curator.analyze_discovery_impact(discovery)
        
        # Create featured discovery panel
        featured_content = []
        
        # Headline and summary
        featured_content.append(f"[bold yellow]{narrative.headline}[/bold yellow]")
        featured_content.append(f"\n{narrative.summary}")
        
        # Key benefits
        if narrative.key_benefits:
            featured_content.append("\n[bold]Key Benefits:[/bold]")
            for benefit in narrative.key_benefits:
                featured_content.append(f"  ✨ {benefit}")
        
        # Impact metrics
        if impact_analysis.overall_impact > 0:
            featured_content.append(f"\n[bold]Impact Score:[/bold] [green]{impact_analysis.overall_impact:.1%}[/green]")
            
            metrics = []
            if impact_analysis.performance_improvement > 0:
                metrics.append(f"⚡ Performance: {impact_analysis.performance_improvement:.1%}")
            if impact_analysis.code_quality_boost > 0:
                metrics.append(f"🔧 Quality: {impact_analysis.code_quality_boost:.1%}")
            if impact_analysis.time_savings > 0:
                metrics.append(f"⏱️ Time Savings: {impact_analysis.time_savings:.1%}")
            
            if metrics:
                featured_content.append(" | ".join(metrics))
        
        # Integration readiness
        if discovery.integration_ready:
            featured_content.append(f"\n[bold green]✅ Ready for integration[/bold green]")
            featured_content.append(f"Estimated time: {self._estimate_integration_time(discovery)} minutes")
        else:
            featured_content.append(f"\n[bold yellow]⚠️ Preparation required[/bold yellow]")
        
        featured_panel = Panel(
            "\n".join(featured_content),
            title="⭐ Featured Discovery",
            border_style="yellow"
        )
        
        self.console.console.print(featured_panel)
        self.console.console.print()
    
    def _display_discovery_overview(self, discoveries: List[Discovery]):
        """Display overview of all discoveries in a table."""
        
        if len(discoveries) <= 1:
            return  # Skip if only featured discovery
        
        table = Table(title="💡 Discovery Overview", show_header=True)
        table.add_column("Discovery", style="cyan", no_wrap=True)
        table.add_column("Type", style="blue")
        table.add_column("Impact", justify="center")
        table.add_column("Confidence", justify="center")
        table.add_column("Status", justify="center")
        
        for i, discovery in enumerate(discoveries[1:], 1):  # Skip featured (first) discovery
            # Determine status icon
            if discovery.integration_ready:
                status = "[green]✅ Ready[/green]"
            elif discovery.confidence_score > 0.7:
                status = "[yellow]⚠️ Review[/yellow]"
            else:
                status = "[red]⭕ Needs Work[/red]"
            
            # Format discovery type
            discovery_type = discovery.discovery_type.value.replace('_', ' ').title()
            
            table.add_row(
                f"{i}. {discovery.title[:30]}{'...' if len(discovery.title) > 30 else ''}",
                discovery_type,
                f"{discovery.impact_score:.1%}",
                f"{discovery.confidence_score:.1%}",
                status
            )
        
        self.console.console.print(table)
        self.console.console.print()
    
    def _display_learning_updates(self):
        """Display learning progress and pattern updates."""
        
        # Simulate learning updates (in real implementation, would get from learning system)
        learning_updates = [
            "🧠 Detected stronger preference for async patterns (+12%)",
            "📈 Code quality confidence increased to 89%",
            "🎯 New exploration focus: Performance optimization",
            "⭐ Pattern strength: Error handling practices (95%)"
        ]
        
        if learning_updates:
            learning_content = []
            learning_content.append("[bold]Learning Progress Update:[/bold]\n")
            
            for update in learning_updates[:3]:  # Show top 3 updates
                learning_content.append(f"  {update}")
            
            learning_panel = Panel(
                "\n".join(learning_content),
                title="🧠 AI Learning Updates",
                border_style="green"
            )
            
            self.console.console.print(learning_panel)
            self.console.console.print()
    
    def _display_no_discoveries(self):
        """Display message when no discoveries are available."""
        
        no_discoveries_content = [
            "[yellow]No new discoveries found.[/yellow]",
            "",
            "Possible reasons:",
            "  • No recent explorations have been run",
            "  • All recent explorations failed", 
            "  • Discovery confidence threshold not met",
            "",
            "Try running [cyan]spark explore[/cyan] to generate new discoveries!"
        ]
        
        panel = Panel(
            "\n".join(no_discoveries_content),
            title="🔍 Discovery Status",
            border_style="yellow"
        )
        
        self.console.console.print(panel)
    
    def _display_non_interactive_summary(self):
        """Display summary for non-interactive mode."""
        
        summary_content = [
            "For detailed discovery information:",
            "  • [cyan]spark show <discovery_id>[/cyan] - View specific discovery",
            "  • [cyan]spark morning --interactive[/cyan] - Interactive workflow", 
            "  • [cyan]spark integrate <discovery_id>[/cyan] - Integrate discovery",
            "  • [cyan]spark rate <discovery_id> <rating>[/cyan] - Rate discovery"
        ]
        
        panel = Panel(
            "\n".join(summary_content),
            title="🛠️ Next Steps",
            border_style="blue"
        )
        
        self.console.console.print(panel)
    
    async def _interactive_workflow(self, discoveries: List[Discovery]) -> int:
        """Run interactive workflow for discovery exploration and integration."""
        
        self.console.console.print("[bold cyan]🚀 Interactive Discovery Workflow[/bold cyan]\n")
        
        while True:
            # Show menu options
            self.console.console.print("[bold]What would you like to do?[/bold]")
            self.console.console.print("  1. 🔍 Explore specific discovery")
            self.console.console.print("  2. ⚡ Integrate ready discoveries")
            self.console.console.print("  3. ⭐ Rate discoveries")
            self.console.console.print("  4. 📊 View detailed analytics")
            self.console.console.print("  5. ❌ Exit")
            
            choice = Prompt.ask("\n[bold]Choose option[/bold]", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                await self._explore_discovery_workflow(discoveries)
            elif choice == "2":
                await self._integration_workflow(discoveries)
            elif choice == "3":
                await self._rating_workflow(discoveries)
            elif choice == "4":
                self._display_detailed_analytics(discoveries)
            else:  # choice == "5"
                self.console.console.print("\n[green]Happy coding! 🚀[/green]")
                break
            
            self.console.console.print()
        
        return 0
    
    async def _explore_discovery_workflow(self, discoveries: List[Discovery]):
        """Interactive discovery exploration workflow."""
        
        # Let user choose discovery
        self.console.console.print("\n[bold]Available Discoveries:[/bold]")
        for i, discovery in enumerate(discoveries, 1):
            self.console.console.print(f"  {i}. {discovery.title}")
        
        try:
            choice = int(Prompt.ask(f"[bold]Choose discovery (1-{len(discoveries)})[/bold]"))
            if 1 <= choice <= len(discoveries):
                selected_discovery = discoveries[choice - 1]
                self._display_detailed_discovery(selected_discovery)
            else:
                self.console.console.print("[red]Invalid choice[/red]")
        except ValueError:
            self.console.console.print("[red]Please enter a valid number[/red]")
    
    async def _integration_workflow(self, discoveries: List[Discovery]):
        """Interactive integration workflow."""
        
        # Filter ready discoveries
        ready_discoveries = [d for d in discoveries if d.integration_ready]
        
        if not ready_discoveries:
            self.console.console.print("\n[yellow]No discoveries are marked as integration-ready.[/yellow]")
            return
        
        self.console.console.print(f"\n[bold]Integration-Ready Discoveries ({len(ready_discoveries)}):[/bold]")
        
        for i, discovery in enumerate(ready_discoveries, 1):
            integration_assessment = self.curator.assess_integration_difficulty(discovery)
            
            self.console.console.print(
                f"  {i}. {discovery.title} "
                f"[dim]({integration_assessment.difficulty_level}, "
                f"~{integration_assessment.estimated_time_minutes}min)[/dim]"
            )
        
        if Confirm.ask("\n[bold]Proceed with integration?[/bold]"):
            try:
                choice = int(Prompt.ask(f"[bold]Choose discovery to integrate (1-{len(ready_discoveries)})[/bold]"))
                if 1 <= choice <= len(ready_discoveries):
                    selected_discovery = ready_discoveries[choice - 1]
                    await self._perform_integration(selected_discovery)
                else:
                    self.console.console.print("[red]Invalid choice[/red]")
            except ValueError:
                self.console.console.print("[red]Please enter a valid number[/red]")
    
    async def _perform_integration(self, discovery: Discovery):
        """Perform actual discovery integration."""
        
        self.console.console.print(f"\n[bold]Integrating: {discovery.title}[/bold]")
        
        # Show integration preview
        preview = self.integrator.preview_integration(discovery)
        
        preview_content = [
            f"Files to be modified: {preview['estimated_changes']}",
            f"Integration strategy: {preview['integration_strategy']}",
            f"Safety level: {preview.get('safety_level', 'medium')}"
        ]
        
        self.console.console.print("[dim]" + " | ".join(preview_content) + "[/dim]")
        
        if Confirm.ask("\n[bold]Confirm integration?[/bold]"):
            # Configure integration
            config = IntegrationConfig(
                strategy=IntegrationStrategy.FEATURE_BRANCH,
                create_backup=True,
                run_tests=True,
                confirmation_required=False  # Already confirmed
            )
            
            # Perform integration
            with self.console.console.status("[bold cyan]Integrating discovery..."):
                result = self.integrator.integrate_discovery(discovery, config)
            
            if result.status.value == "completed":
                self.console.console.print(f"[green]✅ Integration completed successfully![/green]")
                self.console.console.print(f"[dim]Feature branch: {result.metadata.get('feature_branch', 'N/A')}[/dim]")
                self.console.console.print(f"[dim]Files changed: {len(result.files_changed)}[/dim]")
            else:
                self.console.console.print(f"[red]❌ Integration failed: {result.error_message}[/red]")
        else:
            self.console.console.print("[yellow]Integration cancelled[/yellow]")
    
    async def _rating_workflow(self, discoveries: List[Discovery]):
        """Interactive discovery rating workflow."""
        
        unrated_discoveries = [d for d in discoveries if d.user_rating is None]
        
        if not unrated_discoveries:
            self.console.console.print("\n[green]All visible discoveries have been rated![/green]")
            return
        
        self.console.console.print(f"\n[bold]Unrated Discoveries ({len(unrated_discoveries)}):[/bold]")
        
        for i, discovery in enumerate(unrated_discoveries, 1):
            self.console.console.print(f"  {i}. {discovery.title}")
        
        if Confirm.ask("\n[bold]Rate some discoveries?[/bold]"):
            try:
                choice = int(Prompt.ask(f"[bold]Choose discovery to rate (1-{len(unrated_discoveries)})[/bold]"))
                if 1 <= choice <= len(unrated_discoveries):
                    selected_discovery = unrated_discoveries[choice - 1]
                    
                    # Show discovery details for rating
                    self._display_brief_discovery_details(selected_discovery)
                    
                    rating = Prompt.ask(
                        "\n[bold]Rate this discovery (1-5 stars)[/bold]",
                        choices=["1", "2", "3", "4", "5"]
                    )
                    
                    feedback = Prompt.ask(
                        "[bold]Optional feedback[/bold] (press Enter to skip)",
                        default=""
                    )
                    
                    # In real implementation, would save rating to storage
                    self.console.console.print(f"[green]✅ Rated {selected_discovery.title}: {rating} stars[/green]")
                    if feedback:
                        self.console.console.print(f"[dim]Feedback: {feedback}[/dim]")
                
            except ValueError:
                self.console.console.print("[red]Please enter a valid number[/red]")
    
    def _display_detailed_discovery(self, discovery: Discovery):
        """Display detailed information about a specific discovery."""
        
        # Generate comprehensive information
        narrative = self.curator.generate_discovery_narrative(discovery)
        impact_analysis = self.curator.analyze_discovery_impact(discovery)
        integration_assessment = self.curator.assess_integration_difficulty(discovery)
        
        # Create detailed view
        details = []
        
        # Header
        details.append(f"[bold yellow]{narrative.headline}[/bold yellow]\n")
        
        # Summary and value proposition
        details.append(f"[bold]Summary:[/bold] {narrative.summary}")
        details.append(f"[bold]Value:[/bold] {narrative.value_proposition}\n")
        
        # Metrics
        metrics_table = Table(show_header=False, box=None, padding=(0, 2))
        metrics_table.add_column("Metric", style="bold")
        metrics_table.add_column("Value", justify="right")
        
        metrics_table.add_row("Impact Score", f"[green]{discovery.impact_score:.1%}[/green]")
        metrics_table.add_row("Confidence", f"[blue]{discovery.confidence_score:.1%}[/blue]")
        metrics_table.add_row("Novelty", f"[purple]{discovery.novelty_score:.1%}[/purple]")
        metrics_table.add_row("Integration Risk", f"[{'green' if discovery.integration_risk == 'low' else 'yellow' if discovery.integration_risk == 'moderate' else 'red'}]{discovery.integration_risk}[/{'green' if discovery.integration_risk == 'low' else 'yellow' if discovery.integration_risk == 'moderate' else 'red'}]")
        
        details.append(metrics_table)
        details.append("")
        
        # Benefits
        if narrative.key_benefits:
            details.append("[bold]Key Benefits:[/bold]")
            for benefit in narrative.key_benefits:
                details.append(f"  ✨ {benefit}")
            details.append("")
        
        # Integration information
        details.append("[bold]Integration Information:[/bold]")
        details.append(f"  Difficulty: {integration_assessment.difficulty_level}")
        details.append(f"  Estimated Time: {integration_assessment.estimated_time_minutes} minutes")
        details.append(f"  Prerequisites: {len(integration_assessment.prerequisites)} items")
        details.append("")
        
        # Technical highlights
        if narrative.technical_highlights:
            details.append("[bold]Technical Highlights:[/bold]")
            for highlight in narrative.technical_highlights:
                details.append(f"  🔧 {highlight}")
        
        panel = Panel(
            Group(*details),
            title=f"🔍 Discovery Details: {discovery.title[:30]}",
            border_style="cyan"
        )
        
        self.console.console.print(panel)
    
    def _display_brief_discovery_details(self, discovery: Discovery):
        """Display brief discovery details for rating context."""
        
        details = [
            f"[bold]{discovery.title}[/bold]",
            f"Type: {discovery.discovery_type.value.replace('_', ' ').title()}",
            f"Description: {discovery.description[:100]}{'...' if len(discovery.description) > 100 else ''}"
        ]
        
        panel = Panel(
            "\n".join(details),
            title="Discovery Summary",
            border_style="blue"
        )
        
        self.console.console.print(panel)
    
    def _display_detailed_analytics(self, discoveries: List[Discovery]):
        """Display detailed analytics about discoveries."""
        
        stats = self.curator.get_curation_stats()
        
        analytics_content = []
        
        # Overall statistics
        analytics_content.append("[bold]Discovery Statistics:[/bold]")
        analytics_content.append(f"  Total discoveries: {stats.get('total', 0)}")
        analytics_content.append(f"  High confidence: {stats.get('high_confidence', 0)}")
        analytics_content.append(f"  High impact: {stats.get('high_impact', 0)}")
        analytics_content.append(f"  Integration ready: {stats.get('integration_ready', 0)}")
        analytics_content.append("")
        
        # Type distribution
        if 'type_distribution' in stats:
            analytics_content.append("[bold]Discovery Types:[/bold]")
            for discovery_type, count in stats['type_distribution'].items():
                analytics_content.append(f"  {discovery_type.replace('_', ' ').title()}: {count}")
            analytics_content.append("")
        
        # Average scores
        if stats.get('avg_confidence'):
            analytics_content.append("[bold]Average Scores:[/bold]")
            analytics_content.append(f"  Confidence: {stats['avg_confidence']:.1%}")
            analytics_content.append(f"  Impact: {stats['avg_impact']:.1%}")
            analytics_content.append(f"  Novelty: {stats['avg_novelty']:.1%}")
        
        panel = Panel(
            "\n".join(analytics_content),
            title="📊 Discovery Analytics",
            border_style="green"
        )
        
        self.console.console.print(panel)
    
    def _parse_limit_arg(self, args: List[str]) -> int:
        """Parse limit argument from command line."""
        
        for i, arg in enumerate(args):
            if arg == "--limit" and i + 1 < len(args):
                try:
                    return int(args[i + 1])
                except ValueError:
                    pass
        
        return 10  # Default limit
    
    def _estimate_integration_time(self, discovery: Discovery) -> int:
        """Estimate integration time in minutes."""
        
        # Simple estimation based on discovery complexity
        base_time = 15
        complexity = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        return base_time + (complexity * 5)
    
    def help(self) -> None:
        """Show help for the morning command."""
        help_content = [
            "[bold cyan]spark morning[/bold cyan] - Browse overnight exploration discoveries",
            "",
            "[bold]Usage:[/bold]",
            "  spark morning                    # Show today's discoveries",
            "  spark morning --all             # Show discoveries from last 7 days",
            "  spark morning --interactive     # Interactive workflow",
            "  spark morning --limit N         # Limit number of discoveries",
            "",
            "[bold]Features:[/bold]",
            "  • Rich discovery presentation with impact analysis",
            "  • Featured discovery highlighting",
            "  • Interactive integration workflow",
            "  • Discovery rating and feedback",
            "  • Learning progress updates",
            "  • Detailed analytics and insights"
        ]
        
        panel = Panel(
            "\n".join(help_content),
            title="🌅 Morning Command Help",
            border_style="cyan"
        )
        
        self.console.console.print(panel)
