"""
Session management with comprehensive trajectory recording.

This module provides session management capabilities with CUA trajectory integration
for complete exploration session recording, state persistence, and analytics.
"""

import uuid
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict

from spark.discovery.models import ExplorationSession, ExplorationResult, ExplorationStatus

# Import CUA components for trajectory recording
try:
    from agent.agent.callbacks import TrajectorySaverCallback
    from agent.agent.callbacks.base import BaseCallback
    CUA_AVAILABLE = True
except ImportError:
    CUA_AVAILABLE = False
    BaseCallback = object


@dataclass
class SessionCheckpoint:
    """A checkpoint in an exploration session."""
    id: str
    session_id: str
    timestamp: datetime
    phase: str  # 'goal_generation', 'code_generation', 'validation', 'testing', 'discovery_creation'
    state_data: Dict[str, Any] = field(default_factory=dict)
    progress_percentage: float = 0.0
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)  # CPU, memory, time
    errors: List[str] = field(default_factory=list)


@dataclass
class SessionTrajectory:
    """Complete trajectory of an exploration session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    checkpoints: List[SessionCheckpoint] = field(default_factory=list)
    cua_trajectory_path: Optional[str] = None  # Path to CUA trajectory file
    total_duration: Optional[float] = None
    resource_totals: Dict[str, float] = field(default_factory=dict)
    outcome: Optional[str] = None  # 'completed', 'failed', 'cancelled'
    discoveries_created: int = 0
    quality_metrics: Dict[str, float] = field(default_factory=dict)


class SparkTrajectoryCallback(BaseCallback if CUA_AVAILABLE else object):
    """Custom callback for Spark-specific trajectory recording."""
    
    def __init__(self, session_manager: 'SessionManager', session_id: str):
        if CUA_AVAILABLE:
            super().__init__()
        self.session_manager = session_manager
        self.session_id = session_id
        self.step_count = 0
    
    async def on_step_start(self, step_data: Dict[str, Any]):
        """Called at the start of each agent step."""
        if CUA_AVAILABLE:
            self.step_count += 1
            await self.session_manager.record_step(
                self.session_id, 
                'agent_step_start', 
                {
                    'step_number': self.step_count,
                    'step_data': step_data,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    async def on_step_end(self, step_result: Dict[str, Any]):
        """Called at the end of each agent step."""
        if CUA_AVAILABLE:
            await self.session_manager.record_step(
                self.session_id,
                'agent_step_end',
                {
                    'step_number': self.step_count,
                    'result': step_result,
                    'timestamp': datetime.now().isoformat()
                }
            )


class SessionManager:
    """Manages exploration sessions with comprehensive trajectory recording."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize SessionManager.
        
        Args:
            storage_dir: Directory for storing session data and trajectories
        """
        self.storage_dir = storage_dir or Path.home() / ".spark" / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Active sessions tracking
        self.active_sessions: Dict[str, SessionTrajectory] = {}
        self.session_callbacks: Dict[str, List[Callable]] = {}
        
        # Performance monitoring
        self.resource_monitors: Dict[str, asyncio.Task] = {}
        
        # CUA trajectory integration
        self.cua_trajectory_dir = self.storage_dir / "trajectories"
        self.cua_trajectory_dir.mkdir(exist_ok=True)
    
    async def start_session_recording(
        self,
        session: ExplorationSession,
        enable_cua_trajectory: bool = True,
        checkpoint_interval: int = 30  # seconds
    ) -> SessionTrajectory:
        """
        Start comprehensive recording for an exploration session.
        
        Args:
            session: The exploration session to record
            enable_cua_trajectory: Whether to enable CUA trajectory recording
            checkpoint_interval: Interval for automatic checkpoints
            
        Returns:
            SessionTrajectory instance for the session
        """
        
        session_id = session.id
        trajectory = SessionTrajectory(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        # Store in active sessions
        self.active_sessions[session_id] = trajectory
        self.session_callbacks[session_id] = []
        
        # Create initial checkpoint
        initial_checkpoint = SessionCheckpoint(
            id=str(uuid.uuid4()),
            session_id=session_id,
            timestamp=datetime.now(),
            phase='session_start',
            state_data={
                'goal': session.goal,
                'initiated_by': session.initiated_by,
                'time_limit': session.time_limit,
                'approach_count': session.approach_count,
                'risk_tolerance': session.risk_tolerance
            },
            progress_percentage=0.0
        )
        
        trajectory.checkpoints.append(initial_checkpoint)
        
        # Set up CUA trajectory recording if enabled
        if enable_cua_trajectory and CUA_AVAILABLE:
            trajectory.cua_trajectory_path = str(
                self.cua_trajectory_dir / f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        
        # Start resource monitoring
        if session_id not in self.resource_monitors:
            self.resource_monitors[session_id] = asyncio.create_task(
                self._monitor_session_resources(session_id, checkpoint_interval)
            )
        
        # Save initial state
        await self._save_trajectory(trajectory)
        
        return trajectory
    
    async def create_checkpoint(
        self,
        session_id: str,
        phase: str,
        state_data: Dict[str, Any],
        progress_percentage: float = None,
        intermediate_results: List[Dict[str, Any]] = None,
        errors: List[str] = None
    ) -> SessionCheckpoint:
        """Create a checkpoint in the exploration session."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found in active sessions")
        
        trajectory = self.active_sessions[session_id]
        
        # Calculate progress if not provided
        if progress_percentage is None:
            phase_progress_mapping = {
                'goal_generation': 20,
                'code_generation': 50,
                'validation': 70,
                'testing': 85,
                'discovery_creation': 100
            }
            progress_percentage = phase_progress_mapping.get(phase, 50)
        
        # Monitor resource usage
        resource_usage = await self._get_current_resource_usage()
        
        checkpoint = SessionCheckpoint(
            id=str(uuid.uuid4()),
            session_id=session_id,
            timestamp=datetime.now(),
            phase=phase,
            state_data=state_data or {},
            progress_percentage=progress_percentage,
            intermediate_results=intermediate_results or [],
            resource_usage=resource_usage,
            errors=errors or []
        )
        
        trajectory.checkpoints.append(checkpoint)
        
        # Notify callbacks
        await self._notify_checkpoint_callbacks(session_id, checkpoint)
        
        # Save updated trajectory
        await self._save_trajectory(trajectory)
        
        return checkpoint
    
    async def record_step(self, session_id: str, step_type: str, step_data: Dict[str, Any]):
        """Record a detailed step within a session phase."""
        
        if session_id not in self.active_sessions:
            return  # Silently ignore if session not active
        
        trajectory = self.active_sessions[session_id]
        
        # Add step data to the current checkpoint or create a micro-checkpoint
        current_checkpoint = trajectory.checkpoints[-1] if trajectory.checkpoints else None
        
        step_record = {
            'step_type': step_type,
            'timestamp': datetime.now().isoformat(),
            'data': step_data
        }
        
        if current_checkpoint:
            # Add to intermediate results of current checkpoint
            current_checkpoint.intermediate_results.append(step_record)
        else:
            # Create a micro-checkpoint for the step
            await self.create_checkpoint(
                session_id=session_id,
                phase='step_recording',
                state_data={'step': step_record},
                intermediate_results=[step_record]
            )
    
    async def complete_session_recording(
        self,
        session_id: str,
        outcome: str,
        final_results: Optional[List[ExplorationResult]] = None,
        discoveries_count: int = 0
    ) -> SessionTrajectory:
        """Complete the recording for an exploration session."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found in active sessions")
        
        trajectory = self.active_sessions[session_id]
        trajectory.end_time = datetime.now()
        trajectory.total_duration = (trajectory.end_time - trajectory.start_time).total_seconds()
        trajectory.outcome = outcome
        trajectory.discoveries_created = discoveries_count
        
        # Calculate quality metrics
        trajectory.quality_metrics = await self._calculate_session_metrics(trajectory, final_results)
        
        # Create final checkpoint
        final_checkpoint = SessionCheckpoint(
            id=str(uuid.uuid4()),
            session_id=session_id,
            timestamp=trajectory.end_time,
            phase='session_complete',
            state_data={
                'outcome': outcome,
                'total_duration': trajectory.total_duration,
                'discoveries_created': discoveries_count,
                'quality_metrics': trajectory.quality_metrics
            },
            progress_percentage=100.0,
            resource_usage=await self._get_current_resource_usage()
        )
        
        trajectory.checkpoints.append(final_checkpoint)
        
        # Stop resource monitoring
        if session_id in self.resource_monitors:
            self.resource_monitors[session_id].cancel()
            del self.resource_monitors[session_id]
        
        # Final save
        await self._save_trajectory(trajectory)
        
        # Move from active to archived
        archived_trajectory = trajectory
        del self.active_sessions[session_id]
        if session_id in self.session_callbacks:
            del self.session_callbacks[session_id]
        
        return archived_trajectory
    
    async def get_session_trajectory(self, session_id: str) -> Optional[SessionTrajectory]:
        """Get the trajectory for a session (active or archived)."""
        
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from storage
        return await self._load_trajectory(session_id)
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a session."""
        
        trajectory = await self.get_session_trajectory(session_id)
        if not trajectory:
            return {'error': f'Session {session_id} not found'}
        
        analytics = {
            'session_id': session_id,
            'duration': trajectory.total_duration,
            'outcome': trajectory.outcome,
            'checkpoints_count': len(trajectory.checkpoints),
            'discoveries_created': trajectory.discoveries_created,
            'quality_metrics': trajectory.quality_metrics,
            'resource_usage': trajectory.resource_totals,
            'timeline': []
        }
        
        # Build timeline from checkpoints
        for checkpoint in trajectory.checkpoints:
            analytics['timeline'].append({
                'timestamp': checkpoint.timestamp.isoformat(),
                'phase': checkpoint.phase,
                'progress': checkpoint.progress_percentage,
                'errors_count': len(checkpoint.errors),
                'resource_usage': checkpoint.resource_usage
            })
        
        # Phase duration analysis
        phase_durations = {}
        prev_checkpoint = None
        for checkpoint in trajectory.checkpoints:
            if prev_checkpoint:
                duration = (checkpoint.timestamp - prev_checkpoint.timestamp).total_seconds()
                phase_durations[checkpoint.phase] = duration
            prev_checkpoint = checkpoint
        
        analytics['phase_durations'] = phase_durations
        
        return analytics
    
    def add_session_callback(self, session_id: str, callback: Callable[[SessionCheckpoint], None]):
        """Add a callback for session checkpoint events."""
        if session_id not in self.session_callbacks:
            self.session_callbacks[session_id] = []
        self.session_callbacks[session_id].append(callback)
    
    def get_cua_trajectory_callback(self, session_id: str) -> Optional['SparkTrajectoryCallback']:
        """Get a CUA trajectory callback for the session."""
        if not CUA_AVAILABLE:
            return None
        return SparkTrajectoryCallback(self, session_id)
    
    async def _monitor_session_resources(self, session_id: str, interval: int):
        """Monitor resource usage for a session."""
        try:
            while session_id in self.active_sessions:
                resource_usage = await self._get_current_resource_usage()
                
                # Store resource totals
                trajectory = self.active_sessions[session_id]
                for metric, value in resource_usage.items():
                    if metric not in trajectory.resource_totals:
                        trajectory.resource_totals[metric] = 0
                    trajectory.resource_totals[metric] += value
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass  # Normal cancellation
    
    async def _get_current_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage metrics."""
        import psutil
        
        try:
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'threads_count': process.num_threads()
            }
        except Exception:
            return {'cpu_percent': 0.0, 'memory_mb': 0.0, 'threads_count': 1}
    
    async def _calculate_session_metrics(
        self,
        trajectory: SessionTrajectory,
        results: Optional[List[ExplorationResult]]
    ) -> Dict[str, float]:
        """Calculate quality metrics for a completed session."""
        
        metrics = {
            'completion_rate': 1.0 if trajectory.outcome == 'completed' else 0.0,
            'efficiency_score': 0.0,
            'error_rate': 0.0,
            'discovery_rate': 0.0
        }
        
        if trajectory.total_duration and trajectory.total_duration > 0:
            # Efficiency: discoveries per minute
            metrics['discovery_rate'] = trajectory.discoveries_created / (trajectory.total_duration / 60)
            
            # Error rate: errors per checkpoint
            total_errors = sum(len(cp.errors) for cp in trajectory.checkpoints)
            metrics['error_rate'] = total_errors / len(trajectory.checkpoints) if trajectory.checkpoints else 0
        
        # Results-based metrics
        if results:
            successful_results = [r for r in results if r.success]
            metrics['success_rate'] = len(successful_results) / len(results)
            
            # Average execution time
            avg_execution_time = sum(r.execution_time for r in results) / len(results)
            metrics['avg_execution_time'] = avg_execution_time
        
        return metrics
    
    async def _save_trajectory(self, trajectory: SessionTrajectory):
        """Save trajectory to persistent storage."""
        trajectory_file = self.storage_dir / f"trajectory_{trajectory.session_id}.json"
        
        # Convert to serializable format
        trajectory_dict = asdict(trajectory)
        
        # Handle datetime serialization
        for checkpoint_dict in trajectory_dict['checkpoints']:
            checkpoint_dict['timestamp'] = checkpoint_dict['timestamp'].isoformat()
        
        trajectory_dict['start_time'] = trajectory_dict['start_time'].isoformat()
        if trajectory_dict['end_time']:
            trajectory_dict['end_time'] = trajectory_dict['end_time'].isoformat()
        
        with open(trajectory_file, 'w') as f:
            json.dump(trajectory_dict, f, indent=2)
    
    async def _load_trajectory(self, session_id: str) -> Optional[SessionTrajectory]:
        """Load trajectory from persistent storage."""
        trajectory_file = self.storage_dir / f"trajectory_{session_id}.json"
        
        if not trajectory_file.exists():
            return None
        
        try:
            with open(trajectory_file, 'r') as f:
                trajectory_dict = json.load(f)
            
            # Handle datetime deserialization
            trajectory_dict['start_time'] = datetime.fromisoformat(trajectory_dict['start_time'])
            if trajectory_dict['end_time']:
                trajectory_dict['end_time'] = datetime.fromisoformat(trajectory_dict['end_time'])
            
            for checkpoint_dict in trajectory_dict['checkpoints']:
                checkpoint_dict['timestamp'] = datetime.fromisoformat(checkpoint_dict['timestamp'])
            
            # Reconstruct objects
            checkpoints = [
                SessionCheckpoint(**cp_dict) for cp_dict in trajectory_dict['checkpoints']
            ]
            trajectory_dict['checkpoints'] = checkpoints
            
            return SessionTrajectory(**trajectory_dict)
            
        except Exception as e:
            print(f"Error loading trajectory for session {session_id}: {e}")
            return None
    
    async def _notify_checkpoint_callbacks(self, session_id: str, checkpoint: SessionCheckpoint):
        """Notify all callbacks for a session checkpoint."""
        if session_id in self.session_callbacks:
            for callback in self.session_callbacks[session_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(checkpoint)
                    else:
                        callback(checkpoint)
                except Exception as e:
                    print(f"Session callback error: {e}")