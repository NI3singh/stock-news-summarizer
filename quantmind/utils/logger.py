"""QuantMind v2 — logging setup (loguru).

Importing this module configures the global loguru ``logger`` exactly once: a
colorized console sink (level driven by ``settings.log_level``) plus a rotating
DEBUG file sink at ``logs/quantmind.log``. Import the configured logger via
``from quantmind.utils import logger``.
"""
import sys
from pathlib import Path

from loguru import logger

from quantmind.config import settings

# Start from a clean slate (drop loguru's default stderr handler).
logger.remove()

# Ensure the log directory exists (relative to CWD; gitignored).
Path("logs").mkdir(exist_ok=True)

# Console sink — colorized, level driven by configuration.
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | {message}",
    level=settings.log_level,
    colorize=True,
)

# File sink — always DEBUG, rotated and retained; no color tags.
logger.add(
    "logs/quantmind.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
)

# Re-export the configured singleton.
__all__ = ["logger"]
