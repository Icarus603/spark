"""
Discovery curation and ranking system.

This module provides intelligent curation and ranking of discoveries to help users
identify the most valuable and relevant exploration results.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re
import math
from enum import Enum

from spark.discovery.models import Discovery, DiscoveryType, FeedbackRating
from spark.storage.discovery_storage import DiscoveryStorage
from spark.discovery.ranking_methods import RankingCalculator
from spark.discovery.analysis_methods import DiscoveryAnalyzer


class RankingFactor(Enum):
    """Factors used in multi-factor ranking."""
    TECHNICAL_VALUE = "technical_value"
    RELEVANCE = "relevance"
    ACTIONABILITY = "actionability" 
    NOVELTY = "novelty"
    IMPACT_POTENTIAL = "impact_potential"
    USER_ALIGNMENT = "user_alignment"
    RECENCY = "recency"
    COMPLEXITY = "complexity"


@dataclass
class ImpactAnalysis:
    """Analysis of discovery impact and benefits."""
    performance_improvement: float = 0.0
    code_quality_boost: float = 0.0
    learning_value: float = 0.0
    time_savings: float = 0.0
    maintainability_gain: float = 0.0
    reusability_score: float = 0.0
    overall_impact: float = 0.0
    confidence_level: float = 0.0
    quantified_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationAssessment:
    """Assessment of integration difficulty and requirements."""
    difficulty_level: str = "moderate"  # easy, moderate, hard, expert
    estimated_time_minutes: int = 30
    prerequisites: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    rollback_complexity: str = "simple"  # simple, moderate, complex
    conflict_risk: float = 0.3
    testing_requirements: List[str] = field(default_factory=list)
    dependencies_needed: List[str] = field(default_factory=list)
    

@dataclass
class DiscoveryNarrative:
    """Generated narrative for discovery presentation."""
    headline: str
    summary: str
    value_proposition: str
    key_benefits: List[str] = field(default_factory=list)
    integration_story: str = ""
    technical_highlights: List[str] = field(default_factory=list)
    risk_assessment: str = ""


@dataclass
class CurationCriteria:
    """Criteria for discovery curation."""
    min_confidence: float = 0.5
    max_age_days: Optional[int] = None
    discovery_types: Optional[List[DiscoveryType]] = None
    min_impact: float = 0.0
    include_rated_only: bool = False
    exclude_integrated: bool = False
    ranking_weights: Dict[RankingFactor, float] = field(default_factory=lambda: {
        RankingFactor.TECHNICAL_VALUE: 0.25,
        RankingFactor.RELEVANCE: 0.20,
        RankingFactor.ACTIONABILITY: 0.15,
        RankingFactor.IMPACT_POTENTIAL: 0.15,
        RankingFactor.NOVELTY: 0.10,
        RankingFactor.USER_ALIGNMENT: 0.10,
        RankingFactor.RECENCY: 0.05
    })
    focus_factors: List[RankingFactor] = field(default_factory=list)


class DiscoveryCurator:
    """Curates and ranks discoveries for optimal presentation."""
    
    def __init__(self, storage: Optional[DiscoveryStorage] = None):
        self.storage = storage or DiscoveryStorage()
        self.ranking_calculator = RankingCalculator()
        self.analyzer = DiscoveryAnalyzer()
    
    def curate_discoveries(
        self,
        limit: int = 10,
        criteria: Optional[CurationCriteria] = None
    ) -> List[Discovery]:
        """Curate and rank discoveries based on advanced criteria."""
        
        criteria = criteria or CurationCriteria()
        
        # Get all discoveries
        all_discoveries = self.storage.get_discoveries(limit=limit * 2)  # Get more to filter
        
        # Filter discoveries
        filtered_discoveries = self._filter_discoveries(all_discoveries, criteria)
        
        # Rank discoveries with multi-factor algorithm
        ranked_discoveries = self._rank_discoveries(filtered_discoveries, criteria)
        
        # Return top discoveries
        return ranked_discoveries[:limit]
    
    def get_featured_discovery(self) -> Optional[Discovery]:
        """Get the most featured-worthy discovery."""
        
        criteria = CurationCriteria(
            min_confidence=0.7,
            min_impact=0.6,
            max_age_days=7  # Recent discoveries preferred for featuring
        )
        
        discoveries = self.curate_discoveries(limit=5, criteria=criteria)
        
        if not discoveries:
            return None
        
        # Return the top-ranked discovery
        return discoveries[0]
    
    def get_recent_discoveries(self, days: int = 7, limit: int = 10) -> List[Discovery]:
        """Get recent discoveries from the last N days."""
        
        criteria = CurationCriteria(
            max_age_days=days,
            min_confidence=0.4  # Lower threshold for recent items
        )
        
        return self.curate_discoveries(limit=limit, criteria=criteria)
    
    def get_discoveries_by_type(self, discovery_type: DiscoveryType, limit: int = 10) -> List[Discovery]:
        """Get discoveries of a specific type."""
        
        criteria = CurationCriteria(
            discovery_types=[discovery_type],
            min_confidence=0.5
        )
        
        return self.curate_discoveries(limit=limit, criteria=criteria)
    
    def get_high_impact_discoveries(self, limit: int = 5) -> List[Discovery]:
        """Get the highest impact discoveries."""
        
        criteria = CurationCriteria(
            min_impact=0.7,
            min_confidence=0.6
        )
        
        return self.curate_discoveries(limit=limit, criteria=criteria)
    
    def get_discoveries_needing_feedback(self, limit: int = 5) -> List[Discovery]:
        """Get discoveries that need user feedback."""
        
        all_discoveries = self.storage.get_discoveries(limit=50)
        
        # Find discoveries without ratings that are worth rating
        unrated_discoveries = [
            d for d in all_discoveries
            if d.user_rating is None and d.confidence_score > 0.6
        ]
        
        # Rank by potential value
        ranked = self._rank_discoveries(unrated_discoveries)
        
        return ranked[:limit]
    
    def _filter_discoveries(self, discoveries: List[Discovery], criteria: CurationCriteria) -> List[Discovery]:
        """Filter discoveries based on criteria."""
        
        filtered = []
        
        for discovery in discoveries:
            # Check confidence threshold
            if discovery.confidence_score < criteria.min_confidence:
                continue
            
            # Check impact threshold
            if discovery.impact_score < criteria.min_impact:
                continue
            
            # Check age
            if criteria.max_age_days:
                age_days = (datetime.now() - discovery.created_at).days
                if age_days > criteria.max_age_days:
                    continue
            
            # Check discovery type
            if criteria.discovery_types and discovery.discovery_type not in criteria.discovery_types:
                continue
            
            # Check rating requirement
            if criteria.include_rated_only and discovery.user_rating is None:
                continue
            
            # Check integration status
            if criteria.exclude_integrated and discovery.integrated_at is not None:
                continue
            
            filtered.append(discovery)
        
        return filtered
    
    def _rank_discoveries(self, discoveries: List[Discovery], criteria: Optional[CurationCriteria] = None) -> List[Discovery]:
        """Rank discoveries using advanced multi-factor ranking algorithms."""
        
        criteria = criteria or CurationCriteria()
        
        def calculate_multi_factor_score(discovery: Discovery) -> Tuple[float, Dict[str, float]]:
            """Calculate comprehensive multi-factor ranking score."""
            
            factor_scores = {}
            
            # Technical Value Score
            factor_scores[RankingFactor.TECHNICAL_VALUE.value] = self._calculate_technical_value_score(discovery)
            
            # Relevance Score  
            factor_scores[RankingFactor.RELEVANCE.value] = self._calculate_relevance_score(discovery)
            
            # Actionability Score
            factor_scores[RankingFactor.ACTIONABILITY.value] = self._calculate_actionability_score(discovery)
            
            # Impact Potential Score
            factor_scores[RankingFactor.IMPACT_POTENTIAL.value] = self._calculate_impact_potential_score(discovery)
            
            # Novelty Score (enhanced)
            factor_scores[RankingFactor.NOVELTY.value] = self._calculate_enhanced_novelty_score(discovery)
            
            # User Alignment Score
            factor_scores[RankingFactor.USER_ALIGNMENT.value] = self._calculate_user_alignment_score(discovery)
            
            # Recency Score
            factor_scores[RankingFactor.RECENCY.value] = self._calculate_recency_score(discovery)
            
            # Calculate weighted final score
            final_score = 0.0
            weights = criteria.ranking_weights
            
            for factor, weight in weights.items():
                score = factor_scores.get(factor.value, 0.0)
                # Apply focus boost if this factor is in focus
                if factor in criteria.focus_factors:
                    score *= 1.3  # 30% boost for focused factors
                final_score += weight * score
                
            # Apply user feedback multiplier (very important)
            if discovery.user_rating:
                rating_multiplier = 0.7 + (discovery.user_rating.value / 10.0)  # 0.8 to 1.2
                final_score *= rating_multiplier
            
            return final_score, factor_scores
        
        # Calculate scores and sort
        scored_discoveries = []
        for discovery in discoveries:
            score, factor_breakdown = calculate_multi_factor_score(discovery)
            scored_discoveries.append((discovery, score, factor_breakdown))
        
        # Sort by score (descending)
        scored_discoveries.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted discoveries with score metadata
        ranked_discoveries = []
        for discovery, score, factors in scored_discoveries:
            # Store ranking metadata in discovery for later use
            discovery.metadata = discovery.metadata or {}
            discovery.metadata['ranking_score'] = score
            discovery.metadata['factor_scores'] = factors
            ranked_discoveries.append(discovery)
        
        return ranked_discoveries
    
    # Ranking factor calculation methods (delegate to RankingCalculator)
    def _calculate_technical_value_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_technical_value_score(discovery)
    
    def _calculate_relevance_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_relevance_score(discovery)
    
    def _calculate_actionability_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_actionability_score(discovery)
    
    def _calculate_impact_potential_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_impact_potential_score(discovery)
    
    def _calculate_enhanced_novelty_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_enhanced_novelty_score(discovery)
    
    def _calculate_user_alignment_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_user_alignment_score(discovery)
    
    def _calculate_recency_score(self, discovery: Discovery) -> float:
        return self.ranking_calculator.calculate_recency_score(discovery)
    
    def get_curation_stats(self) -> Dict[str, Any]:
        """Get curation statistics."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        
        if not all_discoveries:
            return {'total': 0}
        
        stats = {
            'total': len(all_discoveries),
            'high_confidence': len([d for d in all_discoveries if d.confidence_score > 0.8]),
            'high_impact': len([d for d in all_discoveries if d.impact_score > 0.7]),
            'integration_ready': len([d for d in all_discoveries if d.integration_ready]),
            'with_feedback': len([d for d in all_discoveries if d.user_rating is not None]),
            'recent_7_days': len([d for d in all_discoveries if (datetime.now() - d.created_at).days <= 7]),
        }
        
        # Type distribution
        type_counts = {}
        for discovery in all_discoveries:
            type_name = discovery.discovery_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        stats['type_distribution'] = type_counts
        
        # Average scores
        if all_discoveries:
            stats['avg_confidence'] = sum(d.confidence_score for d in all_discoveries) / len(all_discoveries)
            stats['avg_impact'] = sum(d.impact_score for d in all_discoveries) / len(all_discoveries)
            stats['avg_novelty'] = sum(d.novelty_score for d in all_discoveries) / len(all_discoveries)
        
        # Rating distribution
        rated_discoveries = [d for d in all_discoveries if d.user_rating]
        if rated_discoveries:
            rating_counts = {}
            for discovery in rated_discoveries:
                rating = discovery.user_rating.value
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
            stats['rating_distribution'] = rating_counts
            stats['avg_rating'] = sum(d.user_rating.value for d in rated_discoveries) / len(rated_discoveries)
        
        return stats
    
    def suggest_exploration_topics(self, limit: int = 5) -> List[str]:
        """Suggest topics for future exploration based on successful discoveries."""
        
        # Get high-rated discoveries
        high_rated = []
        all_discoveries = self.storage.get_discoveries(limit=100)
        
        for discovery in all_discoveries:
            if (discovery.user_rating and discovery.user_rating.value >= 4) or discovery.overall_score() > 0.8:
                high_rated.append(discovery)
        
        if not high_rated:
            return [
                "Create utility functions for common tasks",
                "Implement testing strategies for your codebase",
                "Explore performance optimization techniques",
                "Develop code organization patterns",
                "Create documentation and examples"
            ]
        
        # Analyze successful patterns
        successful_tags = []
        successful_types = []
        
        for discovery in high_rated:
            successful_tags.extend(discovery.tags)
            successful_types.append(discovery.discovery_type.value)
        
        # Generate suggestions based on patterns
        suggestions = []
        
        # From successful tags
        common_tags = sorted(set(successful_tags), key=successful_tags.count, reverse=True)[:3]
        for tag in common_tags:
            suggestions.append(f"Explore more {tag}-related implementations")
        
        # From successful types
        common_types = sorted(set(successful_types), key=successful_types.count, reverse=True)[:2]
        for discovery_type in common_types:
            type_name = discovery_type.replace('_', ' ').title()
            suggestions.append(f"Focus on {type_name} opportunities")
        
        # Add variety
        suggestions.extend([
            "Experiment with new programming patterns",
            "Create developer tools and utilities", 
            "Explore integration with external APIs"
        ])
        
        return suggestions[:limit]
    
    def analyze_discovery_impact(self, discovery: Discovery) -> ImpactAnalysis:
        """Perform detailed impact analysis on a discovery."""
        
        impact = ImpactAnalysis()
        
        # Performance analysis
        if discovery.discovery_type == DiscoveryType.PERFORMANCE_OPTIMIZATION:
            impact.performance_improvement = discovery.impact_score * 0.8 + 0.2
            
            # Look for performance metrics in metadata
            for result in discovery.exploration_results:
                if 'performance' in result.metadata:
                    perf_data = result.metadata['performance']
                    if isinstance(perf_data, dict):
                        if 'speedup' in perf_data:
                            impact.quantified_metrics['speedup'] = perf_data['speedup']
                        if 'memory_reduction' in perf_data:
                            impact.quantified_metrics['memory_reduction'] = perf_data['memory_reduction']
        
        # Code quality analysis
        impact.code_quality_boost = self.analyzer.analyze_code_quality_impact(discovery)
        
        # Learning value analysis
        learning_keywords = ['tutorial', 'example', 'pattern', 'best practice', 'guide']
        desc_lower = discovery.description.lower()
        learning_score = sum(0.1 for keyword in learning_keywords if keyword in desc_lower)
        impact.learning_value = min(1.0, learning_score + discovery.novelty_score * 0.5)
        
        # Time savings estimation
        impact.time_savings = self.analyzer.estimate_time_savings(discovery)
        
        # Maintainability gain
        if discovery.discovery_type in [DiscoveryType.REFACTORING, DiscoveryType.CODE_IMPROVEMENT]:
            impact.maintainability_gain = discovery.impact_score * 0.7 + 0.1
        
        # Reusability score
        impact.reusability_score = self.analyzer.calculate_reusability_score(discovery)
        
        # Overall impact (weighted combination)
        impact.overall_impact = (
            impact.performance_improvement * 0.25 +
            impact.code_quality_boost * 0.20 +
            impact.learning_value * 0.15 +
            impact.time_savings * 0.15 +
            impact.maintainability_gain * 0.15 +
            impact.reusability_score * 0.10
        )
        
        # Confidence level based on data quality
        impact.confidence_level = discovery.confidence_score
        
        return impact
    
    def assess_integration_difficulty(self, discovery: Discovery) -> IntegrationAssessment:
        """Assess the difficulty and requirements for integrating a discovery."""
        
        assessment = IntegrationAssessment()
        
        # Base difficulty from integration risk
        risk_to_difficulty = {
            'low': 'easy',
            'moderate': 'moderate', 
            'high': 'hard'
        }
        assessment.difficulty_level = risk_to_difficulty.get(discovery.integration_risk, 'moderate')
        
        # Estimate time based on complexity
        complexity_factors = 0
        
        # Count code artifacts
        total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        complexity_factors += total_artifacts
        
        # Count integration instructions
        complexity_factors += len(discovery.integration_instructions)
        
        # Discovery type complexity
        type_complexity = {
            DiscoveryType.DOCUMENTATION: 15,
            DiscoveryType.CODE_IMPROVEMENT: 30,
            DiscoveryType.NEW_FEATURE: 45,
            DiscoveryType.REFACTORING: 60,
            DiscoveryType.PERFORMANCE_OPTIMIZATION: 45,
            DiscoveryType.TESTING: 30,
            DiscoveryType.TOOLING: 60
        }
        base_time = type_complexity.get(discovery.discovery_type, 30)
        assessment.estimated_time_minutes = base_time + (complexity_factors * 10)
        
        # Analyze prerequisites
        assessment.prerequisites = self.analyzer.analyze_prerequisites(discovery)
        
        # Breaking changes analysis
        assessment.breaking_changes = self.analyzer.detect_breaking_changes(discovery)
        
        # Rollback complexity
        if assessment.breaking_changes or assessment.difficulty_level == 'hard':
            assessment.rollback_complexity = 'complex'
        elif assessment.difficulty_level == 'moderate':
            assessment.rollback_complexity = 'moderate'
        else:
            assessment.rollback_complexity = 'simple'
        
        # Conflict risk assessment
        assessment.conflict_risk = self.analyzer.assess_conflict_risk(discovery)
        
        # Testing requirements
        assessment.testing_requirements = self.analyzer.determine_testing_requirements(discovery)
        
        # Dependencies analysis
        assessment.dependencies_needed = self.analyzer.analyze_dependencies(discovery)
        
        return assessment
    
    def generate_discovery_narrative(self, discovery: Discovery) -> DiscoveryNarrative:
        """Generate a compelling narrative for discovery presentation."""
        
        narrative = DiscoveryNarrative(
            headline=self.analyzer.generate_headline(discovery),
            summary=self.analyzer.generate_summary(discovery),
            value_proposition=self.analyzer.generate_value_proposition(discovery)
        )
        
        # Key benefits
        narrative.key_benefits = self.analyzer.extract_key_benefits(discovery)
        
        # Integration story
        narrative.integration_story = self.analyzer.create_integration_story(discovery)
        
        # Technical highlights
        narrative.technical_highlights = self.analyzer.extract_technical_highlights(discovery)
        
        # Risk assessment narrative
        narrative.risk_assessment = self.analyzer.create_risk_narrative(discovery)
        
        return narrative