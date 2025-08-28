"""
Spark initialization system for first-run setup and configuration.

This module handles the initial setup of Spark, including directory creation,
repository discovery, and user onboarding experience.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any
import shutil

from spark.core.config import SparkConfig, SparkConfiguration
from spark.cli.terminal import SparkConsole, SparkTheme
from spark.cli.errors import SparkInitializationError


class SparkInitializer:
    """Handles Spark initialization and first-run setup."""
    
    def __init__(self, config: SparkConfig, console: SparkConsole):
        self.config = config
        self.console = console
        self.theme = SparkTheme()
    
    async def initialize(self) -> bool:
        """Perform complete Spark initialization."""
        try:
            # Welcome message
            self._show_welcome()
            
            # Check system requirements
            self.console.console.print("🔍 [bold]Checking system requirements...[/bold]")
            if not await self._check_system_requirements():
                return False
            
            # Setup directories
            self.console.console.print("📁 [bold]Setting up directories...[/bold]")
            self._setup_directories()
            
            # Discover repositories
            self.console.console.print("🔍 [bold]Discovering git repositories...[/bold]")
            repos = await self._discover_and_validate_repositories()
            
            if repos:
                self.console.console.print(f"✅ Found {len(repos)} repositories to monitor")
                self._show_discovered_repositories(repos)
                
                # Ask user for confirmation
                if self.console.confirm("Start monitoring these repositories?"):
                    self.config.config.repositories = repos
                else:
                    self.console.console.print("ℹ️ You can add repositories later with 'spark learn --add <path>'")
            else:
                self.console.console.print("ℹ️ No git repositories found. You can add them later with 'spark learn --add <path>'")
            
            # Initialize configuration
            self.console.console.print("⚙️ [bold]Initializing configuration...[/bold]")
            self.config.initialize()
            
            # Setup complete
            self._show_completion()
            return True
            
        except Exception as e:
            raise SparkInitializationError(
                "Initialization failed",
                str(e)
            ) from e
    
    def _show_welcome(self) -> None:
        """Show welcome message and introduction."""
        welcome_text = f"""
{self.theme.SPARK_ICON} [bold blue]Welcome to Spark![/bold blue]

Spark is your AI-powered coding companion that:
• {self.theme.LEARN_ICON} [cyan]Learns[/cyan] your coding patterns and preferences
• {self.theme.EXPLORE_ICON} [purple]Explores[/purple] new approaches while you sleep
• {self.theme.DISCOVER_ICON} [yellow]Discovers[/yellow] valuable improvements each morning
• {self.theme.INTEGRATE_ICON} [green]Integrates[/green] findings safely into your projects

Let's get you set up in just a few moments...
"""
        self.console.console.print(welcome_text)
    
    async def _check_system_requirements(self) -> bool:
        """Check system requirements and dependencies."""
        requirements_met = True
        
        # Check Python version
        import sys
        if sys.version_info < (3, 12):
            self.console.print_warning(
                f"Python {sys.version_info.major}.{sys.version_info.minor} detected",
                "Spark works best with Python 3.12+. Some features may be limited."
            )
        
        # Check git availability
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                git_version = result.stdout.strip()
                self.console.console.print(f"✅ {git_version}")
            else:
                self.console.print_error("Git not found in PATH")
                requirements_met = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.console.print_error("Git not available")
            requirements_met = False
        
        # Check disk space
        config_dir = self.config.config_dir
        if config_dir.parent.exists():
            try:
                disk_usage = shutil.disk_usage(config_dir.parent)
                free_gb = disk_usage.free / (1024**3)
                
                if free_gb < 0.1:  # Less than 100MB
                    self.console.print_error(
                        "Insufficient disk space",
                        f"At least 100MB required, {free_gb:.1f}GB available"
                    )
                    requirements_met = False
                else:
                    self.console.console.print(f"✅ Disk space: {free_gb:.1f}GB available")
            except Exception:
                # Not critical if we can't check disk space
                pass
        
        return requirements_met
    
    def _setup_directories(self) -> None:
        """Create necessary directories for Spark operation."""
        directories = [
            self.config.config_dir,
            self.config.config_dir / "patterns",
            self.config.config_dir / "discoveries", 
            self.config.config_dir / "logs",
            self.config.config_dir / "backups",
            self.config.config_dir / "cache",
            self.config.config_dir / "temp",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.console.console.print(f"  📁 {directory.relative_to(Path.home())}")
    
    async def _discover_and_validate_repositories(self) -> List[str]:
        """Discover and validate git repositories."""
        discovered = []
        
        # Common development directories
        search_paths = [
            Path.home() / "Code",
            Path.home() / "code",
            Path.home() / "Projects",
            Path.home() / "projects",
            Path.home() / "Development", 
            Path.home() / "dev",
            Path.home() / "src",
            Path.home() / "workspace",
            Path.home() / "Documents",
            Path.cwd(),  # Current directory
        ]
        
        with self.console.create_spinner("Scanning for git repositories..."):
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                
                # Look for .git directories
                try:
                    for git_dir in search_path.rglob(".git"):
                        if git_dir.is_dir():
                            repo_path = git_dir.parent
                            
                            # Validate it's a proper git repository
                            if await self._validate_git_repository(repo_path):
                                repo_str = str(repo_path)
                                if repo_str not in discovered:
                                    discovered.append(repo_str)
                                    
                                    # Don't scan too deep or take too long
                                    if len(discovered) >= 15:
                                        break
                        
                        # Limit search depth and time
                        if len(discovered) >= 15:
                            break
                            
                except (PermissionError, OSError):
                    # Skip inaccessible directories
                    continue
                
                if len(discovered) >= 15:
                    break
        
        return discovered[:10]  # Return top 10
    
    async def _validate_git_repository(self, repo_path: Path) -> bool:
        """Validate that a path is a working git repository."""
        try:
            # Check if git status works
            process = await asyncio.create_subprocess_exec(
                'git', 'status', '--porcelain',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2.0)
            return process.returncode == 0
            
        except (asyncio.TimeoutError, OSError, FileNotFoundError):
            return False
    
    def _show_discovered_repositories(self, repositories: List[str]) -> None:
        """Show discovered repositories to the user."""
        self.console.console.print("\n📂 [bold]Discovered repositories:[/bold]")
        
        for i, repo in enumerate(repositories, 1):
            repo_path = Path(repo)
            relative_path = self._get_relative_path(repo_path)
            
            # Get basic repo info
            repo_info = self._get_repository_info(repo_path)
            
            self.console.console.print(
                f"  {i:2}. [cyan]{relative_path}[/cyan] {repo_info}"
            )
        
        self.console.console.print()
    
    def _get_relative_path(self, path: Path) -> str:
        """Get a nice relative path for display."""
        try:
            return str(path.relative_to(Path.home())).replace("\\", "/")
        except ValueError:
            # If not under home directory, show absolute path
            return str(path)
    
    def _get_repository_info(self, repo_path: Path) -> str:
        """Get basic information about a repository."""
        info_parts = []
        
        try:
            # Count files by extension
            code_files = 0
            for pattern in [".py", ".js", ".ts", ".go", ".rs", ".java"]:
                code_files += len(list(repo_path.glob(f"**/*{pattern}")))
            
            if code_files > 0:
                info_parts.append(f"{code_files} files")
            
            # Get primary language (simple heuristic)
            extensions = {}
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and file_path.suffix:
                    ext = file_path.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            if extensions:
                primary_ext = max(extensions, key=extensions.get)
                lang_map = {
                    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                    ".go": "Go", ".rs": "Rust", ".java": "Java", ".cpp": "C++",
                    ".c": "C", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift"
                }
                
                if primary_ext in lang_map:
                    info_parts.append(lang_map[primary_ext])
            
        except (PermissionError, OSError):
            pass
        
        return f"[dim]({', '.join(info_parts)})[/dim]" if info_parts else ""
    
    def _show_completion(self) -> None:
        """Show completion message and next steps."""
        completion_text = f"""
{self.theme.STATUS_READY} [bold green]Setup complete![/bold green]

Spark is now ready to learn your coding patterns.

[bold]Next steps:[/bold]
1. [cyan]spark learn[/cyan] - Start background learning (automatically started)
2. [cyan]spark status[/cyan] - Check learning progress 
3. [cyan]spark explore[/cyan] - Schedule tonight's exploration (after a few days of learning)

[bold]Tips:[/bold]
• Learning happens automatically in the background
• Confidence builds over 5-7 days of normal development
• Explorations work best after reaching 85% confidence
• All data stays local in ~/.spark/ unless you choose to sync

Happy coding! {self.theme.SPARK_ICON}
"""
        self.console.console.print(completion_text)


async def initialize_spark(config: SparkConfig, console: SparkConsole) -> bool:
    """Initialize Spark system with proper error handling."""
    initializer = SparkInitializer(config, console)
    return await initializer.initialize()