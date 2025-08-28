"""
Spark main entry point for direct module execution.

Allows running Spark via: python -m spark
"""

import sys
from spark.cli.main import main

if __name__ == "__main__":
    sys.exit(main())