"""
Enhanced learning integration that combines all new analyzers with storage.

This module demonstrates how to use the enhanced analyzers (style analyzer, 
confidence scorer, file monitor, preference mapper) with the enhanced storage layer
to provide a complete pattern learning pipeline.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from spark.learning.style_analyzer import MultiLanguageStyleAnalyzer
from spark.learning.confidence_scorer import MultiDimensionalConfidenceScorer, PatternType
from spark.learning.file_monitor import FileSystemMonitor, FileChangeEvent
from spark.learning.preference_mapper import PreferenceMapper
from spark.storage.pattern_storage import PatternStorage
from spark.cli.errors import SparkLearningError


class EnhancedLearningEngine:
    """
    Integrated learning engine that combines all enhanced analyzers with storage.
    
    This engine orchestrates the complete pattern learning pipeline:
    1. File monitoring for real-time change detection
    2. AST analysis for code style patterns
    3. Confidence scoring for pattern reliability
    4. Preference mapping for developer behavior analysis
    5. Persistent storage for all pattern data
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        
        # Initialize analyzers
        self.style_analyzer = MultiLanguageStyleAnalyzer()
        self.confidence_scorer = MultiDimensionalConfidenceScorer()
        self.preference_mapper = PreferenceMapper()
        
        # File monitor will be initialized when needed
        self.file_monitor: Optional[FileSystemMonitor] = None
        
        # State tracking
        self.monitored_repositories: List[str] = []
        self.active_sessions: Dict[str, Any] = {}
        
        self.logger = logging.getLogger(f"spark.{self.__class__.__name__}")
    
    def add_repository(self, repository_path: Path) -> bool:
        """Add a repository to the learning engine."""
        try:
            repo_path_str = str(repository_path.resolve())
            
            if repo_path_str in self.monitored_repositories:
                self.logger.info(f"Repository already monitored: {repo_path_str}")
                return True
            
            # Perform initial analysis
            self._analyze_repository_initially(repository_path)
            
            # Add to monitoring if file monitor is active
            if self.file_monitor:
                self.file_monitor.add_path(repository_path, recursive=True)
            
            self.monitored_repositories.append(repo_path_str)
            self.logger.info(f"Added repository to enhanced learning: {repo_path_str}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add repository {repository_path}: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start real-time file monitoring and pattern learning."""
        try:
            if self.file_monitor:
                self.logger.warning("File monitoring already active")
                return True
            
            # Initialize file monitor with pattern update callback
            self.file_monitor = FileSystemMonitor(
                pattern_update_callback=self._on_pattern_update
            )
            
            # Add all monitored repositories
            for repo_path in self.monitored_repositories:
                path = Path(repo_path)
                if path.exists():
                    self.file_monitor.add_path(path, recursive=True)
            
            # Start monitoring
            if not self.file_monitor.start_monitoring():
                self.logger.error("Failed to start file monitoring")
                return False
            
            self.logger.info("Enhanced learning monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop real-time monitoring."""
        try:
            if self.file_monitor:
                self.file_monitor.stop_monitoring()
                self.file_monitor = None
            
            self.logger.info("Enhanced learning monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {e}")
            return False
    
    def _analyze_repository_initially(self, repository_path: Path) -> None:
        """Perform initial comprehensive analysis of a repository."""
        try:
            with PatternStorage(self.storage_path) as storage:
                repo_path_str = str(repository_path)
                
                # 1. AST Analysis
                self.logger.info(f"Performing AST analysis for {repository_path}")
                file_analyses = self.style_analyzer.analyze_directory(repository_path)
                
                # Store AST analyses
                for file_analysis in file_analyses:
                    try:
                        analysis_id = storage.store_ast_analysis(repo_path_str, file_analysis)
                        self.logger.debug(f"Stored AST analysis: {analysis_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to store AST analysis for {file_analysis.file_path}: {e}")
                
                # 2. Confidence Scoring
                if file_analyses:
                    self.logger.info(f"Calculating confidence scores for {len(file_analyses)} files")
                    
                    # Group patterns by type for confidence calculation
                    style_patterns = [
                        {
                            'type': PatternType.STYLE.value,
                            'data': file_analysis.style_profile,
                            'confidence': file_analysis.confidence_score,
                            'file_path': file_analysis.file_path
                        }
                        for file_analysis in file_analyses
                    ]
                    
                    if style_patterns:
                        confidence_score = self.confidence_scorer.calculate_confidence(
                            PatternType.STYLE, style_patterns
                        )
                        
                        # Store confidence score
                        score_id = storage.store_confidence_score(
                            repo_path_str, PatternType.STYLE, confidence_score
                        )
                        self.logger.debug(f"Stored confidence score: {score_id}")
                
                # 3. Preference Analysis (simplified for initial analysis)
                if file_analyses:
                    self.logger.info("Building initial preference profile")
                    
                    # Collect style profiles
                    style_profiles = [
                        {
                            'repository': repo_path_str,
                            'profile': file_analysis.style_profile
                        }
                        for file_analysis in file_analyses
                    ]
                    
                    # Build preference profile
                    preference_profile = self.preference_mapper.build_preference_profile(
                        git_analyses=[],  # Would be populated with git analysis
                        style_profiles=style_profiles,
                        confidence_scores={}
                    )
                    
                    # Store preference profile
                    profile_id = storage.store_preference_profile(repo_path_str, preference_profile)
                    self.logger.debug(f"Stored preference profile: {profile_id}")
                
                self.logger.info(f"Initial analysis completed for {repository_path}")
                
        except Exception as e:
            self.logger.error(f"Failed initial analysis for {repository_path}: {e}")
            raise SparkLearningError(f"Initial analysis failed: {e}") from e
    
    def _on_pattern_update(self, events: List[FileChangeEvent]) -> None:
        """Handle real-time pattern updates from file monitoring."""
        try:
            self.logger.debug(f"Processing {len(events)} file change events")
            
            # Group events by repository
            repo_events = {}
            for event in events:
                # Determine repository for this file
                repo_path = self._get_repository_for_file(event.file_path)
                if repo_path:
                    if repo_path not in repo_events:
                        repo_events[repo_path] = []
                    repo_events[repo_path].append(event)
            
            # Process each repository's events
            with PatternStorage(self.storage_path) as storage:
                for repo_path, repo_events_list in repo_events.items():
                    self._process_repository_events(storage, repo_path, repo_events_list)
            
        except Exception as e:
            self.logger.error(f"Error processing pattern updates: {e}")
    
    def _get_repository_for_file(self, file_path: Path) -> Optional[str]:
        """Determine which repository a file belongs to."""
        file_path_str = str(file_path.resolve())
        
        for repo_path in self.monitored_repositories:
            if file_path_str.startswith(repo_path):
                return repo_path
        
        return None
    
    def _process_repository_events(
        self, 
        storage: PatternStorage, 
        repository_path: str, 
        events: List[FileChangeEvent]
    ) -> None:
        """Process file change events for a specific repository."""
        try:
            # Filter for code files that were modified or created
            code_events = [
                e for e in events 
                if e.is_code_file and e.event_type in ['modified', 'created']
            ]
            
            if not code_events:
                return
            
            self.logger.debug(f"Processing {len(code_events)} code change events for {repository_path}")
            
            # Analyze changed files
            updated_analyses = []
            for event in code_events:
                if event.file_path.exists():
                    try:
                        # Re-analyze the file
                        file_analysis = self.style_analyzer.analyze_file(event.file_path)
                        if file_analysis:
                            # Store updated analysis
                            analysis_id = storage.store_ast_analysis(repository_path, file_analysis)
                            updated_analyses.append(file_analysis)
                            self.logger.debug(f"Updated AST analysis: {analysis_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to re-analyze {event.file_path}: {e}")
            
            # Update confidence scores if we have new analyses
            if updated_analyses:
                style_patterns = [
                    {
                        'type': PatternType.STYLE.value,
                        'data': analysis.style_profile,
                        'confidence': analysis.confidence_score,
                        'file_path': analysis.file_path
                    }
                    for analysis in updated_analyses
                ]
                
                # Recalculate confidence score
                confidence_score = self.confidence_scorer.calculate_confidence(
                    PatternType.STYLE, style_patterns
                )
                
                # Store updated confidence score
                storage.store_confidence_score(repository_path, PatternType.STYLE, confidence_score)
            
            # Store file events for session tracking
            for event in events:
                storage.store_file_event(event)
            
        except Exception as e:
            self.logger.error(f"Failed to process repository events for {repository_path}: {e}")
    
    def get_learning_summary(self, repository_path: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive learning summary including all enhanced data."""
        try:
            with PatternStorage(self.storage_path) as storage:
                # Get enhanced progress
                progress = storage.get_enhanced_progress(repository_path)
                
                # Add monitoring status
                progress['monitoring_active'] = self.file_monitor is not None
                progress['monitored_repositories'] = len(self.monitored_repositories)
                
                # Get recent development sessions
                sessions = storage.get_development_sessions(limit=5)
                progress['recent_sessions'] = sessions
                
                return progress
                
        except Exception as e:
            self.logger.error(f"Failed to get learning summary: {e}")
            return {'error': str(e)}
    
    def get_repository_insights(self, repository_path: str) -> Dict[str, Any]:
        """Get detailed insights for a specific repository."""
        try:
            with PatternStorage(self.storage_path) as storage:
                insights = {
                    'repository_path': repository_path,
                    'timestamp': datetime.now().isoformat(),
                }
                
                # AST Analysis insights
                ast_analyses = storage.get_ast_analyses(repository_path)
                if ast_analyses:
                    insights['ast_analysis'] = {
                        'total_files': len(ast_analyses),
                        'languages': list(set(a['language'] for a in ast_analyses)),
                        'avg_confidence': sum(a['confidence_score'] for a in ast_analyses) / len(ast_analyses),
                        'total_functions': sum(a['function_count'] for a in ast_analyses),
                        'total_classes': sum(a['class_count'] for a in ast_analyses),
                        'avg_complexity': sum(a['avg_complexity'] for a in ast_analyses if a['avg_complexity']) / 
                                        max(1, len([a for a in ast_analyses if a['avg_complexity']]))
                    }
                
                # Confidence Scores
                confidence_scores = storage.get_confidence_scores(repository_path)
                if confidence_scores:
                    insights['confidence_analysis'] = {
                        'total_scores': len(confidence_scores),
                        'pattern_types': list(set(c['pattern_type'] for c in confidence_scores)),
                        'avg_overall_confidence': sum(c['overall_confidence'] for c in confidence_scores) / len(confidence_scores),
                        'avg_statistical_significance': sum(c['statistical_significance'] for c in confidence_scores) / len(confidence_scores)
                    }
                
                # Preference Profiles
                profiles = storage.get_preference_profiles(repository_path)
                if profiles:
                    profile = profiles[0]  # Latest profile
                    insights['preference_profile'] = {
                        'adoption_style': profile['adoption_style'],
                        'problem_solving_approach': profile['problem_solving_approach'],
                        'confidence_score': profile['confidence_score'],
                        'technology_count': len(profile['technology_preferences'])
                    }
                
                return insights
                
        except Exception as e:
            self.logger.error(f"Failed to get repository insights: {e}")
            return {'error': str(e), 'repository_path': repository_path}
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()


async def run_enhanced_learning_demo(repository_paths: List[Path], storage_path: Path) -> None:
    """
    Demonstration of the enhanced learning pipeline.
    
    This function shows how to use all components together for comprehensive
    pattern learning and analysis.
    """
    print("🚀 Starting Enhanced Learning Demo")
    print(f"Repositories: {[str(p) for p in repository_paths]}")
    print(f"Storage: {storage_path}")
    print()
    
    try:
        # Initialize learning engine
        with EnhancedLearningEngine(storage_path) as engine:
            
            # Add repositories
            print("📁 Adding repositories...")
            for repo_path in repository_paths:
                if engine.add_repository(repo_path):
                    print(f"  ✅ Added: {repo_path}")
                else:
                    print(f"  ❌ Failed: {repo_path}")
            print()
            
            # Start monitoring
            print("👀 Starting real-time monitoring...")
            if engine.start_monitoring():
                print("  ✅ Monitoring started successfully")
            else:
                print("  ❌ Failed to start monitoring")
            print()
            
            # Wait a bit for any initial file events
            print("⏳ Waiting for initial analysis...")
            await asyncio.sleep(2)
            print()
            
            # Get learning summary
            print("📊 Learning Summary:")
            summary = engine.get_learning_summary()
            for key, value in summary.items():
                if key not in ['enhanced_patterns']:  # Skip complex nested data
                    print(f"  {key}: {value}")
            print()
            
            # Get insights for each repository
            for repo_path in repository_paths:
                if repo_path.exists():
                    print(f"🔍 Repository Insights: {repo_path.name}")
                    insights = engine.get_repository_insights(str(repo_path))
                    
                    for category, data in insights.items():
                        if category not in ['repository_path', 'timestamp']:
                            print(f"  {category}:")
                            if isinstance(data, dict):
                                for k, v in data.items():
                                    print(f"    {k}: {v}")
                            else:
                                print(f"    {data}")
                    print()
            
            print("✅ Enhanced learning demo completed successfully!")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Learning Engine Demo")
    parser.add_argument("repositories", nargs="+", type=Path, help="Repository paths to analyze")
    parser.add_argument("--storage", type=Path, default="./enhanced_learning.db", help="Storage database path")
    
    args = parser.parse_args()
    
    # Run the demo
    asyncio.run(run_enhanced_learning_demo(args.repositories, args.storage))