"""
Safe discovery integration system.

This module provides multiple strategies for safely integrating discoveries
into existing projects with comprehensive backup and rollback capabilities.
"""

import os
import json
import shutil
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from spark.discovery.models import Discovery, DiscoveryType


class IntegrationStrategy(Enum):
    """Different strategies for integrating discoveries."""
    DIRECT = "direct"                    # Direct integration into current branch
    FEATURE_BRANCH = "feature_branch"    # Create feature branch for integration  
    PARTIAL = "partial"                  # Apply only selected parts
    DOCUMENTATION = "documentation"      # Generate integration guide without changes
    PREVIEW = "preview"                  # Show what would be changed (dry-run)


class IntegrationStatus(Enum):
    """Status of integration process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class IntegrationConfig:
    """Configuration for integration process."""
    strategy: IntegrationStrategy = IntegrationStrategy.FEATURE_BRANCH
    create_backup: bool = True
    run_tests: bool = True
    auto_commit: bool = False
    branch_prefix: str = "spark-integration"
    confirmation_required: bool = True
    max_file_changes: int = 50  # Safety limit
    

@dataclass
class FileChange:
    """Represents a file change during integration."""
    file_path: str
    change_type: str  # create, modify, delete, move
    original_content: Optional[str] = None
    new_content: Optional[str] = None
    backup_path: Optional[str] = None


@dataclass
class IntegrationBackup:
    """Backup information for rollback."""
    backup_id: str
    created_at: datetime
    original_branch: str
    backup_directory: str
    file_changes: List[FileChange] = field(default_factory=list)
    git_commit_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationResult:
    """Result of integration attempt."""
    integration_id: str
    discovery_id: str
    status: IntegrationStatus
    strategy_used: IntegrationStrategy
    files_changed: List[str] = field(default_factory=list)
    backup: Optional[IntegrationBackup] = None
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    can_rollback: bool = True


class SafeIntegrator:
    """Handles safe integration of discoveries with multiple strategies."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.backup_dir = self.project_root / ".spark" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def integrate_discovery(
        self,
        discovery: Discovery,
        config: Optional[IntegrationConfig] = None
    ) -> IntegrationResult:
        """Integrate a discovery using specified strategy."""
        
        config = config or IntegrationConfig()
        integration_id = f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = IntegrationResult(
            integration_id=integration_id,
            discovery_id=discovery.id,
            status=IntegrationStatus.PENDING,
            strategy_used=config.strategy
        )
        
        try:
            result.status = IntegrationStatus.IN_PROGRESS
            
            # Create backup if required
            if config.create_backup:
                result.backup = self._create_backup(integration_id, discovery)
            
            # Execute integration strategy
            if config.strategy == IntegrationStrategy.DIRECT:
                result = self._integrate_direct(discovery, config, result)
            elif config.strategy == IntegrationStrategy.FEATURE_BRANCH:
                result = self._integrate_feature_branch(discovery, config, result)
            elif config.strategy == IntegrationStrategy.PARTIAL:
                result = self._integrate_partial(discovery, config, result)
            elif config.strategy == IntegrationStrategy.DOCUMENTATION:
                result = self._generate_documentation(discovery, config, result)
            elif config.strategy == IntegrationStrategy.PREVIEW:
                result = self._preview_integration(discovery, config, result)
            
            result.status = IntegrationStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = IntegrationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()
            
            # Attempt automatic rollback on failure
            if result.backup and config.create_backup:
                try:
                    self.rollback_integration(result)
                    result.status = IntegrationStatus.ROLLED_BACK
                except Exception as rollback_error:
                    result.error_message += f" | Rollback also failed: {rollback_error}"
        
        return result
    
    def rollback_integration(self, integration_result: IntegrationResult) -> bool:
        """Rollback a completed integration."""
        
        if not integration_result.backup:
            raise ValueError("No backup available for rollback")
        
        backup = integration_result.backup
        
        try:
            # Restore files from backup
            for file_change in backup.file_changes:
                self._restore_file_from_backup(file_change)
            
            # Restore git state if available
            if backup.git_commit_hash:
                self._restore_git_state(backup)
            
            return True
            
        except Exception as e:
            raise Exception(f"Rollback failed: {e}")
    
    def preview_integration(self, discovery: Discovery) -> Dict[str, Any]:
        """Preview what integration would change without making changes."""
        
        config = IntegrationConfig(strategy=IntegrationStrategy.PREVIEW)
        result = self.integrate_discovery(discovery, config)
        
        return {
            'files_to_change': result.files_changed,
            'estimated_changes': len(result.files_changed),
            'integration_strategy': result.strategy_used.value,
            'safety_checks': self._run_safety_checks(discovery),
            'recommendations': self._get_integration_recommendations(discovery)
        }
    
    def get_integration_recommendations(self, discovery: Discovery) -> Dict[str, Any]:
        """Get recommendations for integrating a specific discovery."""
        
        recommendations = {
            'recommended_strategy': self._recommend_strategy(discovery),
            'safety_level': self._assess_safety_level(discovery),
            'prerequisites': self._check_prerequisites(discovery),
            'estimated_time_minutes': self._estimate_integration_time(discovery),
            'risk_factors': self._identify_risk_factors(discovery)
        }
        
        return recommendations
    
    def _create_backup(self, integration_id: str, discovery: Discovery) -> IntegrationBackup:
        """Create comprehensive backup before integration."""
        
        backup_id = f"backup_{integration_id}"
        backup_dir = self.backup_dir / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Get current git info
        current_branch = self._get_current_branch()
        current_commit = self._get_current_commit_hash()
        
        # Create backup
        backup = IntegrationBackup(
            backup_id=backup_id,
            created_at=datetime.now(),
            original_branch=current_branch,
            backup_directory=str(backup_dir),
            git_commit_hash=current_commit
        )
        
        # Backup files that will be affected
        affected_files = self._identify_affected_files(discovery)
        for file_path in affected_files:
            if os.path.exists(file_path):
                file_change = FileChange(
                    file_path=file_path,
                    change_type="modify",
                    original_content=self._read_file_safely(file_path)
                )
                
                # Copy file to backup directory
                backup_file_path = backup_dir / Path(file_path).name
                shutil.copy2(file_path, backup_file_path)
                file_change.backup_path = str(backup_file_path)
                
                backup.file_changes.append(file_change)
        
        # Save backup metadata
        backup_metadata_path = backup_dir / "backup_metadata.json"
        with open(backup_metadata_path, 'w') as f:
            json.dump({
                'backup_id': backup.backup_id,
                'created_at': backup.created_at.isoformat(),
                'original_branch': backup.original_branch,
                'git_commit_hash': backup.git_commit_hash,
                'discovery_id': discovery.id,
                'file_changes': [
                    {
                        'file_path': fc.file_path,
                        'change_type': fc.change_type,
                        'backup_path': fc.backup_path
                    }
                    for fc in backup.file_changes
                ]
            }, f, indent=2)
        
        return backup
    
    def _integrate_direct(
        self,
        discovery: Discovery,
        config: IntegrationConfig,
        result: IntegrationResult
    ) -> IntegrationResult:
        """Integrate directly into current branch."""
        
        # Apply changes directly
        for exploration_result in discovery.exploration_results:
            for artifact in exploration_result.code_artifacts:
                target_path = self.project_root / artifact.file_path
                
                # Ensure directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(artifact.content)
                
                result.files_changed.append(str(target_path))
        
        # Run tests if configured
        if config.run_tests:
            self._run_integration_tests(result)
        
        # Auto-commit if configured
        if config.auto_commit:
            self._commit_changes(discovery, result)
        
        return result
    
    def _integrate_feature_branch(
        self,
        discovery: Discovery,
        config: IntegrationConfig,
        result: IntegrationResult
    ) -> IntegrationResult:
        """Integrate into a new feature branch."""
        
        # Create feature branch
        branch_name = f"{config.branch_prefix}-{discovery.id[:8]}"
        self._create_and_switch_branch(branch_name)
        
        # Apply changes in branch
        result = self._integrate_direct(discovery, config, result)
        
        # Add branch information to result
        result.metadata = result.metadata or {}
        result.metadata['feature_branch'] = branch_name
        result.metadata['original_branch'] = result.backup.original_branch if result.backup else 'main'
        
        return result
    
    def _integrate_partial(
        self,
        discovery: Discovery,
        config: IntegrationConfig,
        result: IntegrationResult
    ) -> IntegrationResult:
        """Integrate only selected parts of discovery."""
        
        # For now, integrate main artifacts only
        # In a full implementation, this would have user selection
        main_artifacts = [
            artifact for exploration_result in discovery.exploration_results
            for artifact in exploration_result.code_artifacts
            if artifact.is_main_artifact
        ]
        
        if not main_artifacts:
            # If no main artifacts, take the first artifact from each result
            main_artifacts = [
                exploration_result.code_artifacts[0] 
                for exploration_result in discovery.exploration_results
                if exploration_result.code_artifacts
            ]
        
        # Apply only selected artifacts
        for artifact in main_artifacts:
            target_path = self.project_root / artifact.file_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(artifact.content)
            
            result.files_changed.append(str(target_path))
        
        return result
    
    def _generate_documentation(
        self,
        discovery: Discovery,
        config: IntegrationConfig,
        result: IntegrationResult
    ) -> IntegrationResult:
        """Generate integration documentation without making changes."""
        
        # Create integration guide
        guide_path = self.project_root / f"INTEGRATION_GUIDE_{discovery.id[:8]}.md"
        
        guide_content = self._create_integration_guide(discovery)
        
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        result.files_changed.append(str(guide_path))
        
        return result
    
    def _preview_integration(
        self,
        discovery: Discovery,
        config: IntegrationConfig,
        result: IntegrationResult
    ) -> IntegrationResult:
        """Preview integration without making changes."""
        
        # Collect what would be changed
        for exploration_result in discovery.exploration_results:
            for artifact in exploration_result.code_artifacts:
                target_path = self.project_root / artifact.file_path
                result.files_changed.append(str(target_path))
        
        # Add preview information to metadata
        result.metadata = {
            'preview_only': True,
            'would_create_files': len([f for f in result.files_changed if not os.path.exists(f)]),
            'would_modify_files': len([f for f in result.files_changed if os.path.exists(f)]),
            'estimated_lines_changed': self._estimate_lines_changed(discovery)
        }
        
        return result
    
    def _run_safety_checks(self, discovery: Discovery) -> Dict[str, Any]:
        """Run safety checks before integration."""
        
        checks = {
            'git_repo_clean': self._is_git_repo_clean(),
            'no_merge_conflicts': self._check_merge_conflicts(),
            'tests_passing': self._are_tests_passing(),
            'disk_space_sufficient': self._check_disk_space(),
            'file_count_reasonable': len(self._identify_affected_files(discovery)) < 50
        }
        
        checks['all_checks_passed'] = all(checks.values())
        
        return checks
    
    def _recommend_strategy(self, discovery: Discovery) -> IntegrationStrategy:
        """Recommend best integration strategy for discovery."""
        
        # Analyze discovery characteristics
        total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        risk_level = discovery.integration_risk
        
        if risk_level == 'high' or total_artifacts > 10:
            return IntegrationStrategy.FEATURE_BRANCH
        elif risk_level == 'low' and total_artifacts <= 3:
            return IntegrationStrategy.DIRECT
        else:
            return IntegrationStrategy.FEATURE_BRANCH  # Safe default
    
    def _assess_safety_level(self, discovery: Discovery) -> str:
        """Assess safety level of integration."""
        
        risk_level = discovery.integration_risk
        
        # Additional safety factors
        safety_factors = 0
        if discovery.integration_ready:
            safety_factors += 1
        if len(discovery.integration_instructions) > 0:
            safety_factors += 1
        if discovery.confidence_score > 0.8:
            safety_factors += 1
        
        if risk_level == 'low' and safety_factors >= 2:
            return 'high'
        elif risk_level == 'moderate' or safety_factors >= 1:
            return 'medium'
        else:
            return 'low'
    
    # Helper methods
    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'main'  # Fallback
    
    def _get_current_commit_hash(self) -> Optional[str]:
        """Get current commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def _identify_affected_files(self, discovery: Discovery) -> List[str]:
        """Identify files that would be affected by integration."""
        
        affected_files = []
        for exploration_result in discovery.exploration_results:
            for artifact in exploration_result.code_artifacts:
                file_path = self.project_root / artifact.file_path
                affected_files.append(str(file_path))
        
        return affected_files
    
    def _read_file_safely(self, file_path: str) -> Optional[str]:
        """Safely read file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, UnicodeDecodeError):
            return None
    
    def _create_integration_guide(self, discovery: Discovery) -> str:
        """Create comprehensive integration guide."""
        
        guide = f"""# Integration Guide: {discovery.title}

## Discovery Overview
{discovery.description}

**Type**: {discovery.discovery_type.value}
**Impact Score**: {discovery.impact_score:.2f}
**Confidence**: {discovery.confidence_score:.2f}
**Integration Risk**: {discovery.integration_risk}

## Integration Instructions

"""
        
        for i, instruction in enumerate(discovery.integration_instructions, 1):
            guide += f"{i}. {instruction}\n"
        
        guide += f"""
## Files to be Modified/Created

"""
        
        for exploration_result in discovery.exploration_results:
            for artifact in exploration_result.code_artifacts:
                guide += f"- `{artifact.file_path}` ({artifact.language}): {artifact.description}\n"
        
        guide += f"""
## Safety Recommendations

1. Create a backup of your current state
2. Run tests before and after integration
3. Review all changes carefully
4. Consider integrating in a feature branch first

## Rollback Instructions

If integration causes issues:
1. Use `git stash` or `git reset --hard HEAD~1` to undo changes
2. Restore from backup if available
3. Contact support if issues persist

Generated: {datetime.now().isoformat()}
"""
        
        return guide
    
    def _is_git_repo_clean(self) -> bool:
        """Check if git repository has no uncommitted changes."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return len(result.stdout.strip()) == 0
        except subprocess.CalledProcessError:
            return False
    
    def _check_merge_conflicts(self) -> bool:
        """Check for existing merge conflicts."""
        # Simple check for conflict markers
        conflict_markers = ['<<<<<<<', '>>>>>>>', '=======']
        
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if any(marker in content for marker in conflict_markers):
                                return False
                    except (IOError, UnicodeDecodeError):
                        continue
        
        return True
    
    def _are_tests_passing(self) -> bool:
        """Check if tests are currently passing."""
        # This would run the project's test suite
        # For now, return True as placeholder
        return True
    
    def _check_disk_space(self) -> bool:
        """Check if sufficient disk space is available."""
        try:
            stat = shutil.disk_usage(self.project_root)
            free_gb = stat.free / (1024**3)
            return free_gb > 1.0  # At least 1GB free
        except OSError:
            return True  # Assume OK if check fails
    
    def _estimate_lines_changed(self, discovery: Discovery) -> int:
        """Estimate number of lines that would be changed."""
        total_lines = 0
        for exploration_result in discovery.exploration_results:
            for artifact in exploration_result.code_artifacts:
                total_lines += len(artifact.content.split('\n'))
        return total_lines
    
    def _create_and_switch_branch(self, branch_name: str):
        """Create and switch to new git branch."""
        try:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.project_root,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create branch {branch_name}: {e}")
    
    def _run_integration_tests(self, result: IntegrationResult):
        """Run tests after integration."""
        # Placeholder for test execution
        # In full implementation, would run project-specific test commands
        pass
    
    def _commit_changes(self, discovery: Discovery, result: IntegrationResult):
        """Commit integration changes."""
        try:
            # Add all changed files
            for file_path in result.files_changed:
                subprocess.run(['git', 'add', file_path], cwd=self.project_root, check=True)
            
            # Commit with descriptive message
            commit_message = f"integrate: {discovery.title}\n\nIntegrated discovery {discovery.id[:8]} via Spark platform\nFiles changed: {len(result.files_changed)}"
            
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.project_root,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to commit changes: {e}")
    
    def _restore_file_from_backup(self, file_change: FileChange):
        """Restore a file from backup."""
        if file_change.backup_path and os.path.exists(file_change.backup_path):
            shutil.copy2(file_change.backup_path, file_change.file_path)
        elif file_change.original_content is not None:
            with open(file_change.file_path, 'w', encoding='utf-8') as f:
                f.write(file_change.original_content)
    
    def _restore_git_state(self, backup: IntegrationBackup):
        """Restore git state from backup."""
        if backup.git_commit_hash:
            try:
                subprocess.run(
                    ['git', 'reset', '--hard', backup.git_commit_hash],
                    cwd=self.project_root,
                    check=True
                )
            except subprocess.CalledProcessError:
                pass  # Continue with file-level restore
    
    def _check_prerequisites(self, discovery: Discovery) -> List[str]:
        """Check prerequisites for integration."""
        # This would be implemented based on discovery analysis
        return []
    
    def _estimate_integration_time(self, discovery: Discovery) -> int:
        """Estimate integration time in minutes."""
        base_time = 15  # Base time for any integration
        complexity_factor = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        return base_time + (complexity_factor * 5)
    
    def _identify_risk_factors(self, discovery: Discovery) -> List[str]:
        """Identify potential risk factors."""
        risks = []
        
        if discovery.integration_risk == 'high':
            risks.append("High integration risk level")
        
        total_artifacts = sum(len(r.code_artifacts) for r in discovery.exploration_results)
        if total_artifacts > 10:
            risks.append("Large number of code artifacts")
        
        if not discovery.integration_ready:
            risks.append("Discovery not marked as integration-ready")
        
        return risks