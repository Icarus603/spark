"""
Comprehensive backup and rollback system for Spark.

This module provides advanced backup and recovery capabilities to ensure
safe integration of discoveries with full rollback capabilities.
"""

import os
import json
import shutil
import hashlib
import subprocess
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class BackupType(Enum):
    """Types of backups that can be created."""
    INTEGRATION = "integration"          # Backup before discovery integration
    SNAPSHOT = "snapshot"               # Full project snapshot
    INCREMENTAL = "incremental"         # Changes since last backup
    GIT_STATE = "git_state"            # Git repository state only


class BackupStatus(Enum):
    """Status of backup operations."""
    CREATING = "creating"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    RESTORING = "restoring"
    RESTORED = "restored"


@dataclass
class BackupMetadata:
    """Metadata for backup tracking."""
    backup_id: str
    backup_type: BackupType
    created_at: datetime
    size_bytes: int
    file_count: int
    git_commit_hash: Optional[str] = None
    git_branch: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    

@dataclass  
class RestorePoint:
    """Represents a point in time that can be restored to."""
    restore_id: str
    backup_id: str
    created_at: datetime
    description: str
    file_paths: List[str] = field(default_factory=list)
    git_state: Optional[Dict[str, str]] = None
    can_restore: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackupSystem:
    """Advanced backup and rollback system."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.backup_root = self.project_root / ".spark" / "backups"
        self.metadata_dir = self.backup_root / "metadata"
        
        # Create directories
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active backups
        self.active_backups: Dict[str, BackupMetadata] = {}
        self._load_existing_backups()
    
    def create_integration_backup(
        self,
        integration_id: str,
        affected_files: List[str],
        description: str = ""
    ) -> BackupMetadata:
        """Create backup before discovery integration."""
        
        backup_id = f"integration_{integration_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.INTEGRATION,
            created_at=datetime.now(),
            size_bytes=0,
            file_count=0,
            description=description or f"Integration backup for {integration_id}"
        )
        
        # Capture git state
        metadata.git_commit_hash = self._get_git_commit_hash()
        metadata.git_branch = self._get_git_branch()
        
        # Backup affected files
        total_size = 0
        file_count = 0
        
        for file_path in affected_files:
            if os.path.exists(file_path):
                # Create relative path for backup
                rel_path = os.path.relpath(file_path, self.project_root)
                backup_file_path = backup_dir / "files" / rel_path
                
                # Ensure backup directory exists
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file with metadata
                shutil.copy2(file_path, backup_file_path)
                
                # Track size and count
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        # Update metadata
        metadata.size_bytes = total_size
        metadata.file_count = file_count
        metadata.checksum = self._calculate_backup_checksum(backup_dir)
        
        # Save metadata
        self._save_backup_metadata(metadata)
        
        # Track active backup
        self.active_backups[backup_id] = metadata
        
        return metadata
    
    def create_project_snapshot(
        self,
        description: str = "",
        exclude_patterns: Optional[List[str]] = None
    ) -> BackupMetadata:
        """Create full project snapshot."""
        
        backup_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        exclude_patterns = exclude_patterns or [
            ".git/*", "node_modules/*", "__pycache__/*", "*.pyc", 
            ".spark/backups/*", "venv/*", ".venv/*"
        ]
        
        # Create backup metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.SNAPSHOT,
            created_at=datetime.now(),
            size_bytes=0,
            file_count=0,
            description=description or "Full project snapshot"
        )
        
        # Capture git state
        metadata.git_commit_hash = self._get_git_commit_hash()
        metadata.git_branch = self._get_git_branch()
        
        # Copy entire project (excluding patterns)
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if self._should_exclude(file_path, exclude_patterns):
                    continue
                
                # Create backup path
                rel_path = os.path.relpath(file_path, self.project_root)
                backup_file_path = backup_dir / "snapshot" / rel_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                try:
                    shutil.copy2(file_path, backup_file_path)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except (IOError, OSError):
                    continue  # Skip files that can't be copied
        
        # Update metadata
        metadata.size_bytes = total_size
        metadata.file_count = file_count
        metadata.checksum = self._calculate_backup_checksum(backup_dir)
        
        # Save metadata
        self._save_backup_metadata(metadata)
        self.active_backups[backup_id] = metadata
        
        return metadata
    
    def create_restore_point(
        self,
        restore_id: str,
        backup_id: str,
        description: str,
        file_paths: Optional[List[str]] = None
    ) -> RestorePoint:
        """Create a restore point for selective recovery."""
        
        if backup_id not in self.active_backups:
            raise ValueError(f"Backup {backup_id} not found")
        
        restore_point = RestorePoint(
            restore_id=restore_id,
            backup_id=backup_id,
            created_at=datetime.now(),
            description=description,
            file_paths=file_paths or [],
            git_state={
                'commit': self._get_git_commit_hash(),
                'branch': self._get_git_branch()
            }
        )
        
        # Save restore point metadata
        restore_path = self.metadata_dir / f"restore_{restore_id}.json"
        with open(restore_path, 'w') as f:
            json.dump({
                'restore_id': restore_point.restore_id,
                'backup_id': restore_point.backup_id,
                'created_at': restore_point.created_at.isoformat(),
                'description': restore_point.description,
                'file_paths': restore_point.file_paths,
                'git_state': restore_point.git_state,
                'can_restore': restore_point.can_restore,
                'metadata': restore_point.metadata
            }, f, indent=2)
        
        return restore_point
    
    def restore_from_backup(
        self,
        backup_id: str,
        file_paths: Optional[List[str]] = None,
        create_pre_restore_backup: bool = True
    ) -> bool:
        """Restore files from backup."""
        
        if backup_id not in self.active_backups:
            raise ValueError(f"Backup {backup_id} not found")
        
        backup_metadata = self.active_backups[backup_id]
        backup_dir = self.backup_root / backup_id
        
        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
        
        # Verify backup integrity
        if not self._verify_backup_integrity(backup_metadata, backup_dir):
            raise ValueError(f"Backup {backup_id} is corrupted")
        
        # Create pre-restore backup if requested
        if create_pre_restore_backup:
            self.create_project_snapshot("Pre-restore snapshot")
        
        try:
            # Determine restore scope
            if file_paths is None:
                # Restore all files from backup
                if backup_metadata.backup_type == BackupType.SNAPSHOT:
                    restore_dir = backup_dir / "snapshot"
                else:
                    restore_dir = backup_dir / "files"
                
                # Restore all files
                for root, dirs, files in os.walk(restore_dir):
                    for file in files:
                        backup_file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(backup_file_path, restore_dir)
                        target_path = self.project_root / rel_path
                        
                        # Ensure target directory exists
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Restore file
                        shutil.copy2(backup_file_path, target_path)
            else:
                # Restore specific files
                for file_path in file_paths:
                    rel_path = os.path.relpath(file_path, self.project_root)
                    
                    if backup_metadata.backup_type == BackupType.SNAPSHOT:
                        backup_file_path = backup_dir / "snapshot" / rel_path
                    else:
                        backup_file_path = backup_dir / "files" / rel_path
                    
                    if backup_file_path.exists():
                        target_path = Path(file_path)
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_file_path, target_path)
            
            # Restore git state if available
            if backup_metadata.git_commit_hash:
                self._restore_git_state(backup_metadata)
            
            return True
            
        except Exception as e:
            raise Exception(f"Restore failed: {e}")
    
    def restore_from_restore_point(self, restore_id: str) -> bool:
        """Restore from a specific restore point."""
        
        restore_path = self.metadata_dir / f"restore_{restore_id}.json"
        if not restore_path.exists():
            raise FileNotFoundError(f"Restore point {restore_id} not found")
        
        # Load restore point metadata
        with open(restore_path, 'r') as f:
            restore_data = json.load(f)
        
        restore_point = RestorePoint(
            restore_id=restore_data['restore_id'],
            backup_id=restore_data['backup_id'],
            created_at=datetime.fromisoformat(restore_data['created_at']),
            description=restore_data['description'],
            file_paths=restore_data['file_paths'],
            git_state=restore_data.get('git_state'),
            can_restore=restore_data.get('can_restore', True),
            metadata=restore_data.get('metadata', {})
        )
        
        if not restore_point.can_restore:
            raise ValueError(f"Restore point {restore_id} is not restorable")
        
        # Restore from backup
        return self.restore_from_backup(
            restore_point.backup_id,
            restore_point.file_paths if restore_point.file_paths else None
        )
    
    def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        since: Optional[datetime] = None
    ) -> List[BackupMetadata]:
        """List available backups."""
        
        backups = list(self.active_backups.values())
        
        # Filter by type
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]
        
        # Filter by date
        if since:
            backups = [b for b in backups if b.created_at >= since]
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)
        
        return backups
    
    def list_restore_points(self) -> List[RestorePoint]:
        """List available restore points."""
        
        restore_points = []
        
        for restore_file in self.metadata_dir.glob("restore_*.json"):
            try:
                with open(restore_file, 'r') as f:
                    restore_data = json.load(f)
                
                restore_point = RestorePoint(
                    restore_id=restore_data['restore_id'],
                    backup_id=restore_data['backup_id'],
                    created_at=datetime.fromisoformat(restore_data['created_at']),
                    description=restore_data['description'],
                    file_paths=restore_data['file_paths'],
                    git_state=restore_data.get('git_state'),
                    can_restore=restore_data.get('can_restore', True),
                    metadata=restore_data.get('metadata', {})
                )
                
                restore_points.append(restore_point)
                
            except (json.JSONDecodeError, KeyError):
                continue  # Skip corrupted restore points
        
        # Sort by creation time (newest first)
        restore_points.sort(key=lambda rp: rp.created_at, reverse=True)
        
        return restore_points
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup and its metadata."""
        
        if backup_id not in self.active_backups:
            return False
        
        # Remove backup directory
        backup_dir = self.backup_root / backup_id
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # Remove metadata file
        metadata_file = self.metadata_dir / f"backup_{backup_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
        
        # Remove from active backups
        del self.active_backups[backup_id]
        
        return True
    
    def cleanup_old_backups(
        self,
        older_than_days: int = 30,
        keep_count: int = 5
    ) -> List[str]:
        """Clean up old backups based on age and count."""
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # Get backups sorted by age
        all_backups = sorted(self.active_backups.values(), key=lambda b: b.created_at, reverse=True)
        
        deleted_backups = []
        
        # Keep recent backups and minimum count
        for i, backup in enumerate(all_backups):
            should_delete = (
                i >= keep_count and  # Keep minimum count
                backup.created_at < cutoff_date  # Older than cutoff
            )
            
            if should_delete:
                if self.delete_backup(backup.backup_id):
                    deleted_backups.append(backup.backup_id)
        
        return deleted_backups
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get detailed information about a backup."""
        return self.active_backups.get(backup_id)
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify integrity of a backup."""
        
        if backup_id not in self.active_backups:
            return False
        
        backup_metadata = self.active_backups[backup_id]
        backup_dir = self.backup_root / backup_id
        
        return self._verify_backup_integrity(backup_metadata, backup_dir)
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get statistics about backup system."""
        
        total_backups = len(self.active_backups)
        total_size = sum(b.size_bytes for b in self.active_backups.values())
        
        # Group by type
        type_counts = {}
        for backup in self.active_backups.values():
            backup_type = backup.backup_type.value
            type_counts[backup_type] = type_counts.get(backup_type, 0) + 1
        
        # Recent backups (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_backups = [b for b in self.active_backups.values() if b.created_at >= week_ago]
        
        return {
            'total_backups': total_backups,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'backup_types': type_counts,
            'recent_backups': len(recent_backups),
            'oldest_backup': min((b.created_at for b in self.active_backups.values()), default=None),
            'newest_backup': max((b.created_at for b in self.active_backups.values()), default=None)
        }
    
    # Private helper methods
    
    def _load_existing_backups(self):
        """Load existing backup metadata."""
        
        for metadata_file in self.metadata_dir.glob("backup_*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    backup_data = json.load(f)
                
                metadata = BackupMetadata(
                    backup_id=backup_data['backup_id'],
                    backup_type=BackupType(backup_data['backup_type']),
                    created_at=datetime.fromisoformat(backup_data['created_at']),
                    size_bytes=backup_data['size_bytes'],
                    file_count=backup_data['file_count'],
                    git_commit_hash=backup_data.get('git_commit_hash'),
                    git_branch=backup_data.get('git_branch'),
                    description=backup_data.get('description', ''),
                    tags=backup_data.get('tags', []),
                    checksum=backup_data.get('checksum')
                )
                
                self.active_backups[metadata.backup_id] = metadata
                
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # Skip corrupted metadata files
    
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to file."""
        
        metadata_file = self.metadata_dir / f"backup_{metadata.backup_id}.json"
        
        with open(metadata_file, 'w') as f:
            json.dump({
                'backup_id': metadata.backup_id,
                'backup_type': metadata.backup_type.value,
                'created_at': metadata.created_at.isoformat(),
                'size_bytes': metadata.size_bytes,
                'file_count': metadata.file_count,
                'git_commit_hash': metadata.git_commit_hash,
                'git_branch': metadata.git_branch,
                'description': metadata.description,
                'tags': metadata.tags,
                'checksum': metadata.checksum
            }, f, indent=2)
    
    def _get_git_commit_hash(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def _get_git_branch(self) -> Optional[str]:
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
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def _calculate_backup_checksum(self, backup_dir: Path) -> str:
        """Calculate checksum for backup verification."""
        
        hasher = hashlib.sha256()
        
        for root, dirs, files in os.walk(backup_dir):
            # Sort for consistent ordering
            dirs.sort()
            files.sort()
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                except IOError:
                    continue
        
        return hasher.hexdigest()
    
    def _verify_backup_integrity(self, metadata: BackupMetadata, backup_dir: Path) -> bool:
        """Verify backup integrity using checksum."""
        
        if not metadata.checksum:
            return True  # No checksum to verify
        
        current_checksum = self._calculate_backup_checksum(backup_dir)
        return current_checksum == metadata.checksum
    
    def _should_exclude(self, file_path: str, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns."""
        
        rel_path = os.path.relpath(file_path, self.project_root)
        
        for pattern in exclude_patterns:
            if pattern.endswith('/*'):
                # Directory pattern
                dir_pattern = pattern[:-2]
                if rel_path.startswith(dir_pattern):
                    return True
            elif pattern.startswith('*.'):
                # Extension pattern
                if rel_path.endswith(pattern[1:]):
                    return True
            elif rel_path == pattern:
                # Exact match
                return True
        
        return False
    
    def _restore_git_state(self, backup_metadata: BackupMetadata):
        """Restore git state from backup metadata."""
        
        if not backup_metadata.git_commit_hash:
            return
        
        try:
            # Check if we can safely reset
            subprocess.run(
                ['git', 'reset', '--hard', backup_metadata.git_commit_hash],
                cwd=self.project_root,
                check=True
            )
        except subprocess.CalledProcessError:
            # If reset fails, continue with file-level restore
            pass