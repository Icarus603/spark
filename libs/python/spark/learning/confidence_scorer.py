"""
Multi-dimensional pattern confidence scoring system.

This module provides sophisticated confidence analysis for detected patterns,
supporting statistical significance testing, temporal stability, and exploration readiness.
"""

import math
import statistics
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from spark.learning.git_patterns import GitAnalysisResult
from spark.learning.style_analyzer import StyleProfile, FileAnalysis


class PatternType(Enum):
    """Types of patterns that can be analyzed."""
    
    GIT_COMMIT = "git_commit"
    GIT_BRANCH = "git_branch" 
    STYLE_NAMING = "style_naming"
    STYLE_STRUCTURE = "style_structure"
    STYLE_COMPLEXITY = "style_complexity"
    LANGUAGE_USAGE = "language_usage"
    ARCHITECTURAL = "architectural"
    TEMPORAL = "temporal"


class ConfidenceLevel(Enum):
    """Confidence level categories."""
    
    VERY_LOW = "very_low"      # <30%
    LOW = "low"                # 30-50%
    MODERATE = "moderate"      # 50-70%
    HIGH = "high"              # 70-85%
    VERY_HIGH = "very_high"    # 85-95%
    EXCEPTIONAL = "exceptional" # >95%


@dataclass
class ConfidenceMetrics:
    """Metrics used for confidence calculation."""
    
    sample_size: int = 0
    consistency_score: float = 0.0
    temporal_stability: float = 0.0
    cross_validation_score: float = 0.0
    statistical_significance: float = 0.0
    recency_weight: float = 1.0
    
    # Pattern-specific metrics
    pattern_strength: float = 0.0
    pattern_uniqueness: float = 0.0
    contextual_relevance: float = 0.0


@dataclass
class ConfidenceScore:
    """Complete confidence analysis result."""
    
    pattern_id: str
    pattern_type: PatternType
    overall_confidence: float
    confidence_level: ConfidenceLevel
    
    # Detailed breakdown
    metrics: ConfidenceMetrics
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    risk_factors: List[str] = field(default_factory=list)
    
    # Exploration readiness
    exploration_ready: bool = False
    exploration_risk_level: str = "moderate"
    
    # Metadata
    calculated_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None


class StatisticalAnalyzer:
    """Statistical analysis utilities for pattern confidence."""
    
    @staticmethod
    def calculate_sample_size_confidence(sample_size: int, min_samples: int = 5, optimal_samples: int = 50) -> float:
        """Calculate confidence based on sample size using sigmoid curve."""
        if sample_size <= 0:
            return 0.0
        
        if sample_size < min_samples:
            return 0.1 * (sample_size / min_samples)
        
        # Sigmoid curve for sample size confidence
        x = (sample_size - min_samples) / (optimal_samples - min_samples)
        return 1 / (1 + math.exp(-6 * (x - 0.5)))
    
    @staticmethod
    def calculate_consistency_score(values: List[float]) -> float:
        """Calculate consistency score based on variance."""
        if len(values) <= 1:
            return 0.0
        
        if all(v == values[0] for v in values):
            return 1.0
        
        # Use coefficient of variation (inverted)
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0
        
        stdev = statistics.stdev(values)
        cv = stdev / abs(mean_val)
        
        # Convert to confidence (lower variance = higher confidence)
        return max(0.0, 1.0 - min(cv, 1.0))
    
    @staticmethod
    def calculate_temporal_stability(timestamps: List[datetime], values: List[float], 
                                   stability_window_days: int = 30) -> float:
        """Calculate how stable a pattern is over time."""
        if len(timestamps) <= 1:
            return 0.0
        
        # Sort by timestamp
        sorted_data = sorted(zip(timestamps, values))
        
        # Calculate stability within windows
        window_size = timedelta(days=stability_window_days)
        stability_scores = []
        
        for i in range(len(sorted_data)):
            window_end = sorted_data[i][0] + window_size
            window_values = []
            
            for j in range(i, len(sorted_data)):
                if sorted_data[j][0] <= window_end:
                    window_values.append(sorted_data[j][1])
                else:
                    break
            
            if len(window_values) >= 2:
                stability = StatisticalAnalyzer.calculate_consistency_score(window_values)
                stability_scores.append(stability)
        
        return statistics.mean(stability_scores) if stability_scores else 0.0
    
    @staticmethod
    def calculate_statistical_significance(observed: List[float], expected: float, 
                                         alpha: float = 0.05) -> float:
        """Calculate statistical significance using simplified t-test."""
        if len(observed) <= 1:
            return 0.0
        
        mean_observed = statistics.mean(observed)
        
        if len(observed) == 1:
            # Single observation, low significance
            return 0.3
        
        stdev = statistics.stdev(observed)
        n = len(observed)
        
        if stdev == 0:
            return 1.0 if mean_observed == expected else 0.0
        
        # Simplified t-statistic
        t_stat = abs(mean_observed - expected) / (stdev / math.sqrt(n))
        
        # Convert to confidence (simplified)
        # Higher t-stat means more significant difference
        significance = min(t_stat / 3.0, 1.0)  # Normalize to 0-1
        
        return significance


class PatternConfidenceScorer:
    """Main confidence scoring engine for patterns."""
    
    def __init__(self):
        self.stat_analyzer = StatisticalAnalyzer()
        self.pattern_history: Dict[str, List[ConfidenceScore]] = defaultdict(list)
    
    def score_git_patterns(self, git_analysis: GitAnalysisResult) -> Dict[PatternType, ConfidenceScore]:
        """Score confidence for git-based patterns."""
        scores = {}
        
        # Score commit patterns
        commit_score = self._score_commit_patterns(git_analysis)
        scores[PatternType.GIT_COMMIT] = commit_score
        
        # Score branch patterns  
        branch_score = self._score_branch_patterns(git_analysis)
        scores[PatternType.GIT_BRANCH] = branch_score
        
        # Score language usage patterns
        language_score = self._score_language_patterns(git_analysis)
        scores[PatternType.LANGUAGE_USAGE] = language_score
        
        return scores
    
    def score_style_patterns(self, style_profile: StyleProfile) -> Dict[PatternType, ConfidenceScore]:
        """Score confidence for style-based patterns."""
        scores = {}
        
        # Score naming patterns
        naming_score = self._score_naming_patterns(style_profile)
        scores[PatternType.STYLE_NAMING] = naming_score
        
        # Score structural patterns
        structure_score = self._score_structure_patterns(style_profile)
        scores[PatternType.STYLE_STRUCTURE] = structure_score
        
        # Score complexity patterns
        complexity_score = self._score_complexity_patterns(style_profile)
        scores[PatternType.STYLE_COMPLEXITY] = complexity_score
        
        return scores
    
    def _score_commit_patterns(self, git_analysis: GitAnalysisResult) -> ConfidenceScore:
        """Score commit pattern confidence."""
        commit_patterns = git_analysis.commit_patterns
        
        # Calculate metrics
        sample_size_confidence = self.stat_analyzer.calculate_sample_size_confidence(
            git_analysis.commit_count
        )
        
        # Consistency metrics
        consistency_factors = []
        
        # Message style consistency
        if commit_patterns.message_style in ["conventional", "descriptive"]:
            consistency_factors.append(0.8)  # Good style
        else:
            consistency_factors.append(0.4)  # Mixed style
        
        # Commit size consistency
        if commit_patterns.prefers_small_commits:
            consistency_factors.append(0.7)
        else:
            consistency_factors.append(0.5)
        
        consistency_score = statistics.mean(consistency_factors) if consistency_factors else 0.0
        
        # Pattern strength based on frequency
        pattern_strength = min(commit_patterns.commit_frequency / 2.0, 1.0)  # 2 commits/day = max
        
        metrics = ConfidenceMetrics(
            sample_size=git_analysis.commit_count,
            consistency_score=consistency_score,
            pattern_strength=pattern_strength,
            statistical_significance=sample_size_confidence
        )
        
        # Overall confidence
        overall = statistics.mean([
            sample_size_confidence,
            consistency_score,
            pattern_strength
        ])
        
        return ConfidenceScore(
            pattern_id=f"commit_{git_analysis.repository_path.replace('/', '_')}",
            pattern_type=PatternType.GIT_COMMIT,
            overall_confidence=overall,
            confidence_level=self._determine_confidence_level(overall),
            metrics=metrics,
            contributing_factors={
                'sample_size': sample_size_confidence,
                'consistency': consistency_score,
                'pattern_strength': pattern_strength
            },
            exploration_ready=overall >= 0.7,
            exploration_risk_level="conservative" if overall >= 0.8 else "moderate"
        )
    
    def _score_branch_patterns(self, git_analysis: GitAnalysisResult) -> ConfidenceScore:
        """Score branch pattern confidence."""
        branch_patterns = git_analysis.branch_patterns
        
        # Simple scoring based on workflow detection
        workflow_confidence = 0.6 if branch_patterns.workflow_type != "personal" else 0.3
        
        metrics = ConfidenceMetrics(
            sample_size=5,  # Simplified
            consistency_score=workflow_confidence,
            pattern_strength=workflow_confidence
        )
        
        return ConfidenceScore(
            pattern_id=f"branch_{git_analysis.repository_path.replace('/', '_')}",
            pattern_type=PatternType.GIT_BRANCH,
            overall_confidence=workflow_confidence,
            confidence_level=self._determine_confidence_level(workflow_confidence),
            metrics=metrics,
            exploration_ready=workflow_confidence >= 0.7
        )
    
    def _score_language_patterns(self, git_analysis: GitAnalysisResult) -> ConfidenceScore:
        """Score language usage pattern confidence."""
        language_patterns = git_analysis.language_patterns
        
        # Base confidence on language distribution clarity
        total_usage = sum(language_patterns.languages.values())
        if total_usage == 0:
            confidence = 0.0
        else:
            # Higher confidence if there's a clear primary language
            max_usage = max(language_patterns.languages.values()) if language_patterns.languages else 0
            confidence = max_usage / total_usage if total_usage > 0 else 0.0
        
        sample_size = len(language_patterns.languages)
        sample_confidence = self.stat_analyzer.calculate_sample_size_confidence(sample_size, 1, 10)
        
        overall = statistics.mean([confidence, sample_confidence])
        
        metrics = ConfidenceMetrics(
            sample_size=sample_size,
            consistency_score=confidence,
            pattern_strength=confidence,
            statistical_significance=sample_confidence
        )
        
        return ConfidenceScore(
            pattern_id=f"language_{git_analysis.repository_path.replace('/', '_')}",
            pattern_type=PatternType.LANGUAGE_USAGE,
            overall_confidence=overall,
            confidence_level=self._determine_confidence_level(overall),
            metrics=metrics,
            exploration_ready=overall >= 0.7
        )
    
    def _score_naming_patterns(self, style_profile: StyleProfile) -> ConfidenceScore:
        """Score naming pattern confidence."""
        
        # Base confidence on existing confidence scores
        base_confidence = style_profile.confidence_scores.get('naming_style', 0.0)
        
        # Sample size from profile
        sample_size = style_profile.sample_sizes.get('naming_samples', 0)
        sample_confidence = self.stat_analyzer.calculate_sample_size_confidence(sample_size)
        
        # Pattern strength based on consistency
        pattern_strength = base_confidence
        
        overall = statistics.mean([base_confidence, sample_confidence, pattern_strength])
        
        metrics = ConfidenceMetrics(
            sample_size=sample_size,
            consistency_score=base_confidence,
            pattern_strength=pattern_strength,
            statistical_significance=sample_confidence
        )
        
        return ConfidenceScore(
            pattern_id=f"naming_{style_profile.preferred_naming_style}",
            pattern_type=PatternType.STYLE_NAMING,
            overall_confidence=overall,
            confidence_level=self._determine_confidence_level(overall),
            metrics=metrics,
            contributing_factors={
                'base_confidence': base_confidence,
                'sample_size': sample_confidence,
                'pattern_strength': pattern_strength
            },
            exploration_ready=overall >= 0.7
        )
    
    def _score_structure_patterns(self, style_profile: StyleProfile) -> ConfidenceScore:
        """Score structural pattern confidence."""
        
        # Base on function pattern confidence
        function_confidence = style_profile.confidence_scores.get('function_patterns', 0.0)
        functions_analyzed = style_profile.sample_sizes.get('functions_analyzed', 0)
        
        sample_confidence = self.stat_analyzer.calculate_sample_size_confidence(
            functions_analyzed, min_samples=10, optimal_samples=100
        )
        
        # Pattern strength based on type hint and docstring usage
        type_pattern_strength = min(style_profile.type_hint_usage * 2, 1.0)  # 50% usage = max
        doc_pattern_strength = min(style_profile.docstring_coverage * 2, 1.0)
        
        pattern_strength = statistics.mean([type_pattern_strength, doc_pattern_strength])
        
        overall = statistics.mean([function_confidence, sample_confidence, pattern_strength])
        
        metrics = ConfidenceMetrics(
            sample_size=functions_analyzed,
            consistency_score=function_confidence,
            pattern_strength=pattern_strength,
            statistical_significance=sample_confidence
        )
        
        return ConfidenceScore(
            pattern_id="structure_patterns",
            pattern_type=PatternType.STYLE_STRUCTURE,
            overall_confidence=overall,
            confidence_level=self._determine_confidence_level(overall),
            metrics=metrics,
            contributing_factors={
                'function_confidence': function_confidence,
                'type_usage': type_pattern_strength,
                'documentation': doc_pattern_strength
            },
            exploration_ready=overall >= 0.7
        )
    
    def _score_complexity_patterns(self, style_profile: StyleProfile) -> ConfidenceScore:
        """Score complexity pattern confidence."""
        
        # Base on function samples
        functions_analyzed = style_profile.sample_sizes.get('functions_analyzed', 0)
        sample_confidence = self.stat_analyzer.calculate_sample_size_confidence(
            functions_analyzed, min_samples=5, optimal_samples=50
        )
        
        # Pattern strength based on reasonable complexity preferences
        preferred_complexity = style_profile.preferred_complexity
        preferred_function_length = style_profile.preferred_function_length
        preferred_nesting = style_profile.preferred_nesting_depth
        
        # Reasonable ranges (higher confidence for moderate values)
        complexity_reasonableness = 1.0 - abs(preferred_complexity - 5) / 15  # 5 is ideal
        length_reasonableness = 1.0 - abs(preferred_function_length - 20) / 50  # 20 is ideal
        nesting_reasonableness = 1.0 - abs(preferred_nesting - 3) / 10  # 3 is ideal
        
        pattern_strength = statistics.mean([
            max(0, complexity_reasonableness),
            max(0, length_reasonableness), 
            max(0, nesting_reasonableness)
        ])
        
        overall = statistics.mean([sample_confidence, pattern_strength])
        
        metrics = ConfidenceMetrics(
            sample_size=functions_analyzed,
            pattern_strength=pattern_strength,
            statistical_significance=sample_confidence
        )
        
        return ConfidenceScore(
            pattern_id="complexity_patterns",
            pattern_type=PatternType.STYLE_COMPLEXITY,
            overall_confidence=overall,
            confidence_level=self._determine_confidence_level(overall),
            metrics=metrics,
            contributing_factors={
                'complexity_preference': complexity_reasonableness,
                'length_preference': length_reasonableness,
                'nesting_preference': nesting_reasonableness
            },
            exploration_ready=overall >= 0.7
        )
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level category."""
        if confidence < 0.3:
            return ConfidenceLevel.VERY_LOW
        elif confidence < 0.5:
            return ConfidenceLevel.LOW
        elif confidence < 0.7:
            return ConfidenceLevel.MODERATE
        elif confidence < 0.85:
            return ConfidenceLevel.HIGH
        elif confidence < 0.95:
            return ConfidenceLevel.VERY_HIGH
        else:
            return ConfidenceLevel.EXCEPTIONAL
    
    def calculate_exploration_readiness(self, pattern_scores: Dict[PatternType, ConfidenceScore]) -> Dict[str, Any]:
        """Calculate overall exploration readiness based on all patterns."""
        
        if not pattern_scores:
            return {
                'ready': False,
                'overall_confidence': 0.0,
                'readiness_score': 0.0,
                'blocking_factors': ['No patterns detected'],
                'recommendations': ['Continue coding to build pattern confidence']
            }
        
        # Calculate weighted average confidence
        weights = {
            PatternType.GIT_COMMIT: 0.25,
            PatternType.GIT_BRANCH: 0.15,
            PatternType.STYLE_NAMING: 0.20,
            PatternType.STYLE_STRUCTURE: 0.25,
            PatternType.STYLE_COMPLEXITY: 0.15,
            PatternType.LANGUAGE_USAGE: 0.10,
        }
        
        total_weight = 0
        weighted_confidence = 0
        
        for pattern_type, score in pattern_scores.items():
            weight = weights.get(pattern_type, 0.1)
            weighted_confidence += score.overall_confidence * weight
            total_weight += weight
        
        overall_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
        
        # Readiness criteria
        ready = overall_confidence >= 0.75  # 75% threshold for exploration
        
        # Identify blocking factors
        blocking_factors = []
        for pattern_type, score in pattern_scores.items():
            if score.overall_confidence < 0.5:  # Low confidence patterns
                blocking_factors.append(f"Low {pattern_type.value} confidence ({score.overall_confidence:.1%})")
        
        # Generate recommendations
        recommendations = []
        if overall_confidence < 0.5:
            recommendations.append("Continue normal development to build stronger patterns")
        elif overall_confidence < 0.75:
            recommendations.append("Add more repositories or continue coding in existing ones")
        else:
            recommendations.append("Ready for autonomous exploration!")
        
        # Risk assessment
        risk_level = "conservative"
        if overall_confidence >= 0.9:
            risk_level = "balanced"
        elif overall_confidence >= 0.8:
            risk_level = "moderate"
        
        return {
            'ready': ready,
            'overall_confidence': overall_confidence,
            'readiness_score': overall_confidence,
            'confidence_level': self._determine_confidence_level(overall_confidence).value,
            'risk_level': risk_level,
            'blocking_factors': blocking_factors,
            'recommendations': recommendations,
            'pattern_breakdown': {
                pattern_type.value: {
                    'confidence': score.overall_confidence,
                    'ready': score.exploration_ready,
                    'sample_size': score.metrics.sample_size
                }
                for pattern_type, score in pattern_scores.items()
            }
        }