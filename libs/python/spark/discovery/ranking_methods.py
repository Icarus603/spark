"""
Ranking calculation methods for the discovery curator.

This module contains all the detailed ranking factor calculation methods
to keep the main curator.py file focused on high-level logic.
"""

from typing import List, Dict, Any
from datetime import datetime

from spark.discovery.models import Discovery, DiscoveryType


class RankingCalculator:
    """Handles detailed ranking calculations for discovery factors."""
    
    def calculate_technical_value_score(self, discovery: Discovery) -> float:
        """Calculate technical value based on code quality, performance, and learning value."""
        
        # Base technical metrics from discovery
        base_score = (discovery.confidence_score + discovery.impact_score) / 2.0
        
        # Analyze code artifacts for quality indicators
        quality_boost = 0.0
        if discovery.exploration_results:
            for result in discovery.exploration_results:
                for artifact in result.code_artifacts:
                    # Check for quality indicators in code
                    code = artifact.content.lower()
                    
                    # Type hints boost
                    if 'def ' in code and (':' in code or '->' in code):
                        quality_boost += 0.1
                    
                    # Documentation boost
                    if '"""' in code or "'''" in code:
                        quality_boost += 0.1
                    
                    # Error handling boost
                    if 'try:' in code or 'except' in code:
                        quality_boost += 0.1
                    
                    # Testing boost
                    if 'test' in artifact.file_path.lower() or 'assert' in code:
                        quality_boost += 0.15
        
        # Performance optimization boost
        perf_boost = 0.0
        if discovery.discovery_type == DiscoveryType.PERFORMANCE_OPTIMIZATION:
            perf_boost = 0.2
        elif 'performance' in discovery.description.lower():
            perf_boost = 0.1
            
        # Learning value boost
        learning_boost = 0.0
        learning_keywords = ['pattern', 'example', 'tutorial', 'guide', 'best practice']
        desc_lower = discovery.description.lower()
        for keyword in learning_keywords:
            if keyword in desc_lower:
                learning_boost += 0.05
                
        return min(1.0, base_score + quality_boost + perf_boost + learning_boost)
    
    def calculate_relevance_score(self, discovery: Discovery) -> float:
        """Calculate relevance to current user patterns and project context."""
        
        # Base relevance from pattern alignment
        pattern_alignment = len(discovery.source_patterns) * 0.1
        
        # Tag relevance (simulated - would integrate with actual pattern system)
        tag_relevance = 0.0
        common_tags = ['python', 'async', 'testing', 'performance', 'utility']
        for tag in discovery.tags:
            if tag.lower() in common_tags:
                tag_relevance += 0.1
        
        # Discovery type relevance based on recent activity
        type_relevance = 0.5  # Default moderate relevance
        if discovery.discovery_type in [DiscoveryType.CODE_IMPROVEMENT, DiscoveryType.PERFORMANCE_OPTIMIZATION]:
            type_relevance = 0.8
            
        # Recency of similar discoveries (avoid redundancy)
        redundancy_penalty = 0.0
        # This would check for similar discoveries in the last week
        
        return min(1.0, max(0.0, pattern_alignment + tag_relevance + type_relevance - redundancy_penalty))
    
    def calculate_actionability_score(self, discovery: Discovery) -> float:
        """Calculate how easily the discovery can be integrated."""
        
        # Base actionability from integration readiness
        base_score = 0.8 if discovery.integration_ready else 0.4
        
        # Integration risk penalty
        risk_penalties = {
            'low': 0.0,
            'moderate': -0.1,
            'high': -0.3
        }
        risk_penalty = risk_penalties.get(discovery.integration_risk, -0.1)
        
        # Instructions quality boost
        instruction_boost = 0.0
        if discovery.integration_instructions:
            instruction_boost = min(0.2, len(discovery.integration_instructions) * 0.05)
        
        # Code artifact completeness boost
        completeness_boost = 0.0
        if discovery.exploration_results:
            total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
            completeness_boost = min(0.2, total_artifacts * 0.05)
            
        return min(1.0, max(0.0, base_score + risk_penalty + instruction_boost + completeness_boost))
    
    def calculate_impact_potential_score(self, discovery: Discovery) -> float:
        """Calculate potential impact and benefits."""
        
        # Base impact score
        base_impact = discovery.impact_score
        
        # Discovery type impact multipliers
        type_multipliers = {
            DiscoveryType.PERFORMANCE_OPTIMIZATION: 1.3,
            DiscoveryType.CODE_IMPROVEMENT: 1.2,
            DiscoveryType.NEW_FEATURE: 1.1,
            DiscoveryType.REFACTORING: 1.0,
            DiscoveryType.TESTING: 0.9,
            DiscoveryType.DOCUMENTATION: 0.8,
            DiscoveryType.TOOLING: 1.1
        }
        type_multiplier = type_multipliers.get(discovery.discovery_type, 1.0)
        
        # Scope impact (more artifacts = potentially higher impact)
        scope_boost = 0.0
        if discovery.exploration_results:
            total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
            scope_boost = min(0.3, total_artifacts * 0.05)
        
        # Innovation boost for novel approaches
        innovation_boost = discovery.novelty_score * 0.2
        
        return min(1.0, (base_impact * type_multiplier) + scope_boost + innovation_boost)
    
    def calculate_enhanced_novelty_score(self, discovery: Discovery) -> float:
        """Calculate enhanced novelty score with pattern analysis."""
        
        # Base novelty score
        base_novelty = discovery.novelty_score
        
        # Tag-based novelty (uncommon tags are more novel)
        tag_novelty = 0.0
        uncommon_tags = ['experimental', 'innovative', 'novel', 'creative', 'unique']
        for tag in discovery.tags:
            if tag.lower() in uncommon_tags:
                tag_novelty += 0.1
        
        # Approach novelty (multiple different approaches)
        approach_novelty = 0.0
        unique_approaches = set()
        for result in discovery.exploration_results:
            unique_approaches.add(result.approach)
        approach_novelty = min(0.2, len(unique_approaches) * 0.05)
        
        # Cross-domain novelty (combining different technologies)
        cross_domain_boost = 0.0
        tech_keywords = ['api', 'database', 'web', 'ml', 'ai', 'async', 'concurrent']
        desc_lower = discovery.description.lower()
        tech_count = sum(1 for keyword in tech_keywords if keyword in desc_lower)
        if tech_count > 1:
            cross_domain_boost = 0.1
            
        return min(1.0, base_novelty + tag_novelty + approach_novelty + cross_domain_boost)
    
    def calculate_user_alignment_score(self, discovery: Discovery) -> float:
        """Calculate alignment with user preferences and feedback history."""
        
        # User rating alignment
        rating_score = 0.5  # Default neutral
        if discovery.user_rating:
            rating_score = discovery.user_rating.value / 5.0
        
        # Pattern source alignment
        pattern_score = min(0.3, len(discovery.source_patterns) * 0.1)
        
        # Historical preference alignment (simulated)
        # This would analyze past high-rated discoveries for patterns
        historical_alignment = 0.6  # Placeholder
        
        return (rating_score * 0.5) + (pattern_score * 0.3) + (historical_alignment * 0.2)
    
    def calculate_recency_score(self, discovery: Discovery) -> float:
        """Calculate recency score with time decay."""
        
        age_days = (datetime.now() - discovery.created_at).days
        
        # More aggressive decay for very old discoveries
        if age_days <= 1:
            return 1.0  # Perfect score for today
        elif age_days <= 7:
            return 0.9 - (age_days - 1) * 0.05  # 5% decay per day
        elif age_days <= 30:
            return 0.6 - (age_days - 7) * 0.02  # 2% decay per day after week
        else:
            return max(0.1, 0.3 - (age_days - 30) * 0.01)  # 1% decay after month