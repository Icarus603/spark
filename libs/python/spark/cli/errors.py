"""
Error handling and exception classes for Spark CLI.

This module provides comprehensive error handling with proper exception hierarchy
and user-friendly error reporting for the Spark CLI.
"""

import sys
import traceback
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

from spark.cli.terminal import get_console, SparkTheme


class SparkErrorCode(Enum):
    """Standard error codes for Spark operations."""
    
    # General errors
    UNKNOWN_ERROR = "SPARK_E001"
    INITIALIZATION_FAILED = "SPARK_E002"
    CONFIGURATION_ERROR = "SPARK_E003"
    
    # Learning errors
    LEARNING_FAILED = "SPARK_E100"
    PATTERN_DETECTION_FAILED = "SPARK_E101"
    GIT_ANALYSIS_FAILED = "SPARK_E102"
    FILE_MONITORING_FAILED = "SPARK_E103"
    
    # Exploration errors
    EXPLORATION_FAILED = "SPARK_E200"
    CODE_GENERATION_FAILED = "SPARK_E201"
    VALIDATION_FAILED = "SPARK_E202"
    SCHEDULING_FAILED = "SPARK_E203"
    
    # Discovery errors
    DISCOVERY_FAILED = "SPARK_E300"
    CURATION_FAILED = "SPARK_E301"
    PRESENTATION_FAILED = "SPARK_E302"
    
    # Integration errors
    INTEGRATION_FAILED = "SPARK_E400"
    BACKUP_FAILED = "SPARK_E401"
    ROLLBACK_FAILED = "SPARK_E402"
    
    # Storage errors
    STORAGE_ERROR = "SPARK_E500"
    DATABASE_ERROR = "SPARK_E501"
    MIGRATION_FAILED = "SPARK_E502"


class SparkError(Exception):
    """Base exception class for all Spark errors."""
    
    def __init__(
        self,
        message: str,
        error_code: SparkErrorCode = SparkErrorCode.UNKNOWN_ERROR,
        details: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
        self.suggestions = suggestions or []
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/telemetry."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "cause": str(self.cause) if self.cause else None
        }


class SparkInitializationError(SparkError):
    """Raised when Spark initialization fails."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message,
            SparkErrorCode.INITIALIZATION_FAILED,
            details,
            suggestions=[
                "Check that you have write permissions to ~/.spark/",
                "Ensure git is available in your PATH",
                "Try running 'spark --help' for basic functionality"
            ]
        )


class SparkConfigurationError(SparkError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message,
            SparkErrorCode.CONFIGURATION_ERROR,
            details,
            suggestions=[
                "Run 'spark' to reinitialize configuration",
                "Check ~/.spark/config.toml for syntax errors",
                "Delete ~/.spark/ to reset all settings"
            ]
        )


class SparkLearningError(SparkError):
    """Raised when learning operations fail."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message,
            SparkErrorCode.LEARNING_FAILED,
            details,
            suggestions=[
                "Check that git repositories are accessible",
                "Ensure you have read permissions for project files",
                "Try running 'spark learn --reset' to restart learning"
            ]
        )


class SparkExplorationError(SparkError):
    """Raised when exploration operations fail."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message,
            SparkErrorCode.EXPLORATION_FAILED,
            details,
            suggestions=[
                "Check your internet connection for AI model access",
                "Verify that exploration goals are realistic",
                "Try reducing the exploration scope or time limit"
            ]
        )


class SparkStorageError(SparkError):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message,
            SparkErrorCode.STORAGE_ERROR,
            details,
            suggestions=[
                "Check disk space in ~/.spark/",
                "Ensure database files are not corrupted",
                "Try backing up and reinitializing storage"
            ]
        )


class SparkErrorHandler:
    """Central error handling and reporting system."""
    
    def __init__(self, console=None):
        self.console = console or get_console()
        self.theme = SparkTheme()
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        show_traceback: bool = False
    ) -> None:
        """Handle and display error with appropriate formatting."""
        
        if isinstance(error, SparkError):
            self._handle_spark_error(error, context)
        else:
            self._handle_generic_error(error, context, show_traceback)
    
    def _handle_spark_error(
        self,
        error: SparkError,
        context: Optional[str] = None
    ) -> None:
        """Handle Spark-specific errors with structured reporting."""
        
        # Error header
        context_text = f" ({context})" if context else ""
        self.console.print_error(f"{error.message}{context_text}")
        
        # Error details
        if error.details:
            self.console.console.print(f"💡 [dim]{error.details}[/dim]")
        
        # Error code
        self.console.console.print(f"🔍 Error Code: [dim]{error.error_code.value}[/dim]")
        
        # Suggestions
        if error.suggestions:
            self.console.console.print("\n💡 [bold]Suggestions:[/bold]")
            for i, suggestion in enumerate(error.suggestions, 1):
                self.console.console.print(f"   {i}. [cyan]{suggestion}[/cyan]")
        
        # Root cause
        if error.cause:
            self.console.console.print(f"\n🔍 Root cause: [dim]{error.cause}[/dim]")
    
    def _handle_generic_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        show_traceback: bool = False
    ) -> None:
        """Handle generic Python exceptions."""
        
        error_type = type(error).__name__
        error_message = str(error)
        
        context_text = f" ({context})" if context else ""
        self.console.print_error(f"{error_type}: {error_message}{context_text}")
        
        if show_traceback:
            self.console.console.print("\n[dim]Traceback:[/dim]")
            self.console.console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        # Generic suggestions
        self.console.console.print("\n💡 [bold]General troubleshooting:[/bold]")
        suggestions = [
            "Run 'spark --help' for available commands",
            "Check 'spark status' for system health",
            "Report issues at: https://github.com/anthropics/claude-code/issues"
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            self.console.console.print(f"   {i}. [cyan]{suggestion}[/cyan]")
    
    def handle_keyboard_interrupt(self) -> None:
        """Handle Ctrl+C gracefully."""
        self.console.console.print("\n👋 [yellow]Operation cancelled by user[/yellow]")
    
    def handle_critical_error(
        self,
        error: Exception,
        context: str = "Critical system error"
    ) -> None:
        """Handle critical errors that require immediate attention."""
        
        self.console.console.print(f"\n🚨 [bold red]CRITICAL ERROR[/bold red]")
        self.console.console.print(f"Context: [red]{context}[/red]")
        self.console.console.print(f"Error: [red]{error}[/red]")
        
        self.console.console.print("\n💥 [bold]This is a critical system error.[/bold]")
        self.console.console.print("Please report this issue with the following information:")
        self.console.console.print(f"- Error: {type(error).__name__}: {error}")
        self.console.console.print(f"- Context: {context}")
        self.console.console.print(f"- Python version: {sys.version}")
        self.console.console.print(f"- Platform: {sys.platform}")
        
        # Always show traceback for critical errors
        self.console.console.print("\n[dim]Full traceback:[/dim]")
        self.console.console.print(f"[dim]{traceback.format_exc()}[/dim]")


def handle_cli_error(func):
    """Decorator for CLI command error handling."""
    
    def wrapper(*args, **kwargs):
        error_handler = SparkErrorHandler()
        
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            error_handler.handle_keyboard_interrupt()
            return 1
        except SparkError as e:
            error_handler.handle_error(e, context=func.__name__)
            return 1
        except Exception as e:
            error_handler.handle_critical_error(e, context=f"Command: {func.__name__}")
            return 1
    
    return wrapper


def handle_async_cli_error(func):
    """Decorator for async CLI command error handling."""
    
    async def wrapper(*args, **kwargs):
        error_handler = SparkErrorHandler()
        
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            error_handler.handle_keyboard_interrupt()
            return 1
        except SparkError as e:
            error_handler.handle_error(e, context=func.__name__)
            return 1
        except Exception as e:
            error_handler.handle_critical_error(e, context=f"Async Command: {func.__name__}")
            return 1
    
    return wrapper


# Global error handler instance
_error_handler: Optional[SparkErrorHandler] = None

def get_error_handler() -> SparkErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = SparkErrorHandler()
    return _error_handler