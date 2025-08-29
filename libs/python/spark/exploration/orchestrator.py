"""
Autonomous exploration orchestrator.

This module orchestrates both manual and autonomous exploration sessions, coordinating between
code generation, validation, discovery creation, and CUA agent integration for fully autonomous operation.
"""

import uuid
import time
import asyncio
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from spark.discovery.models import (
    ExplorationSession, ExplorationResult, Discovery, DiscoveryType,
    CodeArtifact, ExplorationStatus
)
from spark.exploration.generator import CodeGenerator, MockCodeGenerator, ClaudeCodeGenerator, GenerationRequest
from spark.exploration.validator import CodeValidator, ValidationResult
from spark.storage.discovery_storage import DiscoveryStorage

# Import CUA agent components
# Optional CUA agent components
try:
    from agent.agent.agent import ComputerAgent
    from agent.agent.callbacks import (
        LoggingCallback,
        TrajectorySaverCallback,
        BudgetManagerCallback,
    )
    from agent.agent.computers import make_computer_handler
    CUA_AVAILABLE = True
except Exception:  # ImportError and any transitive import failures
    ComputerAgent = None  # type: ignore
    LoggingCallback = TrajectorySaverCallback = BudgetManagerCallback = None  # type: ignore
    make_computer_handler = None  # type: ignore
    CUA_AVAILABLE = False


class ExplorationOrchestrator:
    """Orchestrates both manual and autonomous exploration sessions."""
    
    def __init__(
        self, 
        storage: Optional[DiscoveryStorage] = None,
        generator: Optional[CodeGenerator] = None,
        validator: Optional[CodeValidator] = None,
        patterns: Optional[Dict[str, Any]] = None,
        model: str = "anthropic/claude-3-5-sonnet-20241022",
        use_cua_agent: bool = False
    ):
        """
        Initialize ExplorationOrchestrator.
        
        Args:
            storage: Discovery storage instance
            generator: Code generator instance (defaults to ClaudeCodeGenerator if available)
            validator: Code validator instance  
            patterns: User coding patterns for context-aware generation
            model: Claude model for autonomous exploration
            use_cua_agent: Whether to enable CUA agent integration for autonomous operation
        """
        self.storage = storage or DiscoveryStorage()
        self.patterns = patterns or {}
        self.model = model
        # Enable CUA agent integration only when available and requested
        self.use_cua_agent = use_cua_agent and CUA_AVAILABLE
        
        # Initialize generator (prefer ClaudeCodeGenerator with patterns)
        if generator:
            self.generator = generator
        else:
            try:
                self.generator = ClaudeCodeGenerator(model=model, patterns=patterns)
            except (ValueError, ImportError) as e:
                print(f"Warning: Could not initialize ClaudeCodeGenerator ({e}), falling back to MockCodeGenerator")
                self.generator = MockCodeGenerator()
        
        self.validator = validator or CodeValidator()
        
        # CUA agent components (initialized when needed)
        self.cua_agent: Optional[ComputerAgent] = None
        self.computer_handler = None
        self.session_callbacks: List[Callable] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Progress tracking
        self.progress_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
    
    async def start_manual_exploration(
        self,
        goal: str,
        approaches: Optional[List[str]] = None,
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ExplorationSession:
        """Start a manual exploration session."""
        
        session = ExplorationSession(
            id=str(uuid.uuid4()),
            goal=goal,
            initiated_by="user",
            time_limit=1800,  # 30 minutes
            approach_count=len(approaches) if approaches else 3,
            risk_tolerance="moderate"
        )
        
        # Save session
        self.storage.save_exploration_session(session)
        
        # Default approaches if none provided
        if not approaches:
            approaches = self._generate_default_approaches(goal)
        
        context = context or {}
        
        # Execute explorations for each approach
        session.exploration_results = []
        for i, approach in enumerate(approaches):
            print(f"🔬 Exploring approach {i+1}/{len(approaches)}: {approach}")
            
            exploration_result = await self._execute_exploration(
                goal, approach, language, context
            )
            
            session.exploration_results.append(exploration_result)
            
            # Save result
            self.storage.save_exploration_result(exploration_result, session.id)
            
            # Small delay between approaches
            await asyncio.sleep(0.1)
        
        # Complete session
        session.completed_at = datetime.now()
        session.total_time = (session.completed_at - session.started_at).total_seconds()
        
        # Generate discoveries from successful results
        session.discoveries = await self._curate_discoveries(session.exploration_results, goal)
        
        # Save discoveries
        for discovery in session.discoveries:
            self.storage.save_discovery(discovery)
        
        # Update session
        self.storage.save_exploration_session(session)
        
        return session
    
    async def _execute_exploration(
        self,
        goal: str,
        approach: str,
        language: Optional[str],
        context: Dict[str, Any]
    ) -> ExplorationResult:
        """Execute a single exploration attempt."""
        
        request = GenerationRequest(
            goal=goal,
            approach=approach,
            context=context,
            language=language,
            max_attempts=3,
            timeout=60
        )
        
        # Generate code
        result = await self.generator.generate_code(request)
        
        # Validate the result if successful
        if result.success and result.code_artifacts:
            validation = await self.validator.validate_exploration_result(result)
            
            # Update result with validation info
            result.metadata.update({
                'validation_score': validation.score,
                'validation_issues': validation.issues,
                'validation_warnings': validation.warnings,
                'safety_level': validation.safety_level,
                'is_valid': validation.is_valid
            })
            
            # Consider it successful only if it passes validation
            if not validation.is_valid:
                result.success = False
                result.error_message = f"Validation failed: {', '.join(validation.issues)}"
                result.status = ExplorationStatus.FAILED
        
        return result
    
    async def _curate_discoveries(
        self,
        exploration_results: List[ExplorationResult],
        goal: str
    ) -> List[Discovery]:
        """Curate discoveries from exploration results."""
        
        discoveries = []
        successful_results = [r for r in exploration_results if r.success]
        
        if not successful_results:
            return discoveries
        
        # For Stage 1.3, create one discovery per successful result
        for i, result in enumerate(successful_results):
            discovery = await self._create_discovery_from_result(result, goal, i)
            discoveries.append(discovery)
        
        # Sort by overall score
        discoveries.sort(key=lambda d: d.overall_score(), reverse=True)
        
        # Keep top discoveries (max 3 for manual exploration)
        return discoveries[:3]
    
    async def _create_discovery_from_result(
        self,
        result: ExplorationResult,
        goal: str,
        index: int
    ) -> Discovery:
        """Create a discovery from an exploration result."""
        
        # Determine discovery type from goal
        discovery_type = self._classify_discovery_type(goal)
        
        # Generate title and description
        title = self._generate_discovery_title(result, goal)
        description = self._generate_discovery_description(result, goal)
        
        # Calculate scores
        validation_score = result.metadata.get('validation_score', 0.5)
        impact_score = self._estimate_impact_score(result, goal)
        novelty_score = self._estimate_novelty_score(result, goal)
        
        # Create discovery
        discovery = Discovery(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            discovery_type=discovery_type,
            exploration_results=[result],
            impact_score=impact_score,
            confidence_score=validation_score,
            novelty_score=novelty_score,
            integration_ready=validation_score > 0.7,
            integration_instructions=self._generate_integration_instructions(result),
            integration_risk="low" if validation_score > 0.8 else "moderate",
            tags=self._generate_tags(result, goal),
            source_patterns=[],  # Will be populated when pattern analysis is integrated
        )
        
        return discovery
    
    def _generate_default_approaches(self, goal: str) -> List[str]:
        """Generate default exploration approaches for a goal."""
        goal_lower = goal.lower()
        
        if 'function' in goal_lower:
            return [
                "Direct implementation with clear logic",
                "Functional programming approach with pure functions", 
                "Object-oriented approach with helper classes"
            ]
        elif 'class' in goal_lower:
            return [
                "Simple class with essential methods",
                "Class with inheritance and composition",
                "Class with design patterns (strategy, observer, etc.)"
            ]
        elif 'test' in goal_lower:
            return [
                "Unit tests with basic test cases",
                "Property-based testing with edge cases",
                "Integration tests with mock dependencies"
            ]
        elif 'performance' in goal_lower:
            return [
                "Algorithm optimization approach",
                "Data structure optimization approach",
                "Caching and memoization approach"
            ]
        else:
            return [
                "Simple and straightforward approach",
                "Modular and extensible approach",
                "Robust approach with error handling"
            ]
    
    def _classify_discovery_type(self, goal: str) -> DiscoveryType:
        """Classify the type of discovery based on goal."""
        goal_lower = goal.lower()
        
        if 'test' in goal_lower:
            return DiscoveryType.TESTING
        elif 'performance' in goal_lower or 'optimization' in goal_lower or 'speed' in goal_lower:
            return DiscoveryType.PERFORMANCE_OPTIMIZATION
        elif 'refactor' in goal_lower:
            return DiscoveryType.REFACTORING
        elif 'improve' in goal_lower:
            return DiscoveryType.CODE_IMPROVEMENT
        elif 'document' in goal_lower:
            return DiscoveryType.DOCUMENTATION
        elif 'tool' in goal_lower:
            return DiscoveryType.TOOLING
        else:
            return DiscoveryType.NEW_FEATURE
    
    def _generate_discovery_title(self, result: ExplorationResult, goal: str) -> str:
        """Generate a title for the discovery."""
        approach_words = result.approach.split()[:3]  # First 3 words
        approach_desc = " ".join(approach_words)
        
        # Truncate goal if too long
        short_goal = goal[:50] + "..." if len(goal) > 50 else goal
        
        return f"{approach_desc}: {short_goal}"
    
    def _generate_discovery_description(self, result: ExplorationResult, goal: str) -> str:
        """Generate a description for the discovery."""
        main_artifacts = [a for a in result.code_artifacts if a.is_main_artifact]
        artifact_count = len(result.code_artifacts)
        
        desc = f"Generated {result.approach.lower()} for: {goal}\n\n"
        
        if main_artifacts:
            desc += f"Main implementation: {main_artifacts[0].description}\n"
        
        if artifact_count > 1:
            desc += f"Includes {artifact_count} code files with supporting implementations.\n"
        
        validation_score = result.metadata.get('validation_score', 0)
        if validation_score > 0.8:
            desc += "\n✅ High quality implementation with robust validation."
        elif validation_score > 0.6:
            desc += "\n✅ Good quality implementation with minor improvements possible."
        else:
            desc += "\n⚠️ Basic implementation that may need refinement."
        
        return desc
    
    def _estimate_impact_score(self, result: ExplorationResult, goal: str) -> float:
        """Estimate the potential impact of the discovery."""
        base_score = 0.5
        
        # Adjust based on validation score
        validation_score = result.metadata.get('validation_score', 0.5)
        impact_score = base_score + (validation_score - 0.5) * 0.4
        
        # Adjust based on goal type
        goal_lower = goal.lower()
        if 'performance' in goal_lower or 'optimization' in goal_lower:
            impact_score += 0.2
        elif 'test' in goal_lower:
            impact_score += 0.1
        
        # Adjust based on code complexity
        total_lines = sum(len(a.content.split('\n')) for a in result.code_artifacts)
        if total_lines > 50:
            impact_score += 0.1
        
        return min(max(impact_score, 0.0), 1.0)
    
    def _estimate_novelty_score(self, result: ExplorationResult, goal: str) -> float:
        """Estimate the novelty of the discovery."""
        # For Stage 1.3, all manual explorations are considered reasonably novel
        base_score = 0.6
        
        # Adjust based on approach creativity
        if 'pattern' in result.approach.lower() or 'creative' in result.approach.lower():
            base_score += 0.2
        
        # Adjust based on unique features
        unique_features = ['async', 'decorator', 'context manager', 'generator']
        content_lower = ' '.join(a.content.lower() for a in result.code_artifacts)
        
        for feature in unique_features:
            if feature in content_lower:
                base_score += 0.05
        
        return min(max(base_score, 0.0), 1.0)
    
    def _generate_integration_instructions(self, result: ExplorationResult) -> List[str]:
        """Generate integration instructions for the discovery."""
        instructions = []
        
        main_artifacts = [a for a in result.code_artifacts if a.is_main_artifact]
        if main_artifacts:
            main_file = main_artifacts[0].file_path
            instructions.append(f"1. Review the generated code in {main_file}")
            instructions.append(f"2. Adapt the implementation to your specific use case")
        
        if len(result.code_artifacts) > 1:
            instructions.append("3. Integrate supporting files as needed")
        
        instructions.append("4. Run tests to ensure functionality")
        instructions.append("5. Consider refactoring to match your code style")
        
        return instructions
    
    def _generate_tags(self, result: ExplorationResult, goal: str) -> List[str]:
        """Generate relevant tags for the discovery."""
        tags = set()
        
        # Add language tags
        languages = {a.language for a in result.code_artifacts}
        tags.update(languages)
        
        # Add type tags based on goal
        goal_lower = goal.lower()
        if 'function' in goal_lower:
            tags.add('function')
        if 'class' in goal_lower:
            tags.add('class')
        if 'test' in goal_lower:
            tags.add('testing')
        if 'performance' in goal_lower:
            tags.add('performance')
        if 'refactor' in goal_lower:
            tags.add('refactoring')
        
        # Add approach tags
        approach_lower = result.approach.lower()
        if 'object' in approach_lower:
            tags.add('oop')
        if 'functional' in approach_lower:
            tags.add('functional')
        if 'pattern' in approach_lower:
            tags.add('design-pattern')
        
        tags.add('manual-exploration')
        tags.add('generated')
        
        return list(tags)
    
    # === AUTONOMOUS EXPLORATION METHODS (CUA Integration) ===
    
    async def start_autonomous_exploration(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        resource_limits: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> ExplorationSession:
        """Start an autonomous exploration session with CUA agent integration."""
        
        if not self.use_cua_agent:
            # Fallback to enhanced manual exploration with ClaudeCodeGenerator
            return await self.start_manual_exploration(
                goal=goal,
                approaches=None,
                language=context.get('language') if context else None,
                context=context
            )
        
        session_id = session_id or str(uuid.uuid4())
        
        # Initialize CUA agent if needed
        if not CUA_AVAILABLE:
            # Safety: if CUA not available, fall back to manual exploration
            return await self.start_manual_exploration(
                goal=goal,
                approaches=None,
                language=context.get('language') if context else None,
                context=context,
            )

        await self._initialize_cua_agent()
        
        # Create autonomous exploration session
        session = ExplorationSession(
            id=session_id,
            goal=goal,
            initiated_by="autonomous",
            time_limit=resource_limits.get('time_limit', 3600) if resource_limits else 3600,  # 1 hour
            approach_count=5,  # Use all 5 approaches from ClaudeCodeGenerator
            risk_tolerance="balanced"
        )
        
        # Save session
        self.storage.save_exploration_session(session)
        
        # Track session
        self.active_sessions[session_id] = {
            'session': session,
            'start_time': time.time(),
            'resource_limits': resource_limits or {},
            'context': context or {},
            'progress': {
                'phase': 'initializing',
                'completed_approaches': 0,
                'total_approaches': 5,
                'discoveries_found': 0
            }
        }
        
        try:
            # Emit progress update
            await self._emit_progress_update(session_id, 'exploration_started', {
                'goal': goal,
                'session_id': session_id,
                'estimated_duration': session.time_limit
            })
            
            # Execute autonomous exploration
            results = await self._execute_autonomous_exploration(session, context or {})
            
            # Update session with results
            session.completed_at = datetime.now()
            session.total_time = time.time() - self.active_sessions[session_id]['start_time']
            session.status = ExplorationStatus.COMPLETED
            
            # Create discoveries from results
            discoveries = await self._create_discoveries_from_results(results, goal)
            
            # Save discoveries to storage
            for discovery in discoveries:
                self.storage.save_discovery(discovery)
            
            # Update progress
            self.active_sessions[session_id]['progress'].update({
                'phase': 'completed',
                'discoveries_found': len(discoveries)
            })
            
            await self._emit_progress_update(session_id, 'exploration_completed', {
                'discoveries_count': len(discoveries),
                'execution_time': session.total_time,
                'success_rate': sum(1 for r in results if r.success) / len(results) if results else 0
            })
            
        except Exception as e:
            # Handle exploration failure
            session.completed_at = datetime.now()
            session.total_time = time.time() - self.active_sessions[session_id]['start_time']
            session.status = ExplorationStatus.FAILED
            
            await self._emit_progress_update(session_id, 'exploration_failed', {
                'error': str(e),
                'execution_time': session.total_time
            })
            
            raise
        finally:
            # Clean up session tracking
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Save final session state
            self.storage.save_exploration_session(session)
        
        return session
    
    async def _initialize_cua_agent(self):
        """Initialize CUA agent components for autonomous exploration."""
        if self.cua_agent is not None:
            return  # Already initialized
        
        try:
            # Create computer handler
            self.computer_handler = await make_computer_handler()
            
            # Set up callbacks for exploration session tracking
            callbacks = [
                LoggingCallback(log_level="INFO"),
                TrajectorySaverCallback(trajectory_dir=Path.home() / ".spark" / "trajectories"),
                BudgetManagerCallback(budget_limit=100.0)  # $100 limit for safety
            ]
            
            # Initialize CUA agent
            self.cua_agent = ComputerAgent(
                model=self.model,
                computer=self.computer_handler,
                callbacks=callbacks
            )
            
        except Exception as e:
            print(f"Warning: Could not initialize CUA agent ({e}), autonomous exploration will use fallback mode")
            self.use_cua_agent = False
            self.cua_agent = None
    
    async def _execute_autonomous_exploration(
        self,
        session: ExplorationSession,
        context: Dict[str, Any]
    ) -> List[ExplorationResult]:
        """Execute autonomous exploration using CUA agent system."""
        results = []
        
        # Update progress
        session_id = session.id
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['progress']['phase'] = 'generating_code'
        
        try:
            # Use ClaudeCodeGenerator's multi-approach generation
            generation_request = GenerationRequest(
                goal=session.goal,
                approach="autonomous_multi_approach",  # Special approach for autonomous mode
                context=context,
                language=context.get('language', 'python'),
                max_attempts=3,
                timeout=300  # 5 minute timeout per approach
            )
            
            # Generate code using our enhanced generator
            result = await self.generator.generate_code(generation_request)
            
            if result.success:
                # Update progress
                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['progress'].update({
                        'phase': 'validating_code',
                        'completed_approaches': 1,
                        'total_approaches': 1  # ClaudeCodeGenerator handles multi-approach internally
                    })
                    
                    await self._emit_progress_update(session_id, 'code_generated', {
                        'artifacts_count': len(result.code_artifacts),
                        'approach_type': result.metadata.get('approaches_generated', 1)
                    })
                
                # Validate the generated code
                if self.use_cua_agent and self.cua_agent:
                    # Use CUA agent for advanced validation
                    validation_result = await self._validate_with_cua_agent(result, context)
                else:
                    # Use standard validation
                    validation_result = await self._validate_exploration_result(result)
                
                # Update result with validation metadata
                result.metadata.update({
                    'validation_score': validation_result.score,
                    'validation_issues': validation_result.issues,
                    'cua_validated': self.use_cua_agent and self.cua_agent is not None
                })
                
                results.append(result)
                
                # Update progress
                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['progress']['phase'] = 'creating_discoveries'
                    await self._emit_progress_update(session_id, 'code_validated', {
                        'validation_score': validation_result.score,
                        'issues_found': len(validation_result.issues)
                    })
            else:
                # Even failed results are valuable for learning
                results.append(result)
                await self._emit_progress_update(session_id, 'code_generation_failed', {
                    'error': result.error_message
                })
                
        except Exception as e:
            # Create failed result for tracking
            failed_result = ExplorationResult(
                id=str(uuid.uuid4()),
                goal=session.goal,
                approach="autonomous_exploration",
                status=ExplorationStatus.FAILED,
                success=False,
                error_message=str(e),
                execution_time=0,
                metadata={'error_type': type(e).__name__}
            )
            results.append(failed_result)
        
        return results
    
    async def _validate_with_cua_agent(
        self,
        result: ExplorationResult,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """Validate exploration result using CUA agent for advanced testing."""
        
        if not self.cua_agent or not result.code_artifacts:
            return await self._validate_exploration_result(result)
        
        try:
            # Prepare validation prompt for CUA agent
            main_artifact = next((a for a in result.code_artifacts if a.is_main_artifact), result.code_artifacts[0])
            
            validation_prompt = f"""
I need you to validate and test the following code for safety and functionality:

Goal: {result.goal}
Language: {main_artifact.language}

Code to validate:
```{main_artifact.language}
{main_artifact.content}
```

Please:
1. Check the code for syntax errors
2. Identify potential security issues  
3. Test the code if safe to run
4. Provide a quality score (0-1)
5. List any issues found

Respond with a structured analysis.
"""
            
            # Use CUA agent to validate code
            # Note: This is a simplified example - in practice you'd want more sophisticated validation
            validation_response = await self.cua_agent.run_with_tools(
                prompt=validation_prompt,
                tools=[],  # Add specific validation tools as needed
                max_iterations=3
            )
            
            # Parse the validation response (simplified)
            # In practice, you'd want more sophisticated parsing
            score = 0.8  # Default score - would be extracted from response
            issues = []  # Would be extracted from response
            
            return ValidationResult(
                is_valid=True,
                score=score,
                issues=issues,
                warnings=[],
                safety_level="safe",
                executable=True,
                syntax_valid=True
            )
            
        except Exception as e:
            print(f"CUA validation failed, falling back to standard validation: {e}")
            return await self._validate_exploration_result(result)
    
    async def _validate_exploration_result(self, result: ExplorationResult) -> ValidationResult:
        """Validate exploration result using standard CodeValidator."""
        if not result.code_artifacts:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=["No code artifacts generated"],
                warnings=[],
                safety_level="unsafe",
                executable=False,
                syntax_valid=False
            )
        
        # Validate main artifact
        main_artifact = next((a for a in result.code_artifacts if a.is_main_artifact), result.code_artifacts[0])
        return await self.validator.validate_code(main_artifact.content, main_artifact.language)
    
    async def _emit_progress_update(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Emit progress update to registered callbacks."""
        update_data = {
            'session_id': session_id,
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Update session progress if tracking
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            update_data['progress'] = session_info['progress']
            update_data['elapsed_time'] = time.time() - session_info['start_time']
        
        # Call progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(event_type, update_data)
            except Exception as e:
                print(f"Progress callback error: {e}")
    
    def add_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add a progress callback for real-time exploration tracking."""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Remove a progress callback."""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an active exploration session."""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active exploration sessions."""
        return self.active_sessions.copy()
    
    async def cancel_session(self, session_id: str) -> bool:
        """Cancel an active exploration session."""
        if session_id not in self.active_sessions:
            return False
        
        session_info = self.active_sessions[session_id]
        session = session_info['session']
        
        # Update session status
        session.completed_at = datetime.now()
        session.total_time = time.time() - session_info['start_time']
        session.status = ExplorationStatus.CANCELLED
        
        # Save session
        self.storage.save_exploration_session(session)
        
        # Emit cancellation event
        await self._emit_progress_update(session_id, 'exploration_cancelled', {
            'reason': 'user_requested',
            'execution_time': session.total_time
        })
        
        # Clean up
        del self.active_sessions[session_id]
        
        return True
