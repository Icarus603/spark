"""
Code generation interface for explorations.

This module provides the interface for generating code during explorations.
In Stage 1.3, this uses mock generation for testing. In later stages, this will
integrate with Claude Code SDK for real AI-powered code generation.
"""

import uuid
import time
import asyncio
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Optional dependency for Claude integration; guard at import time
try:
    import litellm  # type: ignore
    LITELLM_AVAILABLE = True
except Exception:  # ImportError and any env import issues
    litellm = None  # type: ignore
    LITELLM_AVAILABLE = False

from spark.discovery.models import CodeArtifact, ExplorationResult, ExplorationStatus


@dataclass
class GenerationRequest:
    """Request for code generation."""
    goal: str
    approach: str
    context: Dict[str, Any]
    language: Optional[str] = None
    max_attempts: int = 3
    timeout: int = 60


class CodeGenerator(ABC):
    """Abstract base class for code generators."""
    
    @abstractmethod
    async def generate_code(self, request: GenerationRequest) -> ExplorationResult:
        """Generate code based on the request."""
        pass


class MockCodeGenerator(CodeGenerator):
    """Mock code generator for Stage 1.3 testing."""
    
    def __init__(self):
        self.generation_count = 0
    
    async def generate_code(self, request: GenerationRequest) -> ExplorationResult:
        """Generate mock code for testing purposes."""
        start_time = time.time()
        self.generation_count += 1
        
        result_id = str(uuid.uuid4())
        
        try:
            # Simulate generation time
            await self._simulate_generation_delay()
            
            # Generate mock artifacts based on goal
            artifacts = self._generate_mock_artifacts(request)
            
            execution_time = time.time() - start_time
            
            return ExplorationResult(
                id=result_id,
                goal=request.goal,
                approach=request.approach,
                status=ExplorationStatus.COMPLETED,
                code_artifacts=artifacts,
                success=True,
                execution_time=execution_time,
                metadata={
                    'generator_type': 'mock',
                    'language': request.language or 'python',
                    'generation_number': self.generation_count,
                    'context_keys': list(request.context.keys())
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExplorationResult(
                id=result_id,
                goal=request.goal,
                approach=request.approach,
                status=ExplorationStatus.FAILED,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                metadata={
                    'generator_type': 'mock',
                    'generation_number': self.generation_count
                }
            )
    
    async def _simulate_generation_delay(self):
        """Simulate realistic generation time."""
        import asyncio
        await asyncio.sleep(0.5)  # Simulate 500ms generation time
    
    def _generate_mock_artifacts(self, request: GenerationRequest) -> List[CodeArtifact]:
        """Generate mock code artifacts based on the request goal."""
        goal_lower = request.goal.lower()
        language = request.language or 'python'
        
        artifacts = []
        
        if 'function' in goal_lower or 'utility' in goal_lower:
            artifacts.append(self._create_function_artifact(request, language))
            
        elif 'class' in goal_lower or 'object' in goal_lower:
            artifacts.append(self._create_class_artifact(request, language))
            
        elif 'test' in goal_lower:
            artifacts.extend(self._create_test_artifacts(request, language))
            
        elif 'performance' in goal_lower or 'optimization' in goal_lower:
            artifacts.extend(self._create_performance_artifacts(request, language))
            
        elif 'refactor' in goal_lower:
            artifacts.extend(self._create_refactoring_artifacts(request, language))
            
        else:
            # Default: create a general purpose artifact
            artifacts.append(self._create_general_artifact(request, language))
        
        return artifacts
    
    def _create_function_artifact(self, request: GenerationRequest, language: str) -> CodeArtifact:
        """Create a mock function artifact."""
        if language == 'python':
            content = f'''def {self._extract_function_name(request.goal)}():
    """
    {request.goal}
    
    This is a mock implementation generated for exploration purposes.
    """
    # Mock implementation
    print(f"Executing: {request.goal}")
    return True
'''
        else:
            content = f'// Mock {language} function for: {request.goal}\n// TODO: Implement actual functionality'
        
        return CodeArtifact(
            file_path=f'mock_{language}_function.{self._get_extension(language)}',
            content=content,
            description=f'Mock {language} function implementing: {request.goal}',
            language=language,
            is_main_artifact=True
        )
    
    def _create_class_artifact(self, request: GenerationRequest, language: str) -> CodeArtifact:
        """Create a mock class artifact."""
        class_name = self._extract_class_name(request.goal)
        
        if language == 'python':
            content = f'''class {class_name}:
    """
    {request.goal}
    
    This is a mock implementation generated for exploration purposes.
    """
    
    def __init__(self):
        self.initialized = True
    
    def execute(self):
        """Execute the main functionality."""
        print(f"Executing {class_name}: {request.goal}")
        return True
'''
        else:
            content = f'// Mock {language} class for: {request.goal}\n// TODO: Implement actual functionality'
        
        return CodeArtifact(
            file_path=f'mock_{class_name.lower()}.{self._get_extension(language)}',
            content=content,
            description=f'Mock {language} class implementing: {request.goal}',
            language=language,
            is_main_artifact=True
        )
    
    def _create_test_artifacts(self, request: GenerationRequest, language: str) -> List[CodeArtifact]:
        """Create mock test artifacts."""
        artifacts = []
        
        if language == 'python':
            test_content = f'''import unittest

class Test{self._extract_class_name(request.goal)}(unittest.TestCase):
    """
    Test cases for: {request.goal}
    
    This is a mock test implementation generated for exploration purposes.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Mock test implementation
        self.assertTrue(True, "Mock test always passes")
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Mock test implementation
        self.assertIsNotNone(None or "Mock value")

if __name__ == '__main__':
    unittest.main()
'''
        else:
            test_content = f'// Mock {language} tests for: {request.goal}\n// TODO: Implement actual tests'
        
        artifacts.append(CodeArtifact(
            file_path=f'test_mock.{self._get_extension(language)}',
            content=test_content,
            description=f'Mock {language} tests for: {request.goal}',
            language=language,
            is_main_artifact=True
        ))
        
        return artifacts
    
    def _create_performance_artifacts(self, request: GenerationRequest, language: str) -> List[CodeArtifact]:
        """Create mock performance optimization artifacts."""
        artifacts = []
        
        # Main optimization
        if language == 'python':
            content = f'''import time
from functools import wraps

def performance_optimized_{self._extract_function_name(request.goal)}():
    """
    Performance optimized version: {request.goal}
    
    This is a mock optimization generated for exploration purposes.
    """
    # Mock optimization - using list comprehension instead of loops
    result = [x for x in range(1000) if x % 2 == 0]
    return result

def benchmark():
    """Benchmark the optimization."""
    start_time = time.time()
    result = performance_optimized_{self._extract_function_name(request.goal)}()
    end_time = time.time()
    
    print(f"Execution time: {{end_time - start_time:.4f}} seconds")
    print(f"Result length: {{len(result)}}")
    return end_time - start_time
'''
        else:
            content = f'// Mock {language} performance optimization for: {request.goal}\n// TODO: Implement actual optimization'
        
        artifacts.append(CodeArtifact(
            file_path=f'optimized_mock.{self._get_extension(language)}',
            content=content,
            description=f'Performance optimized version of: {request.goal}',
            language=language,
            is_main_artifact=True
        ))
        
        return artifacts
    
    def _create_refactoring_artifacts(self, request: GenerationRequest, language: str) -> List[CodeArtifact]:
        """Create mock refactoring artifacts."""
        artifacts = []
        
        # Before/after comparison
        if language == 'python':
            before_content = '''# BEFORE: Original implementation
def old_implementation():
    """Original code that needs refactoring."""
    data = []
    for i in range(100):
        if i % 2 == 0:
            data.append(i * 2)
    return data
'''
            
            after_content = '''# AFTER: Refactored implementation
def refactored_implementation():
    """Refactored code with improved readability and performance."""
    return [i * 2 for i in range(100) if i % 2 == 0]
'''
        else:
            before_content = f'// BEFORE: Original {language} code\n// TODO: Show original implementation'
            after_content = f'// AFTER: Refactored {language} code\n// TODO: Show refactored implementation'
        
        artifacts.extend([
            CodeArtifact(
                file_path=f'before_refactoring.{self._get_extension(language)}',
                content=before_content,
                description=f'Original code before refactoring: {request.goal}',
                language=language
            ),
            CodeArtifact(
                file_path=f'after_refactoring.{self._get_extension(language)}',
                content=after_content,
                description=f'Refactored code: {request.goal}',
                language=language,
                is_main_artifact=True
            )
        ])
        
        return artifacts
    
    def _create_general_artifact(self, request: GenerationRequest, language: str) -> CodeArtifact:
        """Create a general mock artifact."""
        if language == 'python':
            content = f'''"""
General implementation for: {request.goal}

This is a mock implementation generated for exploration purposes.
"""

def main():
    """Main entry point."""
    print("Mock implementation for: {request.goal}")
    print("Approach: {request.approach}")
    
    # Mock implementation logic
    result = {{"status": "success", "message": "Mock execution completed"}}
    return result

if __name__ == "__main__":
    result = main()
    print(f"Result: {{result}}")
'''
        else:
            content = f'// Mock {language} implementation for: {request.goal}\n// TODO: Implement actual functionality'
        
        return CodeArtifact(
            file_path=f'mock_implementation.{self._get_extension(language)}',
            content=content,
            description=f'General mock implementation for: {request.goal}',
            language=language,
            is_main_artifact=True
        )
    
    def _extract_function_name(self, goal: str) -> str:
        """Extract a valid function name from the goal."""
        # Simple extraction - replace spaces and special chars with underscores
        name = ''.join(c if c.isalnum() else '_' for c in goal.lower())
        name = name.strip('_')[:30]  # Limit length
        return name or 'generated_function'
    
    def _extract_class_name(self, goal: str) -> str:
        """Extract a valid class name from the goal."""
        # Convert to PascalCase
        words = goal.replace('_', ' ').split()
        name = ''.join(word.capitalize() for word in words if word.isalnum())
        return name[:30] or 'GeneratedClass'
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            'python': 'py',
            'javascript': 'js', 
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'rust': 'rs',
            'go': 'go'
        }
        return extensions.get(language.lower(), 'txt')


class ClaudeCodeGenerator(CodeGenerator):
    """Real AI-powered code generator using Claude Code SDK integration."""
    
    def __init__(self, model: str = "anthropic/claude-3-5-sonnet-20241022", patterns: Optional[Dict[str, Any]] = None):
        """
        Initialize ClaudeCodeGenerator.
        
        Args:
            model: Claude model to use for generation
            patterns: User coding patterns for context-aware generation
        """
        self.model = model
        self.patterns = patterns or {}
        self.generation_count = 0
        
        # Ensure API key is available
        if not os.getenv('ANTHROPIC_API_KEY'):
            raise ValueError("ANTHROPIC_API_KEY environment variable required for ClaudeCodeGenerator")
    
    async def generate_code(self, request: GenerationRequest) -> ExplorationResult:
        """Generate code using Claude Code SDK with multi-approach generation."""
        start_time = time.time()
        self.generation_count += 1
        result_id = str(uuid.uuid4())
        
        try:
            # Generate multiple approaches (3-5 variations)
            approaches = await self._generate_multiple_approaches(request)
            
            # Select best approach based on ranking criteria
            best_approach = self._rank_approaches(approaches, request)
            
            # Create code artifacts from the best approach
            artifacts = await self._create_artifacts_from_approach(best_approach, request)
            
            execution_time = time.time() - start_time
            
            return ExplorationResult(
                id=result_id,
                goal=request.goal,
                approach=request.approach,
                status=ExplorationStatus.COMPLETED,
                code_artifacts=artifacts,
                success=True,
                execution_time=execution_time,
                metadata={
                    'generator_type': 'claude_code_sdk',
                    'model': self.model,
                    'generation_number': self.generation_count,
                    'approaches_generated': len(approaches),
                    'patterns_used': list(self.patterns.keys()),
                    'context_keys': list(request.context.keys())
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ExplorationResult(
                id=result_id,
                goal=request.goal,
                approach=request.approach,
                status=ExplorationStatus.FAILED,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                metadata={
                    'generator_type': 'claude_code_sdk',
                    'model': self.model,
                    'generation_number': self.generation_count,
                    'error_type': type(e).__name__
                }
            )
    
    async def _generate_multiple_approaches(self, request: GenerationRequest) -> List[Dict[str, Any]]:
        """Generate 3-5 different approaches to the same goal."""
        approach_prompts = [
            self._create_simple_approach_prompt(request),
            self._create_modular_approach_prompt(request),
            self._create_performance_approach_prompt(request),
            self._create_robust_approach_prompt(request),
            self._create_innovative_approach_prompt(request)
        ]
        
        approaches = []
        tasks = []
        
        # Generate approaches in parallel for efficiency
        for i, prompt in enumerate(approach_prompts):
            task = self._generate_single_approach(prompt, f"approach_{i+1}", request)
            tasks.append(task)
        
        # Wait for all approaches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                approaches.append({
                    'id': f"approach_{i+1}",
                    'content': result,
                    'type': ['simple', 'modular', 'performance', 'robust', 'innovative'][i]
                })
        
        return approaches
    
    async def _generate_single_approach(self, prompt: str, approach_id: str, request: GenerationRequest) -> Optional[str]:
        """Generate a single approach using Claude."""
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._create_system_prompt(request)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7,
                timeout=30
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating {approach_id}: {e}")
            return None
    
    def _create_system_prompt(self, request: GenerationRequest) -> str:
        """Create system prompt with user patterns and context."""
        base_prompt = """You are an expert code generation assistant specializing in creating high-quality, working code that matches the user's coding patterns and style preferences.

Key principles:
1. Generate complete, executable code that runs without modification
2. Follow the user's established coding patterns and style preferences
3. Include appropriate error handling and edge case considerations
4. Add clear comments and documentation
5. Ensure code is production-ready and maintainable

"""
        
        # Add pattern-aware context
        if self.patterns:
            pattern_context = "User's coding patterns:\n"
            
            if 'language_preferences' in self.patterns:
                pattern_context += f"- Preferred languages: {', '.join(self.patterns['language_preferences'])}\n"
            
            if 'style_preferences' in self.patterns:
                style = self.patterns['style_preferences']
                pattern_context += f"- Code style: {style.get('primary_style', 'clean and readable')}\n"
                pattern_context += f"- Function length preference: {style.get('function_length', 'moderate')}\n"
                pattern_context += f"- Error handling style: {style.get('error_handling', 'explicit')}\n"
            
            if 'testing_patterns' in self.patterns:
                testing = self.patterns['testing_patterns']
                pattern_context += f"- Testing approach: {testing.get('style', 'comprehensive')}\n"
                pattern_context += f"- Test framework preference: {testing.get('framework', 'unittest')}\n"
            
            base_prompt += pattern_context + "\n"
        
        # Add context-specific information
        if request.context:
            context_info = "Current project context:\n"
            for key, value in request.context.items():
                if isinstance(value, str) and len(value) < 100:
                    context_info += f"- {key}: {value}\n"
                elif isinstance(value, (list, dict)):
                    context_info += f"- {key}: {str(value)[:100]}...\n"
            base_prompt += context_info + "\n"
        
        return base_prompt
    
    def _create_simple_approach_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for simple, straightforward approach."""
        language = request.language or 'python'
        return f"""Create a simple and straightforward {language} implementation for: {request.goal}

Approach: {request.approach}

Focus on:
- Clear, readable code
- Minimal complexity
- Direct solution to the problem
- Good variable names and comments

Generate complete, working code with example usage."""
    
    def _create_modular_approach_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for modular, extensible approach."""
        language = request.language or 'python'
        return f"""Create a modular and extensible {language} implementation for: {request.goal}

Approach: {request.approach}

Focus on:
- Modular design with clear separation of concerns
- Extensible architecture for future enhancements
- Reusable components
- Clean interfaces and abstractions

Generate complete, working code with example usage showing modularity."""
    
    def _create_performance_approach_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for performance-optimized approach."""
        language = request.language or 'python'
        return f"""Create a performance-optimized {language} implementation for: {request.goal}

Approach: {request.approach}

Focus on:
- Efficient algorithms and data structures
- Memory optimization
- Time complexity considerations
- Benchmarking capabilities

Generate complete, working code with performance measurements and example usage."""
    
    def _create_robust_approach_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for robust, error-handling approach.""" 
        language = request.language or 'python'
        return f"""Create a robust {language} implementation with comprehensive error handling for: {request.goal}

Approach: {request.approach}

Focus on:
- Comprehensive error handling and validation
- Edge case handling
- Logging and debugging capabilities
- Graceful failure modes

Generate complete, working code with extensive error handling and example usage."""
    
    def _create_innovative_approach_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for innovative, boundary-pushing approach."""
        language = request.language or 'python'
        return f"""Create an innovative and creative {language} implementation for: {request.goal}

Approach: {request.approach}

Focus on:
- Creative problem-solving approaches
- Modern language features and patterns
- Innovative use of libraries or frameworks
- Experimental but practical solutions

Generate complete, working code that pushes creative boundaries while remaining practical."""
    
    def _rank_approaches(self, approaches: List[Dict[str, Any]], request: GenerationRequest) -> Dict[str, Any]:
        """Rank approaches based on quality and user preferences."""
        if not approaches:
            raise ValueError("No approaches generated successfully")
        
        # Simple ranking based on approach type and user patterns
        scores = {}
        
        for approach in approaches:
            score = 0
            approach_type = approach['type']
            
            # Base scoring by approach type
            type_scores = {
                'simple': 3,      # Always valuable for clarity
                'modular': 4,     # Generally preferred for maintainability  
                'performance': 2, # Valuable for optimization goals
                'robust': 4,      # Important for production code
                'innovative': 2   # Interesting but potentially risky
            }
            score += type_scores.get(approach_type, 1)
            
            # Bonus for matching user patterns
            if self.patterns:
                if 'performance' in request.goal.lower() and approach_type == 'performance':
                    score += 2
                if 'robust' in request.goal.lower() or 'production' in request.goal.lower():
                    if approach_type == 'robust':
                        score += 2
                if self.patterns.get('style_preferences', {}).get('primary_style') == 'modular':
                    if approach_type == 'modular':
                        score += 1
            
            # Content quality scoring (basic heuristics)
            content = approach.get('content', '')
            if content:
                # Prefer longer, more detailed implementations
                score += min(len(content) / 500, 2)
                
                # Bonus for including tests, documentation
                if 'test' in content.lower() or 'example' in content.lower():
                    score += 1
                if 'def ' in content or 'class ' in content:  # Structured code
                    score += 1
            
            scores[approach['id']] = score
        
        # Return highest scoring approach
        best_id = max(scores.items(), key=lambda x: x[1])[0]
        return next(a for a in approaches if a['id'] == best_id)
    
    async def _create_artifacts_from_approach(self, approach: Dict[str, Any], request: GenerationRequest) -> List[CodeArtifact]:
        """Convert Claude's generated approach into CodeArtifacts."""
        content = approach.get('content', '')
        if not content:
            return []
        
        artifacts = []
        language = request.language or 'python'
        extension = self._get_extension(language)
        
        # Try to extract multiple code blocks if present
        code_blocks = self._extract_code_blocks(content)
        
        if code_blocks:
            # Multiple code files generated
            for i, (block_content, block_type) in enumerate(code_blocks):
                file_name = self._generate_filename(request.goal, block_type, extension, i)
                artifacts.append(CodeArtifact(
                    file_path=file_name,
                    content=block_content,
                    description=f"{approach['type'].title()} {language} implementation: {request.goal}",
                    language=language,
                    is_main_artifact=(i == 0),
                    metadata={
                        'approach_type': approach['type'],
                        'model': self.model,
                        'block_type': block_type
                    }
                ))
        else:
            # Single code block or plain content
            file_name = self._generate_filename(request.goal, 'main', extension, 0)
            artifacts.append(CodeArtifact(
                file_path=file_name,
                content=content,
                description=f"{approach['type'].title()} {language} implementation: {request.goal}",
                language=language,
                is_main_artifact=True,
                metadata={
                    'approach_type': approach['type'],
                    'model': self.model
                }
            ))
        
        return artifacts
    
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
                code_blocks.append((code.strip(), block_type))
        
        return code_blocks
    
    def _generate_filename(self, goal: str, block_type: str, extension: str, index: int) -> str:
        """Generate appropriate filename for the code artifact."""
        # Clean goal for filename
        clean_goal = ''.join(c if c.isalnum() else '_' for c in goal.lower())[:30].strip('_')
        
        if block_type == 'test' or 'test' in block_type:
            return f"test_{clean_goal}.{extension}"
        elif block_type == 'main' or index == 0:
            return f"{clean_goal}.{extension}"
        else:
            return f"{clean_goal}_{block_type}_{index}.{extension}"
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts', 
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'rust': 'rs',
            'go': 'go',
            'html': 'html',
            'css': 'css',
            'bash': 'sh',
            'shell': 'sh'
        }
        return extensions.get(language.lower(), 'txt')
