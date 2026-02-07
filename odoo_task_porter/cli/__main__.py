"""Run the CLI package with ``python -m odoo_task_porter.cli``."""
from __future__ import annotations

import sys

from odoo_task_porter.cli import main


if __name__ == "__main__":
    sys.exit(main())
