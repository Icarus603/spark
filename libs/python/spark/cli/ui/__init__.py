"""
Interactive UI components for Spark CLI.

This package provides rich terminal interfaces for visualizing pattern analysis,
development sessions, and real-time learning insights.
"""

from .dashboard import (
    InteractiveDashboard,
    DashboardConfig,
    DashboardMetrics,
    create_dashboard
)

__all__ = [
    'InteractiveDashboard',
    'DashboardConfig', 
    'DashboardMetrics',
    'create_dashboard'
]