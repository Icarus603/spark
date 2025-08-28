"""
Preference mapping engine for understanding developer preferences and learning trajectories.

This module analyzes collected patterns to build predictive models of developer choices,
technology adoption patterns, and learning interests using rule-based inference.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import statistics

from spark.learning.git_patterns import GitAnalysisResult
from spark.learning.style_analyzer import StyleProfile
from spark.learning.confidence_scorer import ConfidenceScore, PatternType


class AdoptionStyle(Enum):
    """Technology adoption patterns."""
    
    EARLY_ADOPTER = "early_adopter"      # Tries new things quickly
    MAINSTREAM = "mainstream"            # Adopts proven technologies
    CONSERVATIVE = "conservative"        # Sticks with established tools
    PRAGMATIC = "pragmatic"             # Adopts based on project needs


class ProblemSolvingApproach(Enum):
    """Problem-solving approach preferences."""
    
    PERFORMANCE_FOCUSED = "performance"     # Optimizes for speed/efficiency
    READABILITY_FOCUSED = "readability"     # Prioritizes clean, clear code
    BALANCED = "balanced"                   # Balances multiple concerns
    SAFETY_FOCUSED = "safety"              # Prioritizes correctness/testing
    RAPID_ITERATION = "rapid_iteration"     # Prioritizes quick development


class LearningStyle(Enum):
    """Learning and exploration preferences."""
    
    DEEP_DIVE = "deep_dive"            # Learns technologies thoroughly
    BREADTH_FIRST = "breadth_first"    # Explores many technologies
    PROJECT_DRIVEN = "project_driven"  # Learns to solve specific problems
    EXPERIMENTAL = "experimental"      # Likes to experiment and prototype


@dataclass
class TechnologyPreference:
    """Preference for a specific technology or category."""
    
    name: str
    category: str  # language, framework, tool, paradigm
    preference_score: float  # 0-1, higher = more preferred
    confidence: float
    usage_frequency: float
    recency_score: float  # How recently it was used
    
    # Context information
    project_types: Set[str] = field(default_factory=set)
    use_cases: List[str] = field(default_factory=list)
    
    # Trends
    adoption_date: Optional[datetime] = None
    usage_trend: str = "stable"  # increasing, decreasing, stable


@dataclass
class ExplorationInterest:
    """Represents interest in exploring a specific area."""
    
    area: str
    interest_score: float  # 0-1
    reasoning: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    
    # Exploration metadata
    difficulty_level: str = "moderate"  # easy, moderate, advanced
    time_investment: str = "medium"     # low, medium, high
    practical_value: float = 0.5       # How practical/applicable it is


@dataclass
class PreferenceProfile:
    """Complete preference profile for a developer."""
    
    # High-level patterns
    adoption_style: AdoptionStyle
    problem_solving_approach: ProblemSolvingApproach
    learning_style: LearningStyle
    
    # Technology preferences
    language_preferences: Dict[str, TechnologyPreference] = field(default_factory=dict)
    framework_preferences: Dict[str, TechnologyPreference] = field(default_factory=dict)
    tool_preferences: Dict[str, TechnologyPreference] = field(default_factory=dict)
    paradigm_preferences: Dict[str, TechnologyPreference] = field(default_factory=dict)
    
    # Exploration interests
    exploration_interests: List[ExplorationInterest] = field(default_factory=list)
    
    # Context patterns
    work_vs_personal: Dict[str, Any] = field(default_factory=dict)
    project_size_preferences: Dict[str, float] = field(default_factory=dict)
    
    # Meta information
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Learning trajectory
    skill_development_areas: List[str] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    next_learning_suggestions: List[str] = field(default_factory=list)


class PreferenceAnalyzer:
    """Analyzes patterns to extract preference information."""
    
    def __init__(self):
        # Technology category mappings
        self.language_categories = {
            'python': 'dynamic_typed',
            'javascript': 'dynamic_typed', 
            'typescript': 'static_typed',
            'go': 'static_compiled',
            'rust': 'static_compiled',
            'java': 'static_compiled',
            'swift': 'static_compiled',
            'kotlin': 'static_compiled'
        }
        
        self.framework_indicators = {
            'react', 'vue', 'angular', 'svelte',  # Frontend
            'express', 'fastapi', 'flask', 'django',  # Backend
            'tensorflow', 'pytorch', 'scikit-learn'  # ML
        }
        
        # Technology recency weights (newer = higher score)
        self.technology_ages = {
            'rust': 0.9, 'typescript': 0.8, 'go': 0.8, 'swift': 0.7,
            'python': 0.6, 'javascript': 0.5, 'java': 0.4, 'c': 0.2
        }
    
    def analyze_git_preferences(self, git_analysis: GitAnalysisResult) -> Dict[str, Any]:
        """Extract preferences from git analysis."""
        
        preferences = {
            'commit_style': self._analyze_commit_style(git_analysis.commit_patterns),
            'workflow_style': self._analyze_workflow_style(git_analysis.branch_patterns),
            'collaboration_style': self._analyze_collaboration_style(git_analysis),
            'language_adoption': self._analyze_language_adoption(git_analysis.language_patterns)
        }
        
        return preferences
    
    def analyze_style_preferences(self, style_profile: StyleProfile) -> Dict[str, Any]:
        """Extract preferences from style analysis."""
        
        preferences = {
            'code_organization': self._analyze_code_organization(style_profile),
            'type_safety_preference': self._analyze_type_safety(style_profile),
            'documentation_preference': self._analyze_documentation(style_profile),
            'complexity_tolerance': self._analyze_complexity_tolerance(style_profile),
            'architectural_style': self._analyze_architectural_style(style_profile)
        }
        
        return preferences
    
    def _analyze_commit_style(self, commit_patterns) -> Dict[str, Any]:
        """Analyze commit style preferences."""
        
        if commit_patterns.message_style == "conventional":
            discipline_score = 0.8
        elif commit_patterns.message_style == "descriptive":
            discipline_score = 0.6
        else:
            discipline_score = 0.3
        
        size_preference = "small" if commit_patterns.prefers_small_commits else "large"
        
        return {
            'discipline_score': discipline_score,
            'commit_size_preference': size_preference,
            'frequency_preference': min(commit_patterns.commit_frequency / 3.0, 1.0),
            'approach': "methodical" if discipline_score > 0.6 else "flexible"
        }
    
    def _analyze_workflow_style(self, branch_patterns) -> Dict[str, Any]:
        """Analyze workflow preferences."""
        
        workflow_scores = {
            'gitflow': 0.8,      # Disciplined, structured
            'feature_branch': 0.6,  # Organized
            'trunk': 0.4,        # Rapid iteration
            'personal': 0.2      # Informal
        }
        
        organization_score = workflow_scores.get(branch_patterns.workflow_type, 0.5)
        
        return {
            'organization_score': organization_score,
            'workflow_type': branch_patterns.workflow_type,
            'collaboration_readiness': 0.8 if branch_patterns.uses_pr_workflow else 0.3,
            'approach': "structured" if organization_score > 0.6 else "flexible"
        }
    
    def _analyze_collaboration_style(self, git_analysis: GitAnalysisResult) -> Dict[str, Any]:
        """Analyze collaboration preferences."""
        
        # Simple analysis based on available data
        commit_count = git_analysis.commit_count
        
        if commit_count > 100:
            collaboration_comfort = 0.7
        elif commit_count > 20:
            collaboration_comfort = 0.5
        else:
            collaboration_comfort = 0.3
        
        return {
            'collaboration_comfort': collaboration_comfort,
            'communication_style': "structured" if git_analysis.commit_patterns.message_style == "conventional" else "informal"
        }
    
    def _analyze_language_adoption(self, language_patterns) -> Dict[str, Any]:
        """Analyze language adoption patterns."""
        
        if not language_patterns.languages:
            return {'adoption_style': AdoptionStyle.CONSERVATIVE.value, 'diversity_score': 0.0}
        
        # Calculate diversity score
        diversity_score = len(language_patterns.languages) / 10.0  # Normalize to 0-1
        
        # Check for modern languages
        modern_languages = {'rust', 'go', 'typescript', 'swift', 'kotlin'}
        modern_usage = sum(
            usage for lang, usage in language_patterns.languages.items()
            if lang.lower() in modern_languages
        )
        
        # Determine adoption style
        if modern_usage > 0.3:  # >30% modern language usage
            adoption_style = AdoptionStyle.EARLY_ADOPTER
        elif diversity_score > 0.5:  # High diversity
            adoption_style = AdoptionStyle.PRAGMATIC
        elif diversity_score > 0.3:
            adoption_style = AdoptionStyle.MAINSTREAM
        else:
            adoption_style = AdoptionStyle.CONSERVATIVE
        
        return {
            'adoption_style': adoption_style.value,
            'diversity_score': min(diversity_score, 1.0),
            'modern_tech_usage': modern_usage,
            'primary_language_dominance': max(language_patterns.languages.values()) if language_patterns.languages else 0
        }
    
    def _analyze_code_organization(self, style_profile: StyleProfile) -> Dict[str, Any]:
        """Analyze code organization preferences."""
        
        organization_indicators = {
            'modular': 0.7,
            'layered': 0.8,
            'domain': 0.9,
            'flat': 0.3
        }
        
        organization_score = organization_indicators.get(style_profile.preferred_structure, 0.5)
        
        return {
            'organization_score': organization_score,
            'structure_preference': style_profile.preferred_structure,
            'import_discipline': 0.7 if style_profile.import_organization == "grouped" else 0.4
        }
    
    def _analyze_type_safety(self, style_profile: StyleProfile) -> Dict[str, Any]:
        """Analyze type safety preferences."""
        
        type_safety_score = style_profile.type_hint_usage
        
        if type_safety_score > 0.7:
            preference = "strong"
        elif type_safety_score > 0.3:
            preference = "moderate"
        else:
            preference = "minimal"
        
        return {
            'type_safety_score': type_safety_score,
            'preference': preference,
            'safety_vs_speed': "safety" if type_safety_score > 0.5 else "speed"
        }
    
    def _analyze_documentation(self, style_profile: StyleProfile) -> Dict[str, Any]:
        """Analyze documentation preferences."""
        
        doc_score = style_profile.docstring_coverage
        
        if doc_score > 0.7:
            approach = "thorough"
        elif doc_score > 0.4:
            approach = "selective"
        else:
            approach = "minimal"
        
        return {
            'documentation_score': doc_score,
            'approach': approach,
            'self_documenting_preference': 0.8 if doc_score < 0.3 else 0.4
        }
    
    def _analyze_complexity_tolerance(self, style_profile: StyleProfile) -> Dict[str, Any]:
        """Analyze complexity tolerance."""
        
        # Analyze preferred complexity metrics
        function_length_score = 1.0 - abs(style_profile.preferred_function_length - 20) / 50
        complexity_score = 1.0 - abs(style_profile.preferred_complexity - 5) / 15
        nesting_score = 1.0 - abs(style_profile.preferred_nesting_depth - 3) / 10
        
        tolerance_score = statistics.mean([
            max(0, function_length_score),
            max(0, complexity_score),
            max(0, nesting_score)
        ])
        
        if tolerance_score > 0.7:
            tolerance = "low"  # Prefers simple code
        elif tolerance_score > 0.4:
            tolerance = "moderate"
        else:
            tolerance = "high"  # Comfortable with complex code
        
        return {
            'tolerance_score': tolerance_score,
            'tolerance_level': tolerance,
            'simplicity_preference': tolerance_score
        }
    
    def _analyze_architectural_style(self, style_profile: StyleProfile) -> Dict[str, Any]:
        """Analyze architectural preferences."""
        
        # Based on OOP vs functional preference
        if style_profile.oop_vs_functional > 0.7:
            style = "object_oriented"
        elif style_profile.oop_vs_functional < 0.3:
            style = "functional"
        else:
            style = "mixed"
        
        # Async usage indicates modern/performance focus
        async_preference = style_profile.async_usage > 0.3
        
        return {
            'architectural_style': style,
            'oop_vs_functional': style_profile.oop_vs_functional,
            'async_adoption': async_preference,
            'modern_patterns': async_preference
        }


class PreferenceMapper:
    """Main preference mapping engine."""
    
    def __init__(self):
        self.analyzer = PreferenceAnalyzer()
        self.cached_profiles: Dict[str, PreferenceProfile] = {}
    
    def build_preference_profile(
        self,
        git_analyses: List[GitAnalysisResult],
        style_profiles: List[StyleProfile],
        confidence_scores: Dict[PatternType, ConfidenceScore]
    ) -> PreferenceProfile:
        """Build a complete preference profile."""
        
        # Analyze individual components
        git_prefs = []
        for git_analysis in git_analyses:
            prefs = self.analyzer.analyze_git_preferences(git_analysis)
            git_prefs.append(prefs)
        
        style_prefs = []
        for style_profile in style_profiles:
            prefs = self.analyzer.analyze_style_preferences(style_profile)
            style_prefs.append(prefs)
        
        # Aggregate preferences
        aggregated_git = self._aggregate_git_preferences(git_prefs)
        aggregated_style = self._aggregate_style_preferences(style_prefs)
        
        # Determine high-level patterns
        adoption_style = self._determine_adoption_style(aggregated_git, aggregated_style)
        problem_solving_approach = self._determine_problem_solving_approach(aggregated_git, aggregated_style)
        learning_style = self._determine_learning_style(aggregated_git, aggregated_style)
        
        # Build technology preferences
        language_prefs = self._build_language_preferences(git_analyses, style_profiles)
        
        # Generate exploration interests
        exploration_interests = self._generate_exploration_interests(
            aggregated_git, aggregated_style, language_prefs, confidence_scores
        )
        
        # Calculate confidence scores
        profile_confidence = self._calculate_profile_confidence(confidence_scores)
        
        return PreferenceProfile(
            adoption_style=adoption_style,
            problem_solving_approach=problem_solving_approach,
            learning_style=learning_style,
            language_preferences=language_prefs,
            exploration_interests=exploration_interests,
            confidence_scores=profile_confidence
        )
    
    def _aggregate_git_preferences(self, git_prefs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate git preferences across repositories."""
        if not git_prefs:
            return {}
        
        # Average numerical scores
        commit_disciplines = [p.get('commit_style', {}).get('discipline_score', 0.5) for p in git_prefs]
        organization_scores = [p.get('workflow_style', {}).get('organization_score', 0.5) for p in git_prefs]
        
        # Most common categorical preferences
        adoption_styles = [p.get('language_adoption', {}).get('adoption_style', 'mainstream') for p in git_prefs]
        adoption_style_counts = Counter(adoption_styles)
        most_common_adoption = adoption_style_counts.most_common(1)[0][0] if adoption_styles else 'mainstream'
        
        return {
            'discipline_score': statistics.mean(commit_disciplines) if commit_disciplines else 0.5,
            'organization_score': statistics.mean(organization_scores) if organization_scores else 0.5,
            'adoption_style': most_common_adoption,
            'diversity_scores': [p.get('language_adoption', {}).get('diversity_score', 0.3) for p in git_prefs]
        }
    
    def _aggregate_style_preferences(self, style_prefs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate style preferences across projects."""
        if not style_prefs:
            return {}
        
        # Average scores
        type_safety_scores = [p.get('type_safety_preference', {}).get('type_safety_score', 0.3) for p in style_prefs]
        doc_scores = [p.get('documentation_preference', {}).get('documentation_score', 0.3) for p in style_prefs]
        complexity_scores = [p.get('complexity_tolerance', {}).get('tolerance_score', 0.5) for p in style_prefs]
        
        return {
            'type_safety_score': statistics.mean(type_safety_scores) if type_safety_scores else 0.3,
            'documentation_score': statistics.mean(doc_scores) if doc_scores else 0.3,
            'complexity_tolerance': statistics.mean(complexity_scores) if complexity_scores else 0.5,
            'organization_scores': [p.get('code_organization', {}).get('organization_score', 0.5) for p in style_prefs]
        }
    
    def _determine_adoption_style(self, git_prefs: Dict[str, Any], style_prefs: Dict[str, Any]) -> AdoptionStyle:
        """Determine technology adoption style."""
        
        # Primary indicator: git-based adoption analysis
        git_adoption = git_prefs.get('adoption_style', 'mainstream')
        
        # Secondary indicators
        type_safety = style_prefs.get('type_safety_score', 0.3)
        diversity = statistics.mean(git_prefs.get('diversity_scores', [0.3]))
        
        # Map to enum
        if git_adoption == 'early_adopter' or (type_safety > 0.6 and diversity > 0.5):
            return AdoptionStyle.EARLY_ADOPTER
        elif git_adoption == 'conservative' or (type_safety < 0.3 and diversity < 0.3):
            return AdoptionStyle.CONSERVATIVE
        elif diversity > 0.5:
            return AdoptionStyle.PRAGMATIC
        else:
            return AdoptionStyle.MAINSTREAM
    
    def _determine_problem_solving_approach(self, git_prefs: Dict[str, Any], style_prefs: Dict[str, Any]) -> ProblemSolvingApproach:
        """Determine problem-solving approach."""
        
        discipline_score = git_prefs.get('discipline_score', 0.5)
        type_safety_score = style_prefs.get('type_safety_score', 0.3)
        doc_score = style_prefs.get('documentation_score', 0.3)
        complexity_tolerance = style_prefs.get('complexity_tolerance', 0.5)
        
        # Calculate approach scores
        safety_score = (type_safety_score + doc_score + discipline_score) / 3
        performance_score = complexity_tolerance  # Higher complexity tolerance may indicate performance focus
        readability_score = (1 - complexity_tolerance + doc_score) / 2
        
        # Determine primary approach
        if safety_score > 0.7:
            return ProblemSolvingApproach.SAFETY_FOCUSED
        elif performance_score > 0.7 and readability_score < 0.4:
            return ProblemSolvingApproach.PERFORMANCE_FOCUSED
        elif readability_score > 0.7:
            return ProblemSolvingApproach.READABILITY_FOCUSED
        elif discipline_score < 0.4:  # Low discipline = rapid iteration
            return ProblemSolvingApproach.RAPID_ITERATION
        else:
            return ProblemSolvingApproach.BALANCED
    
    def _determine_learning_style(self, git_prefs: Dict[str, Any], style_prefs: Dict[str, Any]) -> LearningStyle:
        """Determine learning style."""
        
        diversity = statistics.mean(git_prefs.get('diversity_scores', [0.3]))
        organization_score = git_prefs.get('organization_score', 0.5)
        
        # Heuristic-based determination
        if diversity > 0.6:
            return LearningStyle.BREADTH_FIRST
        elif organization_score > 0.7:
            return LearningStyle.DEEP_DIVE
        elif organization_score < 0.4:
            return LearningStyle.EXPERIMENTAL
        else:
            return LearningStyle.PROJECT_DRIVEN
    
    def _build_language_preferences(
        self, 
        git_analyses: List[GitAnalysisResult], 
        style_profiles: List[StyleProfile]
    ) -> Dict[str, TechnologyPreference]:
        """Build language preference mappings."""
        
        language_prefs = {}
        
        # Aggregate language usage across all analyses
        language_usage = defaultdict(float)
        for git_analysis in git_analyses:
            for lang, usage in git_analysis.language_patterns.languages.items():
                language_usage[lang] += usage
        
        # Normalize usage scores
        total_usage = sum(language_usage.values())
        if total_usage > 0:
            for lang in language_usage:
                language_usage[lang] /= total_usage
        
        # Create preferences
        for lang, usage in language_usage.items():
            recency_score = self.analyzer.technology_ages.get(lang, 0.5)
            
            preference = TechnologyPreference(
                name=lang,
                category='language',
                preference_score=usage,
                confidence=min(usage * 2, 1.0),  # Higher usage = higher confidence
                usage_frequency=usage,
                recency_score=recency_score
            )
            
            language_prefs[lang] = preference
        
        return language_prefs
    
    def _generate_exploration_interests(
        self,
        git_prefs: Dict[str, Any],
        style_prefs: Dict[str, Any],
        language_prefs: Dict[str, TechnologyPreference],
        confidence_scores: Dict[PatternType, ConfidenceScore]
    ) -> List[ExplorationInterest]:
        """Generate exploration interests based on patterns."""
        
        interests = []
        
        # Based on adoption style
        adoption_style = git_prefs.get('adoption_style', 'mainstream')
        if adoption_style == 'early_adopter':
            interests.append(ExplorationInterest(
                area="Cutting-edge language features",
                interest_score=0.8,
                reasoning=["Shows early adoption patterns", "High diversity in tech usage"],
                difficulty_level="advanced"
            ))
        
        # Based on type safety preference
        type_safety_score = style_prefs.get('type_safety_score', 0.3)
        if type_safety_score > 0.6:
            interests.append(ExplorationInterest(
                area="Advanced type systems",
                interest_score=type_safety_score,
                reasoning=["High type hint usage indicates type safety preference"],
                related_patterns=["style_structure", "style_naming"]
            ))
        
        # Based on primary language
        primary_lang = max(language_prefs.items(), key=lambda x: x[1].usage_frequency)[0] if language_prefs else None
        
        if primary_lang == 'python':
            interests.extend([
                ExplorationInterest(
                    area="Python performance optimization",
                    interest_score=0.7,
                    reasoning=["Primary Python user", "May benefit from performance insights"],
                    practical_value=0.8
                ),
                ExplorationInterest(
                    area="Modern Python features",
                    interest_score=0.6,
                    reasoning=["Python usage suggests interest in language evolution"]
                )
            ])
        
        # Based on complexity tolerance
        complexity_tolerance = style_prefs.get('complexity_tolerance', 0.5)
        if complexity_tolerance < 0.4:  # Prefers simple code
            interests.append(ExplorationInterest(
                area="Code simplification patterns",
                interest_score=0.7,
                reasoning=["Shows preference for simple, readable code"],
                practical_value=0.9
            ))
        
        # Based on confidence levels
        overall_confidence = statistics.mean([
            score.overall_confidence 
            for score in confidence_scores.values()
        ]) if confidence_scores else 0.5
        
        if overall_confidence > 0.8:
            interests.append(ExplorationInterest(
                area="Advanced architectural patterns",
                interest_score=0.8,
                reasoning=["High pattern confidence suggests readiness for advanced topics"],
                difficulty_level="advanced"
            ))
        
        return sorted(interests, key=lambda x: x.interest_score, reverse=True)[:10]  # Top 10
    
    def _calculate_profile_confidence(self, confidence_scores: Dict[PatternType, ConfidenceScore]) -> Dict[str, float]:
        """Calculate confidence scores for preference profile."""
        
        if not confidence_scores:
            return {'overall': 0.3, 'preferences': 0.3, 'exploration': 0.2}
        
        # Overall confidence from pattern analysis
        overall = statistics.mean([score.overall_confidence for score in confidence_scores.values()])
        
        # Preference confidence based on sample sizes
        sample_sizes = [score.metrics.sample_size for score in confidence_scores.values()]
        preference_confidence = min(statistics.mean(sample_sizes) / 50, 1.0) if sample_sizes else 0.3
        
        # Exploration confidence (higher overall confidence = more exploration ready)
        exploration_confidence = min(overall * 1.2, 1.0)
        
        return {
            'overall': overall,
            'preferences': preference_confidence,
            'exploration': exploration_confidence,
            'technology_mapping': min(preference_confidence * 1.1, 1.0)
        }