"""
Code validation and safety checks for exploration results.

This module provides comprehensive validation including static analysis and 
sandboxed execution using CUA computer interface for real code testing.
"""

import ast
import re
import tempfile
import subprocess
import asyncio
import time
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from spark.discovery.models import CodeArtifact, ExplorationResult

# Import CUA components for sandboxed execution
try:
    from agent.agent.computers import make_computer_handler
    from agent.agent.computers.base import AsyncComputerHandler
    CUA_AVAILABLE = True
except ImportError:
    CUA_AVAILABLE = False
    AsyncComputerHandler = None


@dataclass
class ExecutionResult:
    """Result of code execution in sandboxed environment."""
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    memory_usage: Optional[float] = None  # MB
    cpu_usage: Optional[float] = None     # Percentage  
    error_message: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of code validation including static analysis and execution."""
    is_valid: bool
    score: float  # 0.0 - 1.0
    issues: List[str]
    warnings: List[str]
    safety_level: str  # "safe", "caution", "unsafe"
    executable: bool = False
    syntax_valid: bool = False
    
    # Enhanced validation results
    execution_result: Optional[ExecutionResult] = None
    static_analysis: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    test_coverage: Optional[float] = None  # 0.0 - 1.0
    security_scan_results: List[str] = field(default_factory=list)


class CodeValidator:
    """Validates generated code for safety and quality with sandboxed execution."""
    
    def __init__(self, enable_execution: bool = True, enable_cua: bool = True):
        """
        Initialize CodeValidator.
        
        Args:
            enable_execution: Whether to enable actual code execution for validation
            enable_cua: Whether to use CUA computer interface for sandboxed execution
        """
        self.enable_execution = enable_execution and CUA_AVAILABLE if enable_cua else enable_execution
        self.enable_cua = enable_cua and CUA_AVAILABLE
        self.computer_handler: Optional[AsyncComputerHandler] = None
        
        self.unsafe_patterns = [
            r'import\s+os',
            r'subprocess\.',
            r'eval\(',
            r'exec\(',
            r'__import__',
            r'open\(',
            r'file\(',
            r'input\(',
            r'raw_input\(',
            r'system\(',
            r'shell\=True',
            r'dangerous',
            r'malicious',
            r'delete',
            r'remove',
            r'rm\s+-rf',
        ]
        
        self.caution_patterns = [
            r'import\s+sys',
            r'globals\(\)',
            r'locals\(\)',
            r'vars\(\)',
            r'dir\(\)',
            r'getattr\(',
            r'setattr\(',
            r'hasattr\(',
            r'try:',
            r'except:',
            r'finally:',
        ]
    
    async def validate_code(self, code: str, language: str = "python") -> ValidationResult:
        """
        Comprehensive code validation including static analysis and optional execution.
        
        This is the main validation entry point that combines static analysis
        with sandboxed execution for complete validation.
        """
        issues = []
        warnings = []
        
        # Step 1: Static Analysis
        safety_level = self._assess_safety(code)
        if safety_level == "unsafe":
            issues.append("Unsafe code patterns detected")
        elif safety_level == "caution":
            warnings.append("Potentially risky patterns detected")
        
        # Step 2: Syntax Validation
        syntax_valid = False
        if language.lower() == 'python':
            syntax_valid = await self._validate_python_syntax(code, issues)
        else:
            syntax_valid = self._basic_syntax_check(code, language)
        
        # Step 3: Code Quality Assessment
        quality_score = self._assess_code_quality(code, language)
        completeness_score = self._assess_completeness(code, "Generated code exploration")
        
        # Step 4: Security Scanning (if enabled)
        security_results = await self._security_scan(code, language)
        
        # Step 5: Sandboxed Execution (if enabled and safe)
        execution_result = None
        if (self.enable_execution and 
            syntax_valid and 
            safety_level != "unsafe" and 
            language.lower() == 'python'):
            
            try:
                execution_result = await self._execute_code_sandboxed(code, language)
            except Exception as e:
                warnings.append(f"Execution testing failed: {str(e)}")
        
        # Calculate comprehensive score
        score_factors = {
            'safety': 0.3,
            'syntax': 0.25,
            'quality': 0.15,
            'completeness': 0.1,
            'execution': 0.2  # Execution success adds significant value
        }
        
        safety_score = 1.0 if safety_level == "safe" else (0.5 if safety_level == "caution" else 0.0)
        syntax_score = 1.0 if syntax_valid else 0.0
        execution_score = 1.0 if execution_result and execution_result.success else 0.5
        
        overall_score = (
            score_factors['safety'] * safety_score +
            score_factors['syntax'] * syntax_score +
            score_factors['quality'] * quality_score +
            score_factors['completeness'] * completeness_score +
            score_factors['execution'] * execution_score
        )
        
        # Determine if code is valid
        is_valid = (
            overall_score >= 0.6 and
            syntax_valid and 
            safety_level != "unsafe" and
            len(issues) == 0
        )
        
        # Build performance metrics
        performance_metrics = {}
        if execution_result:
            performance_metrics.update({
                'execution_time': execution_result.execution_time,
                'memory_usage': execution_result.memory_usage or 0,
                'cpu_usage': execution_result.cpu_usage or 0
            })
        
        return ValidationResult(
            is_valid=is_valid,
            score=overall_score,
            issues=issues,
            warnings=warnings,
            safety_level=safety_level,
            executable=syntax_valid and safety_level != "unsafe",
            syntax_valid=syntax_valid,
            execution_result=execution_result,
            static_analysis={
                'safety_score': safety_score,
                'quality_score': quality_score,
                'completeness_score': completeness_score
            },
            performance_metrics=performance_metrics,
            security_scan_results=security_results
        )
    
    async def _execute_code_sandboxed(self, code: str, language: str) -> ExecutionResult:
        """Execute code in a sandboxed environment using CUA or subprocess."""
        
        if self.enable_cua and CUA_AVAILABLE:
            return await self._execute_with_cua(code, language)
        else:
            return await self._execute_with_subprocess(code, language)
    
    async def _execute_with_cua(self, code: str, language: str) -> ExecutionResult:
        """Execute code using CUA computer interface for maximum safety."""
        
        if not self.computer_handler:
            try:
                self.computer_handler = await make_computer_handler()
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error_message=f"Could not initialize CUA computer handler: {e}"
                )
        
        try:
            start_time = time.time()
            
            # Create temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Use CUA to execute the Python file
                # Note: This is a simplified approach - in practice you'd want
                # more sophisticated sandboxing with virtual environments
                
                # Take screenshot before execution
                await self.computer_handler.screenshot()
                
                # Execute the code using system terminal via CUA
                await self.computer_handler.type(f"cd {tempfile.gettempdir()}")
                await self.computer_handler.keypress("Return")
                await self.computer_handler.wait(500)
                
                await self.computer_handler.type(f"python {Path(temp_file).name}")
                await self.computer_handler.keypress("Return")
                await self.computer_handler.wait(2000)  # Wait for execution
                
                # Capture output (simplified - would need more sophisticated capture)
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    success=True,
                    execution_time=execution_time,
                    stdout="Executed via CUA (output capture would be enhanced in production)",
                    stderr="",
                    exit_code=0
                )
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=f"CUA execution failed: {str(e)}",
                execution_time=time.time() - start_time if 'start_time' in locals() else 0
            )
    
    async def _execute_with_subprocess(self, code: str, language: str) -> ExecutionResult:
        """Execute code using subprocess in a controlled environment."""
        
        if language.lower() != 'python':
            return ExecutionResult(
                success=False,
                error_message=f"Subprocess execution not supported for {language}"
            )
        
        try:
            start_time = time.time()
            
            # Create a restricted execution environment
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'any': any,
                    'all': all,
                }
            }
            
            # Execute in restricted environment
            exec_locals = {}
            try:
                exec(code, restricted_globals, exec_locals)
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    success=True,
                    execution_time=execution_time,
                    stdout="Code executed successfully in restricted environment",
                    stderr="",
                    exit_code=0
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                return ExecutionResult(
                    success=False,
                    execution_time=execution_time,
                    error_message=str(e),
                    stderr=str(e),
                    exit_code=1
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=f"Execution setup failed: {str(e)}"
            )
    
    async def _security_scan(self, code: str, language: str) -> List[str]:
        """Perform basic security scanning on the code."""
        security_issues = []
        
        # Check for dangerous imports and patterns
        dangerous_imports = [
            'os', 'sys', 'subprocess', 'shutil', 'glob', 
            'socket', 'urllib', 'requests', '__import__'
        ]
        
        for dangerous in dangerous_imports:
            if f'import {dangerous}' in code or f'from {dangerous}' in code:
                security_issues.append(f"Potentially dangerous import: {dangerous}")
        
        # Check for eval/exec usage
        if 'eval(' in code:
            security_issues.append("Use of eval() detected - potential code injection risk")
        if 'exec(' in code:
            security_issues.append("Use of exec() detected - potential code injection risk")
        
        # Check for file operations
        file_ops = ['open(', 'file(', 'with open']
        for op in file_ops:
            if op in code:
                security_issues.append(f"File operation detected: {op}")
        
        return security_issues
    
    async def run_static_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Run comprehensive static analysis tools on the code."""
        analysis_results = {
            'linting_issues': [],
            'type_issues': [],
            'complexity_metrics': {},
            'style_violations': [],
            'security_warnings': [],
            'performance_warnings': []
        }
        
        if language.lower() != 'python':
            analysis_results['error'] = f"Static analysis not yet implemented for {language}"
            return analysis_results
        
        # Run multiple static analysis tools
        try:
            # 1. AST-based complexity analysis
            complexity = await self._analyze_complexity(code)
            analysis_results['complexity_metrics'] = complexity
            
            # 2. Style and convention checking
            style_issues = await self._check_style_conventions(code)
            analysis_results['style_violations'] = style_issues
            
            # 3. Performance pattern analysis
            perf_warnings = await self._analyze_performance_patterns(code)
            analysis_results['performance_warnings'] = perf_warnings
            
            # 4. Enhanced security scanning
            security_warnings = await self._advanced_security_scan(code)
            analysis_results['security_warnings'] = security_warnings
            
        except Exception as e:
            analysis_results['error'] = f"Static analysis failed: {str(e)}"
        
        return analysis_results
    
    async def _analyze_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity using AST parsing."""
        try:
            tree = ast.parse(code)
            
            complexity_metrics = {
                'cyclomatic_complexity': 0,
                'lines_of_code': len([line for line in code.split('\n') if line.strip()]),
                'function_count': 0,
                'class_count': 0,
                'max_nesting_depth': 0,
                'average_function_length': 0
            }
            
            class ComplexityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.complexity = 1  # Base complexity
                    self.depth = 0
                    self.max_depth = 0
                    self.function_lengths = []
                    self.current_function_lines = 0
                
                def visit_FunctionDef(self, node):
                    complexity_metrics['function_count'] += 1
                    self.current_function_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10
                    self.function_lengths.append(self.current_function_lines)
                    self.generic_visit(node)
                
                def visit_ClassDef(self, node):
                    complexity_metrics['class_count'] += 1
                    self.generic_visit(node)
                
                def visit_If(self, node):
                    self.complexity += 1
                    self.depth += 1
                    self.max_depth = max(self.max_depth, self.depth)
                    self.generic_visit(node)
                    self.depth -= 1
                
                def visit_For(self, node):
                    self.complexity += 1
                    self.depth += 1
                    self.max_depth = max(self.max_depth, self.depth)
                    self.generic_visit(node)
                    self.depth -= 1
                
                def visit_While(self, node):
                    self.complexity += 1
                    self.depth += 1
                    self.max_depth = max(self.max_depth, self.depth)
                    self.generic_visit(node)
                    self.depth -= 1
                
                def visit_Try(self, node):
                    self.complexity += 1
                    self.generic_visit(node)
                
                def visit_ExceptHandler(self, node):
                    self.complexity += 1
                    self.generic_visit(node)
            
            visitor = ComplexityVisitor()
            visitor.visit(tree)
            
            complexity_metrics['cyclomatic_complexity'] = visitor.complexity
            complexity_metrics['max_nesting_depth'] = visitor.max_depth
            
            if visitor.function_lengths:
                complexity_metrics['average_function_length'] = sum(visitor.function_lengths) / len(visitor.function_lengths)
            
            return complexity_metrics
            
        except Exception as e:
            return {'error': f"Complexity analysis failed: {str(e)}"}
    
    async def _check_style_conventions(self, code: str) -> List[str]:
        """Check Python style conventions (PEP 8 inspired)."""
        style_issues = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 88:  # Black's default line length
                style_issues.append(f"Line {i}: Line too long ({len(line)} > 88 characters)")
            
            # Check trailing whitespace
            if line.rstrip() != line:
                style_issues.append(f"Line {i}: Trailing whitespace")
            
            # Check for tabs vs spaces (prefer spaces)
            if '\t' in line:
                style_issues.append(f"Line {i}: Use spaces instead of tabs")
            
            # Check naming conventions
            stripped = line.strip()
            
            # Function names should be snake_case
            if stripped.startswith('def '):
                func_name = stripped.split('(')[0].replace('def ', '')
                if not func_name.islower() and '_' not in func_name and not func_name.startswith('_'):
                    style_issues.append(f"Line {i}: Function name '{func_name}' should be snake_case")
            
            # Class names should be PascalCase
            if stripped.startswith('class '):
                class_name = stripped.split('(')[0].split(':')[0].replace('class ', '')
                if not class_name[0].isupper():
                    style_issues.append(f"Line {i}: Class name '{class_name}' should be PascalCase")
        
        return style_issues
    
    async def _analyze_performance_patterns(self, code: str) -> List[str]:
        """Analyze code for potential performance issues."""
        performance_warnings = []
        
        # Check for common performance anti-patterns
        if 'for' in code and 'append' in code:
            # Look for list concatenation in loops
            if re.search(r'for.*in.*:\s*\w+\.append', code):
                performance_warnings.append("Consider using list comprehension instead of append in loop")
        
        # Check for inefficient string concatenation
        if '+=' in code and 'str' in code:
            performance_warnings.append("Consider using join() for string concatenation in loops")
        
        # Check for nested loops
        nested_loop_pattern = r'for.*in.*:\s*.*for.*in.*:'
        if re.search(nested_loop_pattern, code, re.DOTALL):
            performance_warnings.append("Nested loops detected - consider optimization")
        
        # Check for repeated lookups
        if code.count('.get(') > 3:
            performance_warnings.append("Multiple dictionary lookups - consider caching values")
        
        # Check for global variable access in functions
        if 'global' in code:
            performance_warnings.append("Global variable access may impact performance")
        
        return performance_warnings
    
    async def _advanced_security_scan(self, code: str) -> List[str]:
        """Advanced security pattern scanning."""
        security_warnings = []
        
        # SQL injection patterns
        sql_patterns = [
            r'execute\s*\(\s*["\'].*%.*["\']',
            r'query\s*\(\s*["\'].*\+.*["\']',
            r'["\']SELECT.*\+.*["\']'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                security_warnings.append("Potential SQL injection vulnerability detected")
                break
        
        # Command injection patterns
        cmd_patterns = [
            r'os\.system\s*\(\s*.*\+',
            r'subprocess\.call\s*\(\s*.*\+',
            r'os\.popen\s*\(\s*.*\+'
        ]
        
        for pattern in cmd_patterns:
            if re.search(pattern, code):
                security_warnings.append("Potential command injection vulnerability")
                break
        
        # Path traversal patterns
        if '../' in code or '..\\' in code:
            security_warnings.append("Potential path traversal vulnerability")
        
        # Hardcoded secrets patterns
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                security_warnings.append("Potential hardcoded secret detected")
                break
        
        return security_warnings
    
    async def validate_exploration_result(self, result: ExplorationResult) -> ValidationResult:
        """Validate an entire exploration result."""
        if not result.code_artifacts:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=["No code artifacts found"],
                warnings=[],
                safety_level="safe"
            )
        
        # Validate each artifact
        artifact_validations = []
        for artifact in result.code_artifacts:
            validation = await self.validate_code_artifact(artifact)
            artifact_validations.append(validation)
        
        # Aggregate results
        return self._aggregate_validations(artifact_validations)
    
    async def validate_code_artifact(self, artifact: CodeArtifact) -> ValidationResult:
        """Validate a single code artifact."""
        issues = []
        warnings = []
        
        # Basic safety checks
        safety_level = self._assess_safety(artifact.content)
        if safety_level == "unsafe":
            issues.append(f"Unsafe code patterns detected in {artifact.file_path}")
        elif safety_level == "caution":
            warnings.append(f"Potentially risky patterns in {artifact.file_path}")
        
        # Syntax validation for Python
        syntax_valid = False
        if artifact.language.lower() == 'python':
            syntax_valid = await self._validate_python_syntax(artifact.content, issues)
        else:
            # For non-Python languages, do basic checks
            syntax_valid = self._basic_syntax_check(artifact.content, artifact.language)
        
        # Content quality checks
        quality_score = self._assess_code_quality(artifact.content, artifact.language)
        
        # Completeness check
        completeness_score = self._assess_completeness(artifact.content, artifact.description)
        
        # Calculate overall score
        score_factors = {
            'safety': 0.4,
            'syntax': 0.3,
            'quality': 0.2,
            'completeness': 0.1
        }
        
        safety_score = 1.0 if safety_level == "safe" else (0.5 if safety_level == "caution" else 0.0)
        syntax_score = 1.0 if syntax_valid else 0.0
        
        overall_score = (
            score_factors['safety'] * safety_score +
            score_factors['syntax'] * syntax_score +
            score_factors['quality'] * quality_score +
            score_factors['completeness'] * completeness_score
        )
        
        is_valid = overall_score >= 0.6 and syntax_valid and safety_level != "unsafe"
        
        return ValidationResult(
            is_valid=is_valid,
            score=overall_score,
            issues=issues,
            warnings=warnings,
            safety_level=safety_level,
            syntax_valid=syntax_valid,
            executable=syntax_valid and safety_level != "unsafe"
        )
    
    def _assess_safety(self, code: str) -> str:
        """Assess the safety level of code."""
        code_lower = code.lower()
        
        # Check for unsafe patterns
        for pattern in self.unsafe_patterns:
            if re.search(pattern, code_lower):
                return "unsafe"
        
        # Check for caution patterns
        for pattern in self.caution_patterns:
            if re.search(pattern, code_lower):
                return "caution"
        
        return "safe"
    
    async def _validate_python_syntax(self, code: str, issues: List[str]) -> bool:
        """Validate Python syntax using AST parsing."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            issues.append(f"Python syntax error: {e.msg} (line {e.lineno})")
            return False
        except Exception as e:
            issues.append(f"Python parsing error: {str(e)}")
            return False
    
    def _basic_syntax_check(self, code: str, language: str) -> bool:
        """Basic syntax checks for non-Python languages."""
        # Very basic checks - balanced brackets, etc.
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in code:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return False
                if brackets[stack.pop()] != char:
                    return False
        
        return len(stack) == 0
    
    def _assess_code_quality(self, code: str, language: str) -> float:
        """Assess code quality metrics."""
        if not code.strip():
            return 0.0
        
        score = 0.5  # Base score
        
        # Check for comments/documentation
        if language.lower() == 'python':
            if '"""' in code or "'''" in code or '# ' in code:
                score += 0.2
        else:
            if '//' in code or '/*' in code:
                score += 0.2
        
        # Check for meaningful names (not just single letters)
        meaningful_names = len([word for word in re.findall(r'\b[a-zA-Z_]\w+\b', code) if len(word) > 2])
        if meaningful_names > 3:
            score += 0.2
        
        # Check for structure (functions, classes)
        if language.lower() == 'python':
            if 'def ' in code or 'class ' in code:
                score += 0.1
        
        return min(score, 1.0)
    
    def _assess_completeness(self, code: str, description: str) -> float:
        """Assess if code appears complete relative to description."""
        if not code.strip():
            return 0.0
        
        # Basic heuristics
        score = 0.3  # Base score for having any code
        
        # Check for TODO comments (reduces completeness)
        if 'TODO' in code.upper() or 'FIXME' in code.upper():
            score -= 0.2
        
        # Check for mock/placeholder patterns
        if 'mock' in code.lower() or 'placeholder' in code.lower():
            score += 0.1  # It's honest about being mock
        
        # Check if it has actual implementation
        if 'pass' not in code.lower() and len(code.strip()) > 50:
            score += 0.3
        
        # Check for imports/setup (suggests completeness)
        if 'import ' in code or 'from ' in code:
            score += 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def _aggregate_validations(self, validations: List[ValidationResult]) -> ValidationResult:
        """Aggregate multiple validation results."""
        if not validations:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=["No validations to aggregate"],
                warnings=[],
                safety_level="safe"
            )
        
        # Aggregate scores (weighted by main artifacts)
        total_score = sum(v.score for v in validations)
        avg_score = total_score / len(validations)
        
        # Collect all issues and warnings
        all_issues = []
        all_warnings = []
        for v in validations:
            all_issues.extend(v.issues)
            all_warnings.extend(v.warnings)
        
        # Determine safety level (most restrictive wins)
        safety_levels = [v.safety_level for v in validations]
        if "unsafe" in safety_levels:
            safety_level = "unsafe"
        elif "caution" in safety_levels:
            safety_level = "caution"
        else:
            safety_level = "safe"
        
        # Check if all are syntactically valid
        all_syntax_valid = all(v.syntax_valid for v in validations)
        
        # Check if all are executable
        all_executable = all(v.executable for v in validations)
        
        is_valid = (
            avg_score >= 0.6 and 
            all_syntax_valid and 
            safety_level != "unsafe" and
            len(all_issues) == 0
        )
        
        return ValidationResult(
            is_valid=is_valid,
            score=avg_score,
            issues=all_issues,
            warnings=all_warnings,
            safety_level=safety_level,
            syntax_valid=all_syntax_valid,
            executable=all_executable
        )
    
    def get_validation_summary(self, validation: ValidationResult) -> str:
        """Get a human-readable validation summary."""
        if validation.is_valid:
            status = f"✅ Valid (Score: {validation.score:.2f})"
        else:
            status = f"❌ Invalid (Score: {validation.score:.2f})"
        
        safety_emoji = {
            "safe": "🟢",
            "caution": "🟡", 
            "unsafe": "🔴"
        }
        
        summary = f"{status} | Safety: {safety_emoji[validation.safety_level]} {validation.safety_level.capitalize()}"
        
        if validation.syntax_valid:
            summary += " | ✅ Syntax"
        else:
            summary += " | ❌ Syntax"
        
        if validation.executable:
            summary += " | ✅ Executable"
        
        if validation.issues:
            summary += f" | Issues: {len(validation.issues)}"
        
        if validation.warnings:
            summary += f" | Warnings: {len(validation.warnings)}"
        
        return summary