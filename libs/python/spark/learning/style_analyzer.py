"""
AST-based code style analyzer for multi-language pattern detection.

This module analyzes code structure, style, and patterns across different programming
languages to understand developer preferences and coding habits.
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
import statistics

from spark.cli.errors import SparkLearningError


@dataclass
class FunctionAnalysis:
    """Analysis results for a single function."""
    
    name: str
    line_count: int
    complexity: int  # Cyclomatic complexity
    nesting_depth: int
    parameter_count: int
    return_type_hint: bool
    docstring: bool
    naming_style: str  # snake_case, camelCase, PascalCase
    is_async: bool = False
    is_method: bool = False
    is_private: bool = False
    uses_type_hints: bool = False


@dataclass
class ClassAnalysis:
    """Analysis results for a single class."""
    
    name: str
    method_count: int
    property_count: int
    inheritance_depth: int
    naming_style: str
    has_docstring: bool
    is_dataclass: bool = False
    uses_slots: bool = False
    methods: List[FunctionAnalysis] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    
    file_path: str
    language: str
    line_count: int
    comment_ratio: float
    import_count: int
    function_count: int
    class_count: int
    
    # Style patterns
    naming_conventions: Dict[str, int] = field(default_factory=dict)
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    function_lengths: List[int] = field(default_factory=list)
    nesting_depths: List[int] = field(default_factory=list)
    
    # Language-specific patterns
    language_features: Dict[str, int] = field(default_factory=dict)
    architectural_patterns: List[str] = field(default_factory=list)
    
    # Detailed analysis
    functions: List[FunctionAnalysis] = field(default_factory=list)
    classes: List[ClassAnalysis] = field(default_factory=list)
    
    # Metadata
    analysis_date: datetime = field(default_factory=datetime.now)
    analysis_duration: float = 0.0


@dataclass
class StyleProfile:
    """Aggregated style profile across multiple files."""
    
    # General preferences
    preferred_naming_style: str = "snake_case"
    preferred_function_length: int = 20
    preferred_complexity: int = 5
    preferred_nesting_depth: int = 3
    
    # Type system usage
    type_hint_usage: float = 0.0
    docstring_coverage: float = 0.0
    
    # Language-specific patterns
    async_usage: float = 0.0
    oop_vs_functional: float = 0.5  # 0=functional, 1=OOP
    error_handling_style: str = "exceptions"
    
    # Testing patterns
    test_organization: str = "separate"  # separate, alongside, none
    testing_framework: str = "pytest"
    test_naming_style: str = "descriptive"
    
    # Architectural preferences
    preferred_structure: str = "modular"  # flat, modular, layered, domain
    import_organization: str = "grouped"  # alphabetical, grouped, length
    
    # Confidence scores
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    sample_sizes: Dict[str, int] = field(default_factory=dict)


class PythonASTAnalyzer:
    """Python-specific AST analysis."""
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a Python file using AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = FileAnalysis(
                file_path=str(file_path),
                language="python",
                line_count=len(content.split('\n')),
                comment_ratio=self._calculate_comment_ratio(content),
                import_count=self._count_imports(tree),
                function_count=0,
                class_count=0
            )
            
            # Analyze AST nodes
            self._analyze_ast_nodes(tree, analysis, content)
            
            return analysis
            
        except Exception as e:
            raise SparkLearningError(f"Failed to analyze Python file {file_path}", str(e))
    
    def _calculate_comment_ratio(self, content: str) -> float:
        """Calculate ratio of comment lines to total lines."""
        lines = content.split('\n')
        comment_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or '"""' in stripped or "'''" in stripped:
                comment_lines += 1
        
        return comment_lines / max(len(lines), 1)
    
    def _count_imports(self, tree: ast.AST) -> int:
        """Count import statements."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                count += 1
        return count
    
    def _analyze_ast_nodes(self, tree: ast.AST, analysis: FileAnalysis, content: str) -> None:
        """Analyze all AST nodes for patterns."""
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_analysis = self._analyze_function(node, content)
                analysis.functions.append(func_analysis)
                analysis.function_count += 1
                
                # Update aggregates
                analysis.function_lengths.append(func_analysis.line_count)
                analysis.nesting_depths.append(func_analysis.nesting_depth)
                analysis.naming_conventions[func_analysis.naming_style] = \
                    analysis.naming_conventions.get(func_analysis.naming_style, 0) + 1
                
                # Track language features
                if func_analysis.is_async:
                    analysis.language_features['async'] = \
                        analysis.language_features.get('async', 0) + 1
                if func_analysis.uses_type_hints:
                    analysis.language_features['type_hints'] = \
                        analysis.language_features.get('type_hints', 0) + 1
                
            elif isinstance(node, ast.ClassDef):
                class_analysis = self._analyze_class(node, content)
                analysis.classes.append(class_analysis)
                analysis.class_count += 1
                
                analysis.naming_conventions[class_analysis.naming_style] = \
                    analysis.naming_conventions.get(class_analysis.naming_style, 0) + 1
    
    def _analyze_function(self, node: ast.FunctionDef, content: str) -> FunctionAnalysis:
        """Analyze a function definition."""
        
        # Calculate line count
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        line_count = end_line - start_line + 1
        
        # Determine naming style
        naming_style = self._detect_naming_style(node.name)
        
        # Check for type hints
        has_return_type = node.returns is not None
        has_param_types = any(arg.annotation is not None for arg in node.args.args)
        
        # Check for docstring
        has_docstring = (
            len(node.body) > 0 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)
        )
        
        # Calculate complexity (simplified)
        complexity = self._calculate_complexity(node)
        
        # Calculate nesting depth
        nesting_depth = self._calculate_nesting_depth(node)
        
        return FunctionAnalysis(
            name=node.name,
            line_count=line_count,
            complexity=complexity,
            nesting_depth=nesting_depth,
            parameter_count=len(node.args.args),
            return_type_hint=has_return_type,
            docstring=has_docstring,
            naming_style=naming_style,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=False,  # Would need parent context
            is_private=node.name.startswith('_'),
            uses_type_hints=has_return_type or has_param_types
        )
    
    def _analyze_class(self, node: ast.ClassDef, content: str) -> ClassAnalysis:
        """Analyze a class definition."""
        
        # Count methods and properties
        method_count = 0
        property_count = 0
        methods = []
        
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                method_count += 1
                func_analysis = self._analyze_function(child, content)
                func_analysis.is_method = True
                methods.append(func_analysis)
            elif isinstance(child, ast.AnnAssign) or isinstance(child, ast.Assign):
                property_count += 1
        
        # Check for docstring
        has_docstring = (
            len(node.body) > 0 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)
        )
        
        # Check if it's a dataclass (simplified)
        is_dataclass = any(
            isinstance(decorator, ast.Name) and decorator.id == 'dataclass'
            for decorator in node.decorator_list
        )
        
        return ClassAnalysis(
            name=node.name,
            method_count=method_count,
            property_count=property_count,
            inheritance_depth=len(node.bases),
            naming_style=self._detect_naming_style(node.name),
            has_docstring=has_docstring,
            is_dataclass=is_dataclass,
            uses_slots=False,  # Would need deeper analysis
            methods=methods
        )
    
    def _detect_naming_style(self, name: str) -> str:
        """Detect naming convention used."""
        if re.match(r'^[a-z]+(_[a-z]+)*$', name):
            return "snake_case"
        elif re.match(r'^[a-z]+([A-Z][a-z]*)*$', name):
            return "camelCase"
        elif re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', name):
            return "PascalCase"
        elif re.match(r'^[A-Z][A-Z_]*[A-Z]$', name):
            return "SCREAMING_SNAKE_CASE"
        else:
            return "mixed"
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # And/Or operators add complexity
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        
        def calculate_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    calculate_depth(child, current_depth + 1)
                else:
                    calculate_depth(child, current_depth)
        
        calculate_depth(node)
        return max_depth


class JavaScriptAnalyzer:
    """JavaScript/TypeScript analysis using pattern matching."""
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze JavaScript/TypeScript file using regex patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            is_typescript = file_path.suffix.lower() in ['.ts', '.tsx']
            
            analysis = FileAnalysis(
                file_path=str(file_path),
                language="typescript" if is_typescript else "javascript",
                line_count=len(content.split('\n')),
                comment_ratio=self._calculate_comment_ratio(content),
                import_count=self._count_imports(content),
                function_count=0,
                class_count=0
            )
            
            # Analyze patterns using regex
            self._analyze_functions(content, analysis)
            self._analyze_classes(content, analysis)
            self._analyze_language_features(content, analysis)
            
            return analysis
            
        except Exception as e:
            raise SparkLearningError(f"Failed to analyze JS/TS file {file_path}", str(e))
    
    def _calculate_comment_ratio(self, content: str) -> float:
        """Calculate comment ratio for JS/TS."""
        lines = content.split('\n')
        comment_lines = 0
        
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if '/*' in stripped:
                in_block_comment = True
            if '*/' in stripped:
                in_block_comment = False
                comment_lines += 1
                continue
            
            if in_block_comment or stripped.startswith('//'):
                comment_lines += 1
        
        return comment_lines / max(len(lines), 1)
    
    def _count_imports(self, content: str) -> int:
        """Count import/require statements."""
        import_patterns = [
            r'^\s*import\s+',
            r'^\s*const\s+.*=\s*require\(',
            r'^\s*from\s+["\']',
        ]
        
        count = 0
        for line in content.split('\n'):
            for pattern in import_patterns:
                if re.match(pattern, line):
                    count += 1
                    break
        
        return count
    
    def _analyze_functions(self, content: str, analysis: FileAnalysis) -> None:
        """Analyze function patterns."""
        
        # Function patterns
        function_patterns = [
            r'function\s+(\w+)\s*\(',  # function declaration
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{',  # arrow function
            r'(\w+)\s*:\s*function\s*\(',  # object method
            r'(\w+)\s*\([^)]*\)\s*{',  # method shorthand
        ]
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                func_name = match.group(1)
                
                # Simple function analysis
                func_analysis = FunctionAnalysis(
                    name=func_name,
                    line_count=10,  # Simplified
                    complexity=3,   # Simplified
                    nesting_depth=2,
                    parameter_count=2,
                    return_type_hint=':' in match.group(0),
                    docstring=False,
                    naming_style=self._detect_naming_style(func_name),
                    is_async='async' in match.group(0)
                )
                
                analysis.functions.append(func_analysis)
                analysis.function_count += 1
                
                # Update naming conventions
                analysis.naming_conventions[func_analysis.naming_style] = \
                    analysis.naming_conventions.get(func_analysis.naming_style, 0) + 1
    
    def _analyze_classes(self, content: str, analysis: FileAnalysis) -> None:
        """Analyze class patterns."""
        
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*{'
        matches = re.finditer(class_pattern, content, re.MULTILINE)
        
        for match in matches:
            class_name = match.group(1)
            
            class_analysis = ClassAnalysis(
                name=class_name,
                method_count=3,  # Simplified
                property_count=2,
                inheritance_depth=1 if 'extends' in match.group(0) else 0,
                naming_style=self._detect_naming_style(class_name),
                has_docstring=False
            )
            
            analysis.classes.append(class_analysis)
            analysis.class_count += 1
    
    def _analyze_language_features(self, content: str, analysis: FileAnalysis) -> None:
        """Analyze language-specific features."""
        
        # TypeScript features
        if 'interface' in content:
            analysis.language_features['interfaces'] = \
                len(re.findall(r'interface\s+\w+', content))
        
        if 'type ' in content:
            analysis.language_features['type_aliases'] = \
                len(re.findall(r'type\s+\w+\s*=', content))
        
        # Modern JS features
        if '=>' in content:
            analysis.language_features['arrow_functions'] = \
                len(re.findall(r'=>', content))
        
        if 'async' in content:
            analysis.language_features['async_await'] = \
                len(re.findall(r'async\s+function|async\s*\(', content))
    
    def _detect_naming_style(self, name: str) -> str:
        """Detect naming convention."""
        if re.match(r'^[a-z]+([A-Z][a-z]*)*$', name):
            return "camelCase"
        elif re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', name):
            return "PascalCase"
        elif re.match(r'^[a-z]+(_[a-z]+)*$', name):
            return "snake_case"
        else:
            return "mixed"


class MultiLanguageStyleAnalyzer:
    """Main style analyzer that coordinates multiple language analyzers."""
    
    def __init__(self):
        self.analyzers = {
            '.py': PythonASTAnalyzer(),
            '.js': JavaScriptAnalyzer(),
            '.ts': JavaScriptAnalyzer(),
            '.jsx': JavaScriptAnalyzer(),
            '.tsx': JavaScriptAnalyzer(),
        }
        
        # Language extensions mapping
        self.language_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript', 
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp'
        }
    
    async def analyze_repository(self, repo_path: Path, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze all supported files in a repository."""
        
        if not file_patterns:
            file_patterns = list(self.analyzers.keys())
        
        analysis_results = {
            'repository_path': str(repo_path),
            'analysis_date': datetime.now().isoformat(),
            'files_analyzed': 0,
            'languages': defaultdict(int),
            'file_analyses': [],
            'aggregated_style': None
        }
        
        # Find and analyze files
        for pattern in file_patterns:
            files = list(repo_path.rglob(f"*{pattern}"))
            
            for file_path in files:
                if self._should_analyze_file(file_path):
                    try:
                        analyzer = self.analyzers.get(pattern)
                        if analyzer:
                            file_analysis = analyzer.analyze_file(file_path)
                            analysis_results['file_analyses'].append(file_analysis)
                            analysis_results['files_analyzed'] += 1
                            analysis_results['languages'][file_analysis.language] += 1
                        
                    except Exception as e:
                        # Log error but continue with other files
                        continue
        
        # Generate aggregated style profile
        if analysis_results['file_analyses']:
            analysis_results['aggregated_style'] = self._aggregate_style_profile(
                analysis_results['file_analyses']
            )
        
        return analysis_results
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        
        # Skip common directories
        skip_dirs = {
            'node_modules', '__pycache__', '.git', 'venv', '.venv',
            'dist', 'build', '.pytest_cache', 'target', '.mypy_cache'
        }
        
        if any(part in skip_dirs for part in file_path.parts):
            return False
        
        # Skip test files for now (they have different patterns)
        if 'test' in file_path.stem.lower():
            return False
        
        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 100000:  # 100KB limit
                return False
        except OSError:
            return False
        
        return True
    
    def _aggregate_style_profile(self, file_analyses: List[FileAnalysis]) -> StyleProfile:
        """Aggregate individual file analyses into a style profile."""
        
        profile = StyleProfile()
        
        if not file_analyses:
            return profile
        
        # Aggregate naming conventions
        all_naming_styles = defaultdict(int)
        all_function_lengths = []
        all_complexities = []
        all_nesting_depths = []
        
        type_hint_count = 0
        total_functions = 0
        docstring_count = 0
        async_count = 0
        
        for file_analysis in file_analyses:
            # Combine naming conventions
            for style, count in file_analysis.naming_conventions.items():
                all_naming_styles[style] += count
            
            # Aggregate function metrics
            for func in file_analysis.functions:
                all_function_lengths.append(func.line_count)
                all_complexities.append(func.complexity)
                all_nesting_depths.append(func.nesting_depth)
                total_functions += 1
                
                if func.uses_type_hints:
                    type_hint_count += 1
                if func.docstring:
                    docstring_count += 1
                if func.is_async:
                    async_count += 1
        
        # Determine preferred styles
        if all_naming_styles:
            profile.preferred_naming_style = max(all_naming_styles, key=all_naming_styles.get)
        
        if all_function_lengths:
            profile.preferred_function_length = int(statistics.median(all_function_lengths))
        
        if all_complexities:
            profile.preferred_complexity = int(statistics.median(all_complexities))
        
        if all_nesting_depths:
            profile.preferred_nesting_depth = int(statistics.median(all_nesting_depths))
        
        # Calculate usage ratios
        if total_functions > 0:
            profile.type_hint_usage = type_hint_count / total_functions
            profile.docstring_coverage = docstring_count / total_functions
            profile.async_usage = async_count / total_functions
        
        # Calculate confidence scores based on sample sizes
        profile.confidence_scores = {
            'naming_style': min(sum(all_naming_styles.values()) / 20, 1.0),
            'function_patterns': min(total_functions / 50, 1.0),
            'type_usage': min(total_functions / 30, 1.0) if total_functions > 0 else 0.0,
        }
        
        profile.sample_sizes = {
            'functions_analyzed': total_functions,
            'files_analyzed': len(file_analyses),
            'naming_samples': sum(all_naming_styles.values())
        }
        
        return profile
    
    def analyze_file(self, file_path: Path) -> Optional[FileAnalysis]:
        """Analyze a single file."""
        extension = file_path.suffix.lower()
        analyzer = self.analyzers.get(extension)
        
        if analyzer and self._should_analyze_file(file_path):
            try:
                return analyzer.analyze_file(file_path)
            except Exception:
                return None
        
        return None