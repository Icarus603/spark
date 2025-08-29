"""
Spark rate command implementation.

Handles user feedback and rating for discoveries.
"""

from typing import List
from spark.cli.terminal import get_console
from spark.cli.errors import handle_async_cli_error
from spark.discovery.feedback import FeedbackCollector
from spark.discovery.models import FeedbackRating
from spark.storage.discovery_storage import DiscoveryStorage


class RateCommand:
    """Implementation of the 'spark rate' command."""
    
    def __init__(self):
        self.console = get_console()
        self.storage = DiscoveryStorage()
        self.feedback_collector = FeedbackCollector(self.storage)
    
    @handle_async_cli_error
    async def execute(self, args: List[str]) -> int:
        """Execute the rate command."""
        
        if not args:
            # Show usage help
            self.help()
            return 0
        
        # Parse arguments: discovery_id rating [feedback]
        if len(args) < 2:
            self.console.print_error(
                "Missing required arguments",
                "Usage: spark rate <discovery-id> <rating> [feedback]"
            )
            return 1
        
        discovery_id = args[0]
        rating_str = args[1]
        feedback_text = " ".join(args[2:]) if len(args) > 2 else ""
        
        # Validate rating
        try:
            rating_value = int(rating_str)
            if rating_value < 1 or rating_value > 5:
                raise ValueError("Rating must be between 1 and 5")
            rating = FeedbackRating(rating_value)
        except (ValueError, TypeError) as e:
            self.console.print_error(
                f"Invalid rating: {rating_str}",
                "Rating must be a number from 1 (Terrible) to 5 (Excellent)"
            )
            return 1
        
        # Find discovery by partial ID
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
            
            # Show matching options with their IDs
            for discovery in matching_discoveries[:5]:
                self.console.console.print(
                    f"  {discovery.id[:8]} - {discovery.title[:60]}"
                )
            return 1
        
        discovery = matching_discoveries[0]
        
        # Submit rating
        success = self.feedback_collector.rate_discovery(
            discovery.id,
            rating,
            feedback_text
        )
        
        if success:
            rating_emoji = {
                1: "😞",
                2: "😐", 
                3: "😊",
                4: "😃",
                5: "🤩"
            }
            
            rating_names = {
                1: "Terrible",
                2: "Poor",
                3: "Neutral",
                4: "Good", 
                5: "Excellent"
            }
            
            self.console.console.print(
                f"✅ [green]Rating submitted![/green] "
                f"{rating_emoji[rating_value]} {rating_names[rating_value]} "
                f"({rating_value}/5)"
            )
            
            if feedback_text:
                self.console.console.print(f"💬 Feedback: [dim]{feedback_text}[/dim]")
            
            self.console.console.print(
                f"[dim]Discovery: {discovery.title[:60]}[/dim]"
            )
            
            # Show encouragement for feedback
            if rating_value >= 4:
                self.console.console.print("\n🎉 Thanks for the positive feedback! This helps improve future explorations.")
            elif rating_value <= 2:
                self.console.console.print("\n📝 Thanks for the honest feedback. We'll use this to improve code generation quality.")
            
            return 0
        else:
            self.console.print_error(
                "Failed to submit rating",
                "Please try again or check discovery ID"
            )
            return 1
    
    def help(self) -> None:
        """Show help for the rate command."""
        help_text = """
[bold cyan]spark rate[/bold cyan] - Rate and provide feedback for discoveries

[bold]Usage:[/bold]
  spark rate <discovery-id> <rating> [feedback]

[bold]Arguments:[/bold]
  discovery-id        ID or partial ID of the discovery (use 'spark show' to list)
  rating              Rating from 1-5:
                        1 = Terrible    😞
                        2 = Poor        😐  
                        3 = Neutral     😊
                        4 = Good        😃
                        5 = Excellent   🤩
  feedback            Optional feedback message (in quotes if multiple words)

[bold]Examples:[/bold]
  spark rate abc12345 5 \"Excellent implementation, exactly what I needed!\"
  spark rate def67890 3 \"Good but needs some refinement\"
  spark rate 12345 1 \"Doesn't work as expected\"
  spark rate abc 4      # Rating without feedback message

[bold]Why rate discoveries?[/bold]
  • Helps Spark learn your preferences
  • Improves future exploration quality  
  • Guides discovery curation and ranking
  • Provides valuable feedback for continuous improvement

[bold]Tips:[/bold]
  • You only need the first 8 characters of the discovery ID
  • Use descriptive feedback to help improve future results
  • Rate discoveries soon after viewing them for accurate assessment
  • Consider both code quality and usefulness when rating
        """
        self.console.console.print(help_text)