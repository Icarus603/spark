"""
Cross-platform file system monitor for real-time pattern learning.

This module provides efficient file system monitoring that triggers pattern analysis
when code files are modified, enabling continuous learning and development rhythm tracking.
"""

import os
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from spark.cli.errors import SparkLearningError
from spark.learning.style_analyzer import MultiLanguageStyleAnalyzer


@dataclass
class FileChangeEvent:
    """Represents a file system change event."""
    
    file_path: Path
    event_type: str  # modified, created, deleted
    timestamp: datetime
    file_size: int = 0
    is_code_file: bool = False
    language: Optional[str] = None


@dataclass
class DevelopmentSession:
    """Represents a development session based on file activity."""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    files_modified: Set[str] = field(default_factory=set)
    total_changes: int = 0
    languages_used: Set[str] = field(default_factory=set)
    active_directories: Set[str] = field(default_factory=set)
    session_duration: Optional[timedelta] = None


@dataclass
class MonitoringStats:
    """Statistics for monitoring performance."""
    
    events_processed: int = 0
    sessions_detected: int = 0
    patterns_triggered: int = 0
    last_activity: Optional[datetime] = None
    monitoring_duration: timedelta = field(default_factory=lambda: timedelta())
    
    # Performance metrics
    cpu_usage_avg: float = 0.0
    memory_usage_mb: float = 0.0
    event_processing_time_ms: float = 0.0


class SparkFileEventHandler(FileSystemEventHandler):
    """Custom event handler for Spark file monitoring."""
    
    def __init__(self, monitor: 'FileSystemMonitor'):
        super().__init__()
        self.monitor = monitor
        self.logger = logging.getLogger(f"spark.monitor.{self.__class__.__name__}")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.monitor._handle_file_event(event.src_path, "modified")
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.monitor._handle_file_event(event.src_path, "created")
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self.monitor._handle_file_event(event.src_path, "deleted")


class FileSystemMonitor:
    """Cross-platform file system monitor for pattern learning."""
    
    def __init__(self, pattern_update_callback: Optional[Callable] = None):
        if not WATCHDOG_AVAILABLE:
            raise SparkLearningError(
                "File monitoring requires watchdog library",
                "Install with: pip install watchdog"
            )
        
        self.observer = Observer()
        self.event_handler = SparkFileEventHandler(self)
        self.pattern_update_callback = pattern_update_callback
        
        # Configuration
        self.monitored_paths: Set[Path] = set()
        self.watch_handles: Dict[str, Any] = {}
        
        # File filtering
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', 
            '.kt', '.swift', '.cpp', '.c', '.h', '.hpp', '.rb', '.php', 
            '.cs', '.scala', '.clj', '.hs', '.elm', '.dart', '.lua', 
            '.r', '.m', '.mm', '.sh', '.bash', '.zsh'
        }
        
        self.ignore_patterns = {
            '__pycache__', 'node_modules', '.git', '.venv', 'venv',
            'build', 'dist', '.pytest_cache', 'target', '.mypy_cache',
            '.DS_Store', '.idea', '.vscode'
        }
        
        # Event tracking
        self.recent_events: deque = deque(maxlen=1000)
        self.event_buffer: deque = deque(maxlen=100)  # Buffer for batch processing
        self.last_activity_time = None
        
        # Session tracking
        self.current_session: Optional[DevelopmentSession] = None
        self.completed_sessions: List[DevelopmentSession] = []
        self.session_timeout = timedelta(minutes=15)  # 15 minutes of inactivity ends session
        
        # Performance tracking
        self.stats = MonitoringStats()
        
        # Analysis integration
        self.style_analyzer = MultiLanguageStyleAnalyzer()
        
        # Threading
        self.monitoring_thread: Optional[threading.Thread] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.event_queue = asyncio.Queue()
        
        self.logger = logging.getLogger(f"spark.{self.__class__.__name__}")
    
    def add_path(self, path: Path, recursive: bool = True) -> bool:
        """Add a path to monitoring."""
        try:
            path = path.resolve()
            
            if not path.exists():
                self.logger.warning(f"Path does not exist: {path}")
                return False
            
            if path in self.monitored_paths:
                self.logger.info(f"Path already monitored: {path}")
                return True
            
            # Add watchdog observer
            watch_handle = self.observer.schedule(
                self.event_handler,
                str(path),
                recursive=recursive
            )
            
            self.monitored_paths.add(path)
            self.watch_handles[str(path)] = watch_handle
            
            self.logger.info(f"Added monitoring for: {path} (recursive: {recursive})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add path {path}: {e}")
            return False
    
    def remove_path(self, path: Path) -> bool:
        """Remove a path from monitoring."""
        try:
            path = path.resolve()
            path_str = str(path)
            
            if path_str in self.watch_handles:
                self.observer.unschedule(self.watch_handles[path_str])
                del self.watch_handles[path_str]
            
            self.monitored_paths.discard(path)
            
            self.logger.info(f"Removed monitoring for: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove path {path}: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start file system monitoring."""
        try:
            if not self.monitored_paths:
                self.logger.warning("No paths configured for monitoring")
                return False
            
            # Start watchdog observer
            self.observer.start()
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._event_processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            self.stats.last_activity = datetime.now()
            self.logger.info(f"Started monitoring {len(self.monitored_paths)} paths")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop file system monitoring."""
        try:
            self.should_stop.set()
            
            # Stop watchdog observer
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5)
            
            # Wait for processing thread
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
            
            self.logger.info("Stopped file system monitoring")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {e}")
            return False
    
    def _handle_file_event(self, file_path: str, event_type: str) -> None:
        """Handle a file system event."""
        try:
            path = Path(file_path)
            
            # Filter out irrelevant files
            if not self._should_monitor_file(path):
                return
            
            # Create event
            event = FileChangeEvent(
                file_path=path,
                event_type=event_type,
                timestamp=datetime.now(),
                is_code_file=self._is_code_file(path),
                language=self._detect_language(path)
            )
            
            # Get file size if it exists
            try:
                if path.exists():
                    event.file_size = path.stat().st_size
            except OSError:
                pass
            
            # Add to event buffer
            self.event_buffer.append(event)
            self.recent_events.append(event)
            self.stats.events_processed += 1
            self.stats.last_activity = event.timestamp
            
            # Update current session
            self._update_current_session(event)
            
            self.logger.debug(f"File event: {event_type} - {path}")
            
        except Exception as e:
            self.logger.error(f"Error handling file event {file_path}: {e}")
    
    def _event_processing_loop(self) -> None:
        """Background thread for processing file events."""
        batch_size = 10
        batch_timeout = 5.0  # seconds
        
        while not self.should_stop.wait(timeout=1.0):
            try:
                # Process events in batches
                if len(self.event_buffer) >= batch_size or \
                   (self.event_buffer and time.time() % batch_timeout < 1.0):
                    
                    # Get batch of events
                    events_to_process = []
                    while self.event_buffer and len(events_to_process) < batch_size:
                        events_to_process.append(self.event_buffer.popleft())
                    
                    if events_to_process:
                        self._process_event_batch(events_to_process)
                
                # Check for session timeout
                self._check_session_timeout()
                
            except Exception as e:
                self.logger.error(f"Error in event processing loop: {e}")
    
    def _process_event_batch(self, events: List[FileChangeEvent]) -> None:
        """Process a batch of file events."""
        try:
            start_time = time.time()
            
            # Group events by file and type
            file_events = defaultdict(list)
            for event in events:
                file_events[event.file_path].append(event)
            
            # Trigger pattern analysis for modified code files
            code_files_changed = []
            for file_path, file_event_list in file_events.items():
                # Only process the latest event for each file
                latest_event = max(file_event_list, key=lambda e: e.timestamp)
                
                if latest_event.is_code_file and latest_event.event_type in ['modified', 'created']:
                    code_files_changed.append(latest_event)
            
            # Trigger pattern updates if callback is provided
            if self.pattern_update_callback and code_files_changed:
                try:
                    self.pattern_update_callback(code_files_changed)
                    self.stats.patterns_triggered += 1
                except Exception as e:
                    self.logger.error(f"Error in pattern update callback: {e}")
            
            # Update performance stats
            processing_time = (time.time() - start_time) * 1000
            self.stats.event_processing_time_ms = processing_time
            
        except Exception as e:
            self.logger.error(f"Error processing event batch: {e}")
    
    def _should_monitor_file(self, path: Path) -> bool:
        """Check if a file should be monitored."""
        
        # Check if any part of the path contains ignored patterns
        path_parts = path.parts
        for part in path_parts:
            if any(ignore_pattern in part.lower() for ignore_pattern in self.ignore_patterns):
                return False
        
        # Check file extension
        if not self._is_code_file(path):
            return False
        
        # Check file size (skip very large files)
        try:
            if path.exists() and path.stat().st_size > 1_000_000:  # 1MB limit
                return False
        except OSError:
            pass
        
        return True
    
    def _is_code_file(self, path: Path) -> bool:
        """Check if a file is a code file."""
        return path.suffix.lower() in self.code_extensions
    
    def _detect_language(self, path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp'
        }
        
        return extension_map.get(path.suffix.lower())
    
    def _update_current_session(self, event: FileChangeEvent) -> None:
        """Update the current development session."""
        now = event.timestamp
        
        # Start new session if none exists or if too much time has passed
        if (self.current_session is None or 
            (self.current_session.end_time and 
             now - self.current_session.end_time > self.session_timeout)):
            
            # End previous session if it exists
            if self.current_session and not self.current_session.end_time:
                self._end_current_session()
            
            # Start new session
            self.current_session = DevelopmentSession(
                session_id=f"session_{now.strftime('%Y%m%d_%H%M%S')}",
                start_time=now
            )
            self.stats.sessions_detected += 1
        
        # Update current session
        if self.current_session:
            self.current_session.files_modified.add(str(event.file_path))
            self.current_session.total_changes += 1
            
            if event.language:
                self.current_session.languages_used.add(event.language)
            
            # Track active directory
            self.current_session.active_directories.add(str(event.file_path.parent))
            
            # Update end time
            self.current_session.end_time = now
    
    def _check_session_timeout(self) -> None:
        """Check if current session should be ended due to inactivity."""
        if (self.current_session and 
            self.current_session.end_time and
            datetime.now() - self.current_session.end_time > self.session_timeout):
            
            self._end_current_session()
    
    def _end_current_session(self) -> None:
        """End the current development session."""
        if self.current_session and self.current_session.end_time:
            self.current_session.session_duration = (
                self.current_session.end_time - self.current_session.start_time
            )
            
            # Add to completed sessions
            self.completed_sessions.append(self.current_session)
            
            # Keep only recent sessions (last 50)
            if len(self.completed_sessions) > 50:
                self.completed_sessions = self.completed_sessions[-50:]
            
            self.logger.info(
                f"Ended session {self.current_session.session_id}: "
                f"{self.current_session.total_changes} changes, "
                f"{len(self.current_session.files_modified)} files, "
                f"{self.current_session.session_duration}"
            )
            
            self.current_session = None
    
    def get_development_rhythm(self) -> Dict[str, Any]:
        """Analyze development rhythm from session data."""
        if not self.completed_sessions:
            return {'sessions': 0, 'patterns': {}}
        
        # Analyze session patterns
        session_durations = [
            s.session_duration.total_seconds() / 3600  # Convert to hours
            for s in self.completed_sessions 
            if s.session_duration
        ]
        
        session_sizes = [s.total_changes for s in self.completed_sessions]
        
        # Time of day analysis
        session_hours = [s.start_time.hour for s in self.completed_sessions]
        hour_distribution = defaultdict(int)
        for hour in session_hours:
            hour_distribution[hour] += 1
        
        # Most active hours
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'total_sessions': len(self.completed_sessions),
            'average_session_duration': sum(session_durations) / len(session_durations) if session_durations else 0,
            'average_changes_per_session': sum(session_sizes) / len(session_sizes) if session_sizes else 0,
            'peak_hours': [(hour, count) for hour, count in peak_hours],
            'languages_used': list(set().union(*(s.languages_used for s in self.completed_sessions))),
            'current_session': {
                'active': self.current_session is not None,
                'duration': (datetime.now() - self.current_session.start_time).total_seconds() / 3600 
                           if self.current_session else 0,
                'changes': self.current_session.total_changes if self.current_session else 0
            }
        }
    
    def get_stats(self) -> MonitoringStats:
        """Get monitoring statistics."""
        self.stats.monitoring_duration = (
            datetime.now() - self.stats.last_activity 
            if self.stats.last_activity else timedelta()
        )
        return self.stats
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()