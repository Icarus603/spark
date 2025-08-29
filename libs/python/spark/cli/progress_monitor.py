"""
Real-time progress monitoring and visualization for exploration sessions.

This module provides comprehensive progress tracking with rich terminal output,
real-time updates, and detailed session monitoring capabilities.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Thread
import signal
import sys

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align

from spark.discovery.models import ExplorationSession, ExplorationStatus
from spark.core.session_manager import SessionManager, SessionCheckpoint


@dataclass
class ProgressMetrics:
    """Metrics for progress tracking."""
    session_id: str
    phase: str
    progress_percentage: float
    elapsed_time: float
    estimated_remaining: Optional[float] = None
    throughput: Optional[float] = None  # operations per minute
    error_count: int = 0
    warnings_count: int = 0
    discoveries_found: int = 0
    resource_usage: Dict[str, float] = None


class ProgressMonitor:
    """Real-time progress monitoring for exploration sessions."""
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize ProgressMonitor.
        
        Args:
            session_manager: SessionManager instance for tracking sessions
        """
        self.session_manager = session_manager
        self.console = Console()
        self.active_monitors: Dict[str, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.live_display: Optional[Live] = None
        self.update_interval = 1.0  # seconds
        self.shutdown_requested = False
        
        # Progress tracking state
        self.session_progress: Dict[str, Progress] = {}
        self.session_tasks: Dict[str, TaskID] = {}
        self.session_metrics: Dict[str, ProgressMetrics] = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.shutdown_requested = True
        self.stop_all_monitoring()
        sys.exit(0)
    
    async def start_monitoring(self, session_id: str, show_live_display: bool = True) -> bool:
        """
        Start monitoring a session with real-time progress display.
        
        Args:
            session_id: Session ID to monitor
            show_live_display: Whether to show live terminal display
            
        Returns:
            True if monitoring started successfully
        """
        
        if session_id in self.active_monitors:
            return False  # Already monitoring
        
        # Verify session exists
        trajectory = await self.session_manager.get_session_trajectory(session_id)
        if not trajectory:
            return False
        
        # Initialize monitoring state
        self.active_monitors[session_id] = {
            'start_time': time.time(),
            'last_update': time.time(),
            'checkpoint_count': 0,
            'show_live': show_live_display,
            'phase_history': []
        }
        
        # Create progress tracking
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bright_green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        
        self.session_progress[session_id] = progress
        
        # Add main task
        task_id = progress.add_task(
            f"Session {session_id[:8]}...",
            total=100
        )
        self.session_tasks[session_id] = task_id
        
        # Initialize metrics
        self.session_metrics[session_id] = ProgressMetrics(
            session_id=session_id,
            phase="initializing",
            progress_percentage=0.0,
            elapsed_time=0.0,
            resource_usage={}
        )
        
        # Start monitoring task
        monitor_task = asyncio.create_task(
            self._monitor_session_loop(session_id)
        )
        self.monitoring_tasks[session_id] = monitor_task
        
        # Start live display if requested
        if show_live_display:
            await self._start_live_display(session_id)
        
        return True
    
    async def stop_monitoring(self, session_id: str) -> bool:
        """Stop monitoring a specific session."""
        
        if session_id not in self.active_monitors:
            return False
        
        # Cancel monitoring task
        if session_id in self.monitoring_tasks:
            self.monitoring_tasks[session_id].cancel()
            del self.monitoring_tasks[session_id]
        
        # Cleanup progress tracking
        if session_id in self.session_progress:
            self.session_progress[session_id].stop()
            del self.session_progress[session_id]
        
        if session_id in self.session_tasks:
            del self.session_tasks[session_id]
        
        if session_id in self.session_metrics:
            del self.session_metrics[session_id]
        
        # Stop live display if this was the last session
        if len(self.active_monitors) == 1 and self.live_display:
            self.live_display.stop()
            self.live_display = None
        
        del self.active_monitors[session_id]
        
        return True
    
    def stop_all_monitoring(self):
        """Stop monitoring all active sessions."""
        session_ids = list(self.active_monitors.keys())
        
        for session_id in session_ids:
            # Use synchronous cleanup since this might be called from signal handler
            if session_id in self.monitoring_tasks:
                self.monitoring_tasks[session_id].cancel()
            
            if session_id in self.session_progress:
                self.session_progress[session_id].stop()
        
        # Stop live display
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
        
        # Clear all state
        self.active_monitors.clear()
        self.monitoring_tasks.clear()
        self.session_progress.clear()
        self.session_tasks.clear()
        self.session_metrics.clear()
    
    async def get_session_status_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive status summary for a session."""
        
        trajectory = await self.session_manager.get_session_trajectory(session_id)
        if not trajectory:
            return {'error': f'Session {session_id} not found'}
        
        # Calculate current metrics
        current_time = datetime.now()
        elapsed = (current_time - trajectory.start_time).total_seconds()
        
        latest_checkpoint = trajectory.checkpoints[-1] if trajectory.checkpoints else None
        
        status = {
            'session_id': session_id,
            'start_time': trajectory.start_time.isoformat(),
            'elapsed_time': elapsed,
            'current_phase': latest_checkpoint.phase if latest_checkpoint else 'unknown',
            'progress_percentage': latest_checkpoint.progress_percentage if latest_checkpoint else 0.0,
            'checkpoints_count': len(trajectory.checkpoints),
            'outcome': trajectory.outcome,
            'discoveries_created': trajectory.discoveries_created,
            'is_active': session_id in self.active_monitors
        }
        
        # Add resource usage if available
        if latest_checkpoint and latest_checkpoint.resource_usage:
            status['current_resource_usage'] = latest_checkpoint.resource_usage
        
        # Add error information
        total_errors = sum(len(cp.errors) for cp in trajectory.checkpoints)
        status['total_errors'] = total_errors
        
        if latest_checkpoint and latest_checkpoint.errors:
            status['recent_errors'] = latest_checkpoint.errors
        
        return status
    
    async def get_all_active_sessions_status(self) -> List[Dict[str, Any]]:
        """Get status for all active monitoring sessions."""
        
        active_sessions = list(self.active_monitors.keys())
        statuses = []
        
        for session_id in active_sessions:
            status = await self.get_session_status_summary(session_id)
            statuses.append(status)
        
        return statuses
    
    def display_session_summary_table(self, sessions: List[Dict[str, Any]]):
        """Display a summary table of session statuses."""
        
        if not sessions:
            self.console.print("[yellow]No active exploration sessions[/yellow]")
            return
        
        table = Table(title="Active Exploration Sessions", show_header=True)
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Phase", style="magenta")
        table.add_column("Progress", style="green")
        table.add_column("Duration", style="blue")
        table.add_column("Discoveries", style="yellow")
        table.add_column("Errors", style="red")
        table.add_column("Status", style="white")
        
        for session in sessions:
            session_id_short = session['session_id'][:8] + "..."
            phase = session.get('current_phase', 'unknown')
            progress = f"{session.get('progress_percentage', 0):.1f}%"
            
            # Format duration
            elapsed = session.get('elapsed_time', 0)
            duration = str(timedelta(seconds=int(elapsed)))
            
            discoveries = str(session.get('discoveries_created', 0))
            errors = str(session.get('total_errors', 0))
            
            # Status indicator
            if session.get('is_active'):
                if session.get('outcome') == 'completed':
                    status = "✅ Completed"
                elif session.get('outcome') == 'failed':
                    status = "❌ Failed"
                else:
                    status = "🔄 Running"
            else:
                status = "⏸️ Inactive"
            
            table.add_row(
                session_id_short,
                phase,
                progress,
                duration,
                discoveries,
                errors,
                status
            )
        
        self.console.print(table)
    
    async def _start_live_display(self, session_id: str):
        """Start live display for session monitoring."""
        
        if self.live_display is not None:
            return  # Already displaying
        
        layout = self._create_monitoring_layout()
        
        self.live_display = Live(
            layout,
            console=self.console,
            refresh_per_second=2,
            auto_refresh=True
        )
        
        self.live_display.start()
    
    def _create_monitoring_layout(self) -> Layout:
        """Create the monitoring layout for live display."""
        
        layout = Layout(name="root")
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="progress", ratio=2),
            Layout(name="metrics", ratio=1)
        )
        
        return layout
    
    async def _monitor_session_loop(self, session_id: str):
        """Main monitoring loop for a session."""
        
        try:
            while not self.shutdown_requested and session_id in self.active_monitors:
                # Update session metrics
                await self._update_session_metrics(session_id)
                
                # Update progress display
                await self._update_progress_display(session_id)
                
                # Update live display if active
                if self.live_display and self.live_display.is_started:
                    await self._update_live_display()
                
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            pass  # Normal cancellation
        except Exception as e:
            self.console.print(f"[red]Monitoring error for session {session_id}: {e}[/red]")
    
    async def _update_session_metrics(self, session_id: str):
        """Update metrics for a monitored session."""
        
        trajectory = await self.session_manager.get_session_trajectory(session_id)
        if not trajectory:
            return
        
        monitor_data = self.active_monitors[session_id]
        current_time = time.time()
        
        # Get latest checkpoint
        latest_checkpoint = trajectory.checkpoints[-1] if trajectory.checkpoints else None
        
        if latest_checkpoint:
            # Update progress metrics
            metrics = self.session_metrics[session_id]
            metrics.phase = latest_checkpoint.phase
            metrics.progress_percentage = latest_checkpoint.progress_percentage
            metrics.elapsed_time = current_time - monitor_data['start_time']
            metrics.error_count = sum(len(cp.errors) for cp in trajectory.checkpoints)
            metrics.discoveries_found = trajectory.discoveries_created
            
            # Update resource usage
            if latest_checkpoint.resource_usage:
                metrics.resource_usage = latest_checkpoint.resource_usage.copy()
            
            # Calculate throughput if we have checkpoints
            if len(trajectory.checkpoints) > 1:
                checkpoint_rate = len(trajectory.checkpoints) / (metrics.elapsed_time / 60)  # per minute
                metrics.throughput = checkpoint_rate
            
            # Estimate remaining time
            if metrics.progress_percentage > 0:
                remaining_progress = 100 - metrics.progress_percentage
                time_per_percent = metrics.elapsed_time / metrics.progress_percentage
                metrics.estimated_remaining = remaining_progress * time_per_percent
        
        monitor_data['last_update'] = current_time
        monitor_data['checkpoint_count'] = len(trajectory.checkpoints) if trajectory else 0
    
    async def _update_progress_display(self, session_id: str):
        """Update the progress bar display for a session."""
        
        if session_id not in self.session_progress or session_id not in self.session_tasks:
            return
        
        progress = self.session_progress[session_id]
        task_id = self.session_tasks[session_id]
        metrics = self.session_metrics[session_id]
        
        # Update progress bar
        progress.update(
            task_id,
            completed=metrics.progress_percentage,
            description=f"[bold blue]{metrics.phase.title().replace('_', ' ')}[/bold blue]"
        )
    
    async def _update_live_display(self):
        """Update the live display layout with current information."""
        
        if not self.live_display or not self.live_display.is_started:
            return
        
        layout = self.live_display.renderable
        
        # Update header
        layout["header"].update(
            Panel(
                Align.center(Text("🚀 Spark Autonomous Exploration Monitor", style="bold cyan")),
                style="blue"
            )
        )
        
        # Update progress section
        progress_content = []
        for session_id, progress in self.session_progress.items():
            progress_content.append(progress)
        
        if progress_content:
            layout["progress"].update(Panel("\n".join(str(p) for p in progress_content), title="Progress"))
        
        # Update metrics section
        metrics_table = Table(title="Session Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="yellow")
        
        for session_id, metrics in self.session_metrics.items():
            if session_id in self.active_monitors:
                metrics_table.add_row("Phase", metrics.phase.title().replace('_', ' '))
                metrics_table.add_row("Elapsed", f"{metrics.elapsed_time:.1f}s")
                if metrics.estimated_remaining:
                    metrics_table.add_row("Est. Remaining", f"{metrics.estimated_remaining:.1f}s")
                metrics_table.add_row("Discoveries", str(metrics.discoveries_found))
                metrics_table.add_row("Errors", str(metrics.error_count))
                
                if metrics.resource_usage:
                    for resource, value in metrics.resource_usage.items():
                        if isinstance(value, (int, float)):
                            metrics_table.add_row(resource.title(), f"{value:.1f}")
        
        layout["metrics"].update(Panel(metrics_table))
        
        # Update footer
        active_count = len(self.active_monitors)
        footer_text = f"Monitoring {active_count} session(s) | Press Ctrl+C to exit"
        layout["footer"].update(
            Panel(
                Align.center(Text(footer_text, style="dim")),
                style="dim"
            )
        )
    
    def print_session_details(self, session_status: Dict[str, Any]):
        """Print detailed information about a session."""
        
        session_id = session_status['session_id']
        
        # Create detailed panel
        details_table = Table(title=f"Session Details: {session_id}", show_header=False)
        details_table.add_column("Property", style="cyan", width=20)
        details_table.add_column("Value", style="white")
        
        details_table.add_row("Session ID", session_id)
        details_table.add_row("Start Time", session_status.get('start_time', 'Unknown'))
        details_table.add_row("Current Phase", session_status.get('current_phase', 'Unknown'))
        details_table.add_row("Progress", f"{session_status.get('progress_percentage', 0):.1f}%")
        
        elapsed = session_status.get('elapsed_time', 0)
        details_table.add_row("Duration", str(timedelta(seconds=int(elapsed))))
        
        details_table.add_row("Checkpoints", str(session_status.get('checkpoints_count', 0)))
        details_table.add_row("Discoveries", str(session_status.get('discoveries_created', 0)))
        details_table.add_row("Total Errors", str(session_status.get('total_errors', 0)))
        
        # Resource usage
        if 'current_resource_usage' in session_status:
            resources = session_status['current_resource_usage']
            for resource, value in resources.items():
                if isinstance(value, (int, float)):
                    unit = "%" if "percent" in resource else ("MB" if "memory" in resource else "")
                    details_table.add_row(f"  {resource.title()}", f"{value:.1f} {unit}")
        
        self.console.print(Panel(details_table))
        
        # Show recent errors if any
        if 'recent_errors' in session_status and session_status['recent_errors']:
            error_panel = Panel(
                "\n".join(f"• {error}" for error in session_status['recent_errors'][-5:]),  # Last 5 errors
                title="Recent Errors",
                style="red"
            )
            self.console.print(error_panel)