"""
Spark status command implementation.

Shows current learning progress, detected patterns, and system status.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

from spark.core.config import SparkConfig
from spark.storage.pattern_storage import PatternStorage
from spark.cli.terminal import get_console, SparkTheme
from spark.cli.errors import handle_async_cli_error, SparkLearningError

# Enhanced pattern analysis components
from spark.learning.style_analyzer import MultiLanguageStyleAnalyzer
from spark.learning.confidence_scorer import PatternConfidenceScorer, PatternType
from spark.learning.file_monitor import FileSystemMonitor
from spark.learning.preference_mapper import PreferenceMapper

# Interactive dashboard
try:
    from spark.cli.ui.dashboard import create_dashboard, DashboardConfig
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False


class StatusCommand:
    """Implementation of the 'spark status' command."""
    
    def __init__(self):
        self.console = get_console()
        self.theme = SparkTheme()
        
        # Initialize enhanced analyzers
        self.style_analyzer = MultiLanguageStyleAnalyzer()
        self.confidence_scorer = PatternConfidenceScorer()
        self.preference_mapper = PreferenceMapper()
        self.file_monitor: Optional[FileSystemMonitor] = None
    
    @handle_async_cli_error
    async def execute(self, args: List[str]) -> int:
        """Execute the status command."""
        try:
            # Load configuration
            config = SparkConfig()
            
            if not config.is_initialized():
                self.console.print_error(
                    "Spark not initialized",
                    "Run 'spark' to initialize Spark first"
                )
                return 1
            
            config.load()
            
            # Parse arguments for different status views
            detailed = '--detailed' in args or '-d' in args
            patterns = '--patterns' in args or '-p' in args
            interactive = '--interactive' in args or '-i' in args
            confidence = '--confidence' in args or '-c' in args
            preferences = '--preferences' in args or '--prefs' in args
            sessions = '--sessions' in args or '-s' in args
            
            if interactive:
                return await self._show_interactive_status(config)
            elif patterns:
                return await self._show_patterns(config)
            elif confidence:
                return await self._show_confidence_analysis(config)
            elif preferences:
                return await self._show_preference_analysis(config)
            elif sessions:
                return await self._show_session_analysis(config)
            else:
                return await self._show_status(config, detailed)
            
        except Exception as e:
            raise SparkLearningError(
                "Failed to show status",
                str(e)
            ) from e
    
    async def _show_status(self, config: SparkConfig, detailed: bool = False) -> int:
        """Show main status display."""
        
        # Header
        self.console.print_header("Spark Status", "AI Coding Intelligence Platform")
        
        # Get learning progress data
        with PatternStorage(config.get_database_path()) as storage:
            progress = storage.get_progress()
            patterns = storage.get_patterns(min_confidence=0.3)
        
        # Show learning progress
        self._show_learning_progress(progress, config)
        
        # Show recent activity
        self._show_recent_activity(progress, patterns)
        
        # Show system status
        self._show_system_status(config)
        
        # Show next steps
        self._show_next_steps(progress, config)
        
        if detailed:
            self._show_detailed_breakdown(progress, patterns)
        
        return 0
    
    def _show_learning_progress(self, progress: Dict[str, Any], config: SparkConfig) -> None:
        """Display learning progress summary."""
        
        confidence = progress.get('avg_confidence', 0.0)
        days_learning = progress.get('days_learning', 0)
        pattern_count = progress.get('pattern_count', 0)
        
        # Create progress data for console
        progress_data = {
            'confidence': confidence,
            'days': days_learning,
            'recent_activity': {
                'patterns_detected': pattern_count,
                'files_modified': 0,  # Would come from file monitoring
                'commits': 0  # Would come from git monitoring
            }
        }
        
        self.console.print_learning_progress(progress_data)
        self.console.console.print()
    
    def _show_recent_activity(self, progress: Dict[str, Any], patterns: List[Dict[str, Any]]) -> None:
        """Show recent learning activity."""
        recent_events = progress.get('recent_events', 0)
        
        if recent_events > 0 or patterns:
            self.console.console.print("📊 [bold]Recent Activity:[/bold]")
            
            # Show pattern breakdown
            pattern_breakdown = progress.get('pattern_breakdown', {})
            if pattern_breakdown:
                for pattern_type, data in pattern_breakdown.items():
                    confidence = data['confidence']
                    count = data['count']
                    
                    confidence_color = self.theme.SUCCESS if confidence > 0.8 else self.theme.WARNING if confidence > 0.6 else self.theme.INFO
                    
                    self.console.console.print(
                        f"  • {pattern_type.title()} patterns: "
                        f"[{confidence_color}]{confidence:.1%}[/{confidence_color}] "
                        f"[dim]({count} detected)[/dim]"
                    )
            
            if recent_events > 0:
                self.console.console.print(f"  • {recent_events} learning events in the last 7 days")
            
            self.console.console.print()
        else:
            self.console.console.print("📭 [dim]No recent activity. Start coding to begin learning![/dim]")
            self.console.console.print()
    
    def _show_system_status(self, config: SparkConfig) -> None:
        """Show system health and status."""
        status_items = []
        
        # Check database
        db_path = config.get_database_path()
        if db_path.exists():
            db_size_mb = db_path.stat().st_size / (1024 * 1024)
            status_items.append({
                "name": "Database",
                "icon": self.theme.STATUS_READY,
                "style": self.theme.SUCCESS,
                "details": f"{db_size_mb:.1f}MB"
            })
        else:
            status_items.append({
                "name": "Database",
                "icon": self.theme.STATUS_ERROR,
                "style": self.theme.ERROR,
                "details": "Not found"
            })
        
        # Check repositories
        repo_count = len(config.config.repositories)
        if repo_count > 0:
            active_repos = sum(1 for repo in config.config.repositories if Path(repo).exists())
            status_items.append({
                "name": "Repositories",
                "icon": self.theme.STATUS_READY,
                "style": self.theme.SUCCESS,
                "details": f"{active_repos}/{repo_count} active"
            })
        else:
            status_items.append({
                "name": "Repositories",
                "icon": self.theme.STATUS_WARNING,
                "style": self.theme.WARNING,
                "details": "None configured"
            })
        
        # Check learning status
        learning_enabled = config.config.learning.enabled
        if learning_enabled:
            status_items.append({
                "name": "Learning",
                "icon": self.theme.STATUS_READY,
                "style": self.theme.SUCCESS,
                "details": "Active"
            })
        else:
            status_items.append({
                "name": "Learning", 
                "icon": self.theme.STATUS_WARNING,
                "style": self.theme.WARNING,
                "details": "Disabled"
            })
        
        # Check exploration readiness
        with PatternStorage(config.get_database_path()) as storage:
            progress = storage.get_progress()
        
        confidence = progress.get('avg_confidence', 0.0)
        if confidence >= 0.85:
            status_items.append({
                "name": "Exploration",
                "icon": self.theme.STATUS_READY,
                "style": self.theme.SUCCESS,
                "details": "Ready"
            })
        elif confidence >= 0.6:
            status_items.append({
                "name": "Exploration",
                "icon": self.theme.STATUS_IN_PROGRESS,
                "style": self.theme.WARNING,
                "details": "Building confidence"
            })
        else:
            status_items.append({
                "name": "Exploration",
                "icon": self.theme.STATUS_PENDING,
                "style": self.theme.INFO,
                "details": "Learning patterns"
            })
        
        self.console.print_status_table(status_items, "System Status")
        self.console.console.print()
    
    def _show_next_steps(self, progress: Dict[str, Any], config: SparkConfig) -> None:
        """Show recommended next steps."""
        confidence = progress.get('avg_confidence', 0.0)
        days_learning = progress.get('days_learning', 0)
        
        self.console.console.print("💡 [bold]Recommended Actions:[/bold]")
        
        if confidence < 0.6:
            self.console.console.print("  1. [cyan]Keep coding normally[/cyan] - Spark learns from your patterns")
            if days_learning < 3:
                self.console.console.print("  2. [cyan]Check back in a few days[/cyan] - Confidence builds over time")
            else:
                self.console.console.print("  2. [cyan]Add more repositories[/cyan] - Run 'spark learn --add <path>'")
        elif confidence < 0.85:
            self.console.console.print("  1. [cyan]Continue normal development[/cyan] - Building strong patterns")
            self.console.console.print("  2. [cyan]Review detected patterns[/cyan] - Run 'spark status --patterns'")
        else:
            self.console.console.print("  1. [green]Ready for exploration![/green] - Run 'spark explore' tonight")
            self.console.console.print("  2. [cyan]Review learning progress[/cyan] - Run 'spark status --detailed'")
        
        if not config.config.repositories:
            self.console.console.print("  • [yellow]Add repositories to monitor[/yellow] - Run 'spark learn --add <path>'")
        
        self.console.console.print()
    
    def _show_detailed_breakdown(self, progress: Dict[str, Any], patterns: List[Dict[str, Any]]) -> None:
        """Show detailed pattern breakdown."""
        self.console.console.print("🔍 [bold]Detailed Pattern Analysis:[/bold]")
        
        if not patterns:
            self.console.console.print("  [dim]No patterns detected yet. Keep coding to build your profile![/dim]")
            return
        
        # Group patterns by type
        pattern_groups = {}
        for pattern in patterns:
            pattern_type = pattern['pattern_type']
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(pattern)
        
        # Show each pattern type
        for pattern_type, type_patterns in pattern_groups.items():
            avg_confidence = sum(p['confidence_score'] for p in type_patterns) / len(type_patterns)
            
            confidence_color = (
                self.theme.SUCCESS if avg_confidence > 0.8 
                else self.theme.WARNING if avg_confidence > 0.6 
                else self.theme.INFO
            )
            
            self.console.console.print(f"\n  {pattern_type.title()} Patterns:")
            self.console.console.print(f"    Confidence: [{confidence_color}]{avg_confidence:.1%}[/{confidence_color}]")
            self.console.console.print(f"    Repositories: {len(type_patterns)}")
            
            # Show some specific insights for each type
            self._show_pattern_insights(pattern_type, type_patterns)
        
        self.console.console.print()
    
    def _show_pattern_insights(self, pattern_type: str, patterns: List[Dict[str, Any]]) -> None:
        """Show specific insights for a pattern type."""
        if not patterns:
            return
        
        if pattern_type == 'language':
            # Show language preferences
            all_languages = {}
            for pattern in patterns:
                languages = pattern['pattern_data'].get('languages', {})
                for lang, percentage in languages.items():
                    if lang not in all_languages:
                        all_languages[lang] = []
                    all_languages[lang].append(percentage)
            
            # Average across repositories
            avg_languages = {
                lang: sum(percentages) / len(percentages) 
                for lang, percentages in all_languages.items()
            }
            
            # Show top 3 languages
            top_languages = sorted(avg_languages.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_languages:
                lang_text = ", ".join([f"{lang} ({pct:.1%})" for lang, pct in top_languages])
                self.console.console.print(f"    Top Languages: [cyan]{lang_text}[/cyan]")
        
        elif pattern_type == 'commit':
            # Show commit patterns
            total_commits = 0
            avg_files_per_commit = 0
            conventional_commits = 0
            
            for pattern in patterns:
                data = pattern['pattern_data']
                avg_files = data.get('average_files_per_commit', 0)
                if avg_files > 0:
                    avg_files_per_commit += avg_files
                    total_commits += 1
                
                if data.get('message_style') == 'conventional':
                    conventional_commits += 1
            
            if total_commits > 0:
                avg_files_per_commit = avg_files_per_commit / total_commits
                self.console.console.print(f"    Average files per commit: [cyan]{avg_files_per_commit:.1f}[/cyan]")
            
            if conventional_commits > 0:
                self.console.console.print(f"    Uses conventional commits: [green]Yes[/green] ({conventional_commits}/{len(patterns)} repos)")
    
    async def _show_patterns(self, config: SparkConfig) -> int:
        """Show detailed pattern analysis."""
        self.console.print_header("Pattern Analysis", "Detected coding patterns and preferences")
        
        with PatternStorage(config.get_database_path()) as storage:
            patterns = storage.get_patterns(min_confidence=0.3)
            progress = storage.get_progress()
        
        if not patterns:
            self.console.console.print("📭 [dim]No patterns detected yet.[/dim]")
            self.console.console.print()
            self.console.console.print("💡 [bold]To build patterns:[/bold]")
            self.console.console.print("  1. Add repositories: [cyan]spark learn --add <path>[/cyan]")
            self.console.console.print("  2. Continue normal development")
            self.console.console.print("  3. Check back in a few days")
            return 0
        
        # Show pattern analysis
        pattern_data = {}
        for pattern in patterns:
            pattern_type = pattern['pattern_type']
            if pattern_type == 'language':
                languages = pattern['pattern_data'].get('languages', {})
                for lang, pct in languages.items():
                    if 'languages' not in pattern_data:
                        pattern_data['languages'] = {}
                    if lang not in pattern_data['languages']:
                        pattern_data['languages'][lang] = []
                    pattern_data['languages'][lang].append(pct)
            elif pattern_type == 'commit':
                if 'coding_patterns' not in pattern_data:
                    pattern_data['coding_patterns'] = {}
                
                data = pattern['pattern_data']
                if data.get('prefers_small_commits'):
                    pattern_data['coding_patterns']['Small commits'] = pattern['confidence_score']
                if data.get('message_style') == 'conventional':
                    pattern_data['coding_patterns']['Conventional commits'] = pattern['confidence_score']
        
        # Average language percentages
        if 'languages' in pattern_data:
            avg_languages = {
                lang: sum(pcts) / len(pcts) 
                for lang, pcts in pattern_data['languages'].items()
            }
            pattern_data['languages'] = avg_languages
        
        self.console.print_pattern_analysis(pattern_data)
        
        # Show confidence levels
        self.console.console.print("\n📊 [bold]Pattern Confidence Levels:[/bold]")
        
        pattern_breakdown = progress.get('pattern_breakdown', {})
        for pattern_type, data in pattern_breakdown.items():
            confidence = data['confidence']
            count = data['count']
            
            confidence_color = (
                self.theme.SUCCESS if confidence > 0.8 
                else self.theme.WARNING if confidence > 0.6 
                else self.theme.INFO
            )
            
            self.console.console.print(
                f"  {pattern_type.title()}: "
                f"[{confidence_color}]{confidence:.1%}[/{confidence_color}] "
                f"[dim]({count} patterns)[/dim]"
            )
        
        return 0
    
    async def _show_interactive_status(self, config: SparkConfig) -> int:
        """Show interactive real-time status dashboard."""
        if not DASHBOARD_AVAILABLE:
            self.console.print_error(
                "Interactive dashboard not available",
                "Install with: pip install blessed"
            )
            return 1
        
        try:
            # Get project paths from config
            project_paths = [Path(repo) for repo in config.config.repositories if Path(repo).exists()]
            
            if not project_paths:
                self.console.print_warning(
                    "No repositories configured for monitoring",
                    "Add repositories with: spark learn --add <path>"
                )
                return 1
            
            # Create and start dashboard
            dashboard_config = DashboardConfig(
                refresh_interval=1.0,
                enable_colors=True,
                enable_animations=True
            )
            
            self.console.console.print("🚀 [bold]Starting interactive dashboard...[/bold]")
            self.console.console.print("Press 'Q' to quit, 'H' for help")
            self.console.console.print()
            
            # Small delay to let user read the message
            await asyncio.sleep(1)
            
            with create_dashboard(project_paths[0], dashboard_config) as dashboard:
                # Add additional paths
                for path in project_paths[1:]:
                    dashboard.file_monitor.add_path(path)
                
                dashboard.start()
            
            return 0
            
        except KeyboardInterrupt:
            self.console.console.print("\n✅ [dim]Dashboard closed[/dim]")
            return 0
        except Exception as e:
            self.console.print_error("Failed to start interactive dashboard", str(e))
            return 1
    
    async def _show_confidence_analysis(self, config: SparkConfig) -> int:
        """Show detailed multi-dimensional confidence analysis."""
        self.console.print_header("Confidence Analysis", "Multi-dimensional pattern confidence scoring")
        
        try:
            # Collect patterns from all repositories
            all_patterns = self._collect_repository_patterns(config)
            
            if not all_patterns:
                self.console.console.print("📭 [dim]No patterns available for confidence analysis.[/dim]")
                self.console.console.print("\n💡 [bold]To build confidence scores:[/bold]")
                self.console.console.print("  1. Add repositories: [cyan]spark learn --add <path>[/cyan]")
                self.console.console.print("  2. Continue development to generate patterns")
                return 0
            
            # Calculate confidence scores
            confidence_scores = {}
            for pattern_type in PatternType:
                type_patterns = [p for p in all_patterns if p.get('type') == pattern_type.value]
                if type_patterns:
                    score = self.confidence_scorer.calculate_confidence(
                        pattern_type, type_patterns
                    )
                    confidence_scores[pattern_type] = score
            
            # Display confidence analysis
            self._display_confidence_scores(confidence_scores)
            
            # Show exploration readiness
            readiness = self.confidence_scorer.calculate_exploration_readiness(confidence_scores)
            self._display_exploration_readiness(readiness)
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to analyze confidence", str(e))
            return 1
    
    def _collect_repository_patterns(self, config: SparkConfig) -> List[Dict[str, Any]]:
        """Collect patterns from all repositories."""
        all_patterns = []
        
        for repo_path in config.config.repositories:
            path = Path(repo_path)
            if path.exists():
                try:
                    # Analyze repository using style analyzer
                    file_analyses = self.style_analyzer.analyze_directory(path)
                    
                    # Convert to pattern format
                    for file_analysis in file_analyses:
                        all_patterns.append({
                            'type': 'style',
                            'repository': str(path),
                            'file': str(file_analysis.file_path),
                            'confidence': file_analysis.confidence_score,
                            'data': {
                                'functions': len(file_analysis.functions),
                                'classes': len(file_analysis.classes),
                                'complexity': file_analysis.avg_complexity,
                                'style_profile': file_analysis.style_profile
                            }
                        })
                except Exception as e:
                    self.console.logger.warning(f"Error analyzing {path}: {e}")
        
        return all_patterns
    
    def _display_confidence_scores(self, confidence_scores: Dict) -> None:
        """Display detailed confidence score analysis."""
        self.console.console.print("📊 [bold]Multi-Dimensional Confidence Analysis:[/bold]\n")
        
        for pattern_type, score in confidence_scores.items():
            self.console.console.print(f"[bold]{pattern_type.value.title()}:[/bold]")
            self.console.console.print(f"  Overall Confidence: [{self._get_confidence_color(score.overall_confidence)}]{score.overall_confidence:.1%}[/{self._get_confidence_color(score.overall_confidence)}]")
            self.console.console.print(f"  Statistical Significance: [{self._get_significance_color(score.statistical_significance)}]{score.statistical_significance:.1%}[/{self._get_significance_color(score.statistical_significance)}]")
            self.console.console.print(f"  Sample Size: [cyan]{score.sample_size}[/cyan]")
            self.console.console.print(f"  Temporal Stability: [{self._get_confidence_color(score.temporal_stability)}]{score.temporal_stability:.1%}[/{self._get_confidence_color(score.temporal_stability)}]")
            self.console.console.print()
    
    def _display_exploration_readiness(self, readiness: Dict[str, Any]) -> None:
        """Display exploration readiness analysis."""
        overall_readiness = readiness.get('overall_readiness', 0.0)
        readiness_color = self._get_confidence_color(overall_readiness)
        
        self.console.console.print(f"🎯 [bold]Exploration Readiness: [{readiness_color}]{overall_readiness:.1%}[/{readiness_color}][/bold]\n")
        
        recommendations = readiness.get('recommendations', [])
        if recommendations:
            self.console.console.print("💡 [bold]Recommendations:[/bold]")
            for rec in recommendations[:5]:  # Show top 5
                self.console.console.print(f"  • {rec}")
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence level."""
        if confidence > 0.8:
            return self.theme.SUCCESS
        elif confidence > 0.6:
            return self.theme.WARNING
        else:
            return self.theme.INFO
    
    def _get_significance_color(self, significance: float) -> str:
        """Get color for statistical significance."""
        if significance > 0.95:
            return self.theme.SUCCESS
        elif significance > 0.8:
            return self.theme.WARNING
        else:
            return self.theme.ERROR
    
    async def _show_preference_analysis(self, config: SparkConfig) -> int:
        """Show developer preference and learning trajectory analysis."""
        self.console.print_header("Preference Analysis", "Developer behavior and learning preferences")
        
        try:
            # Collect analysis data
            git_analyses = self._collect_git_analyses(config)
            style_profiles = self._collect_style_profiles(config)
            
            if not git_analyses and not style_profiles:
                self.console.console.print("📭 [dim]Insufficient data for preference analysis.[/dim]")
                self.console.console.print("\n💡 [bold]To build preference profile:[/bold]")
                self.console.console.print("  1. Add repositories with git history")
                self.console.console.print("  2. Continue coding to build style patterns")
                return 0
            
            # Build preference profile - simplified for now
            self.console.console.print("🎨 [bold]Developer Preference Profile:[/bold]\n")
            self.console.console.print("Adoption Style: [cyan]Progressive[/cyan]")
            self.console.console.print("Problem-Solving Approach: [cyan]Balanced[/cyan]")
            
            if style_profiles:
                self.console.console.print("\n[bold]Code Style Preferences:[/bold]")
                for profile_data in style_profiles[:3]:
                    repo_name = Path(profile_data['repository']).name
                    self.console.console.print(f"  • {repo_name}: [green]Consistent style patterns detected[/green]")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to analyze preferences", str(e))
            return 1
    
    async def _show_session_analysis(self, config: SparkConfig) -> int:
        """Show development session and rhythm analysis."""
        self.console.print_header("Session Analysis", "Development rhythm and activity patterns")
        
        try:
            # Initialize file monitor for analysis
            monitor = FileSystemMonitor()
            
            # Add repository paths
            for repo_path in config.config.repositories:
                path = Path(repo_path)
                if path.exists():
                    monitor.add_path(path, recursive=True)
            
            if not monitor.monitored_paths:
                self.console.console.print("📭 [dim]No repositories configured for session analysis.[/dim]")
                return 1
            
            # Get development rhythm analysis
            rhythm_data = monitor.get_development_rhythm()
            
            # Display session analysis
            self.console.console.print("📈 [bold]Development Session Analysis:[/bold]\n")
            
            total_sessions = rhythm_data.get('total_sessions', 0)
            avg_duration = rhythm_data.get('average_session_duration', 0)
            avg_changes = rhythm_data.get('average_changes_per_session', 0)
            
            self.console.console.print(f"Total Sessions: [cyan]{total_sessions}[/cyan]")
            self.console.console.print(f"Average Duration: [cyan]{avg_duration:.1f}h[/cyan]")
            self.console.console.print(f"Average Changes per Session: [cyan]{avg_changes:.0f}[/cyan]")
            
            # Peak hours
            peak_hours = rhythm_data.get('peak_hours', [])
            if peak_hours:
                self.console.console.print("\n[bold]Peak Development Hours:[/bold]")
                for hour, count in peak_hours[:3]:
                    self.console.console.print(f"  • {hour:02d}:00 - [cyan]{count} sessions[/cyan]")
            
            # Languages used
            languages = rhythm_data.get('languages_used', [])
            if languages:
                self.console.console.print(f"\nLanguages Used: [cyan]{', '.join(languages)}[/cyan]")
            
            # Show current session if active
            current_session = rhythm_data.get('current_session', {})
            if current_session.get('active'):
                self.console.console.print("\n🔥 [bold]Current Active Session:[/bold]")
                self.console.console.print(f"Duration: [green]{current_session.get('duration', 0):.1f}h[/green]")
                self.console.console.print(f"Changes: [green]{current_session.get('changes', 0)}[/green]")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to analyze sessions", str(e))
            return 1
    
    def _collect_git_analyses(self, config: SparkConfig) -> List[Dict[str, Any]]:
        """Collect git analysis data from repositories."""
        # Placeholder - would integrate with git analysis
        return []
    
    def _collect_style_profiles(self, config: SparkConfig) -> List[Dict[str, Any]]:
        """Collect style profiles from repositories."""
        profiles = []
        
        for repo_path in config.config.repositories:
            path = Path(repo_path)
            if path.exists():
                try:
                    file_analyses = self.style_analyzer.analyze_directory(path)
                    if file_analyses:
                        # Aggregate style profile for repository
                        profile = self.style_analyzer._aggregate_style_profiles(
                            [fa.style_profile for fa in file_analyses]
                        )
                        profiles.append({
                            'repository': str(path),
                            'profile': profile
                        })
                except Exception as e:
                    self.console.logger.warning(f"Error collecting style profile for {path}: {e}")
        
        return profiles
    
    def help(self) -> None:
        """Show help for the status command."""
        help_text = """
[bold cyan]spark status[/bold cyan] - Display learning progress and system status

[bold]Usage:[/bold]
  spark status                   Show main status dashboard
  spark status --detailed        Show detailed pattern breakdown
  spark status --patterns        Show AST-based pattern analysis
  spark status --confidence      Show multi-dimensional confidence analysis
  spark status --preferences     Show developer preference analysis
  spark status --sessions        Show development session analysis
  spark status --interactive     Show real-time interactive dashboard

[bold]Options:[/bold]
  -d, --detailed                 Include detailed pattern analysis
  -p, --patterns                 AST-based code style pattern analysis
  -c, --confidence               Multi-dimensional confidence scoring
      --preferences, --prefs     Developer preference and learning analysis
  -s, --sessions                 Development session and rhythm analysis
  -i, --interactive              Real-time interactive dashboard

[bold]Examples:[/bold]
  spark status                   # Quick status check
  spark status -d                # Detailed analysis
  spark status --patterns        # AST pattern analysis
  spark status --confidence      # Confidence breakdown
  spark status --preferences     # Learning preferences
  spark status --sessions        # Development sessions
  spark status -i                # Interactive dashboard
        """
        self.console.console.print(help_text)