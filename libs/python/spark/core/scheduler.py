"""
Exploration scheduling system with cron-like capabilities.

This module provides cross-platform scheduling for autonomous exploration sessions
with resource management and adaptive time control.
"""

import asyncio
import json
import uuid
import time
import platform
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging

from spark.core.config import SparkConfig


class ScheduleType(Enum):
    """Types of schedule patterns."""
    DAILY = "daily"           # Run every day at specific time
    WEEKDAYS = "weekdays"     # Run Monday-Friday only  
    WEEKENDS = "weekends"     # Run Saturday-Sunday only
    WEEKLY = "weekly"         # Run weekly on specific day
    INTERVAL = "interval"     # Run every N hours/minutes
    CRON = "cron"            # Full cron expression


class ScheduleStatus(Enum):
    """Status of scheduled tasks."""
    PENDING = "pending"       # Waiting to run
    RUNNING = "running"       # Currently executing
    COMPLETED = "completed"   # Finished successfully
    FAILED = "failed"         # Execution failed
    CANCELLED = "cancelled"   # Cancelled by user
    PAUSED = "paused"         # Temporarily paused


@dataclass
class ResourceLimits:
    """Resource limits for exploration sessions."""
    
    max_cpu_percent: float = 50.0      # Max CPU usage percentage
    max_memory_mb: int = 1024           # Max memory usage in MB
    max_duration_minutes: int = 120     # Max session duration
    max_concurrent_sessions: int = 1    # Max parallel sessions
    min_battery_percent: int = 30       # Min battery for laptop (0 = ignore)
    max_temperature_celsius: int = 70   # Max CPU temperature (0 = ignore)


@dataclass
class ScheduledTask:
    """A scheduled exploration task."""
    
    id: str
    name: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    
    # Task configuration
    task_function: Optional[Callable] = None
    task_args: Dict[str, Any] = field(default_factory=dict)
    
    # Resource management
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    # Schedule status
    status: ScheduleStatus = ScheduleStatus.PENDING
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    
    # Execution history
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Remove non-serializable function
        data.pop('task_function', None)
        # Convert datetime objects
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """Create from dictionary."""
        # Convert datetime strings back
        for key in ['next_run', 'last_run', 'created_at']:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        
        # Handle nested objects
        if 'resource_limits' in data and isinstance(data['resource_limits'], dict):
            data['resource_limits'] = ResourceLimits(**data['resource_limits'])
        
        # Convert enums
        if 'schedule_type' in data:
            data['schedule_type'] = ScheduleType(data['schedule_type'])
        if 'status' in data:
            data['status'] = ScheduleStatus(data['status'])
        
        return cls(**data)


class ResourceMonitor:
    """Monitors system resources for exploration scheduling."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_resources(self, limits: ResourceLimits) -> Dict[str, Any]:
        """Check current system resources against limits."""
        
        try:
            import psutil
        except ImportError:
            # Fallback if psutil not available
            self.logger.warning("psutil not available, using basic resource monitoring")
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'memory_mb': 0,
                'battery_percent': 100,
                'temperature_celsius': 0,
                'within_limits': True,
                'limiting_factors': []
            }
        
        # Get current resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Battery status (may not be available on desktop)
        battery_percent = 100
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
        except (AttributeError, OSError):
            pass
        
        # Temperature (may not be available on all systems)
        temperature_celsius = 0
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get first available CPU temperature
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        if entries:
                            temperature_celsius = entries[0].current
                            break
        except (AttributeError, OSError):
            pass
        
        # Check limits
        limiting_factors = []
        
        if cpu_percent > limits.max_cpu_percent:
            limiting_factors.append(f"CPU usage ({cpu_percent:.1f}% > {limits.max_cpu_percent}%)")
        
        if memory.used // (1024 * 1024) > limits.max_memory_mb:
            limiting_factors.append(f"Memory usage ({memory.used // (1024 * 1024)}MB > {limits.max_memory_mb}MB)")
        
        if limits.min_battery_percent > 0 and battery_percent < limits.min_battery_percent:
            limiting_factors.append(f"Battery low ({battery_percent}% < {limits.min_battery_percent}%)")
        
        if limits.max_temperature_celsius > 0 and temperature_celsius > limits.max_temperature_celsius:
            limiting_factors.append(f"Temperature high ({temperature_celsius}°C > {limits.max_temperature_celsius}°C)")
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_mb': memory.used // (1024 * 1024),
            'battery_percent': battery_percent,
            'temperature_celsius': temperature_celsius,
            'within_limits': len(limiting_factors) == 0,
            'limiting_factors': limiting_factors
        }
    
    async def wait_for_resources(self, limits: ResourceLimits, timeout_minutes: int = 10) -> bool:
        """Wait for resources to become available within timeout."""
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            resources = await self.check_resources(limits)
            
            if resources['within_limits']:
                return True
            
            self.logger.info(f"Waiting for resources: {', '.join(resources['limiting_factors'])}")
            await asyncio.sleep(30)  # Check every 30 seconds
        
        return False


class SessionManager:
    """Manages active exploration sessions."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    async def start_session(
        self,
        session_id: str,
        task: ScheduledTask,
        task_function: Callable,
        task_args: Dict[str, Any]
    ) -> bool:
        """Start an exploration session."""
        
        # Check concurrent session limits
        if len(self.active_sessions) >= task.resource_limits.max_concurrent_sessions:
            self.logger.warning(f"Cannot start session {session_id}: concurrent limit reached")
            return False
        
        session_info = {
            'session_id': session_id,
            'task_id': task.id,
            'task_name': task.name,
            'start_time': datetime.now(),
            'status': 'running',
            'progress': 0.0,
            'resource_limits': task.resource_limits,
            'task_function': task_function,
            'task_args': task_args
        }
        
        self.active_sessions[session_id] = session_info
        self.logger.info(f"Started exploration session: {session_id}")
        
        try:
            # Execute task in background
            asyncio.create_task(self._execute_session(session_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start session {session_id}: {e}")
            self.active_sessions.pop(session_id, None)
            return False
    
    async def _execute_session(self, session_id: str):
        """Execute a session with monitoring and timeout."""
        
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return
        
        start_time = time.time()
        max_duration = session_info['resource_limits'].max_duration_minutes * 60
        
        try:
            # Execute the task function
            task_function = session_info['task_function']
            task_args = session_info['task_args']
            
            # Run with timeout
            result = await asyncio.wait_for(
                task_function(**task_args),
                timeout=max_duration
            )
            
            # Session completed successfully
            end_time = time.time()
            session_info.update({
                'status': 'completed',
                'end_time': datetime.now(),
                'duration_seconds': end_time - start_time,
                'result': result
            })
            
            self.logger.info(f"Session {session_id} completed successfully")
            
        except asyncio.TimeoutError:
            session_info.update({
                'status': 'timeout',
                'end_time': datetime.now(),
                'duration_seconds': time.time() - start_time,
                'error': 'Session exceeded maximum duration'
            })
            self.logger.warning(f"Session {session_id} timed out")
            
        except Exception as e:
            session_info.update({
                'status': 'failed',
                'end_time': datetime.now(),
                'duration_seconds': time.time() - start_time,
                'error': str(e)
            })
            self.logger.error(f"Session {session_id} failed: {e}")
        
        finally:
            # Move to history and remove from active
            history_entry = session_info.copy()
            history_entry.pop('task_function', None)  # Remove non-serializable function
            self.session_history.append(history_entry)
            self.active_sessions.pop(session_id, None)
    
    async def stop_session(self, session_id: str) -> bool:
        """Stop an active session."""
        
        if session_id not in self.active_sessions:
            return False
        
        session_info = self.active_sessions[session_id]
        session_info.update({
            'status': 'cancelled',
            'end_time': datetime.now()
        })
        
        # Move to history
        history_entry = session_info.copy()
        history_entry.pop('task_function', None)
        self.session_history.append(history_entry)
        self.active_sessions.pop(session_id)
        
        self.logger.info(f"Stopped session: {session_id}")
        return True
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active sessions."""
        sessions = []
        for session in self.active_sessions.values():
            session_copy = session.copy()
            session_copy.pop('task_function', None)  # Remove non-serializable function
            sessions.append(session_copy)
        return sessions
    
    def get_session_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get session execution history."""
        return self.session_history[-limit:]


class ExplorationScheduler:
    """Main scheduler for autonomous exploration sessions."""
    
    def __init__(self, config: Optional[SparkConfig] = None):
        self.config = config or SparkConfig()
        self.tasks: Dict[str, ScheduledTask] = {}
        self.resource_monitor = ResourceMonitor()
        self.session_manager = SessionManager()
        self.logger = logging.getLogger(__name__)
        
        # Scheduler state
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Task registry
        self.task_functions: Dict[str, Callable] = {}
        
        # Persistence
        self.storage_path = Path.home() / ".spark" / "scheduler.json"
        self.storage_path.parent.mkdir(exist_ok=True)
        
        # Load persisted tasks
        self._load_tasks()
    
    def register_task_function(self, name: str, function: Callable):
        """Register a function that can be called by scheduled tasks."""
        self.task_functions[name] = function
        self.logger.info(f"Registered task function: {name}")
    
    async def add_task(
        self,
        name: str,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        task_function_name: str,
        task_args: Dict[str, Any] = None,
        resource_limits: ResourceLimits = None
    ) -> str:
        """Add a new scheduled task."""
        
        task_id = str(uuid.uuid4())
        # Persist the task function name inside task_args so executor can find it
        args = dict(task_args or {})
        if task_function_name:
            args['task_function_name'] = task_function_name

        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            task_args=args,
            resource_limits=resource_limits or ResourceLimits()
        )
        
        # Calculate next run time
        task.next_run = self._calculate_next_run(task)
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        self.logger.info(f"Added scheduled task: {name} ({task_id})")
        return task_id
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Cancel if currently running
        active_sessions = self.session_manager.get_active_sessions()
        for session in active_sessions:
            if session['task_id'] == task_id:
                await self.session_manager.stop_session(session['session_id'])
        
        del self.tasks[task_id]
        self._save_tasks()
        
        self.logger.info(f"Removed scheduled task: {task.name} ({task_id})")
        return True
    
    async def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task."""
        
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].status = ScheduleStatus.PAUSED
        self._save_tasks()
        return True
    
    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status == ScheduleStatus.PAUSED:
            task.status = ScheduleStatus.PENDING
            task.next_run = self._calculate_next_run(task)
            self._save_tasks()
            return True
        
        return False
    
    async def start_scheduler(self):
        """Start the scheduler main loop."""
        
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Exploration scheduler started")
    
    async def stop_scheduler(self):
        """Stop the scheduler main loop."""
        
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Stop all active sessions
        for session_id in list(self.session_manager.active_sessions.keys()):
            await self.session_manager.stop_session(session_id)
        
        self.logger.info("Exploration scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        
        self.logger.info("Scheduler loop started")
        
        try:
            while self.is_running:
                # Check for tasks ready to run
                await self._check_and_run_tasks()
                
                # Wait before next check (every minute)
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            self.logger.info("Scheduler loop cancelled")
        except Exception as e:
            self.logger.error(f"Scheduler loop error: {e}")
    
    async def _check_and_run_tasks(self):
        """Check for tasks that should run and execute them."""
        
        now = datetime.now()
        
        for task_id, task in self.tasks.items():
            # Skip if paused or not scheduled
            if task.status == ScheduleStatus.PAUSED:
                continue
            
            # Skip if not time to run yet
            if not task.next_run or now < task.next_run:
                continue
            
            # Skip if already running
            active_sessions = self.session_manager.get_active_sessions()
            if any(s['task_id'] == task_id for s in active_sessions):
                continue
            
            # Check if task function is available
            task_function_name = task.task_args.get('task_function_name')
            if not task_function_name or task_function_name not in self.task_functions:
                self.logger.warning(f"Task function not found for task {task.name}: {task_function_name}")
                continue
            
            # Check resource availability
            resources = await self.resource_monitor.check_resources(task.resource_limits)
            if not resources['within_limits']:
                self.logger.info(f"Delaying task {task.name} due to resource constraints: {', '.join(resources['limiting_factors'])}")
                # Reschedule for 10 minutes later
                task.next_run = now + timedelta(minutes=10)
                continue
            
            # Execute the task
            await self._execute_task(task)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        
        session_id = f"scheduled_{task.id}_{int(time.time())}"
        task_function_name = task.task_args.get('task_function_name')
        task_function = self.task_functions.get(task_function_name)
        
        if not task_function:
            self.logger.error(f"Task function not found: {task_function_name}")
            return
        
        self.logger.info(f"Executing scheduled task: {task.name}")
        
        # Update task status
        task.status = ScheduleStatus.RUNNING
        task.last_run = datetime.now()
        task.run_count += 1
        
        # Start session
        success = await self.session_manager.start_session(
            session_id=session_id,
            task=task,
            task_function=task_function,
            task_args=task.task_args
        )
        
        if success:
            # Calculate next run time
            task.next_run = self._calculate_next_run(task)
            task.status = ScheduleStatus.PENDING
        else:
            task.failure_count += 1
            task.status = ScheduleStatus.FAILED
            
            # Backoff on failures
            backoff_minutes = min(60, task.failure_count * 10)
            task.next_run = datetime.now() + timedelta(minutes=backoff_minutes)
        
        self._save_tasks()
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate the next run time for a task."""
        
        now = datetime.now()
        config = task.schedule_config
        
        if task.schedule_type == ScheduleType.DAILY:
            hour = config.get('hour', 2)  # Default 2 AM
            minute = config.get('minute', 0)
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            
            return next_run
        
        elif task.schedule_type == ScheduleType.WEEKDAYS:
            hour = config.get('hour', 2)
            minute = config.get('minute', 0)
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Find next weekday
            while next_run <= now or next_run.weekday() >= 5:  # 0=Monday, 6=Sunday
                next_run += timedelta(days=1)
            
            return next_run
        
        elif task.schedule_type == ScheduleType.WEEKENDS:
            hour = config.get('hour', 10)  # Default 10 AM on weekends
            minute = config.get('minute', 0)
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Find next weekend day
            while next_run <= now or next_run.weekday() < 5:
                next_run += timedelta(days=1)
            
            return next_run
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            day_of_week = config.get('day_of_week', 0)  # Monday
            hour = config.get('hour', 2)
            minute = config.get('minute', 0)
            
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return next_run
        
        elif task.schedule_type == ScheduleType.INTERVAL:
            interval_minutes = config.get('interval_minutes', 60)
            return now + timedelta(minutes=interval_minutes)
        
        # For now, CRON is not fully implemented
        elif task.schedule_type == ScheduleType.CRON:
            # Simple fallback - daily at 2 AM
            return self._calculate_next_run(ScheduledTask(
                id=task.id,
                name=task.name,
                schedule_type=ScheduleType.DAILY,
                schedule_config={'hour': 2, 'minute': 0}
            ))
        
        return None
    
    def _save_tasks(self):
        """Persist tasks to storage."""
        
        try:
            tasks_data = {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(tasks_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    def _load_tasks(self):
        """Load tasks from storage."""
        
        try:
            if not self.storage_path.exists():
                return
            
            with open(self.storage_path, 'r') as f:
                tasks_data = json.load(f)
            
            for task_id, task_dict in tasks_data.items():
                try:
                    task = ScheduledTask.from_dict(task_dict)
                    self.tasks[task_id] = task
                except Exception as e:
                    self.logger.error(f"Failed to load task {task_id}: {e}")
                    
            self.logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
            
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
    
    def get_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks."""
        return list(self.tasks.values())
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a specific task."""
        return self.tasks.get(task_id)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        
        active_sessions = self.session_manager.get_active_sessions()
        
        return {
            'is_running': self.is_running,
            'total_tasks': len(self.tasks),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == ScheduleStatus.PENDING]),
            'paused_tasks': len([t for t in self.tasks.values() if t.status == ScheduleStatus.PAUSED]),
            'active_sessions': len(active_sessions),
            'scheduler_info': {
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'storage_path': str(self.storage_path)
            }
        }
