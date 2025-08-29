"""
User feedback collection and analysis for discoveries.

This module handles collecting, storing, and analyzing user feedback to improve
future explorations and discovery curation.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from spark.discovery.models import Discovery, FeedbackRating, DiscoveryType
from spark.storage.discovery_storage import DiscoveryStorage


@dataclass
class FeedbackAnalysis:
    """Analysis results from user feedback."""
    
    total_ratings: int = 0
    average_rating: float = 0.0
    rating_distribution: Dict[int, int] = None
    common_positive_terms: List[str] = None
    common_negative_terms: List[str] = None
    improvement_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.rating_distribution is None:
            self.rating_distribution = {}
        if self.common_positive_terms is None:
            self.common_positive_terms = []
        if self.common_negative_terms is None:
            self.common_negative_terms = []
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []


class FeedbackCollector:
    """Collects and analyzes user feedback for discoveries."""
    
    def __init__(self, storage: Optional[DiscoveryStorage] = None):
        self.storage = storage or DiscoveryStorage()
    
    def rate_discovery(
        self,
        discovery_id: str,
        rating: FeedbackRating,
        feedback_text: str = ""
    ) -> bool:
        """Rate a discovery and optionally provide feedback."""
        
        # Validate discovery exists
        discovery = self.storage.get_discovery_by_id(discovery_id)
        if not discovery:
            return False
        
        # Update rating and feedback
        success = self.storage.update_discovery_rating(discovery_id, rating, feedback_text)
        
        if success:
            # Mark as viewed when rated
            self.storage.mark_discovery_viewed(discovery_id)
        
        return success
    
    def get_discovery_feedback(self, discovery_id: str) -> Optional[Tuple[FeedbackRating, str]]:
        """Get existing feedback for a discovery."""
        
        discovery = self.storage.get_discovery_by_id(discovery_id)
        if not discovery or not discovery.user_rating:
            return None
        
        return discovery.user_rating, discovery.user_feedback
    
    def analyze_feedback(self, days: int = 30) -> FeedbackAnalysis:
        """Analyze feedback patterns from the last N days."""
        
        # Get recent discoveries with feedback
        all_discoveries = self.storage.get_discoveries(limit=1000)
        
        # Filter to recent discoveries with ratings
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_rated = [
            d for d in all_discoveries
            if d.user_rating and d.created_at >= cutoff_date
        ]
        
        if not recent_rated:
            return FeedbackAnalysis()
        
        # Calculate basic stats
        ratings = [d.user_rating.value for d in recent_rated]
        avg_rating = sum(ratings) / len(ratings)
        
        # Rating distribution
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        # Analyze feedback text
        feedback_texts = [d.user_feedback for d in recent_rated if d.user_feedback.strip()]
        positive_terms, negative_terms = self._analyze_feedback_sentiment(feedback_texts)
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(recent_rated)
        
        return FeedbackAnalysis(
            total_ratings=len(recent_rated),
            average_rating=avg_rating,
            rating_distribution=rating_dist,
            common_positive_terms=positive_terms,
            common_negative_terms=negative_terms,
            improvement_suggestions=suggestions
        )
    
    def get_feedback_by_type(self, discovery_type: DiscoveryType) -> FeedbackAnalysis:
        """Analyze feedback for a specific discovery type."""
        
        all_discoveries = self.storage.get_discoveries_by_type(discovery_type, limit=1000)
        rated_discoveries = [d for d in all_discoveries if d.user_rating]
        
        if not rated_discoveries:
            return FeedbackAnalysis()
        
        ratings = [d.user_rating.value for d in rated_discoveries]
        avg_rating = sum(ratings) / len(ratings)
        
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        feedback_texts = [d.user_feedback for d in rated_discoveries if d.user_feedback.strip()]
        positive_terms, negative_terms = self._analyze_feedback_sentiment(feedback_texts)
        
        suggestions = self._generate_type_specific_suggestions(discovery_type, rated_discoveries)
        
        return FeedbackAnalysis(
            total_ratings=len(rated_discoveries),
            average_rating=avg_rating,
            rating_distribution=rating_dist,
            common_positive_terms=positive_terms,
            common_negative_terms=negative_terms,
            improvement_suggestions=suggestions
        )
    
    def get_poorly_rated_discoveries(self, threshold: int = 2, limit: int = 10) -> List[Discovery]:
        """Get discoveries with poor ratings for improvement."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        
        poorly_rated = [
            d for d in all_discoveries
            if d.user_rating and d.user_rating.value <= threshold
        ]
        
        # Sort by rating (worst first) then by recency
        poorly_rated.sort(key=lambda d: (d.user_rating.value, d.created_at), reverse=True)
        
        return poorly_rated[:limit]
    
    def get_highly_rated_discoveries(self, threshold: int = 4, limit: int = 10) -> List[Discovery]:
        """Get highly rated discoveries to understand success patterns."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        
        highly_rated = [
            d for d in all_discoveries
            if d.user_rating and d.user_rating.value >= threshold
        ]
        
        # Sort by rating then by overall score
        highly_rated.sort(key=lambda d: (d.user_rating.value, d.overall_score()), reverse=True)
        
        return highly_rated[:limit]
    
    def suggest_feedback_targets(self, limit: int = 5) -> List[Discovery]:
        """Suggest discoveries that would benefit from user feedback."""
        
        all_discoveries = self.storage.get_discoveries(limit=100)
        
        # Find unrated discoveries with decent quality
        unrated = [
            d for d in all_discoveries
            if not d.user_rating and d.confidence_score > 0.6
        ]
        
        # Prioritize by potential value
        def feedback_priority(discovery: Discovery) -> float:
            # Higher priority for newer, higher-quality discoveries
            age_days = (datetime.now() - discovery.created_at).days
            age_factor = max(0.1, 1.0 - (age_days * 0.05))  # Decay over time
            
            quality_factor = discovery.overall_score()
            
            # Boost for integration-ready discoveries
            integration_factor = 1.2 if discovery.integration_ready else 1.0
            
            return quality_factor * age_factor * integration_factor
        
        unrated.sort(key=feedback_priority, reverse=True)
        
        return unrated[:limit]
    
    def _analyze_feedback_sentiment(self, feedback_texts: List[str]) -> Tuple[List[str], List[str]]:
        """Analyze sentiment in feedback text (basic keyword analysis)."""
        
        if not feedback_texts:
            return [], []
        
        # Simple keyword-based sentiment analysis
        positive_keywords = [
            'excellent', 'great', 'good', 'useful', 'helpful', 'perfect', 'awesome',
            'clear', 'clean', 'efficient', 'smart', 'clever', 'elegant', 'solid',
            'works', 'exactly', 'needed', 'love', 'fantastic', 'brilliant'
        ]
        
        negative_keywords = [
            'bad', 'poor', 'terrible', 'awful', 'useless', 'broken', 'wrong',
            'confusing', 'unclear', 'messy', 'incomplete', 'missing', 'error',
            'problem', 'issue', 'difficult', 'hard', 'complex', 'buggy', 'hate'
        ]
        
        all_text = ' '.join(feedback_texts).lower()
        
        # Count keyword occurrences
        positive_found = []
        negative_found = []
        
        for keyword in positive_keywords:
            if keyword in all_text:
                positive_found.append(keyword)
        
        for keyword in negative_keywords:
            if keyword in all_text:
                negative_found.append(keyword)
        
        # Return most common terms (up to 5 each)
        return positive_found[:5], negative_found[:5]
    
    def _generate_improvement_suggestions(self, rated_discoveries: List[Discovery]) -> List[str]:
        """Generate improvement suggestions based on feedback patterns."""
        
        suggestions = []
        
        # Analyze rating patterns
        ratings = [d.user_rating.value for d in rated_discoveries]
        avg_rating = sum(ratings) / len(ratings)
        
        if avg_rating < 3.0:
            suggestions.append("Focus on improving code quality and validation")
            suggestions.append("Consider more thorough testing of generated code")
        
        # Analyze discovery types with poor ratings
        type_ratings = {}
        for discovery in rated_discoveries:
            discovery_type = discovery.discovery_type
            if discovery_type not in type_ratings:
                type_ratings[discovery_type] = []
            type_ratings[discovery_type].append(discovery.user_rating.value)
        
        for discovery_type, type_rating_list in type_ratings.items():
            avg_type_rating = sum(type_rating_list) / len(type_rating_list)
            if avg_type_rating < 2.5:
                type_name = discovery_type.value.replace('_', ' ').title()
                suggestions.append(f"Improve {type_name} generation quality")
        
        # Analyze confidence vs rating correlation
        high_confidence_low_rating = [
            d for d in rated_discoveries
            if d.confidence_score > 0.8 and d.user_rating.value < 3
        ]
        
        if len(high_confidence_low_rating) > len(rated_discoveries) * 0.3:
            suggestions.append("Reassess confidence scoring - high confidence predictions are getting poor ratings")
        
        # Check integration readiness accuracy
        integration_ready_poor = [
            d for d in rated_discoveries
            if d.integration_ready and d.user_rating.value < 3
        ]
        
        if len(integration_ready_poor) > 0:
            suggestions.append("Review integration readiness criteria - some 'ready' discoveries are poorly rated")
        
        # Generic suggestions if no specific patterns found
        if not suggestions:
            suggestions.extend([
                "Continue collecting user feedback to identify improvement patterns",
                "Focus on discoveries with higher user engagement",
                "Consider user preferences in exploration goal generation"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _generate_type_specific_suggestions(
        self,
        discovery_type: DiscoveryType,
        rated_discoveries: List[Discovery]
    ) -> List[str]:
        """Generate suggestions specific to a discovery type."""
        
        suggestions = []
        ratings = [d.user_rating.value for d in rated_discoveries]
        
        if not ratings:
            return suggestions
        
        avg_rating = sum(ratings) / len(ratings)
        type_name = discovery_type.value.replace('_', ' ').title()
        
        if discovery_type == DiscoveryType.CODE_IMPROVEMENT:
            if avg_rating < 3.0:
                suggestions.extend([
                    "Focus on more impactful code improvements",
                    "Better identify actual pain points in existing code",
                    "Provide clearer before/after comparisons"
                ])
        
        elif discovery_type == DiscoveryType.PERFORMANCE_OPTIMIZATION:
            if avg_rating < 3.0:
                suggestions.extend([
                    "Include performance benchmarks with optimizations",
                    "Focus on optimizations with measurable impact",
                    "Provide profiling data to support claims"
                ])
        
        elif discovery_type == DiscoveryType.TESTING:
            if avg_rating < 3.0:
                suggestions.extend([
                    "Generate more comprehensive test cases",
                    "Focus on edge cases and error conditions",
                    "Provide test data setup examples"
                ])
        
        elif discovery_type == DiscoveryType.NEW_FEATURE:
            if avg_rating < 3.0:
                suggestions.extend([
                    "Better align features with user workflow",
                    "Provide more complete feature implementations",
                    "Include integration examples with existing code"
                ])
        
        # Add generic type-specific suggestion
        if avg_rating < 3.5:
            suggestions.append(f"Review and improve {type_name} generation quality")
        
        return suggestions[:3]  # Return top 3 type-specific suggestions
    
    def export_feedback_data(self, format: str = "json") -> Dict[str, Any]:
        """Export feedback data for analysis."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        rated_discoveries = [d for d in all_discoveries if d.user_rating]
        
        feedback_data = {
            "export_date": datetime.now().isoformat(),
            "total_discoveries": len(all_discoveries),
            "rated_discoveries": len(rated_discoveries),
            "feedback_entries": []
        }
        
        for discovery in rated_discoveries:
            entry = {
                "discovery_id": discovery.id,
                "title": discovery.title,
                "discovery_type": discovery.discovery_type.value,
                "rating": discovery.user_rating.value,
                "feedback": discovery.user_feedback,
                "confidence_score": discovery.confidence_score,
                "impact_score": discovery.impact_score,
                "novelty_score": discovery.novelty_score,
                "overall_score": discovery.overall_score(),
                "created_at": discovery.created_at.isoformat(),
                "tags": discovery.tags
            }
            feedback_data["feedback_entries"].append(entry)
        
        return feedback_data
    
    def get_feedback_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze feedback trends over time."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        
        # Filter to discoveries with ratings in the specified period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_rated = [
            d for d in all_discoveries
            if d.user_rating and d.created_at >= cutoff_date
        ]
        
        if not recent_rated:
            return {"trends": [], "summary": "No rated discoveries in specified period"}
        
        # Group by week
        weekly_data = {}
        for discovery in recent_rated:
            # Get week starting Monday
            week_start = discovery.created_at - timedelta(days=discovery.created_at.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "ratings": [],
                    "types": {},
                    "count": 0
                }
            
            weekly_data[week_key]["ratings"].append(discovery.user_rating.value)
            weekly_data[week_key]["count"] += 1
            
            discovery_type = discovery.discovery_type.value
            weekly_data[week_key]["types"][discovery_type] = weekly_data[week_key]["types"].get(discovery_type, 0) + 1
        
        # Calculate trends
        trends = []
        for week_key in sorted(weekly_data.keys()):
            week_data = weekly_data[week_key]
            avg_rating = sum(week_data["ratings"]) / len(week_data["ratings"])
            
            trends.append({
                "week": week_key,
                "count": week_data["count"],
                "average_rating": avg_rating,
                "rating_distribution": {
                    str(i): week_data["ratings"].count(i) for i in range(1, 6)
                },
                "discovery_types": week_data["types"]
            })
        
        # Calculate overall trend
        if len(trends) >= 2:
            first_week_avg = trends[0]["average_rating"]
            last_week_avg = trends[-1]["average_rating"]
            trend_direction = "improving" if last_week_avg > first_week_avg else "declining" if last_week_avg < first_week_avg else "stable"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "trends": trends,
            "summary": f"Rating trend: {trend_direction}",
            "total_rated": len(recent_rated),
            "period_days": days
        }
    
    def analyze_user_preferences(self) -> Dict[str, Any]:
        """Analyze user preferences based on feedback patterns."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        rated_discoveries = [d for d in all_discoveries if d.user_rating]
        
        if not rated_discoveries:
            return {"preferences": {}, "confidence": "low"}
        
        preferences = {}
        
        # Analyze discovery type preferences
        type_ratings = {}
        for discovery in rated_discoveries:
            discovery_type = discovery.discovery_type.value
            if discovery_type not in type_ratings:
                type_ratings[discovery_type] = []
            type_ratings[discovery_type].append(discovery.user_rating.value)
        
        # Calculate average ratings per type
        type_preferences = {}
        for discovery_type, ratings in type_ratings.items():
            if len(ratings) >= 3:  # Need at least 3 ratings for confidence
                avg_rating = sum(ratings) / len(ratings)
                type_preferences[discovery_type] = {
                    "average_rating": avg_rating,
                    "count": len(ratings),
                    "preference_level": self._categorize_preference(avg_rating)
                }
        
        preferences["discovery_types"] = type_preferences
        
        # Analyze complexity preferences
        complexity_ratings = {"simple": [], "moderate": [], "complex": []}
        for discovery in rated_discoveries:
            # Estimate complexity based on confidence score and artifact count
            artifact_count = sum(len(r.code_artifacts) for r in discovery.exploration_results)
            if artifact_count <= 2 and discovery.confidence_score > 0.8:
                complexity_category = "simple"
            elif artifact_count <= 5 and discovery.confidence_score > 0.6:
                complexity_category = "moderate"
            else:
                complexity_category = "complex"
            
            complexity_ratings[complexity_category].append(discovery.user_rating.value)
        
        complexity_preferences = {}
        for complexity, ratings in complexity_ratings.items():
            if ratings:  # If we have ratings for this complexity
                avg_rating = sum(ratings) / len(ratings)
                complexity_preferences[complexity] = {
                    "average_rating": avg_rating,
                    "count": len(ratings),
                    "preference_level": self._categorize_preference(avg_rating)
                }
        
        preferences["complexity"] = complexity_preferences
        
        # Analyze feature preferences
        feature_preferences = self._analyze_feature_preferences(rated_discoveries)
        preferences["features"] = feature_preferences
        
        # Calculate overall preference confidence
        total_ratings = len(rated_discoveries)
        if total_ratings >= 20:
            confidence = "high"
        elif total_ratings >= 10:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "preferences": preferences,
            "confidence": confidence,
            "total_ratings": total_ratings,
            "analysis_date": datetime.now().isoformat()
        }
    
    def get_success_patterns(self) -> Dict[str, Any]:
        """Identify patterns in successful discoveries."""
        
        highly_rated = self.get_highly_rated_discoveries(threshold=4, limit=50)
        
        if not highly_rated:
            return {"patterns": [], "confidence": "low"}
        
        patterns = {}
        
        # Analyze successful discovery characteristics
        avg_confidence = sum(d.confidence_score for d in highly_rated) / len(highly_rated)
        avg_impact = sum(d.impact_score for d in highly_rated) / len(highly_rated)
        avg_novelty = sum(d.novelty_score for d in highly_rated) / len(highly_rated)
        
        patterns["successful_metrics"] = {
            "confidence_threshold": avg_confidence,
            "impact_threshold": avg_impact,
            "novelty_threshold": avg_novelty,
            "sample_size": len(highly_rated)
        }
        
        # Common tags in successful discoveries
        all_tags = []
        for discovery in highly_rated:
            all_tags.extend(discovery.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Find tags that appear in >30% of successful discoveries
        common_success_tags = [
            tag for tag, count in tag_counts.items()
            if count >= len(highly_rated) * 0.3
        ]
        
        patterns["success_indicators"] = common_success_tags
        
        # Analyze integration patterns
        integration_ready_success = [d for d in highly_rated if d.integration_ready]
        patterns["integration_success_rate"] = len(integration_ready_success) / len(highly_rated)
        
        # Discovery type success analysis
        type_success = {}
        for discovery in highly_rated:
            discovery_type = discovery.discovery_type.value
            type_success[discovery_type] = type_success.get(discovery_type, 0) + 1
        
        patterns["successful_types"] = dict(sorted(type_success.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "patterns": patterns,
            "confidence": "high" if len(highly_rated) >= 10 else "medium" if len(highly_rated) >= 5 else "low",
            "recommendations": self._generate_success_recommendations(patterns)
        }
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Generate insights for improving the learning system."""
        
        analysis = self.analyze_feedback()
        preferences = self.analyze_user_preferences()
        success_patterns = self.get_success_patterns()
        
        insights = {
            "feedback_quality": {
                "total_ratings": analysis.total_ratings,
                "average_rating": analysis.average_rating,
                "engagement_level": self._assess_engagement_level(analysis.total_ratings)
            },
            "preference_alignment": self._assess_preference_alignment(preferences),
            "success_factors": success_patterns.get("patterns", {}),
            "improvement_areas": analysis.improvement_suggestions,
            "confidence_accuracy": self._assess_confidence_accuracy(),
            "exploration_effectiveness": self._assess_exploration_effectiveness()
        }
        
        # Generate actionable recommendations
        recommendations = []
        
        if analysis.average_rating < 3.5:
            recommendations.append("Focus on improving overall discovery quality")
        
        if preferences["confidence"] == "high":
            recommendations.append("Use strong user preferences to guide future explorations")
        elif preferences["confidence"] == "low":
            recommendations.append("Collect more feedback to understand user preferences better")
        
        if success_patterns["confidence"] == "high":
            recommendations.append("Apply successful discovery patterns to new explorations")
        
        insights["recommendations"] = recommendations
        insights["analysis_date"] = datetime.now().isoformat()
        
        return insights
    
    def _categorize_preference(self, avg_rating: float) -> str:
        """Categorize preference level based on average rating."""
        if avg_rating >= 4.0:
            return "strong_preference"
        elif avg_rating >= 3.5:
            return "moderate_preference"
        elif avg_rating >= 2.5:
            return "neutral"
        else:
            return "negative_preference"
    
    def _analyze_feature_preferences(self, rated_discoveries: List[Discovery]) -> Dict[str, Any]:
        """Analyze preferences for specific features."""
        
        feature_analysis = {}
        
        # Analyze integration readiness preference
        ready_ratings = [d.user_rating.value for d in rated_discoveries if d.integration_ready]
        not_ready_ratings = [d.user_rating.value for d in rated_discoveries if not d.integration_ready]
        
        if ready_ratings and not_ready_ratings:
            feature_analysis["integration_ready"] = {
                "ready_avg": sum(ready_ratings) / len(ready_ratings),
                "not_ready_avg": sum(not_ready_ratings) / len(not_ready_ratings),
                "preference": "prefers_ready" if sum(ready_ratings) / len(ready_ratings) > sum(not_ready_ratings) / len(not_ready_ratings) else "no_preference"
            }
        
        # Analyze novelty preference
        high_novelty = [d.user_rating.value for d in rated_discoveries if d.novelty_score > 0.7]
        low_novelty = [d.user_rating.value for d in rated_discoveries if d.novelty_score < 0.3]
        
        if high_novelty and low_novelty:
            feature_analysis["novelty"] = {
                "high_novelty_avg": sum(high_novelty) / len(high_novelty),
                "low_novelty_avg": sum(low_novelty) / len(low_novelty),
                "preference": "prefers_novel" if sum(high_novelty) / len(high_novelty) > sum(low_novelty) / len(low_novelty) else "prefers_familiar"
            }
        
        return feature_analysis
    
    def _assess_engagement_level(self, total_ratings: int) -> str:
        """Assess user engagement level based on rating count."""
        if total_ratings >= 50:
            return "high"
        elif total_ratings >= 20:
            return "medium"
        elif total_ratings >= 5:
            return "low"
        else:
            return "very_low"
    
    def _assess_preference_alignment(self, preferences: Dict[str, Any]) -> str:
        """Assess how well we're aligned with user preferences."""
        
        if preferences["confidence"] == "low":
            return "insufficient_data"
        
        # Check if we have strong preferences in multiple categories
        strong_preferences = 0
        prefs = preferences.get("preferences", {})
        
        for category, category_prefs in prefs.items():
            if isinstance(category_prefs, dict):
                for item, item_data in category_prefs.items():
                    if isinstance(item_data, dict) and item_data.get("preference_level") == "strong_preference":
                        strong_preferences += 1
        
        if strong_preferences >= 3:
            return "well_aligned"
        elif strong_preferences >= 1:
            return "partially_aligned"
        else:
            return "poorly_aligned"
    
    def _assess_confidence_accuracy(self) -> Dict[str, Any]:
        """Assess how accurately confidence scores predict user satisfaction."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        rated_discoveries = [d for d in all_discoveries if d.user_rating]
        
        if not rated_discoveries:
            return {"accuracy": "unknown", "correlation": 0.0}
        
        # Calculate correlation between confidence and rating
        confidence_scores = [d.confidence_score for d in rated_discoveries]
        ratings = [d.user_rating.value for d in rated_discoveries]
        
        # Simple correlation calculation
        mean_conf = sum(confidence_scores) / len(confidence_scores)
        mean_rating = sum(ratings) / len(ratings)
        
        numerator = sum((conf - mean_conf) * (rating - mean_rating) for conf, rating in zip(confidence_scores, ratings))
        denominator_conf = sum((conf - mean_conf) ** 2 for conf in confidence_scores)
        denominator_rating = sum((rating - mean_rating) ** 2 for rating in ratings)
        
        if denominator_conf * denominator_rating > 0:
            correlation = numerator / (denominator_conf * denominator_rating) ** 0.5
        else:
            correlation = 0.0
        
        # Assess accuracy
        if correlation > 0.7:
            accuracy = "high"
        elif correlation > 0.4:
            accuracy = "medium"
        elif correlation > 0.1:
            accuracy = "low"
        else:
            accuracy = "poor"
        
        return {
            "accuracy": accuracy,
            "correlation": correlation,
            "sample_size": len(rated_discoveries)
        }
    
    def _assess_exploration_effectiveness(self) -> Dict[str, Any]:
        """Assess how effective explorations are at generating valuable discoveries."""
        
        all_discoveries = self.storage.get_discoveries(limit=1000)
        recent_discoveries = [
            d for d in all_discoveries
            if (datetime.now() - d.created_at).days <= 30
        ]
        
        if not recent_discoveries:
            return {"effectiveness": "unknown", "metrics": {}}
        
        # Calculate metrics
        total_discoveries = len(recent_discoveries)
        rated_discoveries = [d for d in recent_discoveries if d.user_rating]
        high_rated = [d for d in rated_discoveries if d.user_rating.value >= 4]
        integration_ready = [d for d in recent_discoveries if d.integration_ready]
        
        metrics = {
            "total_discoveries": total_discoveries,
            "rating_rate": len(rated_discoveries) / total_discoveries if total_discoveries > 0 else 0,
            "high_rating_rate": len(high_rated) / len(rated_discoveries) if rated_discoveries else 0,
            "integration_ready_rate": len(integration_ready) / total_discoveries if total_discoveries > 0 else 0,
            "average_rating": sum(d.user_rating.value for d in rated_discoveries) / len(rated_discoveries) if rated_discoveries else 0
        }
        
        # Assess overall effectiveness
        if metrics["average_rating"] >= 4.0 and metrics["integration_ready_rate"] >= 0.6:
            effectiveness = "high"
        elif metrics["average_rating"] >= 3.5 and metrics["integration_ready_rate"] >= 0.4:
            effectiveness = "medium"
        else:
            effectiveness = "low"
        
        return {
            "effectiveness": effectiveness,
            "metrics": metrics
        }
    
    def _generate_success_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on success patterns."""
        
        recommendations = []
        
        successful_metrics = patterns.get("successful_metrics", {})
        if successful_metrics:
            conf_threshold = successful_metrics["confidence_threshold"]
            impact_threshold = successful_metrics["impact_threshold"]
            
            recommendations.append(f"Target discoveries with confidence ≥ {conf_threshold:.1%}")
            recommendations.append(f"Focus on high-impact explorations (≥ {impact_threshold:.1%})")
        
        success_indicators = patterns.get("success_indicators", [])
        if success_indicators:
            recommendations.append(f"Prioritize discoveries with tags: {', '.join(success_indicators[:3])}")
        
        successful_types = patterns.get("successful_types", {})
        if successful_types:
            top_type = next(iter(successful_types))
            recommendations.append(f"Consider more {top_type.replace('_', ' ')} discoveries")
        
        integration_success_rate = patterns.get("integration_success_rate", 0)
        if integration_success_rate > 0.7:
            recommendations.append("Continue prioritizing integration-ready discoveries")
        elif integration_success_rate < 0.3:
            recommendations.append("Improve integration readiness assessment")
        
        return recommendations[:5]  # Return top 5 recommendations