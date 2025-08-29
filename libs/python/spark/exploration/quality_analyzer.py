"""
Static analysis and quality assessment for exploration code.

This module provides comprehensive code quality analysis using various
static analysis tools and metrics to assess generated code quality.
"""

import ast
import re
import subprocess
import tempfile
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

# Optional imports for enhanced analysis
try:
    import bandit
    BANDIT_AVAILABLE = True
except ImportError:
    BANDIT_AVAILABLE = False

try:
    import mypy.api
    MYPY_AVAILABLE = True
except ImportError:
    MYPY_AVAILABLE = False


class QualityMetric(Enum):
    """Quality metrics that can be assessed."""
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability" 
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


@dataclass
class QualityIssue:
    """Represents a code quality issue."""
    severity: str  # "error", "warning", "info"
    category: QualityMetric
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class QualityReport:
    """Comprehensive code quality report."""
    overall_score: float  # 0.0 - 10.0 scale
    metric_scores: Dict[QualityMetric, float] = field(default_factory=dict)
    issues: List[QualityIssue] = field(default_factory=list)
    
    # Detailed metrics
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    comment_ratio: float = 0.0
    function_count: int = 0
    class_count: int = 0
    
    # Security analysis
    security_issues: List[str] = field(default_factory=list)
    
    # Style analysis
    style_violations: List[str] = field(default_factory=list)
    
    # Performance insights
    performance_warnings: List[str] = field(default_factory=list)
    
    # Documentation analysis
    documentation_coverage: float = 0.0
    missing_docstrings: List[str] = field(default_factory=list)


class QualityAnalyzer:
    """Comprehensive code quality analyzer using multiple static analysis tools."""
    
    def __init__(self, enable_external_tools: bool = True):
        """
        Initialize QualityAnalyzer.
        
        Args:
            enable_external_tools: Whether to use external tools like ruff, mypy, bandit
        """
        self.enable_external_tools = enable_external_tools
        
        # Check availability of external tools
        self.tools_available = self._check_tool_availability()
    
    def _check_tool_availability(self) -> Dict[str, bool]:
        """Check which external analysis tools are available."""
        tools = {}
        
        # Check for ruff (fast Python linter)
        try:
            subprocess.run(['ruff', '--version'], capture_output=True, check=True)
            tools['ruff'] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools['ruff'] = False
        
        # Check for mypy
        tools['mypy'] = MYPY_AVAILABLE
        
        # Check for bandit
        tools['bandit'] = BANDIT_AVAILABLE
        
        return tools
    
    async def analyze_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Perform comprehensive quality analysis on code.
        
        Args:
            code: Source code to analyze
            language: Programming language
            context: Additional context for analysis
            
        Returns:
            Comprehensive quality report
        """
        
        if language.lower() != 'python':
            # For non-Python languages, provide basic analysis
            return await self._analyze_generic_code(code, language)
        
        # Python-specific comprehensive analysis
        return await self._analyze_python_code(code, context or {})
    
    async def _analyze_python_code(self, code: str, context: Dict[str, Any]) -> QualityReport:
        """Comprehensive Python code analysis."""
        
        issues = []
        metric_scores = {}
        
        # Parse AST for structural analysis
        try:
            tree = ast.parse(code)
            ast_analysis = self._analyze_ast(tree, code)
        except SyntaxError as e:
            return QualityReport(
                overall_score=0.0,
                issues=[QualityIssue(
                    severity="error",
                    category=QualityMetric.STYLE,
                    message=f"Syntax error: {e.msg}",
                    line_number=e.lineno
                )]
            )
        
        # Run individual quality assessments in parallel
        analysis_tasks = [
            self._analyze_complexity(tree, code),
            self._analyze_maintainability(tree, code),
            self._analyze_style(code),
            self._analyze_documentation(tree, code),
            self._analyze_performance(tree, code),
        ]
        
        if self.enable_external_tools:
            if self.tools_available.get('ruff'):
                analysis_tasks.append(self._run_ruff_analysis(code))
            if self.tools_available.get('mypy'):
                analysis_tasks.append(self._run_mypy_analysis(code))
            if self.tools_available.get('bandit'):
                analysis_tasks.append(self._run_bandit_analysis(code))
        
        # Run security analysis
        analysis_tasks.append(self._analyze_security(tree, code))
        
        # Execute all analyses
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Collect results from successful analyses
        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, tuple):
                score, result_issues = result
                if isinstance(score, dict):
                    metric_scores.update(score)
                else:
                    # Handle single score results
                    pass
                issues.extend(result_issues)
            elif isinstance(result, list):
                issues.extend(result)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metric_scores, ast_analysis)
        
        # Build comprehensive report
        return QualityReport(
            overall_score=overall_score,
            metric_scores={QualityMetric(k): v for k, v in metric_scores.items() if k in [m.value for m in QualityMetric]},
            issues=issues,
            cyclomatic_complexity=ast_analysis.get('complexity', 0),
            lines_of_code=ast_analysis.get('lines_of_code', 0),
            comment_ratio=ast_analysis.get('comment_ratio', 0.0),
            function_count=ast_analysis.get('function_count', 0),
            class_count=ast_analysis.get('class_count', 0),
            documentation_coverage=ast_analysis.get('doc_coverage', 0.0),
            missing_docstrings=ast_analysis.get('missing_docstrings', [])
        )
    
    def _analyze_ast(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Extract structural information from AST."""
        
        lines = code.split('\n')
        total_lines = len(lines)
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        functions = []
        classes = []
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                complexity += self._calculate_function_complexity(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        # Documentation analysis
        documented_functions = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node):
                    documented_functions += 1
        
        doc_coverage = documented_functions / len(functions) if functions else 1.0
        missing_docstrings = [f for i, f in enumerate(functions) if i >= documented_functions]
        
        return {
            'lines_of_code': total_lines,
            'comment_ratio': comment_lines / max(total_lines, 1),
            'function_count': len(functions),
            'class_count': len(classes),
            'complexity': complexity,
            'doc_coverage': doc_coverage,
            'missing_docstrings': missing_docstrings
        }
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points that increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    async def _analyze_complexity(self, tree: ast.AST, code: str) -> Tuple[Dict[str, float], List[QualityIssue]]:
        """Analyze code complexity."""
        
        issues = []
        total_complexity = 0
        function_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_complexity = self._calculate_function_complexity(node)
                total_complexity += func_complexity
                function_count += 1
                
                # Flag high complexity functions
                if func_complexity > 10:
                    issues.append(QualityIssue(
                        severity="warning",
                        category=QualityMetric.COMPLEXITY,
                        message=f"Function '{node.name}' has high complexity ({func_complexity})",
                        line_number=node.lineno,
                        suggestion="Consider breaking this function into smaller functions"
                    ))
        
        avg_complexity = total_complexity / max(function_count, 1)
        
        # Score based on average complexity (lower is better)
        complexity_score = max(0, 10 - avg_complexity)
        
        return ({"complexity": complexity_score}, issues)
    
    async def _analyze_maintainability(self, tree: ast.AST, code: str) -> Tuple[Dict[str, float], List[QualityIssue]]:
        """Analyze code maintainability factors."""
        
        issues = []
        lines = code.split('\n')
        
        # Function length analysis
        long_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function length
                func_lines = getattr(node, 'end_lineno', node.lineno) - node.lineno + 1
                if func_lines > 50:
                    long_functions.append(node.name)
                    issues.append(QualityIssue(
                        severity="info",
                        category=QualityMetric.MAINTAINABILITY,
                        message=f"Function '{node.name}' is long ({func_lines} lines)",
                        line_number=node.lineno,
                        suggestion="Consider breaking into smaller functions"
                    ))
        
        # Nesting depth analysis
        max_nesting = self._calculate_max_nesting_depth(tree)
        if max_nesting > 4:
            issues.append(QualityIssue(
                severity="warning",
                category=QualityMetric.MAINTAINABILITY,
                message=f"Deep nesting detected (depth: {max_nesting})",
                suggestion="Reduce nesting depth for better readability"
            ))
        
        # Score maintainability
        maintainability_score = 10.0
        maintainability_score -= len(long_functions) * 0.5  # Penalty for long functions
        maintainability_score -= max(0, max_nesting - 3) * 1.0  # Penalty for deep nesting
        maintainability_score = max(0, maintainability_score)
        
        return ({"maintainability": maintainability_score}, issues)
    
    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth in code."""
        
        def get_depth(node, current_depth=0):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)):
                current_depth += 1
            
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                child_depth = get_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(tree)
    
    async def _analyze_style(self, code: str) -> Tuple[Dict[str, float], List[QualityIssue]]:
        """Analyze code style and formatting."""
        
        issues = []
        lines = code.split('\n')
        
        # Line length analysis
        long_lines = [(i+1, line) for i, line in enumerate(lines) if len(line) > 100]
        for line_num, line in long_lines:
            issues.append(QualityIssue(
                severity="info",
                category=QualityMetric.STYLE,
                message=f"Line too long ({len(line)} chars)",
                line_number=line_num,
                suggestion="Consider breaking long lines"
            ))
        
        # Naming convention checks
        naming_issues = self._check_naming_conventions(code)
        issues.extend(naming_issues)
        
        # Import organization
        import_issues = self._check_import_style(code)
        issues.extend(import_issues)
        
        # Calculate style score
        style_score = 10.0
        style_score -= min(len(long_lines) * 0.1, 2.0)  # Penalty for long lines
        style_score -= min(len(naming_issues) * 0.2, 2.0)  # Penalty for naming issues
        style_score -= min(len(import_issues) * 0.1, 1.0)  # Penalty for import issues
        style_score = max(0, style_score)
        
        return ({"style": style_score}, issues)
    
    def _check_naming_conventions(self, code: str) -> List[QualityIssue]:
        """Check Python naming conventions."""
        
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Functions should be snake_case
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                        issues.append(QualityIssue(
                            severity="info",
                            category=QualityMetric.STYLE,
                            message=f"Function '{node.name}' should use snake_case",
                            line_number=node.lineno,
                            rule_id="naming-convention"
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    # Classes should be PascalCase
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        issues.append(QualityIssue(
                            severity="info",
                            category=QualityMetric.STYLE,
                            message=f"Class '{node.name}' should use PascalCase",
                            line_number=node.lineno,
                            rule_id="naming-convention"
                        ))
        
        except SyntaxError:
            pass  # Skip naming checks if code doesn't parse
        
        return issues
    
    def _check_import_style(self, code: str) -> List[QualityIssue]:
        """Check import statement style."""
        
        issues = []
        lines = code.split('\n')
        
        import_lines = [(i+1, line) for i, line in enumerate(lines) if line.strip().startswith(('import ', 'from '))]
        
        # Check for wildcard imports
        for line_num, line in import_lines:
            if 'import *' in line:
                issues.append(QualityIssue(
                    severity="warning",
                    category=QualityMetric.STYLE,
                    message="Avoid wildcard imports",
                    line_number=line_num,
                    rule_id="wildcard-import"
                ))
        
        return issues
    
    async def _analyze_documentation(self, tree: ast.AST, code: str) -> Tuple[Dict[str, float], List[QualityIssue]]:
        """Analyze documentation quality."""
        
        issues = []
        
        # Check for module docstring
        module_docstring = ast.get_docstring(tree)
        if not module_docstring:
            issues.append(QualityIssue(
                severity="info",
                category=QualityMetric.DOCUMENTATION,
                message="Module missing docstring",
                line_number=1,
                suggestion="Add a module-level docstring"
            ))
        
        # Check function and class docstrings
        functions_without_docs = []
        classes_without_docs = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                if not ast.get_docstring(node):
                    functions_without_docs.append(node.name)
                    issues.append(QualityIssue(
                        severity="info",
                        category=QualityMetric.DOCUMENTATION,
                        message=f"Function '{node.name}' missing docstring",
                        line_number=node.lineno,
                        suggestion="Add a docstring describing the function"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    classes_without_docs.append(node.name)
                    issues.append(QualityIssue(
                        severity="info",
                        category=QualityMetric.DOCUMENTATION,
                        message=f"Class '{node.name}' missing docstring",
                        line_number=node.lineno,
                        suggestion="Add a class docstring"
                    ))
        
        # Calculate documentation score
        total_public_items = len([node for node in ast.walk(tree) 
                                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) 
                                and not node.name.startswith('_')])
        
        documented_items = total_public_items - len(functions_without_docs) - len(classes_without_docs)
        doc_score = (documented_items / max(total_public_items, 1)) * 10
        
        return ({"documentation": doc_score}, issues)
    
    async def _analyze_performance(self, tree: ast.AST, code: str) -> Tuple[Dict[str, float], List[QualityIssue]]:
        """Analyze potential performance issues."""
        
        issues = []
        performance_score = 8.0  # Start with good score
        
        # Check for potential performance anti-patterns
        for node in ast.walk(tree):
            # String concatenation in loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if (isinstance(child, ast.AugAssign) and 
                        isinstance(child.op, ast.Add) and 
                        isinstance(child.target, ast.Name)):
                        issues.append(QualityIssue(
                            severity="info",
                            category=QualityMetric.PERFORMANCE,
                            message="String concatenation in loop detected",
                            line_number=getattr(child, 'lineno', None),
                            suggestion="Consider using join() or f-strings"
                        ))
                        performance_score -= 0.5
            
            # Nested loops (potential O(n²) issues)
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = [child for child in ast.walk(node) 
                              if isinstance(child, (ast.For, ast.While)) and child != node]
                if nested_loops:
                    issues.append(QualityIssue(
                        severity="info",
                        category=QualityMetric.PERFORMANCE,
                        message="Nested loops detected",
                        line_number=node.lineno,
                        suggestion="Consider optimizing algorithm complexity"
                    ))
                    performance_score -= 0.3
        
        return ({"performance": max(0, performance_score)}, issues)
    
    async def _analyze_security(self, tree: ast.AST, code: str) -> List[QualityIssue]:
        """Analyze security issues in code."""
        
        issues = []
        
        # Check for dangerous function calls
        dangerous_calls = ['eval', 'exec', '__import__']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in dangerous_calls:
                    issues.append(QualityIssue(
                        severity="error",
                        category=QualityMetric.SECURITY,
                        message=f"Dangerous function call: {node.func.id}",
                        line_number=node.lineno,
                        suggestion=f"Avoid using {node.func.id} for security reasons"
                    ))
        
        # Check for hardcoded credentials (basic check)
        lines = code.split('\n')
        credential_patterns = [
            r'password\s*=\s*["\']',
            r'api_key\s*=\s*["\']',
            r'secret\s*=\s*["\']',
            r'token\s*=\s*["\']'
        ]
        
        for i, line in enumerate(lines):
            for pattern in credential_patterns:
                if re.search(pattern, line.lower()):
                    issues.append(QualityIssue(
                        severity="warning",
                        category=QualityMetric.SECURITY,
                        message="Potential hardcoded credential detected",
                        line_number=i+1,
                        suggestion="Use environment variables for sensitive data"
                    ))
        
        return issues
    
    async def _run_ruff_analysis(self, code: str) -> List[QualityIssue]:
        """Run ruff linter analysis."""
        
        if not self.tools_available.get('ruff'):
            return []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['ruff', 'check', '--output-format', 'json', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    ruff_issues = json.loads(result.stdout)
                    return [
                        QualityIssue(
                            severity="warning" if issue.get('level') == 'warning' else "error",
                            category=QualityMetric.STYLE,  # Ruff primarily does style
                            message=issue.get('message', ''),
                            line_number=issue.get('location', {}).get('row'),
                            column=issue.get('location', {}).get('column'),
                            rule_id=issue.get('code')
                        )
                        for issue in ruff_issues
                    ]
                
            finally:
                Path(temp_file).unlink(missing_ok=True)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        
        return []
    
    async def _run_mypy_analysis(self, code: str) -> List[QualityIssue]:
        """Run mypy type checking analysis."""
        
        if not self.tools_available.get('mypy'):
            return []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Run mypy programmatically
                stdout, stderr, exit_code = mypy.api.run([temp_file, '--show-error-codes'])
                
                issues = []
                for line in stdout.split('\n'):
                    if ':' in line and 'error:' in line:
                        # Parse mypy output
                        parts = line.split(':')
                        if len(parts) >= 4:
                            try:
                                line_num = int(parts[1])
                                message = ':'.join(parts[3:]).strip()
                                issues.append(QualityIssue(
                                    severity="error",
                                    category=QualityMetric.STYLE,  # Type issues affect maintainability
                                    message=f"Type error: {message}",
                                    line_number=line_num,
                                    rule_id="mypy"
                                ))
                            except ValueError:
                                pass
                
                return issues
                
            finally:
                Path(temp_file).unlink(missing_ok=True)
                
        except Exception:
            pass
        
        return []
    
    async def _run_bandit_analysis(self, code: str) -> List[QualityIssue]:
        """Run bandit security analysis."""
        
        if not self.tools_available.get('bandit'):
            return []
        
        try:
            # Use subprocess to run bandit
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['bandit', '-f', 'json', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    bandit_report = json.loads(result.stdout)
                    issues = []
                    
                    for result_item in bandit_report.get('results', []):
                        issues.append(QualityIssue(
                            severity=result_item.get('issue_severity', 'info').lower(),
                            category=QualityMetric.SECURITY,
                            message=result_item.get('issue_text', ''),
                            line_number=result_item.get('line_number'),
                            rule_id=result_item.get('test_id'),
                            suggestion=result_item.get('issue_description', '')
                        ))
                    
                    return issues
                
            finally:
                Path(temp_file).unlink(missing_ok=True)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        
        return []
    
    async def _analyze_generic_code(self, code: str, language: str) -> QualityReport:
        """Basic analysis for non-Python languages."""
        
        lines = code.split('\n')
        total_lines = len(lines)
        comment_lines = 0
        
        # Basic comment detection for common languages
        comment_patterns = {
            'javascript': [r'^\s*//', r'/\*.*\*/'],
            'typescript': [r'^\s*//', r'/\*.*\*/'], 
            'java': [r'^\s*//', r'/\*.*\*/'],
            'cpp': [r'^\s*//', r'/\*.*\*/', r'^\s*#'],
            'rust': [r'^\s*//', r'/\*.*\*/'],
            'go': [r'^\s*//']
        }
        
        patterns = comment_patterns.get(language.lower(), [r'^\s*#'])
        
        for line in lines:
            for pattern in patterns:
                if re.search(pattern, line):
                    comment_lines += 1
                    break
        
        # Basic quality score based on comment ratio and code length
        comment_ratio = comment_lines / max(total_lines, 1)
        
        quality_score = 5.0  # Base score
        if comment_ratio > 0.1:  # Good commenting
            quality_score += 2.0
        if 20 <= total_lines <= 200:  # Reasonable length
            quality_score += 2.0
        if total_lines > 500:  # Too long
            quality_score -= 1.0
        
        return QualityReport(
            overall_score=min(quality_score, 10.0),
            metric_scores={
                QualityMetric.DOCUMENTATION: comment_ratio * 10,
                QualityMetric.MAINTAINABILITY: min(quality_score, 10.0)
            },
            lines_of_code=total_lines,
            comment_ratio=comment_ratio
        )
    
    def _calculate_overall_score(self, metric_scores: Dict[str, float], ast_analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score from individual metric scores."""
        
        if not metric_scores:
            return 5.0  # Neutral score
        
        # Weights for different quality metrics
        weights = {
            'complexity': 0.25,
            'maintainability': 0.25,
            'style': 0.20,
            'documentation': 0.15,
            'performance': 0.10,
            'security': 0.05  # Security issues are handled as blockers
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric, score in metric_scores.items():
            weight = weights.get(metric, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            final_score = 5.0
        
        # Apply penalties for structural issues
        if ast_analysis.get('complexity', 0) > 20:
            final_score *= 0.9  # High complexity penalty
        
        if ast_analysis.get('doc_coverage', 1.0) < 0.5:
            final_score *= 0.95  # Poor documentation penalty
        
        return max(0.0, min(10.0, final_score))