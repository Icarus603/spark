"""
Conflict resolution system with user guidance.

This module provides intelligent conflict detection and resolution
guidance for discovery integration processes.
"""

import os
import re
import difflib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from spark.discovery.models import Discovery


class ConflictType(Enum):
    """Types of conflicts that can occur during integration."""
    FILE_EXISTS = "file_exists"                 # File already exists with different content
    IMPORT_CONFLICT = "import_conflict"         # Conflicting imports
    FUNCTION_REDEFINITION = "function_redefinition"  # Function already defined
    CLASS_REDEFINITION = "class_redefinition"   # Class already defined
    VARIABLE_CONFLICT = "variable_conflict"     # Variable name conflicts
    STYLE_MISMATCH = "style_mismatch"          # Code style inconsistencies
    DEPENDENCY_CONFLICT = "dependency_conflict" # Conflicting dependencies
    GIT_MERGE = "git_merge"                     # Git merge conflicts


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    OVERWRITE = "overwrite"                     # Replace existing with new
    MERGE = "merge"                            # Merge both versions
    RENAME = "rename"                          # Rename conflicting elements
    SKIP = "skip"                              # Skip conflicting changes
    INTERACTIVE = "interactive"                # User chooses resolution
    AUTO_RESOLVE = "auto_resolve"              # Attempt automatic resolution


@dataclass
class ConflictLocation:
    """Represents a location where conflict occurs."""
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    context_lines: List[str] = field(default_factory=list)


@dataclass
class ConflictDetail:
    """Detailed information about a conflict."""
    conflict_id: str
    conflict_type: ConflictType
    location: ConflictLocation
    existing_content: str
    new_content: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    auto_resolvable: bool = False
    suggested_strategies: List[ResolutionStrategy] = field(default_factory=list)
    user_guidance: str = ""


@dataclass
class ResolutionPlan:
    """Plan for resolving a conflict."""
    conflict_id: str
    strategy: ResolutionStrategy
    resolved_content: Optional[str] = None
    additional_changes: List[str] = field(default_factory=list)
    user_confirmation_required: bool = True
    rollback_instructions: str = ""


class ConflictResolver:
    """Intelligent conflict detection and resolution system."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.detected_conflicts: Dict[str, ConflictDetail] = {}
        self.resolution_plans: Dict[str, ResolutionPlan] = {}
        
    def detect_integration_conflicts(
        self,
        discovery: Discovery,
        target_directory: Optional[str] = None
    ) -> List[ConflictDetail]:
        """Detect potential conflicts before integration."""
        
        target_dir = Path(target_directory) if target_directory else self.project_root
        conflicts = []
        
        for exploration_result in discovery.exploration_results:
            for artifact in exploration_result.code_artifacts:
                target_path = target_dir / artifact.file_path
                
                # File existence conflicts
                if target_path.exists():
                    file_conflicts = self._detect_file_conflicts(
                        target_path,
                        artifact.content,
                        artifact.language
                    )
                    conflicts.extend(file_conflicts)
                
                # Language-specific conflicts
                if artifact.language.lower() == 'python':
                    py_conflicts = self._detect_python_conflicts(
                        target_path,
                        artifact.content
                    )
                    conflicts.extend(py_conflicts)
                
                # Git conflicts
                git_conflicts = self._detect_git_conflicts(target_path)
                conflicts.extend(git_conflicts)
        
        # Store detected conflicts
        for conflict in conflicts:
            self.detected_conflicts[conflict.conflict_id] = conflict
        
        return conflicts
    
    def suggest_resolutions(
        self,
        conflict: ConflictDetail
    ) -> List[ResolutionPlan]:
        """Suggest resolution strategies for a conflict."""
        
        plans = []
        
        if conflict.conflict_type == ConflictType.FILE_EXISTS:
            plans.extend(self._suggest_file_conflict_resolutions(conflict))
        elif conflict.conflict_type == ConflictType.FUNCTION_REDEFINITION:
            plans.extend(self._suggest_function_conflict_resolutions(conflict))
        elif conflict.conflict_type == ConflictType.IMPORT_CONFLICT:
            plans.extend(self._suggest_import_conflict_resolutions(conflict))
        elif conflict.conflict_type == ConflictType.STYLE_MISMATCH:
            plans.extend(self._suggest_style_conflict_resolutions(conflict))
        
        # Store resolution plans
        for plan in plans:
            self.resolution_plans[plan.conflict_id] = plan
        
        return plans
    
    def auto_resolve_conflicts(
        self,
        conflicts: List[ConflictDetail],
        safety_level: str = "conservative"
    ) -> Dict[str, ResolutionPlan]:
        """Attempt automatic resolution of conflicts."""
        
        resolved = {}
        
        for conflict in conflicts:
            if not conflict.auto_resolvable:
                continue
            
            if safety_level == "aggressive":
                # More permissive auto-resolution
                max_severity = "high"
            elif safety_level == "moderate":
                max_severity = "medium"  
            else:  # conservative
                max_severity = "low"
            
            # Only auto-resolve if severity is acceptable
            severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            if severity_levels[conflict.severity] <= severity_levels[max_severity]:
                resolution = self._attempt_auto_resolution(conflict)
                if resolution:
                    resolved[conflict.conflict_id] = resolution
        
        return resolved
    
    def create_resolution_guidance(
        self,
        conflict: ConflictDetail
    ) -> Dict[str, Any]:
        """Create comprehensive guidance for manual conflict resolution."""
        
        guidance = {
            'conflict_summary': self._create_conflict_summary(conflict),
            'impact_assessment': self._assess_conflict_impact(conflict),
            'resolution_options': self._list_resolution_options(conflict),
            'recommended_approach': self._recommend_resolution_approach(conflict),
            'step_by_step_guide': self._create_resolution_steps(conflict),
            'safety_considerations': self._identify_safety_considerations(conflict),
            'testing_requirements': self._suggest_testing_requirements(conflict)
        }
        
        return guidance
    
    def apply_resolution_plan(
        self,
        plan: ResolutionPlan,
        confirm: bool = True
    ) -> bool:
        """Apply a resolution plan to resolve a conflict."""
        
        if plan.user_confirmation_required and not confirm:
            return False
        
        conflict = self.detected_conflicts.get(plan.conflict_id)
        if not conflict:
            return False
        
        try:
            if plan.strategy == ResolutionStrategy.OVERWRITE:
                return self._apply_overwrite_resolution(conflict, plan)
            elif plan.strategy == ResolutionStrategy.MERGE:
                return self._apply_merge_resolution(conflict, plan)
            elif plan.strategy == ResolutionStrategy.RENAME:
                return self._apply_rename_resolution(conflict, plan)
            elif plan.strategy == ResolutionStrategy.SKIP:
                return True  # Skip is always successful
            else:
                return False
                
        except Exception as e:
            print(f"Failed to apply resolution plan: {e}")
            return False
    
    def get_conflict_report(self) -> Dict[str, Any]:
        """Generate comprehensive conflict report."""
        
        conflicts_by_type = {}
        conflicts_by_severity = {}
        
        for conflict in self.detected_conflicts.values():
            # Group by type
            conflict_type = conflict.conflict_type.value
            conflicts_by_type[conflict_type] = conflicts_by_type.get(conflict_type, 0) + 1
            
            # Group by severity
            severity = conflict.severity
            conflicts_by_severity[severity] = conflicts_by_severity.get(severity, 0) + 1
        
        auto_resolvable = sum(1 for c in self.detected_conflicts.values() if c.auto_resolvable)
        
        return {
            'total_conflicts': len(self.detected_conflicts),
            'auto_resolvable': auto_resolvable,
            'manual_resolution_required': len(self.detected_conflicts) - auto_resolvable,
            'conflicts_by_type': conflicts_by_type,
            'conflicts_by_severity': conflicts_by_severity,
            'resolution_plans_created': len(self.resolution_plans)
        }
    
    # Private helper methods
    
    def _detect_file_conflicts(
        self,
        target_path: Path,
        new_content: str,
        language: str
    ) -> List[ConflictDetail]:
        """Detect conflicts when file already exists."""
        
        conflicts = []
        
        if not target_path.exists():
            return conflicts
        
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except (IOError, UnicodeDecodeError):
            return conflicts
        
        if existing_content.strip() == new_content.strip():
            return conflicts  # No conflict if content is identical
        
        # Create file conflict
        conflict = ConflictDetail(
            conflict_id=f"file_conflict_{target_path.name}",
            conflict_type=ConflictType.FILE_EXISTS,
            location=ConflictLocation(file_path=str(target_path)),
            existing_content=existing_content,
            new_content=new_content,
            description=f"File {target_path.name} already exists with different content",
            severity=self._assess_file_conflict_severity(existing_content, new_content),
            auto_resolvable=self._is_file_conflict_auto_resolvable(existing_content, new_content),
            suggested_strategies=[
                ResolutionStrategy.MERGE,
                ResolutionStrategy.OVERWRITE,
                ResolutionStrategy.INTERACTIVE
            ]
        )
        
        conflict.user_guidance = self._generate_file_conflict_guidance(conflict)
        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_python_conflicts(
        self,
        target_path: Path,
        new_content: str
    ) -> List[ConflictDetail]:
        """Detect Python-specific conflicts."""
        
        conflicts = []
        
        if not target_path.exists():
            return conflicts
        
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except (IOError, UnicodeDecodeError):
            return conflicts
        
        # Extract functions and classes from both versions
        existing_funcs = self._extract_python_functions(existing_content)
        new_funcs = self._extract_python_functions(new_content)
        
        existing_classes = self._extract_python_classes(existing_content)
        new_classes = self._extract_python_classes(new_content)
        
        # Check for function redefinitions
        for func_name in new_funcs:
            if func_name in existing_funcs:
                conflict = ConflictDetail(
                    conflict_id=f"func_conflict_{target_path.name}_{func_name}",
                    conflict_type=ConflictType.FUNCTION_REDEFINITION,
                    location=ConflictLocation(
                        file_path=str(target_path),
                        line_number=existing_funcs[func_name].get('line', 1)
                    ),
                    existing_content=existing_funcs[func_name]['content'],
                    new_content=new_funcs[func_name]['content'],
                    description=f"Function '{func_name}' is redefined",
                    severity="medium",
                    auto_resolvable=False,
                    suggested_strategies=[
                        ResolutionStrategy.RENAME,
                        ResolutionStrategy.MERGE,
                        ResolutionStrategy.INTERACTIVE
                    ]
                )
                conflicts.append(conflict)
        
        # Check for class redefinitions
        for class_name in new_classes:
            if class_name in existing_classes:
                conflict = ConflictDetail(
                    conflict_id=f"class_conflict_{target_path.name}_{class_name}",
                    conflict_type=ConflictType.CLASS_REDEFINITION,
                    location=ConflictLocation(
                        file_path=str(target_path),
                        line_number=existing_classes[class_name].get('line', 1)
                    ),
                    existing_content=existing_classes[class_name]['content'],
                    new_content=new_classes[class_name]['content'],
                    description=f"Class '{class_name}' is redefined",
                    severity="high",
                    auto_resolvable=False,
                    suggested_strategies=[
                        ResolutionStrategy.RENAME,
                        ResolutionStrategy.INTERACTIVE
                    ]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_git_conflicts(self, target_path: Path) -> List[ConflictDetail]:
        """Detect existing Git merge conflicts."""
        
        conflicts = []
        
        if not target_path.exists():
            return conflicts
        
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return conflicts
        
        # Check for Git conflict markers
        conflict_markers = ['<<<<<<<', '>>>>>>>', '=======']
        
        for marker in conflict_markers:
            if marker in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if marker in line:
                        conflict = ConflictDetail(
                            conflict_id=f"git_conflict_{target_path.name}_{i}",
                            conflict_type=ConflictType.GIT_MERGE,
                            location=ConflictLocation(
                                file_path=str(target_path),
                                line_number=i + 1,
                                context_lines=lines[max(0, i-3):i+4]
                            ),
                            existing_content=line,
                            new_content="",
                            description=f"Git merge conflict marker found at line {i + 1}",
                            severity="critical",
                            auto_resolvable=False,
                            suggested_strategies=[ResolutionStrategy.INTERACTIVE]
                        )
                        conflicts.append(conflict)
                        break  # One conflict per file is enough
        
        return conflicts
    
    def _extract_python_functions(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract function definitions from Python code."""
        
        functions = {}
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Match function definitions
            match = re.match(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
            if match:
                func_name = match.group(1)
                
                # Extract function body (simplified)
                func_lines = [line]
                j = i + 1
                while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
                    func_lines.append(lines[j])
                    j += 1
                
                functions[func_name] = {
                    'line': i + 1,
                    'content': '\n'.join(func_lines)
                }
        
        return functions
    
    def _extract_python_classes(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract class definitions from Python code."""
        
        classes = {}
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Match class definitions
            match = re.match(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                class_name = match.group(1)
                
                # Extract class body (simplified)
                class_lines = [line]
                j = i + 1
                while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
                    class_lines.append(lines[j])
                    j += 1
                
                classes[class_name] = {
                    'line': i + 1,
                    'content': '\n'.join(class_lines)
                }
        
        return classes
    
    def _assess_file_conflict_severity(self, existing: str, new: str) -> str:
        """Assess severity of file conflict."""
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, existing, new).ratio()
        
        if similarity > 0.8:
            return "low"
        elif similarity > 0.5:
            return "medium"
        else:
            return "high"
    
    def _is_file_conflict_auto_resolvable(self, existing: str, new: str) -> bool:
        """Determine if file conflict can be auto-resolved."""
        
        # Simple heuristics for auto-resolution
        similarity = difflib.SequenceMatcher(None, existing, new).ratio()
        
        # Very similar files might be auto-resolvable
        if similarity > 0.9:
            return True
        
        # Empty existing file is auto-resolvable
        if existing.strip() == "":
            return True
        
        return False
    
    def _generate_file_conflict_guidance(self, conflict: ConflictDetail) -> str:
        """Generate user guidance for file conflicts."""
        
        return f"""
File Conflict Resolution Guidance:

The file '{conflict.location.file_path}' already exists with different content.

Options:
1. MERGE: Combine both versions (recommended for similar files)
2. OVERWRITE: Replace existing with new content (use if new version is complete)
3. INTERACTIVE: Review changes manually before deciding

Safety tip: Always create a backup before applying any resolution.
"""
    
    def _suggest_file_conflict_resolutions(self, conflict: ConflictDetail) -> List[ResolutionPlan]:
        """Suggest resolutions for file conflicts."""
        
        plans = []
        
        # Merge resolution
        merge_plan = ResolutionPlan(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.MERGE,
            resolved_content=self._attempt_merge(conflict.existing_content, conflict.new_content),
            user_confirmation_required=True,
            rollback_instructions="Restore from backup if merge causes issues"
        )
        plans.append(merge_plan)
        
        # Overwrite resolution
        overwrite_plan = ResolutionPlan(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.OVERWRITE,
            resolved_content=conflict.new_content,
            user_confirmation_required=True,
            rollback_instructions="Restore original file from backup"
        )
        plans.append(overwrite_plan)
        
        return plans
    
    def _suggest_function_conflict_resolutions(self, conflict: ConflictDetail) -> List[ResolutionPlan]:
        """Suggest resolutions for function conflicts."""
        
        plans = []
        
        # Rename resolution
        rename_plan = ResolutionPlan(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.RENAME,
            additional_changes=[
                "Rename new function to avoid conflict",
                "Update any references to use new name"
            ],
            user_confirmation_required=True
        )
        plans.append(rename_plan)
        
        return plans
    
    def _suggest_import_conflict_resolutions(self, conflict: ConflictDetail) -> List[ResolutionPlan]:
        """Suggest resolutions for import conflicts."""
        
        plans = []
        
        # Auto-resolve plan for import conflicts
        auto_plan = ResolutionPlan(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.AUTO_RESOLVE,
            user_confirmation_required=False,
            rollback_instructions="Remove duplicate imports if issues occur"
        )
        plans.append(auto_plan)
        
        return plans
    
    def _suggest_style_conflict_resolutions(self, conflict: ConflictDetail) -> List[ResolutionPlan]:
        """Suggest resolutions for style conflicts."""
        
        plans = []
        
        # Auto-resolve style conflicts
        style_plan = ResolutionPlan(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.AUTO_RESOLVE,
            additional_changes=["Apply consistent code formatting"],
            user_confirmation_required=False
        )
        plans.append(style_plan)
        
        return plans
    
    def _attempt_auto_resolution(self, conflict: ConflictDetail) -> Optional[ResolutionPlan]:
        """Attempt automatic resolution of conflict."""
        
        if conflict.conflict_type == ConflictType.IMPORT_CONFLICT:
            return ResolutionPlan(
                conflict_id=conflict.conflict_id,
                strategy=ResolutionStrategy.AUTO_RESOLVE,
                resolved_content=self._resolve_import_conflict(conflict),
                user_confirmation_required=False
            )
        
        return None
    
    def _attempt_merge(self, existing: str, new: str) -> str:
        """Attempt to merge two versions of content."""
        
        # Simple line-based merge
        existing_lines = set(existing.split('\n'))
        new_lines = set(new.split('\n'))
        
        # Combine unique lines (very simple approach)
        merged_lines = sorted(existing_lines.union(new_lines))
        
        return '\n'.join(merged_lines)
    
    def _resolve_import_conflict(self, conflict: ConflictDetail) -> str:
        """Resolve import conflicts by deduplication."""
        
        # Extract imports and deduplicate
        existing_imports = set(re.findall(r'^import\s+.*|^from\s+.*import\s+.*', conflict.existing_content, re.MULTILINE))
        new_imports = set(re.findall(r'^import\s+.*|^from\s+.*import\s+.*', conflict.new_content, re.MULTILINE))
        
        # Combine and sort imports
        all_imports = sorted(existing_imports.union(new_imports))
        
        return '\n'.join(all_imports)
    
    def _create_conflict_summary(self, conflict: ConflictDetail) -> str:
        """Create summary of conflict for user."""
        return f"Conflict in {conflict.location.file_path}: {conflict.description}"
    
    def _assess_conflict_impact(self, conflict: ConflictDetail) -> str:
        """Assess impact of conflict on project."""
        
        impact_levels = {
            "low": "Minimal impact, safe to resolve automatically",
            "medium": "Moderate impact, review recommended", 
            "high": "Significant impact, careful review required",
            "critical": "Critical impact, manual resolution required"
        }
        
        return impact_levels.get(conflict.severity, "Unknown impact")
    
    def _list_resolution_options(self, conflict: ConflictDetail) -> List[str]:
        """List available resolution options."""
        
        return [strategy.value for strategy in conflict.suggested_strategies]
    
    def _recommend_resolution_approach(self, conflict: ConflictDetail) -> str:
        """Recommend best resolution approach."""
        
        if conflict.auto_resolvable:
            return "Auto-resolution recommended (low risk)"
        elif conflict.severity == "low":
            return "Manual review recommended (quick fix)"
        else:
            return "Careful manual resolution required"
    
    def _create_resolution_steps(self, conflict: ConflictDetail) -> List[str]:
        """Create step-by-step resolution guide."""
        
        steps = [
            "1. Review the conflict details carefully",
            "2. Create a backup of current state",
            "3. Choose appropriate resolution strategy",
            "4. Apply the resolution",
            "5. Test the changes thoroughly",
            "6. Commit if everything works correctly"
        ]
        
        return steps
    
    def _identify_safety_considerations(self, conflict: ConflictDetail) -> List[str]:
        """Identify safety considerations for resolution."""
        
        considerations = ["Always create backup before resolution"]
        
        if conflict.severity in ["high", "critical"]:
            considerations.extend([
                "Test thoroughly after resolution",
                "Consider using feature branch",
                "Have rollback plan ready"
            ])
        
        return considerations
    
    def _suggest_testing_requirements(self, conflict: ConflictDetail) -> List[str]:
        """Suggest testing requirements after resolution."""
        
        tests = ["Run unit tests"]
        
        if conflict.conflict_type in [ConflictType.FUNCTION_REDEFINITION, ConflictType.CLASS_REDEFINITION]:
            tests.append("Test affected functionality specifically")
        
        if conflict.severity in ["high", "critical"]:
            tests.extend([
                "Run full test suite",
                "Manual testing of affected areas"
            ])
        
        return tests
    
    # Resolution application methods
    
    def _apply_overwrite_resolution(self, conflict: ConflictDetail, plan: ResolutionPlan) -> bool:
        """Apply overwrite resolution strategy."""
        
        try:
            with open(conflict.location.file_path, 'w', encoding='utf-8') as f:
                f.write(plan.resolved_content or conflict.new_content)
            return True
        except IOError:
            return False
    
    def _apply_merge_resolution(self, conflict: ConflictDetail, plan: ResolutionPlan) -> bool:
        """Apply merge resolution strategy."""
        
        if not plan.resolved_content:
            plan.resolved_content = self._attempt_merge(conflict.existing_content, conflict.new_content)
        
        try:
            with open(conflict.location.file_path, 'w', encoding='utf-8') as f:
                f.write(plan.resolved_content)
            return True
        except IOError:
            return False
    
    def _apply_rename_resolution(self, conflict: ConflictDetail, plan: ResolutionPlan) -> bool:
        """Apply rename resolution strategy."""
        
        # This would implement function/class renaming logic
        # For now, return success as placeholder
        return True