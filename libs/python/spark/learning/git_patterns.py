"""
Git pattern analysis engine for learning developer behaviors and preferences.

This module analyzes git repositories to extract meaningful patterns about
coding style, workflow preferences, development rhythms, and technology choices.
"""

import asyncio
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from spark.cli.errors import SparkLearningError


@dataclass
class CommitPattern:
    """Represents patterns in commit behavior."""
    
    # Timing patterns
    preferred_hours: List[int] = field(default_factory=list)  # Hours when commits happen
    commit_frequency: float = 0.0  # Commits per day average
    session_duration: float = 0.0  # Average coding session length in hours
    
    # Content patterns
    message_style: str = "conventional"  # conventional, descriptive, brief
    average_message_length: int = 0
    common_prefixes: List[Tuple[str, int]] = field(default_factory=list)
    
    # Size patterns
    average_files_per_commit: float = 0.0
    average_lines_per_commit: float = 0.0
    prefers_small_commits: bool = True


@dataclass
class BranchPattern:
    """Represents branching and workflow patterns."""
    
    # Workflow style
    workflow_type: str = "feature_branch"  # feature_branch, gitflow, trunk, personal
    uses_pr_workflow: bool = False
    branch_naming_convention: str = ""  # feature/, fix/, etc.
    
    # Branch behavior
    average_branch_lifetime: float = 0.0  # Days
    merge_vs_rebase: str = "merge"  # merge, rebase, mixed
    deletes_merged_branches: bool = True


@dataclass
class LanguagePattern:
    """Represents language usage and preferences."""
    
    # Primary languages by usage percentage
    languages: Dict[str, float] = field(default_factory=dict)
    
    # File organization
    project_structure_style: str = "standard"  # standard, flat, nested, domain
    test_organization: str = "separate"  # separate, alongside, none
    config_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Technology adoption
    framework_usage: Dict[str, float] = field(default_factory=dict)
    tool_preferences: Dict[str, int] = field(default_factory=dict)


@dataclass
class FilePattern:
    """Represents file organization and modification patterns."""
    
    # Modification patterns
    frequently_modified_types: List[str] = field(default_factory=list)
    large_file_threshold: int = 1000  # Lines
    prefers_single_purpose_files: bool = True
    
    # Organization
    directory_depth_preference: int = 3
    naming_conventions: Dict[str, str] = field(default_factory=dict)
    file_size_preferences: Dict[str, int] = field(default_factory=dict)


@dataclass
class GitAnalysisResult:
    """Complete git analysis results."""
    
    repository_path: str
    analysis_date: datetime
    commit_count: int
    
    # Pattern categories
    commit_patterns: CommitPattern
    branch_patterns: BranchPattern
    language_patterns: LanguagePattern
    file_patterns: FilePattern
    
    # Confidence scores
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    analysis_duration: float = 0.0
    git_config: Dict[str, Any] = field(default_factory=dict)


class GitPatternAnalyzer:
    """Analyzes git repositories to extract developer patterns."""
    
    def __init__(self):
        self.language_extensions = {
            ".py": "Python",
            ".js": "JavaScript", 
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript", 
            ".go": "Go",
            ".rs": "Rust",
            ".java": "Java",
            ".kt": "Kotlin",
            ".swift": "Swift",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++",
            ".hpp": "C++",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".scala": "Scala",
            ".clj": "Clojure",
            ".hs": "Haskell",
            ".elm": "Elm",
            ".dart": "Dart",
            ".lua": "Lua",
            ".r": "R",
            ".m": "Objective-C",
            ".mm": "Objective-C++",
        }
    
    async def analyze_repository(self, repo_path: Path) -> GitAnalysisResult:
        """Analyze a git repository and extract patterns."""
        start_time = datetime.now()
        
        try:
            # Validate repository
            if not await self._is_valid_git_repo(repo_path):
                raise SparkLearningError(f"Invalid git repository: {repo_path}")
            
            # Get git configuration
            git_config = await self._get_git_config(repo_path)
            
            # Analyze different aspects
            commits = await self._get_commit_history(repo_path)
            branches = await self._get_branch_info(repo_path)
            files = await self._analyze_file_structure(repo_path)
            
            # Extract patterns
            commit_patterns = self._analyze_commit_patterns(commits)
            branch_patterns = self._analyze_branch_patterns(branches, commits)
            language_patterns = self._analyze_language_patterns(files, commits)
            file_patterns = self._analyze_file_patterns(files, commits)
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(commits, branches, files)
            
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            return GitAnalysisResult(
                repository_path=str(repo_path),
                analysis_date=datetime.now(),
                commit_count=len(commits),
                commit_patterns=commit_patterns,
                branch_patterns=branch_patterns,
                language_patterns=language_patterns,
                file_patterns=file_patterns,
                confidence_scores=confidence_scores,
                analysis_duration=analysis_duration,
                git_config=git_config
            )
            
        except Exception as e:
            raise SparkLearningError(
                f"Failed to analyze repository {repo_path}",
                str(e)
            ) from e
    
    async def _is_valid_git_repo(self, repo_path: Path) -> bool:
        """Check if path is a valid git repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                'git', 'rev-parse', '--git-dir',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            return process.returncode == 0
            
        except (asyncio.TimeoutError, OSError, FileNotFoundError):
            return False
    
    async def _get_git_config(self, repo_path: Path) -> Dict[str, Any]:
        """Get git configuration for the repository."""
        config = {}
        
        try:
            # Get user info
            for key in ['user.name', 'user.email']:
                process = await asyncio.create_subprocess_exec(
                    'git', 'config', key,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    config[key] = stdout.decode().strip()
            
            # Get remote info
            process = await asyncio.create_subprocess_exec(
                'git', 'remote', '-v',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                remotes = stdout.decode().strip().split('\n')
                config['remotes'] = [line for line in remotes if line]
            
        except Exception:
            pass  # Non-critical
        
        return config
    
    async def _get_commit_history(self, repo_path: Path, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get detailed commit history."""
        try:
            # Get commit log with detailed format
            format_str = "%H|%an|%ae|%at|%s|%b"  # Hash, Author, Email, Timestamp, Subject, Body
            
            process = await asyncio.create_subprocess_exec(
                'git', 'log', f'--max-count={limit}', f'--pretty=format:{format_str}',
                '--numstat',  # Show file change statistics
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            
            if process.returncode != 0:
                return []
            
            return self._parse_git_log(stdout.decode())
            
        except Exception:
            return []
    
    def _parse_git_log(self, log_output: str) -> List[Dict[str, Any]]:
        """Parse git log output into structured data."""
        commits = []
        current_commit = None
        
        lines = log_output.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a commit header line
            if '|' in line and len(line.split('|')) >= 6:
                parts = line.split('|', 5)
                if len(parts) >= 6:
                    # Save previous commit
                    if current_commit:
                        commits.append(current_commit)
                    
                    # Parse commit info
                    current_commit = {
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'timestamp': int(parts[3]) if parts[3].isdigit() else 0,
                        'subject': parts[4],
                        'body': parts[5],
                        'files_changed': [],
                        'lines_added': 0,
                        'lines_removed': 0
                    }
            
            # Parse file statistics
            elif current_commit and '\t' in line:
                parts = line.split('\t')
                if len(parts) == 3:
                    added, removed, filename = parts
                    
                    # Parse numbers (might be '-' for binary files)
                    try:
                        added_num = int(added) if added != '-' else 0
                        removed_num = int(removed) if removed != '-' else 0
                    except ValueError:
                        added_num = removed_num = 0
                    
                    current_commit['files_changed'].append({
                        'filename': filename,
                        'added': added_num,
                        'removed': removed_num
                    })
                    
                    current_commit['lines_added'] += added_num
                    current_commit['lines_removed'] += removed_num
            
            i += 1
        
        # Don't forget the last commit
        if current_commit:
            commits.append(current_commit)
        
        return commits
    
    async def _get_branch_info(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Get branch information."""
        branches = []
        
        try:
            # Get all branches
            process = await asyncio.create_subprocess_exec(
                'git', 'branch', '-a', '--format=%(refname:short)|%(committerdate:iso)|%(subject)',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                for line in stdout.decode().split('\n'):
                    if line.strip() and '|' in line:
                        parts = line.split('|', 2)
                        if len(parts) >= 3:
                            branches.append({
                                'name': parts[0].strip(),
                                'last_commit_date': parts[1].strip(),
                                'last_subject': parts[2].strip()
                            })
            
        except Exception:
            pass
        
        return branches
    
    async def _analyze_file_structure(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze file structure and organization."""
        file_info = {
            'total_files': 0,
            'files_by_extension': defaultdict(int),
            'files_by_directory': defaultdict(int),
            'directory_depth_distribution': defaultdict(int),
            'large_files': [],
            'directory_structure': {}
        }
        
        try:
            # Get all tracked files
            process = await asyncio.create_subprocess_exec(
                'git', 'ls-files',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return file_info
            
            files = stdout.decode().split('\n')
            
            for file_path in files:
                if not file_path.strip():
                    continue
                
                file_info['total_files'] += 1
                path_obj = Path(file_path)
                
                # Extension analysis
                if path_obj.suffix:
                    file_info['files_by_extension'][path_obj.suffix.lower()] += 1
                
                # Directory analysis
                if path_obj.parent != Path('.'):
                    file_info['files_by_directory'][str(path_obj.parent)] += 1
                
                # Depth analysis
                depth = len(path_obj.parts) - 1  # Subtract file name
                file_info['directory_depth_distribution'][depth] += 1
                
                # Check file size
                try:
                    full_path = repo_path / path_obj
                    if full_path.exists() and full_path.is_file():
                        size = full_path.stat().st_size
                        if size > 10000:  # Files larger than 10KB
                            file_info['large_files'].append({
                                'path': file_path,
                                'size': size
                            })
                except (OSError, PermissionError):
                    pass
            
        except Exception:
            pass
        
        return file_info
    
    def _analyze_commit_patterns(self, commits: List[Dict[str, Any]]) -> CommitPattern:
        """Analyze commit behavior patterns."""
        if not commits:
            return CommitPattern()
        
        # Timing analysis
        hours = []
        session_gaps = []
        
        for commit in commits:
            if commit['timestamp']:
                dt = datetime.fromtimestamp(commit['timestamp'])
                hours.append(dt.hour)
        
        # Calculate commit sessions (commits within 4 hours = same session)
        sorted_commits = sorted(commits, key=lambda x: x['timestamp'])
        session_starts = []
        last_timestamp = 0
        
        for commit in sorted_commits:
            if commit['timestamp'] - last_timestamp > 4 * 3600:  # 4 hours gap
                if last_timestamp > 0:
                    session_gaps.append(commit['timestamp'] - last_timestamp)
                session_starts.append(commit['timestamp'])
            last_timestamp = commit['timestamp']
        
        # Message pattern analysis
        messages = [c['subject'] for c in commits if c['subject']]
        message_lengths = [len(msg) for msg in messages]
        
        # Detect conventional commit pattern
        conventional_pattern = re.compile(r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+')
        conventional_commits = sum(1 for msg in messages if conventional_pattern.match(msg.lower()))
        
        # Common prefixes
        prefixes = defaultdict(int)
        for msg in messages:
            words = msg.lower().split()
            if words:
                first_word = words[0].rstrip(':')
                prefixes[first_word] += 1
        
        # Size patterns
        files_per_commit = [len(c['files_changed']) for c in commits if c['files_changed']]
        lines_per_commit = [c['lines_added'] + c['lines_removed'] for c in commits]
        
        return CommitPattern(
            preferred_hours=self._get_peak_hours(hours),
            commit_frequency=self._calculate_commit_frequency(commits),
            session_duration=statistics.mean(session_gaps) / 3600 if session_gaps else 0,
            message_style="conventional" if conventional_commits > len(messages) * 0.5 else "descriptive",
            average_message_length=statistics.mean(message_lengths) if message_lengths else 0,
            common_prefixes=list(Counter(prefixes).most_common(5)),
            average_files_per_commit=statistics.mean(files_per_commit) if files_per_commit else 0,
            average_lines_per_commit=statistics.mean(lines_per_commit) if lines_per_commit else 0,
            prefers_small_commits=statistics.mean(files_per_commit) < 5 if files_per_commit else True
        )
    
    def _analyze_branch_patterns(self, branches: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> BranchPattern:
        """Analyze branching patterns."""
        if not branches:
            return BranchPattern()
        
        # Analyze branch naming
        branch_names = [b['name'] for b in branches if not b['name'].startswith('origin/')]
        
        # Common prefixes
        prefixes = defaultdict(int)
        for name in branch_names:
            if '/' in name:
                prefix = name.split('/')[0]
                prefixes[prefix] += 1
        
        most_common_prefix = max(prefixes.items(), key=lambda x: x[1])[0] if prefixes else ""
        
        # Workflow detection
        has_main_or_master = any(name in ['main', 'master'] for name in branch_names)
        has_develop = any('develop' in name.lower() for name in branch_names)
        feature_branches = sum(1 for name in branch_names if 'feature' in name.lower() or 'feat' in name.lower())
        
        if has_develop and feature_branches > 0:
            workflow_type = "gitflow"
        elif feature_branches > 0:
            workflow_type = "feature_branch"
        elif len(branch_names) <= 2:
            workflow_type = "trunk"
        else:
            workflow_type = "personal"
        
        return BranchPattern(
            workflow_type=workflow_type,
            uses_pr_workflow=len([n for n in branch_names if 'pr' in n.lower() or 'pull' in n.lower()]) > 0,
            branch_naming_convention=most_common_prefix + "/" if most_common_prefix else "",
            average_branch_lifetime=0,  # Would need more complex analysis
            merge_vs_rebase="merge",    # Default assumption
            deletes_merged_branches=True
        )
    
    def _analyze_language_patterns(self, files: Dict[str, Any], commits: List[Dict[str, Any]]) -> LanguagePattern:
        """Analyze language usage patterns."""
        # Language distribution
        extension_counts = files.get('files_by_extension', {})
        language_counts = defaultdict(int)
        
        for ext, count in extension_counts.items():
            if ext in self.language_extensions:
                language = self.language_extensions[ext]
                language_counts[language] += count
        
        total_files = sum(language_counts.values())
        language_percentages = {
            lang: count / total_files for lang, count in language_counts.items()
        } if total_files > 0 else {}
        
        # Project structure analysis
        directories = files.get('files_by_directory', {})
        has_src_dir = any('src' in dir_name.lower() for dir_name in directories)
        has_lib_dir = any('lib' in dir_name.lower() for dir_name in directories)
        has_tests_separate = any('test' in dir_name.lower() for dir_name in directories)
        
        if has_src_dir:
            structure_style = "standard"
        elif has_lib_dir:
            structure_style = "library"
        elif len(directories) <= 3:
            structure_style = "flat"
        else:
            structure_style = "nested"
        
        test_organization = "separate" if has_tests_separate else "none"
        
        return LanguagePattern(
            languages=language_percentages,
            project_structure_style=structure_style,
            test_organization=test_organization,
            config_preferences={},
            framework_usage={},
            tool_preferences={}
        )
    
    def _analyze_file_patterns(self, files: Dict[str, Any], commits: List[Dict[str, Any]]) -> FilePattern:
        """Analyze file organization and modification patterns."""
        # Most modified file types
        extension_changes = defaultdict(int)
        for commit in commits:
            for file_change in commit.get('files_changed', []):
                path_obj = Path(file_change['filename'])
                if path_obj.suffix:
                    extension_changes[path_obj.suffix.lower()] += 1
        
        frequently_modified = [ext for ext, count in 
                             Counter(extension_changes).most_common(5)]
        
        # Directory depth preference
        depth_dist = files.get('directory_depth_distribution', {})
        avg_depth = sum(depth * count for depth, count in depth_dist.items()) / max(sum(depth_dist.values()), 1)
        
        return FilePattern(
            frequently_modified_types=frequently_modified,
            large_file_threshold=1000,
            prefers_single_purpose_files=True,  # Would need more analysis
            directory_depth_preference=int(avg_depth),
            naming_conventions={},
            file_size_preferences={}
        )
    
    def _get_peak_hours(self, hours: List[int]) -> List[int]:
        """Get the most common hours for commits."""
        if not hours:
            return []
        
        hour_counts = Counter(hours)
        # Return hours that are above average frequency
        avg_count = sum(hour_counts.values()) / 24
        return [hour for hour, count in hour_counts.items() if count > avg_count]
    
    def _calculate_commit_frequency(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate commits per day."""
        if not commits:
            return 0.0
        
        timestamps = [c['timestamp'] for c in commits if c['timestamp']]
        if not timestamps:
            return 0.0
        
        time_span_days = (max(timestamps) - min(timestamps)) / (24 * 3600)
        return len(commits) / max(time_span_days, 1)
    
    def _calculate_confidence_scores(
        self, 
        commits: List[Dict[str, Any]], 
        branches: List[Dict[str, Any]], 
        files: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate confidence scores for different pattern types."""
        
        # Base confidence on data quantity and quality
        commit_confidence = min(len(commits) / 50, 1.0)  # 50 commits = 100% confidence
        branch_confidence = min(len(branches) / 5, 1.0)  # 5 branches = 100% confidence  
        file_confidence = min(files.get('total_files', 0) / 100, 1.0)  # 100 files = 100% confidence
        
        # Time span confidence (more data over time = higher confidence)
        if commits:
            timestamps = [c['timestamp'] for c in commits if c['timestamp']]
            if timestamps:
                time_span_days = (max(timestamps) - min(timestamps)) / (24 * 3600)
                time_confidence = min(time_span_days / 30, 1.0)  # 30 days = 100% confidence
            else:
                time_confidence = 0.0
        else:
            time_confidence = 0.0
        
        return {
            'commit_patterns': commit_confidence,
            'branch_patterns': branch_confidence,
            'language_patterns': file_confidence,
            'file_patterns': file_confidence,
            'overall': statistics.mean([commit_confidence, branch_confidence, 
                                      file_confidence, time_confidence])
        }