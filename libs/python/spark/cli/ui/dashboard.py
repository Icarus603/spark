"""
Interactive real-time dashboard for Spark pattern analysis and development insights.

This module provides a rich terminal-based dashboard that displays pattern confidence,
development sessions, exploration readiness, and real-time learning analytics.
"""

import asyncio
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import logging

# Terminal UI libraries with fallbacks
try:
    import blessed
    BLESSED_AVAILABLE = True
except ImportError:
    BLESSED_AVAILABLE = False
    blessed = None

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from spark.cli.errors import SparkLearningError
from spark.learning.style_analyzer import MultiLanguageStyleAnalyzer
from spark.learning.confidence_scorer import MultiDimensionalConfidenceScorer
from spark.learning.file_monitor import FileSystemMonitor
from spark.learning.preference_mapper import PreferenceMapper
from spark.storage.pattern_storage import PatternStorage


@dataclass
class DashboardConfig:
    """Configuration for dashboard display and behavior."""
    
    refresh_interval: float = 1.0  # seconds
    max_log_lines: int = 50
    max_session_history: int = 20
    enable_colors: bool = True
    enable_animations: bool = True
    compact_mode: bool = False
    auto_scroll: bool = True
    theme: str = "default"  # default, dark, light


@dataclass
class DashboardMetrics:
    """Real-time metrics for dashboard display."""
    
    # Pattern confidence metrics
    pattern_confidence: Dict[str, float] = field(default_factory=dict)
    total_patterns: int = 0
    high_confidence_patterns: int = 0
    
    # Development session metrics
    current_session_active: bool = False
    session_duration: float = 0.0  # hours
    session_changes: int = 0
    session_files: int = 0
    
    # File monitoring metrics
    files_watched: int = 0
    events_processed: int = 0
    last_activity: Optional[datetime] = None
    
    # Performance metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    processing_latency: float = 0.0
    
    # Exploration readiness
    exploration_readiness: float = 0.0
    suggested_technologies: List[str] = field(default_factory=list)
    learning_trajectory: str = "stable"


@dataclass
class LogEntry:
    """Dashboard log entry."""
    
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, DEBUG
    message: str
    component: str  # analyzer, scorer, monitor, mapper, dashboard


class InteractiveDashboard:
    """Real-time interactive dashboard for Spark pattern analysis."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        
        # Terminal interface
        if not BLESSED_AVAILABLE:
            raise SparkLearningError(
                "Interactive dashboard requires blessed library",
                "Install with: pip install blessed"
            )
        
        self.term = blessed.Terminal()
        self.running = False
        self.paused = False
        
        # Core components
        self.style_analyzer = MultiLanguageStyleAnalyzer()
        self.confidence_scorer = MultiDimensionalConfidenceScorer()
        self.preference_mapper = PreferenceMapper()
        self.file_monitor: Optional[FileSystemMonitor] = None
        self.pattern_storage = PatternStorage()
        
        # Dashboard state
        self.metrics = DashboardMetrics()
        self.log_entries: deque = deque(maxlen=self.config.max_log_lines)
        self.last_update = datetime.now()
        self.update_thread: Optional[threading.Thread] = None
        
        # Display state
        self.current_view = "main"  # main, patterns, sessions, preferences, logs, help
        self.selected_index = 0
        self.scroll_position = 0
        
        # Colors and styles
        self._setup_colors()
        
        self.logger = logging.getLogger(f"spark.{self.__class__.__name__}")
    
    def _setup_colors(self):
        """Setup color scheme for dashboard."""
        if not self.config.enable_colors:
            # No-color fallback
            self.colors = {
                'header': '',
                'success': '',
                'warning': '',
                'error': '',
                'info': '',
                'highlight': '',
                'dim': '',
                'reset': ''
            }
            return
        
        self.colors = {
            'header': self.term.bold_blue,
            'success': self.term.green,
            'warning': self.term.yellow,
            'error': self.term.red,
            'info': self.term.cyan,
            'highlight': self.term.bold_white,
            'dim': self.term.dim,
            'reset': self.term.normal
        }
    
    def initialize(self, project_path: Path, watch_paths: List[Path] = None) -> bool:
        """Initialize dashboard with project monitoring."""
        try:
            # Initialize file monitoring
            self.file_monitor = FileSystemMonitor(
                pattern_update_callback=self._on_pattern_update
            )
            
            # Add project path to monitoring
            if not self.file_monitor.add_path(project_path, recursive=True):
                self.logger.warning(f"Failed to add project path: {project_path}")
            
            # Add additional watch paths
            if watch_paths:
                for path in watch_paths:
                    self.file_monitor.add_path(path, recursive=True)
            
            # Start file monitoring
            if not self.file_monitor.start_monitoring():
                self.logger.error("Failed to start file monitoring")
                return False
            
            # Load existing patterns
            self._load_existing_patterns()
            
            # Initial metrics update
            self._update_metrics()
            
            self._log("Dashboard initialized successfully", "INFO", "dashboard")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dashboard: {e}")
            return False
    
    def start(self) -> None:
        """Start the interactive dashboard."""
        if self.running:
            return
        
        try:
            self.running = True
            
            # Start background update thread
            self.update_thread = threading.Thread(
                target=self._background_update_loop,
                daemon=True
            )
            self.update_thread.start()
            
            # Enter main loop
            with self.term.cbreak(), self.term.hidden_cursor():
                self._main_loop()
                
        except KeyboardInterrupt:
            self._log("Dashboard interrupted by user", "INFO", "dashboard")
        except Exception as e:
            self._log(f"Dashboard error: {e}", "ERROR", "dashboard")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the dashboard and cleanup resources."""
        if not self.running:
            return
        
        self.running = False
        
        # Stop file monitoring
        if self.file_monitor:
            self.file_monitor.stop_monitoring()
        
        # Wait for update thread
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        
        # Clear screen
        if self.term:
            print(self.term.clear + self.term.home)
        
        self._log("Dashboard stopped", "INFO", "dashboard")
    
    def _main_loop(self) -> None:
        """Main dashboard interaction loop."""
        while self.running:
            try:
                # Clear screen and render
                self._render_dashboard()
                
                # Handle input with timeout
                key = self.term.inkey(timeout=0.5)
                if key:
                    self._handle_input(key)
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                self._log(f"Main loop error: {e}", "ERROR", "dashboard")
                break
    
    def _render_dashboard(self) -> None:
        """Render the complete dashboard interface."""
        output = []
        
        # Header
        output.extend(self._render_header())
        
        # Current view content
        if self.current_view == "main":
            output.extend(self._render_main_view())
        elif self.current_view == "patterns":
            output.extend(self._render_patterns_view())
        elif self.current_view == "sessions":
            output.extend(self._render_sessions_view())
        elif self.current_view == "preferences":
            output.extend(self._render_preferences_view())
        elif self.current_view == "logs":
            output.extend(self._render_logs_view())
        elif self.current_view == "help":
            output.extend(self._render_help_view())
        
        # Footer
        output.extend(self._render_footer())
        
        # Output to terminal
        print(self.term.clear + self.term.home + "\n".join(output), end="")
    
    def _render_header(self) -> List[str]:
        """Render dashboard header."""
        lines = []
        
        # Title bar
        title = f"{self.colors['header']}🚀 Spark AI Learning Dashboard{self.colors['reset']}"
        timestamp = f"{self.colors['dim']}{datetime.now().strftime('%H:%M:%S')}{self.colors['reset']}"
        status = f"{self.colors['success'] if not self.paused else self.colors['warning']}{'●' if not self.paused else '⏸'}{self.colors['reset']}"
        
        lines.append(f"{title} {' ' * (self.term.width - len(title.replace(self.colors['header'], '').replace(self.colors['reset'], '')) - len(timestamp) - 10)} {timestamp} {status}")
        lines.append("─" * self.term.width)
        
        # Navigation tabs
        tabs = [
            ("1", "Main", self.current_view == "main"),
            ("2", "Patterns", self.current_view == "patterns"),
            ("3", "Sessions", self.current_view == "sessions"),
            ("4", "Preferences", self.current_view == "preferences"),
            ("5", "Logs", self.current_view == "logs"),
            ("H", "Help", self.current_view == "help")
        ]
        
        tab_line = ""
        for key, name, active in tabs:
            if active:
                tab_line += f"{self.colors['highlight']}[{key}] {name}{self.colors['reset']} "
            else:
                tab_line += f"{self.colors['dim']}[{key}] {name}{self.colors['reset']} "
        
        lines.append(tab_line)
        lines.append("")
        
        return lines
    
    def _render_main_view(self) -> List[str]:
        """Render main dashboard overview."""
        lines = []
        
        # Quick metrics
        lines.append(f"{self.colors['header']}📊 Overview{self.colors['reset']}")
        lines.append("")
        
        # Pattern confidence summary
        confidence_color = self.colors['success'] if self.metrics.exploration_readiness >= 0.7 else \
                          self.colors['warning'] if self.metrics.exploration_readiness >= 0.4 else self.colors['error']
        
        lines.append(f"Pattern Confidence: {confidence_color}{self.metrics.exploration_readiness:.1%}{self.colors['reset']}")
        lines.append(f"Total Patterns: {self.colors['info']}{self.metrics.total_patterns}{self.colors['reset']}")
        lines.append(f"High Confidence: {self.colors['success']}{self.metrics.high_confidence_patterns}{self.colors['reset']}")
        lines.append("")
        
        # Current session
        if self.metrics.current_session_active:
            lines.append(f"{self.colors['header']}🔥 Active Session{self.colors['reset']}")
            lines.append(f"Duration: {self.colors['info']}{self.metrics.session_duration:.1f}h{self.colors['reset']}")
            lines.append(f"Changes: {self.colors['info']}{self.metrics.session_changes}{self.colors['reset']}")
            lines.append(f"Files: {self.colors['info']}{self.metrics.session_files}{self.colors['reset']}")
        else:
            lines.append(f"{self.colors['dim']}💤 No active session{self.colors['reset']}")
        
        lines.append("")
        
        # File monitoring status
        lines.append(f"{self.colors['header']}👀 Monitoring{self.colors['reset']}")
        lines.append(f"Files Watched: {self.colors['info']}{self.metrics.files_watched}{self.colors['reset']}")
        lines.append(f"Events Processed: {self.colors['info']}{self.metrics.events_processed}{self.colors['reset']}")
        
        if self.metrics.last_activity:
            time_since = datetime.now() - self.metrics.last_activity
            activity_str = f"{time_since.total_seconds():.0f}s ago"
            lines.append(f"Last Activity: {self.colors['info']}{activity_str}{self.colors['reset']}")
        else:
            lines.append(f"Last Activity: {self.colors['dim']}None{self.colors['reset']}")
        
        lines.append("")
        
        # Performance metrics
        if PSUTIL_AVAILABLE:
            cpu_color = self.colors['error'] if self.metrics.cpu_usage > 5.0 else \
                       self.colors['warning'] if self.metrics.cpu_usage > 2.0 else self.colors['success']
            
            lines.append(f"{self.colors['header']}⚡ Performance{self.colors['reset']}")
            lines.append(f"CPU Usage: {cpu_color}{self.metrics.cpu_usage:.1f}%{self.colors['reset']}")
            lines.append(f"Memory: {self.colors['info']}{self.metrics.memory_usage:.1f}MB{self.colors['reset']}")
            lines.append(f"Latency: {self.colors['info']}{self.metrics.processing_latency:.2f}ms{self.colors['reset']}")
            lines.append("")
        
        # Exploration suggestions
        if self.metrics.suggested_technologies:
            lines.append(f"{self.colors['header']}🎯 Exploration Suggestions{self.colors['reset']}")
            for tech in self.metrics.suggested_technologies[:3]:
                lines.append(f"  • {self.colors['highlight']}{tech}{self.colors['reset']}")
        
        return lines
    
    def _render_patterns_view(self) -> List[str]:
        """Render patterns analysis view."""
        lines = []
        
        lines.append(f"{self.colors['header']}🧠 Pattern Analysis{self.colors['reset']}")
        lines.append("")
        
        # Pattern confidence by type
        for pattern_type, confidence in self.metrics.pattern_confidence.items():
            confidence_color = self.colors['success'] if confidence >= 0.7 else \
                             self.colors['warning'] if confidence >= 0.4 else self.colors['error']
            
            bar_length = 20
            filled_length = int(bar_length * confidence)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            lines.append(f"{pattern_type:20} {confidence_color}{bar}{self.colors['reset']} {confidence:.1%}")
        
        return lines
    
    def _render_sessions_view(self) -> List[str]:
        """Render development sessions view."""
        lines = []
        
        lines.append(f"{self.colors['header']}📈 Development Sessions{self.colors['reset']}")
        lines.append("")
        
        if self.file_monitor:
            rhythm = self.file_monitor.get_development_rhythm()
            
            lines.append(f"Total Sessions: {self.colors['info']}{rhythm.get('total_sessions', 0)}{self.colors['reset']}")
            lines.append(f"Avg Duration: {self.colors['info']}{rhythm.get('average_session_duration', 0):.1f}h{self.colors['reset']}")
            lines.append(f"Avg Changes: {self.colors['info']}{rhythm.get('average_changes_per_session', 0):.0f}{self.colors['reset']}")
            lines.append("")
            
            # Peak hours
            peak_hours = rhythm.get('peak_hours', [])
            if peak_hours:
                lines.append(f"{self.colors['header']}⏰ Peak Hours{self.colors['reset']}")
                for hour, count in peak_hours:
                    lines.append(f"  {hour:02d}:00 - {self.colors['info']}{count} sessions{self.colors['reset']}")
        
        return lines
    
    def _render_preferences_view(self) -> List[str]:
        """Render preferences analysis view."""
        lines = []
        
        lines.append(f"{self.colors['header']}🎨 Developer Preferences{self.colors['reset']}")
        lines.append("")
        
        lines.append(f"Learning Trajectory: {self.colors['info']}{self.metrics.learning_trajectory}{self.colors['reset']}")
        lines.append("")
        
        # TODO: Add more preference details when preference mapper data is available
        
        return lines
    
    def _render_logs_view(self) -> List[str]:
        """Render logs view."""
        lines = []
        
        lines.append(f"{self.colors['header']}📋 Activity Logs{self.colors['reset']}")
        lines.append("")
        
        # Show recent log entries
        for entry in list(self.log_entries)[-15:]:  # Show last 15 entries
            level_color = {
                'ERROR': self.colors['error'],
                'WARNING': self.colors['warning'],
                'INFO': self.colors['info'],
                'DEBUG': self.colors['dim']
            }.get(entry.level, self.colors['reset'])
            
            timestamp_str = entry.timestamp.strftime('%H:%M:%S')
            lines.append(f"{self.colors['dim']}{timestamp_str}{self.colors['reset']} "
                        f"{level_color}{entry.level:7}{self.colors['reset']} "
                        f"{self.colors['dim']}{entry.component:10}{self.colors['reset']} "
                        f"{entry.message}")
        
        return lines
    
    def _render_help_view(self) -> List[str]:
        """Render help view."""
        lines = []
        
        lines.append(f"{self.colors['header']}❓ Help & Controls{self.colors['reset']}")
        lines.append("")
        
        controls = [
            ("1-5", "Switch between views"),
            ("Space", "Pause/Resume updates"),
            ("R", "Refresh data"),
            ("C", "Toggle compact mode"),
            ("Q/ESC", "Quit dashboard"),
            ("H/?", "Show this help"),
            ("↑/↓", "Navigate lists"),
        ]
        
        for key, description in controls:
            lines.append(f"{self.colors['highlight']}{key:10}{self.colors['reset']} {description}")
        
        return lines
    
    def _render_footer(self) -> List[str]:
        """Render dashboard footer."""
        lines = []
        
        lines.append("")
        lines.append("─" * self.term.width)
        
        # Controls hint
        controls = f"{self.colors['dim']}[Q]uit [SPACE]pause [R]efresh [H]elp{self.colors['reset']}"
        update_info = f"{self.colors['dim']}Updated: {self.last_update.strftime('%H:%M:%S')}{self.colors['reset']}"
        
        lines.append(f"{controls} {' ' * (self.term.width - len(controls.replace(self.colors['dim'], '').replace(self.colors['reset'], '')) - len(update_info.replace(self.colors['dim'], '').replace(self.colors['reset'], '')) - 2)} {update_info}")
        
        return lines
    
    def _handle_input(self, key) -> None:
        """Handle keyboard input."""
        key_str = str(key).lower()
        
        # View switching
        if key_str == "1":
            self.current_view = "main"
        elif key_str == "2":
            self.current_view = "patterns"
        elif key_str == "3":
            self.current_view = "sessions"
        elif key_str == "4":
            self.current_view = "preferences"
        elif key_str == "5":
            self.current_view = "logs"
        elif key_str in ["h", "?"]:
            self.current_view = "help"
        
        # Controls
        elif key_str == " ":  # Space - pause/resume
            self.paused = not self.paused
            self._log(f"Dashboard {'paused' if self.paused else 'resumed'}", "INFO", "dashboard")
        
        elif key_str == "r":  # Refresh
            self._update_metrics()
            self._log("Dashboard refreshed", "INFO", "dashboard")
        
        elif key_str == "c":  # Toggle compact mode
            self.config.compact_mode = not self.config.compact_mode
            self._log(f"Compact mode {'enabled' if self.config.compact_mode else 'disabled'}", "INFO", "dashboard")
        
        elif key_str in ["q", "escape"]:  # Quit
            self.running = False
        
        # Navigation
        elif key.code == self.term.KEY_UP:
            self.selected_index = max(0, self.selected_index - 1)
        elif key.code == self.term.KEY_DOWN:
            self.selected_index += 1
    
    def _background_update_loop(self) -> None:
        """Background thread for updating metrics."""
        while self.running:
            try:
                if not self.paused:
                    self._update_metrics()
                    self.last_update = datetime.now()
                
                time.sleep(self.config.refresh_interval)
                
            except Exception as e:
                self._log(f"Background update error: {e}", "ERROR", "dashboard")
    
    def _update_metrics(self) -> None:
        """Update dashboard metrics."""
        try:
            # Update pattern confidence metrics
            self._update_pattern_metrics()
            
            # Update session metrics
            self._update_session_metrics()
            
            # Update file monitoring metrics
            self._update_monitoring_metrics()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Update exploration suggestions
            self._update_exploration_metrics()
            
        except Exception as e:
            self._log(f"Error updating metrics: {e}", "ERROR", "dashboard")
    
    def _update_pattern_metrics(self) -> None:
        """Update pattern confidence metrics."""
        # TODO: Implement when pattern storage integration is complete
        self.metrics.total_patterns = 25  # Placeholder
        self.metrics.high_confidence_patterns = 18  # Placeholder
        
        # Placeholder pattern confidence data
        self.metrics.pattern_confidence = {
            "Style Patterns": 0.85,
            "Naming Conventions": 0.72,
            "Error Handling": 0.91,
            "Testing Patterns": 0.63,
            "Documentation": 0.45
        }
    
    def _update_session_metrics(self) -> None:
        """Update development session metrics."""
        if self.file_monitor:
            rhythm = self.file_monitor.get_development_rhythm()
            current_session = rhythm.get('current_session', {})
            
            self.metrics.current_session_active = current_session.get('active', False)
            self.metrics.session_duration = current_session.get('duration', 0)
            self.metrics.session_changes = current_session.get('changes', 0)
            # Placeholder for files count
            self.metrics.session_files = max(1, self.metrics.session_changes // 3)
    
    def _update_monitoring_metrics(self) -> None:
        """Update file monitoring metrics."""
        if self.file_monitor:
            stats = self.file_monitor.get_stats()
            self.metrics.files_watched = len(self.file_monitor.monitored_paths)
            self.metrics.events_processed = stats.events_processed
            self.metrics.last_activity = stats.last_activity
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                self.metrics.cpu_usage = process.cpu_percent()
                self.metrics.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                
                # Placeholder for processing latency
                self.metrics.processing_latency = 1.2
                
            except Exception as e:
                self._log(f"Error updating performance metrics: {e}", "WARNING", "dashboard")
    
    def _update_exploration_metrics(self) -> None:
        """Update exploration readiness metrics."""
        # Calculate overall exploration readiness
        if self.metrics.pattern_confidence:
            confidence_values = list(self.metrics.pattern_confidence.values())
            self.metrics.exploration_readiness = sum(confidence_values) / len(confidence_values)
        
        # Placeholder suggestions
        self.metrics.suggested_technologies = ["FastAPI", "Pytest", "Pydantic"]
        self.metrics.learning_trajectory = "progressive"
    
    def _load_existing_patterns(self) -> None:
        """Load existing patterns from storage."""
        try:
            # TODO: Implement when storage integration is ready
            self._log("Loaded existing patterns", "INFO", "dashboard")
        except Exception as e:
            self._log(f"Error loading patterns: {e}", "WARNING", "dashboard")
    
    def _on_pattern_update(self, events) -> None:
        """Handle pattern update callback from file monitor."""
        try:
            self._log(f"Pattern update triggered by {len(events)} file changes", "INFO", "monitor")
            
            # Trigger pattern re-analysis
            # TODO: Integrate with pattern analysis pipeline
            
        except Exception as e:
            self._log(f"Error handling pattern update: {e}", "ERROR", "monitor")
    
    def _log(self, message: str, level: str, component: str) -> None:
        """Add entry to dashboard log."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            component=component
        )
        self.log_entries.append(entry)
        
        # Also log to standard logger
        getattr(self.logger, level.lower(), self.logger.info)(f"[{component}] {message}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def create_dashboard(project_path: Path, config: Optional[DashboardConfig] = None) -> InteractiveDashboard:
    """Create and initialize a dashboard for the given project."""
    dashboard = InteractiveDashboard(config)
    
    if not dashboard.initialize(project_path):
        raise SparkLearningError("Failed to initialize dashboard")
    
    return dashboard


def main():
    """CLI entry point for dashboard testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Spark Interactive Dashboard")
    parser.add_argument("project_path", type=Path, help="Project path to monitor")
    parser.add_argument("--refresh", type=float, default=1.0, help="Refresh interval in seconds")
    parser.add_argument("--compact", action="store_true", help="Enable compact mode")
    parser.add_argument("--no-colors", action="store_true", help="Disable colors")
    
    args = parser.parse_args()
    
    config = DashboardConfig(
        refresh_interval=args.refresh,
        compact_mode=args.compact,
        enable_colors=not args.no_colors
    )
    
    try:
        with create_dashboard(args.project_path, config) as dashboard:
            dashboard.start()
    except KeyboardInterrupt:
        print("\nDashboard terminated by user.")
    except Exception as e:
        print(f"Dashboard error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()