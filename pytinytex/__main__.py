"""Allow running pytinytex as ``python -m pytinytex``."""

import sys

from .cli import main

sys.exit(main())
