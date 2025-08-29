"""
Error recovery and graceful termination system for exploration sessions.

This module provides comprehensive error handling, recovery strategies,
and graceful termination capabilities for autonomous exploration sessions.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import traceback

from spark.discovery.models import ExplorationSession, ExplorationResult, ExplorationStatus
from spark.core.session_manager import SessionManager, SessionCheckpoint


class ErrorSeverity(Enum):
    """Severity levels for exploration errors."""
    LOW = "low"           # Minor warnings, continue normally
    MEDIUM = "medium"     # Retry with backoff
    HIGH = "high"         # Fallback to alternative approach
    CRITICAL = "critical" # Terminate session gracefully


class RecoveryAction(Enum):
    """Available recovery actions."""
    RETRY = "retry"                    # Retry the same operation
    RETRY_WITH_BACKOFF = "retry_backoff"  # Retry with exponential backoff
    FALLBACK_APPROACH = "fallback"     # Switch to alternative approach
    SKIP_AND_CONTINUE = "skip"         # Skip current operation and continue
    GRACEFUL_TERMINATE = "terminate"   # End session gracefully
    EMERGENCY_STOP = "emergency_stop"  # Immediate termination


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    id: str
    session_id: str
    timestamp: datetime
    phase: str
    error_type: str
    error_message: str
    stack_trace: str
    severity: ErrorSeverity
    recovery_action: Optional[RecoveryAction] = None
    retry_count: int = 0
    context_data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


@dataclass
class RecoveryStrategy:
    """Strategy for handling specific error types."""
    error_pattern: str  # Regex pattern to match error messages
    severity: ErrorSeverity
    max_retries: int
    backoff_multiplier: float = 2.0
    initial_delay: float = 1.0
    recovery_actions: List[RecoveryAction] = field(default_factory=list)
    custom_handler: Optional[Callable] = None


class ErrorRecoveryManager:
    """Manages error recovery and graceful termination for exploration sessions."""
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize ErrorRecoveryManager.
        
        Args:
            session_manager: SessionManager instance for session operations
        """
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.error_records: Dict[str, List[ErrorRecord]] = {}  # session_id -> errors
        self.recovery_strategies: List[RecoveryStrategy] = []
        
        # Session recovery state
        self.session_recovery_state: Dict[str, Dict[str, Any]] = {}
        
        # Termination callbacks
        self.termination_callbacks: List[Callable[[str, str], None]] = []
        
        # Resource cleanup handlers
        self.cleanup_handlers: List[Callable[[str], None]] = []
        
        # Initialize default recovery strategies
        self._setup_default_recovery_strategies()
    
    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies for common error patterns."""
        
        # Network/API errors - retry with backoff
        self.recovery_strategies.append(RecoveryStrategy(
            error_pattern=r"(timeout|connection|network|api)",
            severity=ErrorSeverity.MEDIUM,
            max_retries=3,
            backoff_multiplier=2.0,
            initial_delay=5.0,
            recovery_actions=[RecoveryAction.RETRY_WITH_BACKOFF, RecoveryAction.FALLBACK_APPROACH]
        ))
        
        # Rate limiting - wait and retry
        self.recovery_strategies.append(RecoveryStrategy(
            error_pattern=r"(rate.?limit|too.?many.?requests)",
            severity=ErrorSeverity.MEDIUM,
            max_retries=5,
            backoff_multiplier=3.0,
            initial_delay=60.0,
            recovery_actions=[RecoveryAction.RETRY_WITH_BACKOFF]
        ))
        
        # Resource exhaustion - graceful termination
        self.recovery_strategies.append(RecoveryStrategy(
            error_pattern=r"(out.?of.?memory|disk.?full|resource.?exhausted)",
            severity=ErrorSeverity.CRITICAL,
            max_retries=1,
            recovery_actions=[RecoveryAction.GRACEFUL_TERMINATE]
        ))
        
        # Code generation/validation errors - try alternative approach
        self.recovery_strategies.append(RecoveryStrategy(
            error_pattern=r"(generation.?failed|validation.?error|syntax.?error)",
            severity=ErrorSeverity.MEDIUM,
            max_retries=2,
            recovery_actions=[RecoveryAction.FALLBACK_APPROACH, RecoveryAction.SKIP_AND_CONTINUE]
        ))
        
        # Authentication/permission errors - terminate
        self.recovery_strategies.append(RecoveryStrategy(
            error_pattern=r"(auth|permission|unauthorized|forbidden)",
            severity=ErrorSeverity.HIGH,
            max_retries=1,
            recovery_actions=[RecoveryAction.GRACEFUL_TERMINATE]
        ))
    
    async def handle_error(
        self,
        session_id: str,
        phase: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryAction:
        """
        Handle an error that occurred during exploration.
        
        Args:
            session_id: Session where error occurred
            phase: Current exploration phase
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            RecoveryAction to take
        """
        
        # Create error record
        error_record = ErrorRecord(
            id=f"err_{session_id}_{int(time.time())}",
            session_id=session_id,
            timestamp=datetime.now(),
            phase=phase,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            severity=ErrorSeverity.MEDIUM,  # Will be updated by strategy
            context_data=context or {}
        )
        
        # Store error record
        if session_id not in self.error_records:
            self.error_records[session_id] = []
        self.error_records[session_id].append(error_record)
        
        # Find appropriate recovery strategy
        strategy = self._find_recovery_strategy(error_record)
        if strategy:
            error_record.severity = strategy.severity
            error_record.recovery_action = strategy.recovery_actions[0] if strategy.recovery_actions else RecoveryAction.SKIP_AND_CONTINUE
        else:
            # Default strategy for unmatched errors
            error_record.recovery_action = RecoveryAction.SKIP_AND_CONTINUE
        
        # Log error
        self.logger.error(f"Session {session_id} error in {phase}: {error_record.error_message}")
        
        # Update session checkpoint with error
        await self.session_manager.create_checkpoint(
            session_id=session_id,
            phase=f"{phase}_error_handling",
            state_data={
                'error_id': error_record.id,
                'error_type': error_record.error_type,
                'error_message': error_record.error_message,
                'recovery_action': error_record.recovery_action.value
            },
            errors=[error_record.error_message]
        )
        
        # Execute recovery action
        await self._execute_recovery_action(session_id, error_record, strategy)
        
        return error_record.recovery_action
    
    async def _execute_recovery_action(
        self,
        session_id: str,
        error_record: ErrorRecord,
        strategy: Optional[RecoveryStrategy]
    ):
        """Execute the determined recovery action."""
        
        action = error_record.recovery_action
        
        if action == RecoveryAction.RETRY:
            await self._handle_retry(session_id, error_record, strategy)
        
        elif action == RecoveryAction.RETRY_WITH_BACKOFF:
            await self._handle_retry_with_backoff(session_id, error_record, strategy)
        
        elif action == RecoveryAction.FALLBACK_APPROACH:
            await self._handle_fallback_approach(session_id, error_record)
        
        elif action == RecoveryAction.SKIP_AND_CONTINUE:
            await self._handle_skip_and_continue(session_id, error_record)
        
        elif action == RecoveryAction.GRACEFUL_TERMINATE:
            await self._handle_graceful_termination(session_id, error_record)
        
        elif action == RecoveryAction.EMERGENCY_STOP:
            await self._handle_emergency_stop(session_id, error_record)
    
    async def _handle_retry(self, session_id: str, error_record: ErrorRecord, strategy: Optional[RecoveryStrategy]):
        """Handle simple retry recovery action."""
        
        if not strategy or error_record.retry_count >= strategy.max_retries:
            # Max retries reached, try next recovery action or skip
            await self._escalate_recovery(session_id, error_record, strategy)
            return
        
        error_record.retry_count += 1
        self.logger.info(f"Retrying operation for session {session_id}, attempt {error_record.retry_count}")
        
        # The actual retry will be handled by the calling code
        # We just track the attempt here
    
    async def _handle_retry_with_backoff(
        self,
        session_id: str,
        error_record: ErrorRecord,
        strategy: Optional[RecoveryStrategy]
    ):
        """Handle retry with exponential backoff."""
        
        if not strategy or error_record.retry_count >= strategy.max_retries:
            await self._escalate_recovery(session_id, error_record, strategy)
            return
        
        # Calculate backoff delay
        delay = strategy.initial_delay * (strategy.backoff_multiplier ** error_record.retry_count)
        
        error_record.retry_count += 1
        self.logger.info(f"Retrying with backoff for session {session_id}, attempt {error_record.retry_count}, delay {delay}s")
        
        # Wait before retry
        await asyncio.sleep(delay)
    
    async def _handle_fallback_approach(self, session_id: str, error_record: ErrorRecord):
        """Handle fallback to alternative approach."""
        
        self.logger.info(f"Using fallback approach for session {session_id}")
        
        # Initialize recovery state if not exists
        if session_id not in self.session_recovery_state:
            self.session_recovery_state[session_id] = {
                'fallback_attempts': 0,
                'original_approach': None,
                'fallback_approaches': []
            }
        
        recovery_state = self.session_recovery_state[session_id]
        recovery_state['fallback_attempts'] += 1
        
        # Update session checkpoint
        await self.session_manager.create_checkpoint(
            session_id=session_id,
            phase="fallback_approach",
            state_data={
                'fallback_attempt': recovery_state['fallback_attempts'],
                'reason': error_record.error_message
            }
        )
    
    async def _handle_skip_and_continue(self, session_id: str, error_record: ErrorRecord):
        """Handle skipping current operation and continuing."""
        
        self.logger.info(f"Skipping operation and continuing for session {session_id}")
        
        await self.session_manager.create_checkpoint(
            session_id=session_id,
            phase="skip_operation",
            state_data={
                'skipped_phase': error_record.phase,
                'reason': error_record.error_message
            }
        )
        
        error_record.resolved = True
    
    async def _handle_graceful_termination(self, session_id: str, error_record: ErrorRecord):
        """Handle graceful session termination."""
        
        self.logger.warning(f"Initiating graceful termination for session {session_id}")
        
        # Create termination checkpoint
        await self.session_manager.create_checkpoint(
            session_id=session_id,
            phase="graceful_termination",
            state_data={
                'termination_reason': error_record.error_message,
                'error_severity': error_record.severity.value
            },
            progress_percentage=100.0
        )
        
        # Run cleanup handlers
        await self._run_cleanup_handlers(session_id)
        
        # Complete session recording
        await self.session_manager.complete_session_recording(
            session_id=session_id,
            outcome="terminated_gracefully",
            final_results=None,
            discoveries_count=0
        )
        
        # Notify termination callbacks
        await self._notify_termination_callbacks(session_id, "graceful")
        
        error_record.resolved = True
    
    async def _handle_emergency_stop(self, session_id: str, error_record: ErrorRecord):
        """Handle emergency session termination."""
        
        self.logger.error(f"Emergency stop for session {session_id}")
        
        # Run critical cleanup only
        await self._run_cleanup_handlers(session_id, emergency=True)
        
        # Mark session as failed
        try:
            await self.session_manager.complete_session_recording(
                session_id=session_id,
                outcome="emergency_stopped",
                final_results=None,
                discoveries_count=0
            )
        except Exception as cleanup_error:
            self.logger.error(f"Failed to complete session recording during emergency stop: {cleanup_error}")
        
        # Notify termination callbacks
        await self._notify_termination_callbacks(session_id, "emergency")
        
        error_record.resolved = True
    
    async def _escalate_recovery(
        self,
        session_id: str,
        error_record: ErrorRecord,
        strategy: Optional[RecoveryStrategy]
    ):
        """Escalate to next recovery action when current one fails."""
        
        if strategy and len(strategy.recovery_actions) > 1:
            # Try next recovery action
            next_action = strategy.recovery_actions[1]
            error_record.recovery_action = next_action
            error_record.retry_count = 0  # Reset retry count for new action
            await self._execute_recovery_action(session_id, error_record, strategy)
        else:
            # No more recovery options, graceful terminate
            error_record.recovery_action = RecoveryAction.GRACEFUL_TERMINATE
            await self._handle_graceful_termination(session_id, error_record)
    
    def _find_recovery_strategy(self, error_record: ErrorRecord) -> Optional[RecoveryStrategy]:
        """Find appropriate recovery strategy for an error."""
        
        import re
        
        error_text = f"{error_record.error_type} {error_record.error_message}".lower()
        
        for strategy in self.recovery_strategies:
            if re.search(strategy.error_pattern, error_text, re.IGNORECASE):
                return strategy
        
        return None
    
    async def _run_cleanup_handlers(self, session_id: str, emergency: bool = False):
        """Run registered cleanup handlers for a session."""
        
        for handler in self.cleanup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(session_id)
                else:
                    handler(session_id)
            except Exception as e:
                if emergency:
                    # In emergency mode, don't let cleanup errors block termination
                    self.logger.error(f"Cleanup handler failed during emergency stop: {e}")
                else:
                    self.logger.error(f"Cleanup handler failed: {e}")
    
    async def _notify_termination_callbacks(self, session_id: str, termination_type: str):
        """Notify registered termination callbacks."""
        
        for callback in self.termination_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session_id, termination_type)
                else:
                    callback(session_id, termination_type)
            except Exception as e:
                self.logger.error(f"Termination callback failed: {e}")
    
    def add_recovery_strategy(self, strategy: RecoveryStrategy):
        """Add a custom recovery strategy."""
        self.recovery_strategies.append(strategy)
    
    def add_termination_callback(self, callback: Callable[[str, str], None]):
        """Add a callback to be notified when sessions terminate."""
        self.termination_callbacks.append(callback)
    
    def add_cleanup_handler(self, handler: Callable[[str], None]):
        """Add a cleanup handler to run during session termination."""
        self.cleanup_handlers.append(handler)
    
    def get_session_errors(self, session_id: str) -> List[ErrorRecord]:
        """Get all error records for a session."""
        return self.error_records.get(session_id, [])
    
    def get_error_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get error statistics for a session."""
        
        errors = self.get_session_errors(session_id)
        if not errors:
            return {'total_errors': 0}
        
        stats = {
            'total_errors': len(errors),
            'resolved_errors': len([e for e in errors if e.resolved]),
            'by_severity': {},
            'by_type': {},
            'by_phase': {},
            'retry_statistics': {
                'total_retries': sum(e.retry_count for e in errors),
                'avg_retries': sum(e.retry_count for e in errors) / len(errors)
            }
        }
        
        # Group by severity
        for severity in ErrorSeverity:
            stats['by_severity'][severity.value] = len([e for e in errors if e.severity == severity])
        
        # Group by error type
        error_types = {}
        for error in errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        stats['by_type'] = error_types
        
        # Group by phase
        phases = {}
        for error in errors:
            phases[error.phase] = phases.get(error.phase, 0) + 1
        stats['by_phase'] = phases
        
        return stats
    
    async def force_terminate_session(self, session_id: str, reason: str = "forced_termination"):
        """Force terminate a session (emergency stop)."""
        
        self.logger.warning(f"Force terminating session {session_id}: {reason}")
        
        # Create emergency error record
        error_record = ErrorRecord(
            id=f"force_term_{session_id}_{int(time.time())}",
            session_id=session_id,
            timestamp=datetime.now(),
            phase="forced_termination",
            error_type="ForcedTermination",
            error_message=reason,
            stack_trace="",
            severity=ErrorSeverity.CRITICAL,
            recovery_action=RecoveryAction.EMERGENCY_STOP
        )
        
        # Store error record
        if session_id not in self.error_records:
            self.error_records[session_id] = []
        self.error_records[session_id].append(error_record)
        
        # Execute emergency stop
        await self._handle_emergency_stop(session_id, error_record)
    
    def clear_session_errors(self, session_id: str):
        """Clear all error records for a session (for cleanup)."""
        if session_id in self.error_records:
            del self.error_records[session_id]
        
        if session_id in self.session_recovery_state:
            del self.session_recovery_state[session_id]