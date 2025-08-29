"""
Pattern-driven exploration goal synthesis.

This module generates exploration goals based on learned user patterns,
project analysis, and risk preferences to enable autonomous exploration.
"""

import uuid
import random
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from spark.learning.git_patterns import GitPatternAnalyzer, GitAnalysisResult
from spark.learning.preference_mapper import PreferenceMapper, PreferenceProfile
from spark.discovery.models import Discovery, DiscoveryType
from spark.storage.discovery_storage import DiscoveryStorage
from spark.storage.patterns import PatternStorage


class RiskLevel(Enum):
    """Risk levels for exploration goals."""
    CONSERVATIVE = "conservative"    # Safe, proven patterns
    MODERATE = "moderate"           # Balanced exploration
    EXPERIMENTAL = "experimental"   # Innovative, higher risk


class GoalCategory(Enum):
    """Categories of exploration goals."""
    CODE_IMPROVEMENT = "code_improvement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization" 
    TESTING_ENHANCEMENT = "testing_enhancement"
    REFACTORING_OPPORTUNITY = "refactoring_opportunity"
    NEW_FEATURE_EXPLORATION = "new_feature_exploration"
    TOOLING_ENHANCEMENT = "tooling_enhancement"
    ARCHITECTURAL_IMPROVEMENT = "architectural_improvement"
    LEARNING_EXPERIMENT = "learning_experiment"


@dataclass
class ExplorationGoal:
    """A generated exploration goal with context and metadata."""
    
    id: str
    title: str
    description: str
    category: GoalCategory
    risk_level: RiskLevel
    
    # Execution parameters
    estimated_time_minutes: int = 30
    max_approaches: int = 3
    priority_score: float = 0.5
    
    # Context and reasoning
    source_patterns: List[str] = field(default_factory=list)
    justification: str = ""
    expected_outcomes: List[str] = field(default_factory=list)
    
    # Constraints and preferences
    preferred_languages: List[str] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)
    avoid_patterns: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    project_context: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class GoalGenerationConfig:
    """Configuration for goal generation."""
    
    max_goals_per_session: int = 5
    min_goal_diversity: float = 0.7  # 0-1, higher = more diverse goals
    risk_tolerance: RiskLevel = RiskLevel.MODERATE
    time_budget_minutes: int = 120  # Total time budget for exploration session
    focus_categories: List[GoalCategory] = field(default_factory=list)
    exclude_categories: List[GoalCategory] = field(default_factory=list)
    
    # Pattern influence weights
    recent_work_weight: float = 0.4
    skill_level_weight: float = 0.3
    user_feedback_weight: float = 0.3


class PatternAnalyzer:
    """Analyzes user patterns to inform goal generation."""
    
    def __init__(self, pattern_storage: PatternStorage, discovery_storage: DiscoveryStorage):
        self.pattern_storage = pattern_storage
        self.discovery_storage = discovery_storage
        self.git_analyzer = GitPatternAnalyzer()
        self.preference_mapper = PreferenceMapper()
    
    async def analyze_current_context(self, project_path: str = ".") -> Dict[str, Any]:
        """Analyze current project context for goal generation."""
        
        # Git pattern analysis
        git_result = await self.git_analyzer.analyze_repository(project_path)
        
        # Get recent discoveries and feedback
        recent_discoveries = self.discovery_storage.get_recent_discoveries(days=14, limit=50)
        
        # Analyze user feedback patterns
        feedback_analysis = self._analyze_feedback_patterns(recent_discoveries)
        
        # Project structure analysis  
        project_analysis = await self._analyze_project_structure(project_path)
        
        # Skill level assessment
        skill_assessment = self._assess_skill_levels(git_result, recent_discoveries)
        
        return {
            'git_patterns': git_result,
            'recent_discoveries': recent_discoveries,
            'feedback_patterns': feedback_analysis,
            'project_structure': project_analysis,
            'skill_assessment': skill_assessment,
            'analysis_timestamp': datetime.now()
        }
    
    def _analyze_feedback_patterns(self, discoveries: List[Discovery]) -> Dict[str, Any]:
        """Analyze user feedback to understand preferences."""
        
        if not discoveries:
            return {'average_rating': None, 'preferred_types': [], 'avoided_patterns': []}
        
        rated_discoveries = [d for d in discoveries if d.user_rating]
        
        if not rated_discoveries:
            return {'average_rating': None, 'preferred_types': [], 'avoided_patterns': []}
        
        # Calculate average rating
        avg_rating = sum(d.user_rating.value for d in rated_discoveries) / len(rated_discoveries)
        
        # Find preferred discovery types (high ratings)
        type_ratings = {}
        for discovery in rated_discoveries:
            discovery_type = discovery.discovery_type
            if discovery_type not in type_ratings:
                type_ratings[discovery_type] = []
            type_ratings[discovery_type].append(discovery.user_rating.value)
        
        # Calculate average rating per type
        type_averages = {
            discovery_type: sum(ratings) / len(ratings)
            for discovery_type, ratings in type_ratings.items()
        }
        
        # Preferred types (above average + threshold)
        threshold = 0.5
        preferred_types = [
            discovery_type.value for discovery_type, avg_type_rating 
            in type_averages.items()
            if avg_type_rating > avg_rating + threshold
        ]
        
        # Find patterns in poorly rated discoveries
        poor_discoveries = [d for d in rated_discoveries if d.user_rating.value <= 2]
        avoided_patterns = []
        for discovery in poor_discoveries:
            avoided_patterns.extend(discovery.tags[:2])  # Take first 2 tags as patterns to avoid
        
        return {
            'average_rating': avg_rating,
            'preferred_types': preferred_types,
            'avoided_patterns': list(set(avoided_patterns)),
            'type_ratings': type_averages
        }
    
    async def _analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Analyze project structure for exploration opportunities."""
        
        import os
        from pathlib import Path
        
        project = Path(project_path)
        
        # Basic project analysis
        analysis = {
            'has_tests': False,
            'has_docs': False,
            'main_languages': [],
            'framework_indicators': [],
            'complexity_indicators': [],
            'potential_improvements': []
        }
        
        # Check for test directories
        test_dirs = ['test', 'tests', '__tests__', 'spec', 'cypress', 'e2e']
        for test_dir in test_dirs:
            if (project / test_dir).exists():
                analysis['has_tests'] = True
                break
        
        # Check for documentation
        doc_files = ['README.md', 'README.rst', 'docs/', 'documentation/']
        for doc_file in doc_files:
            if (project / doc_file).exists():
                analysis['has_docs'] = True
                break
        
        # Language detection (simplified)
        extensions = {}
        try:
            for file_path in project.rglob('*'):
                if file_path.is_file() and file_path.suffix:
                    ext = file_path.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1
        except (PermissionError, OSError):
            pass
        
        # Top languages by file count
        sorted_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)
        language_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp',
            '.c': 'c', '.rb': 'ruby', '.php': 'php'
        }
        
        analysis['main_languages'] = [
            language_map.get(ext, ext[1:]) for ext, _ in sorted_extensions[:3]
            if ext in language_map
        ]
        
        # Framework indicators (simplified detection)
        framework_files = {
            'package.json': 'node.js',
            'requirements.txt': 'python',
            'Pipfile': 'python', 
            'go.mod': 'go',
            'Cargo.toml': 'rust',
            'pom.xml': 'java',
            'build.gradle': 'java'
        }
        
        for file_name, framework in framework_files.items():
            if (project / file_name).exists():
                analysis['framework_indicators'].append(framework)
        
        # Suggest potential improvements based on analysis
        if not analysis['has_tests']:
            analysis['potential_improvements'].append('testing_coverage')
        
        if not analysis['has_docs']:
            analysis['potential_improvements'].append('documentation')
        
        if len(analysis['main_languages']) > 2:
            analysis['potential_improvements'].append('code_organization')
        
        return analysis
    
    def _assess_skill_levels(self, git_result: GitAnalysisResult, discoveries: List[Discovery]) -> Dict[str, str]:
        """Assess user skill levels in different areas."""
        
        skill_levels = {}
        
        # Language skill assessment based on git patterns
        if git_result.language_patterns and git_result.language_patterns.languages:
            for language, percentage in git_result.language_patterns.languages.items():
                if percentage > 0.4:  # Primary languages
                    skill_levels[language.lower()] = 'advanced'
                elif percentage > 0.1:  # Secondary languages
                    skill_levels[language.lower()] = 'intermediate'
                else:
                    skill_levels[language.lower()] = 'beginner'
        
        # Assess based on discovery success rates
        if discoveries:
            successful_discoveries = [d for d in discoveries if d.user_rating and d.user_rating.value >= 4]
            success_rate = len(successful_discoveries) / len(discoveries) if discoveries else 0
            
            if success_rate > 0.8:
                skill_levels['general_coding'] = 'advanced'
            elif success_rate > 0.6:
                skill_levels['general_coding'] = 'intermediate'
            else:
                skill_levels['general_coding'] = 'beginner'
        
        return skill_levels


class GoalGenerator:
    """Generates exploration goals based on user patterns and context."""
    
    def __init__(self, pattern_storage: PatternStorage, discovery_storage: DiscoveryStorage):
        self.pattern_storage = pattern_storage
        self.discovery_storage = discovery_storage
        self.pattern_analyzer = PatternAnalyzer(pattern_storage, discovery_storage)
        
        # Goal templates by category and risk level
        self._initialize_goal_templates()
    
    def _initialize_goal_templates(self):
        """Initialize goal generation templates."""
        
        self.goal_templates = {
            GoalCategory.CODE_IMPROVEMENT: {
                RiskLevel.CONSERVATIVE: [
                    "Add error handling to {function_name}",
                    "Improve variable naming in {module_name}",
                    "Add docstrings to {class_name}",
                    "Extract common functionality into utility functions"
                ],
                RiskLevel.MODERATE: [
                    "Refactor {module_name} for better separation of concerns",
                    "Implement design patterns for {functionality}",
                    "Add type hints and improve type safety",
                    "Optimize data structures in {component}"
                ],
                RiskLevel.EXPERIMENTAL: [
                    "Experiment with functional programming paradigms",
                    "Implement advanced metaprogramming techniques",
                    "Try cutting-edge language features",
                    "Explore domain-specific language concepts"
                ]
            },
            GoalCategory.PERFORMANCE_OPTIMIZATION: {
                RiskLevel.CONSERVATIVE: [
                    "Add caching to frequently called functions",
                    "Optimize database queries in {module}",
                    "Reduce memory allocation in loops",
                    "Profile and optimize hot code paths"
                ],
                RiskLevel.MODERATE: [
                    "Implement lazy loading for {component}",
                    "Add connection pooling for external services",
                    "Optimize algorithms with better complexity",
                    "Implement parallel processing where beneficial"
                ],
                RiskLevel.EXPERIMENTAL: [
                    "Experiment with advanced caching strategies",
                    "Try machine learning for performance prediction",
                    "Implement custom memory management",
                    "Explore novel concurrency patterns"
                ]
            },
            GoalCategory.TESTING_ENHANCEMENT: {
                RiskLevel.CONSERVATIVE: [
                    "Add unit tests for {function_name}",
                    "Improve test coverage for {module}",
                    "Add integration tests for {feature}",
                    "Create test data fixtures"
                ],
                RiskLevel.MODERATE: [
                    "Implement property-based testing",
                    "Add performance benchmarking tests",
                    "Create end-to-end test scenarios",
                    "Implement test automation workflows"
                ],
                RiskLevel.EXPERIMENTAL: [
                    "Explore chaos engineering techniques",
                    "Implement AI-powered test generation",
                    "Try advanced mocking and stubbing strategies",
                    "Experiment with mutation testing"
                ]
            }
        }
    
    async def generate_goals(
        self, 
        config: GoalGenerationConfig,
        project_path: str = "."
    ) -> List[ExplorationGoal]:
        """Generate exploration goals based on configuration and context."""
        
        # Analyze current context
        context = await self.pattern_analyzer.analyze_current_context(project_path)
        
        # Generate goal candidates
        candidates = await self._generate_goal_candidates(context, config)
        
        # Score and rank candidates
        ranked_candidates = self._score_and_rank_goals(candidates, context, config)
        
        # Select diverse set of goals
        selected_goals = self._select_diverse_goals(ranked_candidates, config)
        
        # Optimize for time budget
        optimized_goals = self._optimize_time_budget(selected_goals, config)
        
        return optimized_goals[:config.max_goals_per_session]
    
    async def _generate_goal_candidates(
        self,
        context: Dict[str, Any],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Generate candidate goals from various sources."""
        
        candidates = []
        
        # Pattern-driven goals
        pattern_goals = self._generate_pattern_driven_goals(context, config)
        candidates.extend(pattern_goals)
        
        # Project structure driven goals
        structure_goals = self._generate_structure_driven_goals(context, config)
        candidates.extend(structure_goals)
        
        # Feedback-driven goals
        feedback_goals = self._generate_feedback_driven_goals(context, config)
        candidates.extend(feedback_goals)
        
        # Discovery gap analysis goals
        gap_goals = self._generate_gap_analysis_goals(context, config)
        candidates.extend(gap_goals)
        
        return candidates
    
    def _generate_pattern_driven_goals(
        self,
        context: Dict[str, Any],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Generate goals based on detected patterns."""
        
        goals = []
        git_patterns = context.get('git_patterns')
        
        if not git_patterns:
            return goals
        
        # Language-specific goals
        if git_patterns.language_patterns and git_patterns.language_patterns.languages:
            primary_language = max(git_patterns.language_patterns.languages.items(), key=lambda x: x[1])[0]
            
            # Generate language-specific improvement goals
            goal = ExplorationGoal(
                id=str(uuid.uuid4()),
                title=f"Enhance {primary_language} code quality",
                description=f"Explore advanced {primary_language} patterns and best practices",
                category=GoalCategory.CODE_IMPROVEMENT,
                risk_level=config.risk_tolerance,
                estimated_time_minutes=45,
                preferred_languages=[primary_language.lower()],
                justification=f"Primary language ({git_patterns.language_patterns.languages[primary_language]:.1%} of codebase)",
                expected_outcomes=[
                    f"Improved {primary_language} code quality",
                    "Better adherence to language best practices",
                    "Enhanced maintainability"
                ]
            )
            goals.append(goal)
        
        # Commit pattern based goals
        if git_patterns.commit_patterns:
            if git_patterns.commit_patterns.commit_frequency > 10:  # Active development
                goal = ExplorationGoal(
                    id=str(uuid.uuid4()),
                    title="Optimize development workflow automation",
                    description="Create tools and scripts to streamline frequent development tasks",
                    category=GoalCategory.TOOLING_ENHANCEMENT,
                    risk_level=RiskLevel.MODERATE,
                    estimated_time_minutes=60,
                    justification=f"High commit frequency ({git_patterns.commit_patterns.commit_frequency} commits/week) indicates active development",
                    expected_outcomes=[
                        "Reduced manual work",
                        "Faster development cycles",
                        "Automated repetitive tasks"
                    ]
                )
                goals.append(goal)
        
        return goals
    
    def _generate_structure_driven_goals(
        self,
        context: Dict[str, Any], 
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Generate goals based on project structure analysis."""
        
        goals = []
        structure = context.get('project_structure', {})
        
        # Testing goals
        if not structure.get('has_tests', False):
            goal = ExplorationGoal(
                id=str(uuid.uuid4()),
                title="Implement comprehensive testing strategy",
                description="Create a robust testing framework with unit, integration, and end-to-end tests",
                category=GoalCategory.TESTING_ENHANCEMENT,
                risk_level=RiskLevel.CONSERVATIVE,
                estimated_time_minutes=90,
                justification="No existing test structure detected",
                expected_outcomes=[
                    "Comprehensive test coverage",
                    "Automated testing pipeline",
                    "Improved code reliability"
                ],
                focus_areas=['testing', 'quality-assurance']
            )
            goals.append(goal)
        
        # Documentation goals
        if not structure.get('has_docs', False):
            goal = ExplorationGoal(
                id=str(uuid.uuid4()),
                title="Create comprehensive project documentation",
                description="Develop clear documentation including API docs, usage examples, and development guides",
                category=GoalCategory.CODE_IMPROVEMENT,
                risk_level=RiskLevel.CONSERVATIVE,
                estimated_time_minutes=60,
                justification="Limited documentation detected",
                expected_outcomes=[
                    "Clear project documentation",
                    "API documentation",
                    "Developer onboarding guides"
                ],
                focus_areas=['documentation', 'developer-experience']
            )
            goals.append(goal)
        
        # Multi-language organization
        if len(structure.get('main_languages', [])) > 2:
            goal = ExplorationGoal(
                id=str(uuid.uuid4()),
                title="Organize multi-language codebase architecture",
                description="Improve organization and boundaries between different programming languages",
                category=GoalCategory.ARCHITECTURAL_IMPROVEMENT,
                risk_level=RiskLevel.MODERATE,
                estimated_time_minutes=120,
                justification=f"Multiple languages detected: {', '.join(structure['main_languages'])}",
                expected_outcomes=[
                    "Clear language boundaries",
                    "Improved code organization",
                    "Better inter-language interfaces"
                ],
                focus_areas=['architecture', 'organization']
            )
            goals.append(goal)
        
        return goals
    
    def _generate_feedback_driven_goals(
        self,
        context: Dict[str, Any],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Generate goals based on user feedback patterns."""
        
        goals = []
        feedback_patterns = context.get('feedback_patterns', {})
        
        # Focus on preferred discovery types
        preferred_types = feedback_patterns.get('preferred_types', [])
        for discovery_type in preferred_types[:2]:  # Top 2 preferred types
            
            # Map discovery types to goal categories
            type_mapping = {
                'code_improvement': GoalCategory.CODE_IMPROVEMENT,
                'performance_optimization': GoalCategory.PERFORMANCE_OPTIMIZATION,
                'testing': GoalCategory.TESTING_ENHANCEMENT,
                'refactoring': GoalCategory.REFACTORING_OPPORTUNITY
            }
            
            category = type_mapping.get(discovery_type, GoalCategory.CODE_IMPROVEMENT)
            
            goal = ExplorationGoal(
                id=str(uuid.uuid4()),
                title=f"Advanced {discovery_type.replace('_', ' ')} exploration",
                description=f"Deep dive into {discovery_type.replace('_', ' ')} techniques based on your preferences",
                category=category,
                risk_level=config.risk_tolerance,
                estimated_time_minutes=75,
                justification=f"High user rating for {discovery_type} discoveries",
                expected_outcomes=[
                    f"Advanced {discovery_type.replace('_', ' ')} implementations",
                    "Techniques aligned with user preferences",
                    "Higher quality solutions"
                ]
            )
            goals.append(goal)
        
        return goals
    
    def _generate_gap_analysis_goals(
        self,
        context: Dict[str, Any],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Generate goals to fill gaps in user's exploration history."""
        
        goals = []
        discoveries = context.get('recent_discoveries', [])
        
        if not discoveries:
            # If no discoveries, generate starter goals
            starter_goal = ExplorationGoal(
                id=str(uuid.uuid4()),
                title="Explore fundamental development patterns",
                description="Start with essential coding patterns and best practices",
                category=GoalCategory.LEARNING_EXPERIMENT,
                risk_level=RiskLevel.CONSERVATIVE,
                estimated_time_minutes=45,
                justification="No previous exploration history",
                expected_outcomes=[
                    "Foundation of coding patterns",
                    "Understanding of best practices",
                    "Starting point for future exploration"
                ]
            )
            goals.append(starter_goal)
            return goals
        
        # Analyze discovery type distribution
        discovery_types = [d.discovery_type.value for d in discoveries]
        type_counts = {dtype: discovery_types.count(dtype) for dtype in set(discovery_types)}
        
        # Find underexplored areas
        all_categories = [cat.value for cat in GoalCategory]
        underexplored = [cat for cat in all_categories if type_counts.get(cat, 0) < 2]
        
        for category_value in underexplored[:2]:  # Fill top 2 gaps
            try:
                category = GoalCategory(category_value)
                goal = ExplorationGoal(
                    id=str(uuid.uuid4()),
                    title=f"Explore {category_value.replace('_', ' ')} opportunities",
                    description=f"Discover new approaches in {category_value.replace('_', ' ')}",
                    category=category,
                    risk_level=RiskLevel.MODERATE,
                    estimated_time_minutes=60,
                    justification=f"Limited exploration in {category_value}",
                    expected_outcomes=[
                        f"New {category_value.replace('_', ' ')} techniques",
                        "Broadened exploration scope",
                        "Diverse skill development"
                    ]
                )
                goals.append(goal)
            except ValueError:
                continue  # Skip invalid category values
        
        return goals
    
    def _score_and_rank_goals(
        self,
        candidates: List[ExplorationGoal],
        context: Dict[str, Any],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Score and rank goal candidates."""
        
        for goal in candidates:
            score = 0.0
            
            # Base priority score
            score += goal.priority_score * 0.2
            
            # Recent work relevance
            recent_discoveries = context.get('recent_discoveries', [])
            if recent_discoveries:
                similar_discoveries = [
                    d for d in recent_discoveries
                    if d.discovery_type.value == goal.category.value
                ]
                if similar_discoveries:
                    avg_rating = sum(d.user_rating.value for d in similar_discoveries if d.user_rating) / max(len([d for d in similar_discoveries if d.user_rating]), 1)
                    score += (avg_rating / 5.0) * config.recent_work_weight
            
            # Skill level appropriateness
            skill_assessment = context.get('skill_assessment', {})
            if goal.preferred_languages:
                for lang in goal.preferred_languages:
                    skill_level = skill_assessment.get(lang, 'beginner')
                    skill_bonus = {'beginner': 0.3, 'intermediate': 0.5, 'advanced': 0.7}.get(skill_level, 0.3)
                    score += skill_bonus * config.skill_level_weight
            
            # Risk alignment
            risk_bonus = {
                RiskLevel.CONSERVATIVE: 0.3,
                RiskLevel.MODERATE: 0.5,
                RiskLevel.EXPERIMENTAL: 0.7
            }.get(goal.risk_level, 0.5)
            
            if goal.risk_level == config.risk_tolerance:
                score += risk_bonus * 0.3  # Bonus for risk alignment
            
            # Time budget fit
            if goal.estimated_time_minutes <= config.time_budget_minutes:
                score += 0.2
            
            # Focus category alignment
            if config.focus_categories and goal.category in config.focus_categories:
                score += 0.3
            
            # Exclude category penalty
            if goal.category in config.exclude_categories:
                score -= 0.5
            
            goal.priority_score = min(max(score, 0.0), 1.0)
        
        # Sort by score (descending)
        return sorted(candidates, key=lambda g: g.priority_score, reverse=True)
    
    def _select_diverse_goals(
        self,
        ranked_candidates: List[ExplorationGoal],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Select a diverse set of goals avoiding too much overlap."""
        
        selected = []
        used_categories = set()
        
        for goal in ranked_candidates:
            if len(selected) >= config.max_goals_per_session:
                break
            
            # Ensure diversity by category
            if goal.category not in used_categories or len(selected) < 2:
                selected.append(goal)
                used_categories.add(goal.category)
            elif config.min_goal_diversity < 0.5:  # Allow some overlap if diversity requirement is low
                selected.append(goal)
        
        return selected
    
    def _optimize_time_budget(
        self,
        goals: List[ExplorationGoal],
        config: GoalGenerationConfig
    ) -> List[ExplorationGoal]:
        """Optimize goal selection to fit within time budget."""
        
        total_time = sum(goal.estimated_time_minutes for goal in goals)
        
        if total_time <= config.time_budget_minutes:
            return goals
        
        # Simple greedy optimization - select highest priority goals that fit budget
        optimized = []
        remaining_budget = config.time_budget_minutes
        
        for goal in sorted(goals, key=lambda g: g.priority_score, reverse=True):
            if goal.estimated_time_minutes <= remaining_budget:
                optimized.append(goal)
                remaining_budget -= goal.estimated_time_minutes
        
        return optimized