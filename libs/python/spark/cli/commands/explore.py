"""
Spark explore command implementation.

Handles manual exploration sessions and future autonomous exploration.
"""

import uuid
from typing import List, Optional
from pathlib import Path
from spark.cli.terminal import get_console
from spark.cli.errors import handle_async_cli_error
from spark.exploration.orchestrator import ExplorationOrchestrator
from spark.exploration.goal_generator import GoalGenerator, GoalGenerationConfig, RiskLevel
from spark.core.scheduler import ExplorationScheduler, ScheduledTask, ScheduleType, ResourceLimits
from spark.discovery.presenter import DiscoveryPresenter
from spark.storage.discovery_storage import DiscoveryStorage
from spark.storage.patterns import PatternStorage
from spark.core.config import SparkConfig


class ExploreCommand:
    """Implementation of the 'spark explore' command."""
    
    def __init__(self):
        self.console = get_console()
        self.orchestrator = ExplorationOrchestrator()
        self.presenter = DiscoveryPresenter()
        
        # Initialize autonomous exploration components
        self.discovery_storage = DiscoveryStorage()
        # Use SparkConfig database path for consistency
        try:
            cfg = SparkConfig()
            db_path = cfg.get_database_path()
        except Exception:
            # Fallback to ~/.spark/spark.db if config isn't available
            db_path = Path.home() / '.spark' / 'spark.db'
        self.pattern_storage = PatternStorage(db_path)
        self.goal_generator = GoalGenerator(self.pattern_storage, self.discovery_storage)
        self.scheduler = ExplorationScheduler()
        # Register scheduled callback
        try:
            self.scheduler.register_task_function('_run_scheduled_exploration', self._run_scheduled_exploration)
        except Exception:
            pass
    
    @handle_async_cli_error
    async def execute(self, args: List[str]) -> int:
        """Execute the explore command."""
        
        if not args:
            # Show exploration help
            self.help()
            return 0
        
        first_arg = args[0].lower()
        
        if first_arg in ["--manual", "-m", "manual"]:
            # Manual exploration mode
            return await self._start_manual_exploration(args[1:])
        elif first_arg in ["--autonomous", "-a", "autonomous"]:
            # Immediate autonomous exploration
            return await self._start_autonomous_exploration(args[1:])
        elif first_arg in ["--schedule", "-s", "schedule"]:
            # Schedule autonomous exploration
            return await self._schedule_exploration(args[1:])
        elif first_arg in ["--plan", "-p", "plan"]:
            # Evening planning workflow
            return await self._evening_planning_workflow()
        elif first_arg in ["--list-schedules", "--list", "-l"]:
            # List active schedules
            return await self._list_schedules()
        elif first_arg in ["--cancel", "-c"]:
            # Cancel a scheduled exploration
            return await self._cancel_schedule(args[1:])
        elif first_arg in ["--status"]:
            # Show scheduler status
            return await self._show_scheduler_status()
        else:
            # Treat as manual exploration goal
            goal = " ".join(args)
            return await self._explore_goal(goal)
    
    async def _start_manual_exploration(self, args: List[str]) -> int:
        """Start a manual exploration session."""
        
        if not args:
            self.console.print_error(
                "No exploration goal provided",
                "Usage: spark explore --manual \"<your exploration goal>\""
            )
            return 1
        
        goal = " ".join(args)
        return await self._explore_goal(goal)
    
    async def _explore_goal(self, goal: str) -> int:
        """Explore a specific goal."""
        
        if not goal.strip():
            self.console.print_error("Empty exploration goal", "Please provide a meaningful goal")
            return 1
        
        self.console.console.print(f"\n🔬 [bold]Starting Manual Exploration[/bold]")
        self.console.console.print(f"[cyan]Goal:[/cyan] {goal}")
        self.console.console.print()
        
        # Prompt for additional parameters
        language = await self._prompt_for_language()
        approaches = await self._prompt_for_approaches(goal)
        
        self.console.console.print(f"\n⚡ [bold]Generating explorations...[/bold]")
        
        try:
            # Start exploration session
            session = await self.orchestrator.start_manual_exploration(
                goal=goal,
                approaches=approaches,
                language=language,
                context={}
            )
            
            # Show results
            self.console.console.print(f"\n✅ [bold]Exploration completed![/bold]")
            self.console.console.print(f"[dim]Session ID: {session.id[:8]}[/dim]")
            self.console.console.print(f"[dim]Total time: {session.total_time:.1f} seconds[/dim]")
            self.console.console.print(f"[dim]Success rate: {session.success_rate():.1%}[/dim]")
            
            if session.discoveries:
                self.console.console.print(f"\n🎉 [bold]{len(session.discoveries)} discoveries created![/bold]")
                
                # Show discovery summaries
                for i, discovery in enumerate(session.discoveries, 1):
                    self.console.console.print(
                        f"{i}. [cyan]{discovery.title}[/cyan] "
                        f"(Score: {discovery.overall_score():.2f})"
                    )
                
                self.console.console.print(f"\n💡 Use [cyan]spark show[/cyan] to browse discoveries")
                self.console.console.print(f"💡 Use [cyan]spark show {session.discoveries[0].id[:8]}[/cyan] to see details")
                
                return 0
            else:
                self.console.print_warning(
                    "No discoveries were generated",
                    "Try refining your goal or checking for errors"
                )
                return 1
        
        except Exception as e:
            self.console.print_error("Exploration failed", str(e))
            return 1
    
    async def _prompt_for_language(self) -> Optional[str]:
        """Prompt for programming language (simplified for Stage 1.3)."""
        
        # For now, return default Python
        # In a full implementation, this would be an interactive prompt
        return "python"
    
    async def _prompt_for_approaches(self, goal: str) -> Optional[List[str]]:
        """Prompt for exploration approaches (simplified for Stage 1.3)."""
        
        # For now, let the orchestrator generate default approaches
        # In a full implementation, this would be an interactive selection
        return None
    
    async def _start_autonomous_exploration(self, args: List[str]) -> int:
        """Start immediate autonomous exploration."""
        
        self.console.console.print(f"\n🤖 [bold]Starting Autonomous Exploration[/bold]")
        
        # Generate goals based on current context
        try:
            config = GoalGenerationConfig(
                max_goals_per_session=5,
                risk_tolerance=RiskLevel.MODERATE,
                focus_categories=[],
                time_budget_minutes=60
            )
            
            goals = await self.goal_generator.generate_goals(config)
            
            if not goals:
                self.console.print_warning(
                    "No exploration goals generated",
                    "This could be due to insufficient pattern data. Try manual exploration first."
                )
                return 0
            
            self.console.console.print(f"\n🎯 [bold]Generated {len(goals)} exploration goals:[/bold]")
            
            # Present goals to user
            for i, goal in enumerate(goals, 1):
                risk_emoji = {"conservative": "🟢", "moderate": "🟡", "experimental": "🔴"}
                risk_icon = risk_emoji.get(goal.risk_level.value, "🟡")
                
                self.console.console.print(
                    f"{i}. {risk_icon} [cyan]{goal.title}[/cyan]\n"
                    f"   [dim]{goal.description}[/dim]\n"
                    f"   [dim]Category: {goal.category.value.replace('_', ' ').title()}, "
                    f"Time: {goal.estimated_time_minutes}min[/dim]"
                )
            
            self.console.console.print(f"\n⚡ [bold]Executing autonomous explorations...[/bold]")
            
            # Execute each goal
            successful_sessions = 0
            for goal in goals:
                try:
                    session = await self.orchestrator.start_manual_exploration(
                        goal=goal.title,
                        approaches=None,  # Let it generate approaches
                        language=goal.preferred_languages[0] if goal.preferred_languages else None,
                        context={"autonomous": True, "goal_id": goal.id}
                    )
                    
                    if session.is_successful():
                        successful_sessions += 1
                
                except Exception as e:
                    self.console.console.print(f"[red]Goal failed: {goal.title} - {str(e)}[/red]")
            
            # Show results
            self.console.console.print(f"\n✅ [bold]Autonomous exploration completed![/bold]")
            self.console.console.print(f"[dim]Successfully executed {successful_sessions}/{len(goals)} goals[/dim]")
            
            if successful_sessions > 0:
                self.console.console.print(f"\n💡 Use [cyan]spark show[/cyan] to browse new discoveries")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Autonomous exploration failed", str(e))
            return 1
    
    async def _schedule_exploration(self, args: List[str]) -> int:
        """Schedule autonomous exploration for later."""
        
        if not args:
            self.console.print_error(
                "Missing schedule time",
                "Usage: spark explore --schedule \"21:00\" [daily|weekdays|weekends]"
            )
            return 1
        
        schedule_time = args[0]
        schedule_type_str = args[1].lower() if len(args) > 1 else "daily"
        
        # Parse and validate schedule
        try:
            # Simple time parsing (HH:MM format)
            if ":" not in schedule_time:
                raise ValueError("Invalid time format")
            
            hours, minutes = map(int, schedule_time.split(":"))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Invalid time values")
            
        except ValueError:
            self.console.print_error(
                f"Invalid time format: {schedule_time}",
                "Use HH:MM format (e.g., 21:00 for 9 PM)"
            )
            return 1
        
        # Create schedule task
        try:
            # Add to scheduler
            # Map schedule type
            if schedule_type_str == "daily":
                stype = ScheduleType.DAILY
            elif schedule_type_str == "weekdays":
                stype = ScheduleType.WEEKDAYS
            elif schedule_type_str == "weekends":
                stype = ScheduleType.WEEKENDS
            else:
                stype = ScheduleType.DAILY

            task_id = await self.scheduler.add_task(
                name=f"autonomous_exploration_{schedule_time}",
                schedule_type=stype,
                schedule_config={"hour": hours, "minute": minutes},
                task_function_name="_run_scheduled_exploration",
                task_args={},
                resource_limits=ResourceLimits()
            )
            
            # Start scheduler if not already running
            await self.scheduler.start_scheduler()
            
            self.console.console.print(f"✅ [green]Scheduled autonomous exploration![/green]")
            self.console.console.print(f"[dim]Task ID: {task_id}[/dim]")
            self.console.console.print(f"[dim]Time: {schedule_time} {schedule_type}[/dim]")
            self.console.console.print(f"\n💡 Use [cyan]spark explore --list[/cyan] to view all scheduled explorations")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to schedule exploration", str(e))
            return 1
    
    async def _evening_planning_workflow(self) -> int:
        """Interactive evening planning workflow."""
        
        self.console.console.print(f"\n🌅 [bold]Evening Planning Workflow[/bold]")
        self.console.console.print("[dim]Let's plan tonight's exploration session...[/dim]")
        
        try:
            # Analyze current context
            self.console.console.print(f"\n📊 [bold]Analyzing your coding patterns...[/bold]")
            
            # Generate goals with different risk levels
            configs = [
                GoalGenerationConfig(max_goals_per_session=2, risk_tolerance=RiskLevel.CONSERVATIVE, time_budget_minutes=30),
                GoalGenerationConfig(max_goals_per_session=2, risk_tolerance=RiskLevel.MODERATE, time_budget_minutes=45),
                GoalGenerationConfig(max_goals_per_session=1, risk_tolerance=RiskLevel.EXPERIMENTAL, time_budget_minutes=60)
            ]
            
            all_goals = []
            for config in configs:
                goals = await self.goal_generator.generate_goals(config)
                all_goals.extend(goals)
            
            if not all_goals:
                self.console.print_warning(
                    "No goals generated for planning",
                    "Try running some manual explorations first to build pattern data"
                )
                return 0
            
            # Present goals by risk level
            self.console.console.print(f"\n🎯 [bold]Suggested exploration goals:[/bold]")
            
            risk_groups = {"conservative": [], "moderate": [], "experimental": []}
            for goal in all_goals:
                risk_groups[goal.risk_level.value].append(goal)
            
            for risk_level, goals in risk_groups.items():
                if goals:
                    risk_emoji = {"conservative": "🟢", "moderate": "🟡", "experimental": "🔴"}
                    self.console.console.print(f"\n{risk_emoji[risk_level]} [bold]{risk_level.title()} Risk:[/bold]")
                    
                    for i, goal in enumerate(goals, 1):
                        self.console.console.print(
                            f"  {i}. [cyan]{goal.title}[/cyan]\n"
                            f"     [dim]{goal.description[:80]}...[/dim]"
                        )
            
            # For now, auto-schedule a moderate risk exploration
            moderate_goals = risk_groups.get("moderate", [])
            if moderate_goals:
                selected_goal = moderate_goals[0]
                
                self.console.console.print(f"\n📅 [bold]Scheduling tonight's exploration:[/bold]")
                self.console.console.print(f"[cyan]{selected_goal.title}[/cyan]")
                
                # Schedule for 2 AM (when system is likely idle)
                task_id = await self.scheduler.add_task(
                    name=f"evening_planned_exploration",
                    schedule_type=ScheduleType.DAILY,
                    schedule_config={"hour": 2, "minute": 0},
                    task_function_name="_run_scheduled_exploration",
                    task_args={"goal": selected_goal},
                    resource_limits=ResourceLimits(max_duration_minutes=selected_goal.estimated_time_minutes)
                )
                await self.scheduler.start_scheduler()
                
                self.console.console.print(f"✅ [green]Scheduled for 2:00 AM tonight[/green]")
                self.console.console.print(f"[dim]Task ID: {task_id}[/dim]")
                self.console.console.print(f"\n🌙 [bold]Sleep well! I'll explore while you rest.[/bold]")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Evening planning failed", str(e))
            return 1
    
    async def _list_schedules(self) -> int:
        """List all scheduled explorations."""
        
        try:
            tasks = self.scheduler.get_tasks()
            
            if not tasks:
                self.console.print_success("No scheduled explorations", "Use 'spark explore --schedule' to create one")
                return 0
            
            self.console.console.print(f"\n📋 [bold]Scheduled Explorations:[/bold]")
            
            for task in tasks:
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄", 
                    "completed": "✅",
                    "failed": "❌",
                    "paused": "⏸️"
                }
                
                emoji = status_emoji.get(task.status.value, "⏳")
                # Display HH:MM if present
                hour = task.schedule_config.get('hour')
                minute = task.schedule_config.get('minute')
                schedule_time = f"{hour:02d}:{minute:02d}" if hour is not None and minute is not None else task.schedule_config.get('time', 'Unknown')
                
                self.console.console.print(
                    f"{emoji} [cyan]{task.name}[/cyan]\n"
                    f"   [dim]ID: {task.id}[/dim]\n"
                    f"   [dim]Schedule: {schedule_time} {task.schedule_type.value}[/dim]\n"
                    f"   [dim]Status: {task.status.value}[/dim]"
                )
            
            self.console.console.print(f"\n💡 Use [cyan]spark explore --cancel <task-id>[/cyan] to cancel a schedule")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to list schedules", str(e))
            return 1
    
    async def _cancel_schedule(self, args: List[str]) -> int:
        """Cancel a scheduled exploration."""
        
        if not args:
            self.console.print_error(
                "Missing task ID",
                "Usage: spark explore --cancel <task-id>"
            )
            return 1
        
        task_id = args[0]
        
        try:
            success = await self.scheduler.remove_task(task_id)
            
            if success:
                self.console.console.print(f"✅ [green]Cancelled scheduled exploration[/green]")
                self.console.console.print(f"[dim]Task ID: {task_id}[/dim]")
            else:
                self.console.print_error(
                    f"Task not found: {task_id}",
                    "Use 'spark explore --list' to see available tasks"
                )
                return 1
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to cancel schedule", str(e))
            return 1
    
    async def _show_scheduler_status(self) -> int:
        """Show scheduler status and statistics."""
        
        try:
            status = await self.scheduler.get_status()
            tasks = self.scheduler.get_tasks()
            
            self.console.console.print(f"\n📊 [bold]Scheduler Status:[/bold]")
            self.console.console.print(f"Running: {'✅ Yes' if status.get('is_running', False) else '❌ No'}")
            self.console.console.print(f"Total tasks: {status.get('total_tasks', len(tasks))}")
            self.console.console.print(f"Active sessions: {status.get('active_sessions', 0)}")
            
            # Show nearest next run if available
            upcoming = [t.next_run for t in tasks if t.next_run]
            if upcoming:
                next_run = min(upcoming)
                self.console.console.print(f"Next run: {next_run}")
            
            return 0
            
        except Exception as e:
            self.console.print_error("Failed to get scheduler status", str(e))
            return 1
    
    async def _run_scheduled_exploration(self, task_config: dict) -> bool:
        """Run a scheduled exploration (callback for scheduler)."""
        
        try:
            # Generate goals for scheduled exploration
            config = GoalGenerationConfig(
                max_goals_per_session=3,
                risk_tolerance=RiskLevel.MODERATE,
                time_budget_minutes=45
            )
            
            goals = await self.goal_generator.generate_goals(config)
            
            if not goals:
                return False
            
            # Execute the first goal
            goal = goals[0]
            session = await self.orchestrator.start_manual_exploration(
                goal=goal.title,
                approaches=None,
                language=goal.preferred_languages[0] if goal.preferred_languages else None,
                context={"scheduled": True, "goal_id": goal.id}
            )
            
            return session.is_successful()
            
        except Exception:
            return False
    
    def help(self) -> None:
        """Show help for the explore command."""
        help_text = """
[bold cyan]spark explore[/bold cyan] - Manual and autonomous code exploration

[bold]Usage:[/bold]
  spark explore \"<goal>\"                    Manual exploration of a specific goal
  spark explore --manual \"<goal>\"           Explicit manual exploration
  spark explore --autonomous                  Generate and run autonomous explorations
  spark explore --schedule HH:MM [type]      Schedule autonomous exploration
  spark explore --plan                       Interactive evening planning
  spark explore --list                       List scheduled explorations
  spark explore --cancel <task-id>           Cancel a scheduled exploration
  spark explore --status                     Show scheduler status

[bold]Manual Exploration:[/bold]
  Generates multiple approaches for your specific goal, creates working code,
  validates results, and curates them as discoverable insights.

[bold]Autonomous Exploration:[/bold]
  Analyzes your coding patterns and generates relevant exploration goals
  automatically. Can run immediately or be scheduled for later.

[bold]Examples:[/bold]
  # Manual explorations
  spark explore \"Create a utility function for data validation\"
  spark explore --manual \"Implement caching for expensive operations\"
  
  # Autonomous explorations
  spark explore --autonomous                  # Generate and run goals now
  spark explore --plan                       # Interactive evening planning
  spark explore --schedule 21:00 daily       # Schedule for 9 PM daily
  spark explore --schedule 02:00 weekdays    # Schedule for 2 AM on weekdays
  
  # Schedule management
  spark explore --list                       # View all schedules
  spark explore --cancel abc123              # Cancel specific schedule
  spark explore --status                     # Check scheduler status

[bold]What happens during exploration:[/bold]
  1. 🎯 Analyzes patterns and generates relevant goals (autonomous) or uses your goal (manual)
  2. 🔬 Creates multiple code implementations for each goal
  3. ✅ Validates generated code for safety and quality
  4. 🎉 Curates successful results as browseable discoveries
  5. 📊 Provides detailed results and integration guidance

[bold]Schedule Types:[/bold]
  daily      - Run every day at the specified time
  weekdays   - Run Monday through Friday only
  weekends   - Run Saturday and Sunday only

[bold]Tips:[/bold]
  • Use manual exploration for specific goals and learning
  • Use autonomous exploration to discover new possibilities based on your patterns
  • Schedule explorations during low-activity hours (e.g., 2 AM)
  • Check discoveries regularly with 'spark show' and rate them
        """
        self.console.console.print(help_text)
