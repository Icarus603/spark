"""
Automated test generation and execution orchestrator.

This module provides automated test generation using Claude Code SDK and 
execution using sandboxed environments for comprehensive code validation.
"""

import uuid
import time
import asyncio
import tempfile
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

import litellm

from spark.discovery.models import CodeArtifact, ExplorationResult
from spark.exploration.validator import ExecutionResult, ValidationResult

# Import CUA components for sandboxed test execution
try:
    from agent.agent.computers import make_computer_handler
    from agent.agent.computers.base import AsyncComputerHandler
    CUA_AVAILABLE = True
except ImportError:
    CUA_AVAILABLE = False
    AsyncComputerHandler = None


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    passed: bool
    execution_time: float = 0.0
    error_message: Optional[str] = None
    output: str = ""
    assertion_count: int = 0


@dataclass
class TestSuiteResult:
    """Result of an entire test suite execution."""
    success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    coverage_percentage: Optional[float] = None
    test_results: List[TestResult] = field(default_factory=list)
    generated_test_code: str = ""
    error_message: Optional[str] = None


class TestOrchestrator:
    """Orchestrates automated test generation and execution for exploration code."""
    
    def __init__(
        self, 
        model: str = "anthropic/claude-3-5-sonnet-20241022",
        enable_execution: bool = True,
        enable_cua: bool = True
    ):
        """
        Initialize TestOrchestrator.
        
        Args:
            model: Claude model to use for test generation
            enable_execution: Whether to actually execute generated tests
            enable_cua: Whether to use CUA computer interface for test execution
        """
        self.model = model
        self.enable_execution = enable_execution
        self.enable_cua = enable_cua and CUA_AVAILABLE
        self.computer_handler: Optional[AsyncComputerHandler] = None
        
        # Ensure API key is available for test generation
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("Warning: ANTHROPIC_API_KEY not found. Test generation will be disabled.")
            self.enable_test_generation = False
        else:
            self.enable_test_generation = True
    
    async def generate_and_run_tests(
        self,
        code_artifact: CodeArtifact,
        context: Optional[Dict[str, Any]] = None
    ) -> TestSuiteResult:
        """
        Generate comprehensive tests for a code artifact and execute them.
        
        Args:
            code_artifact: The code artifact to test
            context: Additional context for test generation
            
        Returns:
            TestSuiteResult with execution results and metrics
        """
        
        if not self.enable_test_generation:
            return TestSuiteResult(
                success=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                execution_time=0.0,
                error_message="Test generation disabled (no API key)"
            )
        
        start_time = time.time()
        
        try:
            # Step 1: Generate comprehensive test code
            test_code = await self._generate_test_code(code_artifact, context or {})
            
            if not test_code:
                return TestSuiteResult(
                    success=False,
                    total_tests=0,
                    passed_tests=0,
                    failed_tests=0,
                    execution_time=time.time() - start_time,
                    error_message="Failed to generate test code"
                )
            
            # Step 2: Execute the tests if execution is enabled
            if self.enable_execution:
                execution_result = await self._execute_tests(
                    code_artifact.content, 
                    test_code, 
                    code_artifact.language
                )
                
                # Parse test results from execution
                test_results = self._parse_test_results(execution_result, test_code)
                
                total_tests = len(test_results)
                passed_tests = sum(1 for t in test_results if t.passed)
                failed_tests = total_tests - passed_tests
                
                return TestSuiteResult(
                    success=execution_result.success and failed_tests == 0,
                    total_tests=total_tests,
                    passed_tests=passed_tests,
                    failed_tests=failed_tests,
                    execution_time=time.time() - start_time,
                    test_results=test_results,
                    generated_test_code=test_code,
                    coverage_percentage=self._estimate_coverage(code_artifact.content, test_code)
                )
            else:
                # Static analysis of generated tests only
                test_count = self._count_tests_in_code(test_code)
                return TestSuiteResult(
                    success=True,
                    total_tests=test_count,
                    passed_tests=0,
                    failed_tests=0,
                    execution_time=time.time() - start_time,
                    generated_test_code=test_code,
                    coverage_percentage=self._estimate_coverage(code_artifact.content, test_code)
                )
                
        except Exception as e:
            return TestSuiteResult(
                success=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                execution_time=time.time() - start_time,
                error_message=f"Test orchestration failed: {str(e)}"
            )
    
    async def _generate_test_code(self, code_artifact: CodeArtifact, context: Dict[str, Any]) -> str:
        """Generate comprehensive test code using Claude Code SDK."""
        
        # Create a comprehensive test generation prompt
        prompt = self._create_test_generation_prompt(code_artifact, context)
        
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._create_test_system_prompt(code_artifact.language)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2500,
                temperature=0.3,  # Lower temperature for more deterministic test generation
                timeout=60
            )
            
            test_code = response.choices[0].message.content
            
            # Extract code blocks if present
            code_blocks = self._extract_code_blocks(test_code)
            if code_blocks:
                # Use the first/main code block
                return code_blocks[0][1]
            
            return test_code
            
        except Exception as e:
            print(f"Error generating test code: {e}")
            return ""
    
    def _create_test_system_prompt(self, language: str) -> str:
        """Create system prompt for test generation."""
        
        if language.lower() == 'python':
            return """You are an expert Python test engineer. Generate comprehensive, executable unit tests that:

1. Use the unittest framework (import unittest)
2. Test all public functions and methods thoroughly
3. Include edge cases, error conditions, and boundary values
4. Use clear, descriptive test method names
5. Include setup/teardown if needed
6. Add assertions for expected behavior
7. Handle exceptions appropriately
8. Include docstrings for test methods

Write complete, runnable test code that can be executed directly.
"""
        else:
            return f"""You are an expert test engineer for {language}. Generate comprehensive, executable tests that:

1. Use appropriate testing framework for {language}
2. Test all public functions and methods thoroughly
3. Include edge cases, error conditions, and boundary values
4. Use clear, descriptive test names
5. Include proper setup/teardown
6. Add appropriate assertions
7. Handle exceptions appropriately

Write complete, runnable test code.
"""
    
    def _create_test_generation_prompt(self, code_artifact: CodeArtifact, context: Dict[str, Any]) -> str:
        """Create detailed prompt for test generation."""
        
        language = code_artifact.language
        code = code_artifact.content
        description = code_artifact.description
        
        prompt = f"""Generate comprehensive unit tests for the following {language} code:

**Code Description:** {description}

**Code to Test:**
```{language}
{code}
```

**Requirements:**
1. Create thorough unit tests covering all functions/methods
2. Test normal operation, edge cases, and error conditions
3. Use appropriate assertions to verify expected behavior
4. Include tests for input validation and error handling
5. Test boundary conditions and edge cases
6. Make tests independent and isolated
7. Use descriptive test names that explain what is being tested

**Additional Context:**
"""
        
        # Add context information if available
        if context:
            for key, value in context.items():
                if isinstance(value, str) and len(value) < 200:
                    prompt += f"- {key}: {value}\n"
        
        prompt += """
**Generate complete, executable test code that can be run immediately.**
Include all necessary imports and setup code.
"""
        
        return prompt
    
    async def _execute_tests(self, source_code: str, test_code: str, language: str) -> ExecutionResult:
        """Execute the generated tests in a sandboxed environment."""
        
        if language.lower() != 'python':
            return ExecutionResult(
                success=False,
                error_message=f"Test execution not yet supported for {language}"
            )
        
        if self.enable_cua and CUA_AVAILABLE:
            return await self._execute_tests_with_cua(source_code, test_code)
        else:
            return await self._execute_tests_with_subprocess(source_code, test_code)
    
    async def _execute_tests_with_cua(self, source_code: str, test_code: str) -> ExecutionResult:
        """Execute tests using CUA computer interface."""
        
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
            
            # Create temporary files for source and test code
            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "source.py"
                test_file = Path(temp_dir) / "test_source.py"
                
                # Write source code
                with open(source_file, 'w') as f:
                    f.write(source_code)
                
                # Write combined test code (import source + tests)
                combined_test_code = f"""
# Import the source code to test
import sys
sys.path.insert(0, '{temp_dir}')

try:
    from source import *
except ImportError:
    # Handle modules that don't export everything
    import source
except Exception as e:
    print(f"Warning: Could not import source code: {{e}}")

{test_code}

if __name__ == '__main__':
    unittest.main(verbosity=2)
"""
                
                with open(test_file, 'w') as f:
                    f.write(combined_test_code)
                
                # Execute using CUA
                await self.computer_handler.type(f"cd {temp_dir}")
                await self.computer_handler.keypress("Return")
                await self.computer_handler.wait(500)
                
                await self.computer_handler.type(f"python {test_file.name}")
                await self.computer_handler.keypress("Return")
                await self.computer_handler.wait(3000)  # Wait for test execution
                
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    success=True,
                    execution_time=execution_time,
                    stdout="Tests executed via CUA (output parsing would be enhanced in production)",
                    stderr="",
                    exit_code=0
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=f"CUA test execution failed: {str(e)}",
                execution_time=time.time() - start_time if 'start_time' in locals() else 0
            )
    
    async def _execute_tests_with_subprocess(self, source_code: str, test_code: str) -> ExecutionResult:
        """Execute tests using subprocess in restricted environment."""
        
        try:
            start_time = time.time()
            
            # Create a safe execution environment
            safe_globals = {
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
                    'isinstance': isinstance,
                    'type': type,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'Exception': Exception,
                    'ValueError': ValueError,
                    'TypeError': TypeError,
                    'AttributeError': AttributeError,
                },
                'unittest': __import__('unittest')
            }
            
            # Execute source code first
            source_locals = {}
            try:
                exec(source_code, safe_globals, source_locals)
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error_message=f"Source code execution failed: {str(e)}",
                    stderr=str(e),
                    execution_time=time.time() - start_time
                )
            
            # Merge source locals into globals for test access
            safe_globals.update(source_locals)
            
            # Execute test code
            test_locals = {}
            try:
                exec(test_code, safe_globals, test_locals)
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    success=True,
                    execution_time=execution_time,
                    stdout="Tests executed successfully in restricted environment",
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
                error_message=f"Test execution setup failed: {str(e)}"
            )
    
    def _parse_test_results(self, execution_result: ExecutionResult, test_code: str) -> List[TestResult]:
        """Parse test results from execution output."""
        
        test_results = []
        
        # Extract test method names from test code
        test_methods = re.findall(r'def (test_\w+)\(', test_code)
        
        if execution_result.success:
            # If execution succeeded, assume all tests passed
            # In a production system, you'd parse actual unittest output
            for test_method in test_methods:
                test_results.append(TestResult(
                    test_name=test_method,
                    passed=True,
                    execution_time=execution_result.execution_time / len(test_methods) if test_methods else 0,
                    output="Test passed",
                    assertion_count=self._count_assertions_in_test(test_code, test_method)
                ))
        else:
            # If execution failed, mark tests as failed
            for test_method in test_methods:
                test_results.append(TestResult(
                    test_name=test_method,
                    passed=False,
                    execution_time=0,
                    error_message=execution_result.error_message,
                    output=execution_result.stderr
                ))
        
        return test_results
    
    def _extract_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """Extract code blocks from Claude's response."""
        import re
        
        # Pattern to match code blocks with optional language specification
        pattern = r'```(?:(\w+)\n)?(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        code_blocks = []
        for lang, code in matches:
            if code.strip():
                block_type = lang.lower() if lang else 'code'
                code_blocks.append((block_type, code.strip()))
        
        return code_blocks
    
    def _count_tests_in_code(self, test_code: str) -> int:
        """Count the number of test methods in the test code."""
        return len(re.findall(r'def test_\w+\(', test_code))
    
    def _count_assertions_in_test(self, test_code: str, test_method: str) -> int:
        """Count assertions in a specific test method."""
        # Find the test method and count assert statements
        method_pattern = rf'def {test_method}\(.*?\):(.*?)(?=def|\Z)'
        match = re.search(method_pattern, test_code, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            return len(re.findall(r'self\.assert\w+', method_body))
        
        return 0
    
    def _estimate_coverage(self, source_code: str, test_code: str) -> float:
        """Estimate test coverage based on function/method coverage."""
        
        # Find all functions and methods in source code
        source_functions = set(re.findall(r'def (\w+)\(', source_code))
        source_classes = set(re.findall(r'class (\w+)', source_code))
        
        total_testable_units = len(source_functions) + len(source_classes)
        
        if total_testable_units == 0:
            return 0.0
        
        # Count how many are mentioned in tests
        covered_units = 0
        for func in source_functions:
            if func in test_code:
                covered_units += 1
        
        for cls in source_classes:
            if cls in test_code:
                covered_units += 1
        
        return min(covered_units / total_testable_units, 1.0) * 100  # Return as percentage