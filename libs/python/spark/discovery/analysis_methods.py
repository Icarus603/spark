"""
Analysis helper methods for discovery curator.

This module contains detailed analysis methods for impact assessment,
integration difficulty analysis, and narrative generation.
"""

from typing import List, Dict, Any
from datetime import datetime

from spark.discovery.models import Discovery, DiscoveryType


class DiscoveryAnalyzer:
    """Handles detailed analysis of discoveries for curation and presentation."""
    
    def analyze_code_quality_impact(self, discovery: Discovery) -> float:
        """Analyze code quality improvements."""
        quality_score = 0.0
        
        # Check for quality indicators
        for result in discovery.exploration_results:
            for artifact in result.code_artifacts:
                code = artifact.content.lower()
                
                # Type safety indicators
                if 'typing' in code or ': ' in code:
                    quality_score += 0.1
                
                # Documentation
                if '"""' in code or "'''" in code:
                    quality_score += 0.1
                
                # Error handling
                if 'exception' in code or 'error' in code:
                    quality_score += 0.1
                
                # Testing indicators
                if 'test' in artifact.file_path.lower():
                    quality_score += 0.2
        
        return min(1.0, quality_score)
    
    def estimate_time_savings(self, discovery: Discovery) -> float:
        """Estimate time savings from implementing discovery."""
        
        # Base time savings from automation/improvement
        base_savings = 0.0
        
        if discovery.discovery_type == DiscoveryType.TOOLING:
            base_savings = 0.8
        elif discovery.discovery_type == DiscoveryType.PERFORMANCE_OPTIMIZATION:
            base_savings = 0.6
        elif discovery.discovery_type == DiscoveryType.CODE_IMPROVEMENT:
            base_savings = 0.4
        else:
            base_savings = 0.3
        
        # Boost for utility functions
        if 'utility' in discovery.description.lower():
            base_savings += 0.2
        
        return min(1.0, base_savings)
    
    def calculate_reusability_score(self, discovery: Discovery) -> float:
        """Calculate how reusable the discovery is."""
        
        reusability = 0.5  # Base score
        
        # Function/class-based code is more reusable
        for result in discovery.exploration_results:
            for artifact in result.code_artifacts:
                code = artifact.content.lower()
                if 'def ' in code or 'class ' in code:
                    reusability += 0.2
        
        # Generic solutions are more reusable
        generic_keywords = ['generic', 'utility', 'helper', 'common', 'shared']
        desc_lower = discovery.description.lower()
        for keyword in generic_keywords:
            if keyword in desc_lower:
                reusability += 0.1
        
        return min(1.0, reusability)
    
    def analyze_prerequisites(self, discovery: Discovery) -> List[str]:
        """Analyze prerequisites for integration."""
        prerequisites = []
        
        # Check for dependency indicators in code
        for result in discovery.exploration_results:
            for artifact in result.code_artifacts:
                code = artifact.content
                
                # Python imports
                import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith(('import ', 'from '))]
                for imp in import_lines:
                    if not any(stdlib in imp for stdlib in ['os', 'sys', 'json', 'datetime', 'typing']):
                        prerequisites.append(f"Install dependency: {imp}")
        
        return list(set(prerequisites))  # Remove duplicates
    
    def detect_breaking_changes(self, discovery: Discovery) -> bool:
        """Detect if discovery contains breaking changes."""
        
        # Check for breaking change indicators
        breaking_keywords = ['breaking', 'incompatible', 'major change', 'migration required']
        desc_lower = discovery.description.lower()
        
        for keyword in breaking_keywords:
            if keyword in desc_lower:
                return True
        
        # Refactoring often involves breaking changes
        if discovery.discovery_type == DiscoveryType.REFACTORING and discovery.integration_risk == 'high':
            return True
            
        return False
    
    def assess_conflict_risk(self, discovery: Discovery) -> float:
        """Assess risk of integration conflicts."""
        
        base_risk = 0.3  # Default moderate risk
        
        # Risk based on integration risk level
        risk_levels = {
            'low': 0.1,
            'moderate': 0.3,
            'high': 0.7
        }
        base_risk = risk_levels.get(discovery.integration_risk, 0.3)
        
        # Increase risk for complex discoveries
        total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        complexity_risk = min(0.3, total_artifacts * 0.05)
        
        return min(1.0, base_risk + complexity_risk)
    
    def determine_testing_requirements(self, discovery: Discovery) -> List[str]:
        """Determine testing requirements for integration."""
        
        requirements = []
        
        # Basic testing always required
        requirements.append("Unit tests for new functionality")
        
        # Type-specific testing
        if discovery.discovery_type == DiscoveryType.PERFORMANCE_OPTIMIZATION:
            requirements.append("Performance benchmarking")
        elif discovery.discovery_type == DiscoveryType.NEW_FEATURE:
            requirements.append("Integration testing")
            requirements.append("User acceptance testing")
        elif discovery.discovery_type == DiscoveryType.REFACTORING:
            requirements.append("Regression testing")
        
        return requirements
    
    def analyze_dependencies(self, discovery: Discovery) -> List[str]:
        """Analyze external dependencies needed."""
        
        dependencies = []
        
        # Extract from code artifacts
        for result in discovery.exploration_results:
            for artifact in result.code_artifacts:
                # Look for import statements
                lines = artifact.content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith(('import ', 'from ')):
                        # Extract package name
                        if 'import ' in line:
                            pkg = line.split('import ')[1].split('.')[0].split(' as ')[0]
                            if not self._is_stdlib_package(pkg):
                                dependencies.append(pkg)
        
        return list(set(dependencies))  # Remove duplicates
    
    def _is_stdlib_package(self, package: str) -> bool:
        """Check if package is part of Python standard library."""
        stdlib_packages = {
            'os', 'sys', 'json', 'datetime', 'typing', 're', 'math', 'random',
            'collections', 'itertools', 'functools', 'pathlib', 'asyncio', 'threading'
        }
        return package in stdlib_packages
    
    def generate_headline(self, discovery: Discovery) -> str:
        """Generate compelling headline for discovery."""
        
        # Type-based headlines
        type_templates = {
            DiscoveryType.PERFORMANCE_OPTIMIZATION: "⚡ {title} - Boost Your Performance",
            DiscoveryType.NEW_FEATURE: "✨ {title} - New Capability Unlocked", 
            DiscoveryType.CODE_IMPROVEMENT: "🔧 {title} - Code Quality Enhancement",
            DiscoveryType.REFACTORING: "🏗️ {title} - Architecture Improvement",
            DiscoveryType.TESTING: "🧪 {title} - Testing Strategy",
            DiscoveryType.DOCUMENTATION: "📚 {title} - Documentation Update",
            DiscoveryType.TOOLING: "🛠️ {title} - Developer Tool"
        }
        
        template = type_templates.get(discovery.discovery_type, "💡 {title}")
        return template.format(title=discovery.title)
    
    def generate_summary(self, discovery: Discovery) -> str:
        """Generate concise summary of discovery."""
        
        base_summary = discovery.description[:200]  # First 200 chars
        
        # Add impact context
        if discovery.impact_score > 0.8:
            return f"{base_summary} This high-impact discovery could significantly improve your codebase."
        elif discovery.impact_score > 0.6:
            return f"{base_summary} This discovery offers valuable improvements to your workflow."
        else:
            return f"{base_summary} This discovery provides useful enhancements."
    
    def generate_value_proposition(self, discovery: Discovery) -> str:
        """Generate value proposition for discovery."""
        
        # Impact-based value propositions
        if discovery.discovery_type == DiscoveryType.PERFORMANCE_OPTIMIZATION:
            return f"Improve performance and efficiency with confidence score of {discovery.confidence_score:.1%}"
        elif discovery.discovery_type == DiscoveryType.NEW_FEATURE:
            return f"Add new capabilities with {discovery.impact_score:.1%} projected impact"
        elif discovery.discovery_type == DiscoveryType.CODE_IMPROVEMENT:
            return f"Enhance code quality and maintainability with proven benefits"
        else:
            return f"Valuable improvement with {discovery.confidence_score:.1%} confidence level"
    
    def extract_key_benefits(self, discovery: Discovery) -> List[str]:
        """Extract key benefits from discovery."""
        
        benefits = []
        
        # Confidence-based benefit
        if discovery.confidence_score > 0.8:
            benefits.append("High confidence implementation")
        
        # Impact-based benefits
        if discovery.impact_score > 0.7:
            benefits.append("Significant positive impact")
        
        # Type-specific benefits
        type_benefits = {
            DiscoveryType.PERFORMANCE_OPTIMIZATION: "Performance improvements",
            DiscoveryType.CODE_IMPROVEMENT: "Better code quality",
            DiscoveryType.NEW_FEATURE: "Enhanced functionality",
            DiscoveryType.REFACTORING: "Improved architecture",
            DiscoveryType.TESTING: "Better test coverage",
            DiscoveryType.TOOLING: "Developer productivity"
        }
        
        if discovery.discovery_type in type_benefits:
            benefits.append(type_benefits[discovery.discovery_type])
        
        # Integration readiness
        if discovery.integration_ready:
            benefits.append("Ready for immediate integration")
        
        return benefits
    
    def create_integration_story(self, discovery: Discovery) -> str:
        """Create integration story for discovery."""
        
        if discovery.integration_ready:
            return f"This discovery is ready for integration with {len(discovery.integration_instructions)} clear steps. " + \
                   f"Integration should take approximately 30-60 minutes depending on complexity."
        else:
            return "This discovery requires additional preparation before integration. Review the requirements and prepare your environment."
    
    def extract_technical_highlights(self, discovery: Discovery) -> List[str]:
        """Extract technical highlights from discovery."""
        
        highlights = []
        
        # Code artifact highlights
        total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        if total_artifacts > 0:
            highlights.append(f"{total_artifacts} code artifacts generated")
        
        # Language highlights
        languages = set()
        for result in discovery.exploration_results:
            for artifact in result.code_artifacts:
                languages.add(artifact.language)
        
        if languages:
            highlights.append(f"Languages: {', '.join(languages)}")
        
        # Novelty highlight
        if discovery.novelty_score > 0.7:
            highlights.append("Innovative approach")
        
        return highlights
    
    def create_risk_narrative(self, discovery: Discovery) -> str:
        """Create risk assessment narrative."""
        
        risk_level = discovery.integration_risk
        
        risk_narratives = {
            'low': "Low risk integration with minimal chance of conflicts or issues.",
            'moderate': "Moderate risk integration requiring careful testing and validation.",
            'high': "High risk integration requiring extensive testing and rollback planning."
        }
        
        base_narrative = risk_narratives.get(risk_level, "Risk level requires assessment.")
        
        # Add backup information
        if discovery.integration_ready:
            base_narrative += " Comprehensive backup and rollback procedures are included."
        
        return base_narrative