"""
Spark learn command implementation.

Manages background learning from git repositories and file system monitoring.
"""

import asyncio
from typing import List, Dict, Any
from pathlib import Path

from spark.core.config import SparkConfig
from spark.learning.git_patterns import GitPatternAnalyzer
from spark.storage.patterns import PatternStorage
from spark.cli.terminal import get_console, SparkTheme
from spark.cli.errors import handle_async_cli_error, SparkLearningError


class LearnCommand:
    """Implementation of the 'spark learn' command."""
    
    def __init__(self):
        self.console = get_console()
        self.theme = SparkTheme()
        self.analyzer = GitPatternAnalyzer()
    
    @handle_async_cli_error
    async def execute(self, args: List[str]) -> int:
        """Execute the learn command."""
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
            
            # Parse arguments
            if not args:
                return await self._start_learning(config)
            
            command = args[0]
            command_args = args[1:] if len(args) > 1 else []
            
            if command == '--status' or command == 'status':
                return await self._show_learning_status(config)
            elif command == '--stop' or command == 'stop':
                return await self._stop_learning(config)
            elif command == '--add' or command == 'add':
                return await self._add_repository(config, command_args)
            elif command == '--remove' or command == 'remove':
                return await self._remove_repository(config, command_args)
            elif command == '--analyze' or command == 'analyze':
                return await self._analyze_repositories(config, command_args)
            elif command == '--reset' or command == 'reset':
                return await self._reset_learning(config)
            else:
                self.console.print_error(f"Unknown learn command: {command}")
                self.help()
                return 1
            
        except Exception as e:
            raise SparkLearningError(
                "Failed to execute learn command",
                str(e)
            ) from e
    
    async def _start_learning(self, config: SparkConfig) -> int:
        """Start background learning process."""
        
        self.console.console.print("🧠 [bold]Starting Spark Learning[/bold]")
        self.console.console.print()
        
        # Check if repositories are configured
        if not config.config.repositories:
            self.console.print_warning(
                "No repositories configured for learning",
                "Add repositories with 'spark learn --add <path>'"
            )
            return 1
        
        # Show what will be monitored
        self.console.console.print("📂 [bold]Monitoring repositories:[/bold]")
        active_repos = []
        
        for repo_path in config.config.repositories:
            repo_path_obj = Path(repo_path)
            if repo_path_obj.exists() and (repo_path_obj / ".git").exists():
                relative_path = self._get_relative_path(repo_path_obj)
                self.console.console.print(f"  ✅ [cyan]{relative_path}[/cyan]")
                active_repos.append(repo_path)
            else:
                relative_path = self._get_relative_path(repo_path_obj)
                self.console.console.print(f"  ❌ [red]{relative_path}[/red] [dim](not found)[/dim]")
        
        if not active_repos:
            self.console.print_error(
                "No valid repositories found",
                "Check repository paths and ensure they are git repositories"
            )
            return 1
        
        self.console.console.print()
        
        # Update config with only active repos
        if len(active_repos) != len(config.config.repositories):
            config.config.repositories = active_repos
            config.save()
        
        # Start analysis
        self.console.console.print("🔍 [bold]Analyzing repositories for patterns...[/bold]")
        success_count = 0
        
        with PatternStorage(config.get_database_path()) as storage:
            for repo_path in active_repos:
                try:
                    with self.console.create_spinner(f"Analyzing {Path(repo_path).name}...") as progress:
                        progress.start()
                        
                        # Analyze repository
                        analysis = await self.analyzer.analyze_repository(Path(repo_path))
                        
                        # Store results
                        storage.store_analysis(analysis)
                        
                        progress.stop()
                    
                    # Show quick results
                    confidence = analysis.confidence_scores.get('overall', 0.0)
                    confidence_color = (
                        self.theme.SUCCESS if confidence > 0.8 
                        else self.theme.WARNING if confidence > 0.6 
                        else self.theme.INFO
                    )
                    
                    self.console.console.print(
                        f"  ✅ {Path(repo_path).name}: "
                        f"[{confidence_color}]{confidence:.1%} confidence[/{confidence_color}] "
                        f"[dim]({analysis.commit_count} commits)[/dim]"
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    self.console.console.print(
                        f"  ❌ {Path(repo_path).name}: [red]Analysis failed[/red] [dim]({e})[/dim]"
                    )
        
        self.console.console.print()
        
        if success_count > 0:
            # Update configuration to enable learning
            config.config.learning.enabled = True
            config.save()
            
            self.console.print_success(
                f"Learning started successfully!",
                f"Analyzed {success_count}/{len(active_repos)} repositories"
            )
            
            self.console.console.print("\n💡 [bold]What happens next:[/bold]")
            self.console.console.print("  • Patterns are automatically detected from your code")
            self.console.console.print("  • Confidence builds as you continue coding")
            self.console.console.print("  • Check progress with [cyan]'spark status'[/cyan]")
            self.console.console.print("  • When confidence reaches 85%, you can start exploring!")
            
            return 0
        else:
            self.console.print_error(
                "Failed to analyze any repositories",
                "Check repository health and try again"
            )
            return 1
    
    async def _show_learning_status(self, config: SparkConfig) -> int:
        """Show current learning status."""
        
        self.console.console.print("🧠 [bold]Learning Status[/bold]")
        self.console.console.print()
        
        # Check if learning is enabled
        if not config.config.learning.enabled:
            self.console.console.print("📴 [yellow]Learning is currently disabled[/yellow]")
            self.console.console.print("   Run [cyan]'spark learn'[/cyan] to start learning")
            return 0
        
        # Get progress from storage
        with PatternStorage(config.get_database_path()) as storage:
            progress = storage.get_progress()
            patterns = storage.get_patterns(min_confidence=0.1)
        
        # Show overall progress
        confidence = progress.get('avg_confidence', 0.0)
        days_learning = progress.get('days_learning', 0)
        pattern_count = progress.get('pattern_count', 0)
        
        progress_data = {
            'confidence': confidence,
            'days': days_learning,
            'recent_activity': {
                'patterns_detected': pattern_count,
                'commits': 0,  # Would come from file monitoring
                'files_modified': 0
            }
        }
        
        self.console.print_learning_progress(progress_data)
        
        # Show repository status
        self.console.console.print("📂 [bold]Monitored repositories:[/bold]")
        
        repo_patterns = {}
        for pattern in patterns:
            repo_name = pattern['repository_name']
            if repo_name not in repo_patterns:
                repo_patterns[repo_name] = []
            repo_patterns[repo_name].append(pattern)
        
        for repo_path in config.config.repositories:
            repo_name = Path(repo_path).name
            repo_confidence = 0.0
            
            if repo_name in repo_patterns:
                repo_confidences = [p['confidence_score'] for p in repo_patterns[repo_name]]
                repo_confidence = sum(repo_confidences) / len(repo_confidences)
            
            confidence_color = (
                self.theme.SUCCESS if repo_confidence > 0.8 
                else self.theme.WARNING if repo_confidence > 0.6 
                else self.theme.INFO
            )
            
            relative_path = self._get_relative_path(Path(repo_path))
            self.console.console.print(
                f"  • [cyan]{relative_path}[/cyan]: "
                f"[{confidence_color}]{repo_confidence:.1%}[/{confidence_color}]"
            )
        
        # Show learning settings
        self.console.console.print(f"\n⚙️ [bold]Settings:[/bold]")
        self.console.console.print(f"  • Background monitoring: [green]{'Enabled' if config.config.learning.background_monitoring else 'Disabled'}[/green]")
        self.console.console.print(f"  • Confidence threshold: [cyan]{config.config.learning.confidence_threshold:.1%}[/cyan]")
        self.console.console.print(f"  • Pattern retention: [cyan]{config.config.learning.pattern_retention_days} days[/cyan]")
        
        return 0
    
    async def _stop_learning(self, config: SparkConfig) -> int:
        """Stop background learning."""
        
        if not config.config.learning.enabled:
            self.console.console.print("📴 [dim]Learning is already stopped[/dim]")
            return 0
        
        if self.console.confirm("Stop background learning?", default=False):
            config.config.learning.enabled = False
            config.save()
            
            self.console.print_success("Learning stopped")
            self.console.console.print("💡 [dim]Existing patterns are preserved. Run 'spark learn' to resume.[/dim]")
        else:
            self.console.console.print("👍 [dim]Learning continues[/dim]")
        
        return 0
    
    async def _add_repository(self, config: SparkConfig, args: List[str]) -> int:
        """Add a repository to learning."""
        
        if not args:
            self.console.print_error(
                "Repository path required",
                "Usage: spark learn --add <path>"
            )
            return 1
        
        repo_path = Path(args[0]).resolve()
        
        # Validate repository
        if not repo_path.exists():
            self.console.print_error(
                "Path does not exist",
                f"Path: {repo_path}"
            )
            return 1
        
        if not (repo_path / ".git").exists():
            self.console.print_error(
                "Not a git repository",
                f"Path: {repo_path}"
            )
            return 1
        
        # Add to configuration
        if config.add_repository(repo_path):
            config.save()
            
            relative_path = self._get_relative_path(repo_path)
            self.console.print_success(
                f"Added repository: {relative_path}",
                "Run 'spark learn --analyze' to analyze new repository"
            )
        else:
            relative_path = self._get_relative_path(repo_path)
            self.console.print_warning(
                f"Repository already monitored: {relative_path}"
            )
        
        return 0
    
    async def _remove_repository(self, config: SparkConfig, args: List[str]) -> int:
        """Remove a repository from learning."""
        
        if not args:
            self.console.print_error(
                "Repository path required",
                "Usage: spark learn --remove <path>"
            )
            return 1
        
        repo_path = Path(args[0]).resolve()
        
        if config.remove_repository(repo_path):
            config.save()
            
            relative_path = self._get_relative_path(repo_path)
            self.console.print_success(f"Removed repository: {relative_path}")
            
            # Ask about cleaning up data
            if self.console.confirm("Remove stored patterns for this repository?", default=False):
                # TODO: Implement pattern cleanup
                self.console.console.print("🧹 [dim]Pattern cleanup not yet implemented[/dim]")
        else:
            relative_path = self._get_relative_path(repo_path)
            self.console.print_warning(f"Repository not found in monitoring list: {relative_path}")
        
        return 0
    
    async def _analyze_repositories(self, config: SparkConfig, args: List[str]) -> int:
        """Force re-analysis of repositories."""
        
        repos_to_analyze = []
        
        if args:
            # Analyze specific repository
            repo_path = Path(args[0]).resolve()
            if str(repo_path) in config.config.repositories:
                repos_to_analyze = [str(repo_path)]
            else:
                relative_path = self._get_relative_path(repo_path)
                self.console.print_error(
                    f"Repository not monitored: {relative_path}",
                    "Use 'spark learn --add <path>' to add it first"
                )
                return 1
        else:
            # Analyze all repositories
            repos_to_analyze = config.config.repositories
        
        if not repos_to_analyze:
            self.console.console.print("📭 [dim]No repositories to analyze[/dim]")
            return 0
        
        self.console.console.print(f"🔍 [bold]Analyzing {len(repos_to_analyze)} repositories...[/bold]")
        self.console.console.print()
        
        success_count = 0
        
        with PatternStorage(config.get_database_path()) as storage:
            for repo_path in repos_to_analyze:
                repo_name = Path(repo_path).name
                
                try:
                    with self.console.create_spinner(f"Analyzing {repo_name}...") as progress:
                        progress.start()
                        
                        analysis = await self.analyzer.analyze_repository(Path(repo_path))
                        storage.store_analysis(analysis)
                        
                        progress.stop()
                    
                    confidence = analysis.confidence_scores.get('overall', 0.0)
                    confidence_color = (
                        self.theme.SUCCESS if confidence > 0.8 
                        else self.theme.WARNING if confidence > 0.6 
                        else self.theme.INFO
                    )
                    
                    self.console.console.print(
                        f"  ✅ {repo_name}: "
                        f"[{confidence_color}]{confidence:.1%}[/{confidence_color}] "
                        f"[dim]({analysis.commit_count} commits analyzed)[/dim]"
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    self.console.console.print(f"  ❌ {repo_name}: [red]{e}[/red]")
        
        self.console.console.print()
        
        if success_count > 0:
            self.console.print_success(
                f"Analysis complete!",
                f"Successfully analyzed {success_count}/{len(repos_to_analyze)} repositories"
            )
        else:
            self.console.print_error("Analysis failed for all repositories")
        
        return 0
    
    async def _reset_learning(self, config: SparkConfig) -> int:
        """Reset all learning data."""
        
        self.console.print_warning(
            "This will delete all learned patterns and start fresh",
            "All pattern data will be permanently lost"
        )
        
        if not self.console.confirm("Are you sure you want to reset learning?", default=False):
            self.console.console.print("👍 [dim]Learning data preserved[/dim]")
            return 0
        
        try:
            # Delete database file
            db_path = config.get_database_path()
            if db_path.exists():
                db_path.unlink()
            
            # Reset learning configuration
            config.config.learning.enabled = False
            config.save()
            
            self.console.print_success(
                "Learning data reset successfully",
                "Run 'spark learn' to start fresh analysis"
            )
            
            return 0
            
        except Exception as e:
            self.console.print_error(
                "Failed to reset learning data",
                str(e)
            )
            return 1
    
    def _get_relative_path(self, path: Path) -> str:
        """Get a nice relative path for display."""
        try:
            return str(path.relative_to(Path.home())).replace("\\", "/")
        except ValueError:
            return str(path)
    
    def help(self) -> None:
        """Show help for the learn command."""
        help_text = """
[bold cyan]spark learn[/bold cyan] - Manage background learning from git repositories

[bold]Usage:[/bold]
  spark learn                    Start learning from configured repositories
  spark learn --status           Show current learning status
  spark learn --stop             Stop background learning
  spark learn --add <path>       Add repository to learning
  spark learn --remove <path>    Remove repository from learning
  spark learn --analyze [path]   Force re-analysis of repositories
  spark learn --reset            Reset all learning data

[bold]Options:[/bold]
  --status                       Show learning progress and statistics
  --stop                         Disable background learning
  --add <path>                   Add git repository to monitoring
  --remove <path>                Remove repository from monitoring
  --analyze [path]               Re-analyze repositories (all or specific)
  --reset                        Delete all learning data and start fresh

[bold]Examples:[/bold]
  spark learn                    # Start learning from configured repos
  spark learn --add ~/myproject  # Add a specific repository
  spark learn --status           # Check learning progress
  spark learn --analyze          # Force re-analysis of all repos
        """
        self.console.console.print(help_text)