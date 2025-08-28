"""
Configuration management system for Spark.

This module provides comprehensive configuration management with TOML-based persistence,
validation, and migration capabilities for the Spark platform.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
import platform as platform_module

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None

try:
    import tomli_w
except ImportError:
    tomli_w = None

from spark.cli.errors import SparkConfigurationError, SparkInitializationError


@dataclass
class LearningConfig:
    """Configuration for learning engine."""
    
    # Learning behavior
    enabled: bool = True
    auto_start: bool = True
    background_monitoring: bool = True
    
    # File monitoring
    watch_patterns: List[str] = field(default_factory=lambda: [
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.go", "*.rs", "*.java", 
        "*.kt", "*.cpp", "*.c", "*.h", "*.hpp", "*.rb", "*.php", "*.swift"
    ])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "node_modules/*", ".git/*", "__pycache__/*", "*.pyc", 
        "build/*", "dist/*", ".env", ".venv/*"
    ])
    
    # Pattern detection
    confidence_threshold: float = 0.6
    min_samples: int = 5
    pattern_retention_days: int = 90
    
    # Performance
    max_cpu_usage: float = 0.05  # 5% max CPU usage
    max_memory_mb: int = 50      # 50MB max memory usage
    scan_interval_seconds: int = 300  # 5 minutes


@dataclass 
class ExplorationConfig:
    """Configuration for exploration engine."""
    
    # Exploration behavior  
    enabled: bool = True
    auto_schedule: bool = True
    default_time_budget_hours: int = 4
    
    # Scheduling
    preferred_start_time: str = "22:00"  # 10 PM
    max_duration_hours: int = 8
    weekdays_only: bool = False
    
    # Risk and focus
    risk_level: str = "balanced"  # conservative, balanced, experimental
    focus_areas: List[str] = field(default_factory=lambda: [
        "performance", "architecture", "testing", "documentation"
    ])
    
    # Code generation
    max_approaches_per_goal: int = 3
    enable_code_execution: bool = True
    enable_testing: bool = True
    
    # AI integration
    ai_provider: str = "claude"  # claude, openai, local
    model_name: str = "claude-3-sonnet"
    max_tokens: int = 4000
    temperature: float = 0.7


@dataclass
class DiscoveryConfig:
    """Configuration for discovery system."""
    
    # Curation
    max_discoveries_per_session: int = 10
    min_score_threshold: float = 0.6
    diversity_weight: float = 0.3
    
    # Presentation
    show_code_diffs: bool = True
    show_performance_metrics: bool = True
    max_description_length: int = 200
    
    # Integration
    create_backup_before_integration: bool = True
    default_integration_branch: str = "spark-exploration"
    auto_run_tests_after_integration: bool = True


@dataclass
class StorageConfig:
    """Configuration for storage system."""
    
    # Database
    database_file: str = "spark.db"
    backup_retention_days: int = 30
    auto_vacuum: bool = True
    
    # Privacy
    encrypt_sensitive_patterns: bool = True
    anonymize_file_paths: bool = False
    store_code_snippets: bool = True
    
    # Performance
    enable_wal_mode: bool = True
    cache_size_mb: int = 10
    sync_mode: str = "NORMAL"  # OFF, NORMAL, FULL


@dataclass
class UIConfig:
    """Configuration for user interface."""
    
    # Terminal
    use_colors: bool = True
    use_unicode: bool = True
    max_table_width: int = 120
    
    # Progress reporting
    show_progress_bars: bool = True
    show_timestamps: bool = False
    verbose_logging: bool = False
    
    # Interaction
    confirm_destructive_actions: bool = True
    auto_open_discoveries: bool = False


@dataclass
class SparkConfiguration:
    """Main Spark configuration container."""
    
    # Basic metadata
    version: str = "0.1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # System info
    python_version: str = field(default_factory=lambda: f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    platform: str = field(default_factory=platform_module.system)
    hostname: str = field(default_factory=platform_module.node)
    
    # Configuration sections
    learning: LearningConfig = field(default_factory=LearningConfig)
    exploration: ExplorationConfig = field(default_factory=ExplorationConfig)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    # Monitored repositories
    repositories: List[str] = field(default_factory=list)
    
    # User preferences (learned over time)
    preferences: Dict[str, Any] = field(default_factory=dict)


class SparkConfig:
    """Configuration manager for Spark platform."""
    
    DEFAULT_CONFIG_DIR = Path.home() / ".spark"
    CONFIG_FILE = "config.toml"
    BACKUP_SUFFIX = ".backup"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = Path(config_dir) if config_dir else self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.CONFIG_FILE
        self.backup_file = self.config_dir / f"{self.CONFIG_FILE}{self.BACKUP_SUFFIX}"
        
        self.config = SparkConfiguration()
        self._ensure_toml_support()
    
    def _ensure_toml_support(self) -> None:
        """Ensure TOML reading/writing support is available."""
        if tomllib is None:
            raise SparkConfigurationError(
                "TOML support is not available",
                "Install tomli package: pip install tomli"
            )
        
        if tomli_w is None:
            raise SparkConfigurationError(
                "TOML writing support is not available", 
                "Install tomli-w package: pip install tomli-w"
            )
    
    def is_initialized(self) -> bool:
        """Check if Spark configuration has been initialized."""
        return self.config_file.exists() and self.config_dir.is_dir()
    
    def initialize(self) -> None:
        """Initialize Spark configuration directory and files."""
        try:
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.config_dir / "patterns").mkdir(exist_ok=True)
            (self.config_dir / "discoveries").mkdir(exist_ok=True)
            (self.config_dir / "logs").mkdir(exist_ok=True)
            (self.config_dir / "backups").mkdir(exist_ok=True)
            
            # Discover git repositories
            self._discover_repositories()
            
            # Save default configuration
            self.save()
            
        except Exception as e:
            raise SparkInitializationError(
                "Failed to initialize Spark configuration",
                f"Error: {e}"
            ) from e
    
    def _discover_repositories(self) -> None:
        """Automatically discover git repositories to monitor."""
        common_code_dirs = [
            Path.home() / "Code",
            Path.home() / "code", 
            Path.home() / "Projects",
            Path.home() / "projects",
            Path.home() / "Development",
            Path.home() / "dev",
            Path.home() / "src",
            Path.home() / "workspace",
            Path.home() / "Documents",
        ]
        
        discovered_repos = []
        
        for base_dir in common_code_dirs:
            if base_dir.exists():
                # Look for git repositories up to 2 levels deep
                for item in base_dir.rglob(".git"):
                    if item.is_dir():
                        repo_path = str(item.parent)
                        if repo_path not in discovered_repos:
                            discovered_repos.append(repo_path)
                            
                        # Don't go too deep to avoid performance issues
                        if len(discovered_repos) >= 20:
                            break
            
            if len(discovered_repos) >= 20:
                break
        
        self.config.repositories = discovered_repos[:10]  # Limit to 10 for initial setup
    
    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_file.exists():
            raise SparkConfigurationError(
                "Configuration file not found",
                f"Run 'spark' to initialize configuration at {self.config_file}"
            )
        
        try:
            with open(self.config_file, "rb") as f:
                config_data = tomllib.load(f)
            
            # Update configuration with loaded data
            self._update_config_from_dict(config_data)
            
        except Exception as e:
            raise SparkConfigurationError(
                "Failed to load configuration",
                f"Error reading {self.config_file}: {e}"
            ) from e
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Update timestamps
            self.config.updated_at = datetime.now().isoformat()
            
            # Create backup of existing config
            if self.config_file.exists():
                self.config_file.rename(self.backup_file)
            
            # Save new configuration
            config_dict = asdict(self.config)
            with open(self.config_file, "wb") as f:
                tomli_w.dump(config_dict, f)
            
        except Exception as e:
            # Restore backup if save failed
            if self.backup_file.exists():
                self.backup_file.rename(self.config_file)
            
            raise SparkConfigurationError(
                "Failed to save configuration",
                f"Error writing {self.config_file}: {e}"
            ) from e
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Update configuration object from dictionary."""
        
        # Update basic fields
        for field_name in ["version", "created_at", "updated_at", "python_version", 
                          "platform", "hostname", "repositories", "preferences"]:
            if field_name in config_data:
                setattr(self.config, field_name, config_data[field_name])
        
        # Update nested configurations
        if "learning" in config_data:
            self._update_dataclass_from_dict(self.config.learning, config_data["learning"])
        
        if "exploration" in config_data:
            self._update_dataclass_from_dict(self.config.exploration, config_data["exploration"])
        
        if "discovery" in config_data:
            self._update_dataclass_from_dict(self.config.discovery, config_data["discovery"])
        
        if "storage" in config_data:
            self._update_dataclass_from_dict(self.config.storage, config_data["storage"])
        
        if "ui" in config_data:
            self._update_dataclass_from_dict(self.config.ui, config_data["ui"])
    
    def _update_dataclass_from_dict(self, dataclass_instance: Any, data: Dict[str, Any]) -> None:
        """Update a dataclass instance from dictionary data."""
        for key, value in data.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate learning config
        if not 0 <= self.config.learning.confidence_threshold <= 1:
            errors.append("learning.confidence_threshold must be between 0 and 1")
        
        if self.config.learning.min_samples < 1:
            errors.append("learning.min_samples must be at least 1")
        
        if not 0 < self.config.learning.max_cpu_usage <= 1:
            errors.append("learning.max_cpu_usage must be between 0 and 1")
        
        # Validate exploration config
        if self.config.exploration.risk_level not in ["conservative", "balanced", "experimental"]:
            errors.append("exploration.risk_level must be 'conservative', 'balanced', or 'experimental'")
        
        if self.config.exploration.default_time_budget_hours < 1:
            errors.append("exploration.default_time_budget_hours must be at least 1")
        
        # Validate discovery config
        if not 0 <= self.config.discovery.min_score_threshold <= 1:
            errors.append("discovery.min_score_threshold must be between 0 and 1")
        
        # Validate repositories exist
        for repo in self.config.repositories:
            repo_path = Path(repo)
            if not repo_path.exists():
                errors.append(f"Repository path does not exist: {repo}")
            elif not (repo_path / ".git").exists():
                errors.append(f"Path is not a git repository: {repo}")
        
        return errors
    
    def add_repository(self, repo_path: Union[str, Path]) -> bool:
        """Add a repository to monitoring list."""
        repo_str = str(repo_path)
        repo_path = Path(repo_path)
        
        if not repo_path.exists():
            return False
        
        if not (repo_path / ".git").exists():
            return False
        
        if repo_str not in self.config.repositories:
            self.config.repositories.append(repo_str)
            return True
        
        return False
    
    def remove_repository(self, repo_path: Union[str, Path]) -> bool:
        """Remove a repository from monitoring list."""
        repo_str = str(repo_path)
        
        if repo_str in self.config.repositories:
            self.config.repositories.remove(repo_str)
            return True
        
        return False
    
    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        return self.config_dir
    
    def get_database_path(self) -> Path:
        """Get the database file path."""
        return self.config_dir / self.config.storage.database_file
    
    def update_preference(self, key: str, value: Any) -> None:
        """Update a user preference."""
        self.config.preferences[key] = value
        self.config.updated_at = datetime.now().isoformat()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.config.preferences.get(key, default)