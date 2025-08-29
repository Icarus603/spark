"""
Discovery and exploration data models.

This module defines the core data structures for Spark's discovery system,
including exploration results, discovery metadata, and user feedback.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ExplorationStatus(Enum):
    """Status of an exploration session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DiscoveryType(Enum):
    """Types of discoveries that can be made."""
    CODE_IMPROVEMENT = "code_improvement"
    NEW_FEATURE = "new_feature"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    TOOLING = "tooling"


class FeedbackRating(Enum):
    """User feedback ratings for discoveries."""
    EXCELLENT = 5
    GOOD = 4
    NEUTRAL = 3
    POOR = 2
    TERRIBLE = 1


@dataclass
class CodeArtifact:
    """A piece of code generated during exploration."""
    
    file_path: str
    content: str
    description: str
    language: str
    is_main_artifact: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ExplorationResult:
    """Result of a single exploration attempt."""
    
    id: str
    goal: str
    approach: str
    status: ExplorationStatus
    code_artifacts: List[CodeArtifact] = field(default_factory=list)
    success: bool = False
    error_message: Optional[str] = None
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Discovery:
    """A curated exploration result worthy of user attention."""
    
    id: str
    title: str
    description: str
    discovery_type: DiscoveryType
    exploration_results: List[ExplorationResult] = field(default_factory=list)
    
    # Value assessment
    impact_score: float = 0.0
    confidence_score: float = 0.0  
    novelty_score: float = 0.0
    
    # Integration information
    integration_ready: bool = False
    integration_instructions: List[str] = field(default_factory=list)
    integration_risk: str = "moderate"  # low, moderate, high
    
    # User feedback
    user_rating: Optional[FeedbackRating] = None
    user_feedback: str = ""
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    viewed_at: Optional[datetime] = None
    integrated_at: Optional[datetime] = None
    
    # Links to patterns that inspired this discovery
    source_patterns: List[str] = field(default_factory=list)
    
    # Additional metadata used by curator/presenter (ranking, factor scores, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def overall_score(self) -> float:
        """Calculate overall discovery score for ranking."""
        weights = {
            'impact': 0.4,
            'confidence': 0.3, 
            'novelty': 0.2,
            'user_rating': 0.1
        }
        
        rating_score = (self.user_rating.value / 5.0) if self.user_rating else 0.5
        
        return (
            weights['impact'] * self.impact_score +
            weights['confidence'] * self.confidence_score +
            weights['novelty'] * self.novelty_score +
            weights['user_rating'] * rating_score
        )


@dataclass
class ExplorationSession:
    """A complete exploration session with multiple attempts."""
    
    id: str
    goal: str
    initiated_by: str  # "user" or "autonomous"
    
    # Session configuration
    time_limit: int = 1800  # 30 minutes default
    approach_count: int = 3  # Generate 3 variations
    risk_tolerance: str = "moderate"  # low, moderate, high
    
    # Session results
    exploration_results: List[ExplorationResult] = field(default_factory=list)
    discoveries: List[Discovery] = field(default_factory=list)
    
    # Session metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_time: float = 0.0
    
    def is_successful(self) -> bool:
        """Check if session produced any successful discoveries."""
        return len(self.discoveries) > 0
    
    def success_rate(self) -> float:
        """Calculate success rate of exploration attempts."""
        if not self.exploration_results:
            return 0.0
        successful = sum(1 for r in self.exploration_results if r.success)
        return successful / len(self.exploration_results)
