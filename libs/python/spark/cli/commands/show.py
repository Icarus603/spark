"""
Spark show command implementation.

Browses and manages historical discoveries and patterns.
"""

from typing import List
from spark.cli.terminal import get_console
from spark.cli.errors import handle_async_cli_error
from spark.discovery.curator import DiscoveryCurator, CurationCriteria
from spark.discovery.presenter import DiscoveryPresenter
from spark.discovery.models import DiscoveryType
from spark.storage.discovery_storage import DiscoveryStorage


class ShowCommand:
    """Implementation of the 'spark show' command."""
    
    def __init__(self):
        self.console = get_console()
        self.storage = DiscoveryStorage()
        self.curator = DiscoveryCurator(self.storage)
        self.presenter = DiscoveryPresenter()
    
    @handle_async_cli_error
    async def execute(self, args: List[str]) -> int:
        """Execute the show command."""
        
        if not args:
            # Show recent discoveries
            return await self._show_recent_discoveries()
        
        first_arg = args[0].lower()
        
        # Handle special commands
        if first_arg == "--all":
            return await self._show_all_discoveries()
        elif first_arg == "patterns":
            return await self._show_patterns()
        elif first_arg == "stats":
            return await self._show_stats()
        elif first_arg == "suggestions":
            return await self._show_suggestions()
        elif first_arg.startswith("type:"):
            # Show discoveries of specific type
            type_name = first_arg[5:]
            return await self._show_discoveries_by_type(type_name)
        elif len(first_arg) >= 8 and first_arg.replace('-', '').replace('_', '').isalnum():
            # Looks like a discovery ID
            return await self._show_discovery_details(first_arg)
        else:
            # Treat as search query
            query = " ".join(args)
            return await self._search_discoveries(query)
    
    async def _show_recent_discoveries(self) -> int:
        """Show recent discoveries."""
        discoveries = self.curator.get_recent_discoveries(days=30, limit=10)
        
        if not discoveries:
            self.console.print_info(
                "No discoveries found",
                "Try running 'spark explore' to generate some discoveries"
            )
            return 0
        
        self.presenter.show_discovery_list(discoveries, "Recent Discoveries")
        return 0
    
    async def _show_all_discoveries(self) -> int:
        """Show all discoveries."""
        discoveries = self.curator.curate_discoveries(limit=50)
        
        if not discoveries:
            self.console.print_info("No discoveries found", "Run some explorations first")
            return 0
        
        self.presenter.show_discovery_list(discoveries, "All Discoveries")
        return 0
    
    async def _show_patterns(self) -> int:
        """Show detected patterns (placeholder for now)."""
        self.console.print_info(
            "Pattern analysis coming soon",
            "Showing discovery curation statistics for now"
        )
        
        # Use curator stats for consistent presenter format
        stats = self.curator.get_curation_stats()
        self.presenter.show_curation_stats(stats)
        
        return 0
    
    async def _show_stats(self) -> int:
        """Show discovery statistics."""
        stats = self.curator.get_curation_stats()
        self.presenter.show_curation_stats(stats)
        return 0
    
    async def _show_suggestions(self) -> int:
        """Show exploration suggestions."""
        suggestions = self.curator.suggest_exploration_topics()
        self.presenter.show_exploration_suggestions(suggestions)
        return 0
    
    async def _show_discoveries_by_type(self, type_name: str) -> int:
        """Show discoveries of a specific type."""
        # Map type name to DiscoveryType enum
        type_mapping = {
            'feature': DiscoveryType.NEW_FEATURE,
            'improvement': DiscoveryType.CODE_IMPROVEMENT,
            'performance': DiscoveryType.PERFORMANCE_OPTIMIZATION,
            'refactoring': DiscoveryType.REFACTORING,
            'testing': DiscoveryType.TESTING,
            'documentation': DiscoveryType.DOCUMENTATION,
            'tooling': DiscoveryType.TOOLING
        }
        
        discovery_type = type_mapping.get(type_name.lower())
        if not discovery_type:
            self.console.print_error(
                f"Unknown discovery type: {type_name}",
                f"Available types: {', '.join(type_mapping.keys())}"
            )
            return 1
        
        discoveries = self.curator.get_discoveries_by_type(discovery_type)
        
        if not discoveries:
            self.console.print_info(f"No {type_name} discoveries found", "Try running some explorations")
            return 0
        
        type_title = discovery_type.value.replace('_', ' ').title()
        self.presenter.show_discovery_list(discoveries, f"{type_title} Discoveries")
        return 0
    
    async def _show_discovery_details(self, discovery_id: str) -> int:
        """Show detailed information about a specific discovery."""
        # Handle partial IDs (match prefix)
        discoveries = self.storage.get_discoveries(limit=1000)
        matching_discoveries = [
            d for d in discoveries
            if d.id.startswith(discovery_id) or discovery_id in d.id
        ]
        
        if not matching_discoveries:
            self.console.print_error(
                f"Discovery not found: {discovery_id}",
                "Use 'spark show' to list available discoveries"
            )
            return 1
        
        if len(matching_discoveries) > 1:
            self.console.print_warning(
                f"Multiple discoveries match '{discovery_id}':",
                "Please be more specific"
            )
            
            # Show the matching options
            self.presenter.show_discovery_list(matching_discoveries[:5], "Matching Discoveries")
            return 1
        
        discovery = matching_discoveries[0]
        
        # Mark as viewed
        self.storage.mark_discovery_viewed(discovery.id)
        
        # Show detailed information
        self.presenter.show_discovery_details(discovery, show_code=True)
        
        # Show feedback prompt if not rated
        if not discovery.user_rating:
            self.presenter.show_feedback_prompt(discovery.id)
        
        return 0
    
    async def _search_discoveries(self, query: str) -> int:
        """Search discoveries by query."""
        discoveries = self.storage.search_discoveries(query, limit=20)
        
        if not discoveries:
            self.console.print_info(
                f"No discoveries found matching '{query}'",
                "Try different search terms or run more explorations"
            )
            return 0
        
        self.presenter.show_discovery_list(discoveries, f"Search Results: '{query}'")
        return 0
    
    def help(self) -> None:
        """Show help for the show command."""
        help_text = """
[bold cyan]spark show[/bold cyan] - Browse discoveries and patterns

[bold]Usage:[/bold]
  spark show                         List recent discoveries
  spark show --all                   Show all discoveries  
  spark show <discovery-id>          Show detailed discovery info
  spark show <search-terms>          Search discoveries
  spark show type:<type>             Show discoveries by type
  spark show stats                   Show discovery statistics
  spark show suggestions             Show exploration suggestions
  spark show patterns                Show detected patterns (coming soon)

[bold]Discovery Types:[/bold]
  feature, improvement, performance, refactoring, testing, documentation, tooling

[bold]Examples:[/bold]
  spark show abc12345                Show discovery details
  spark show python function        Search for Python function discoveries
  spark show type:performance        Show performance-related discoveries
        """
        self.console.console.print(help_text)
