"""Public interface for the Dari Python client."""

from ._version import __version__
from .client import Dari, DariError

__all__ = ["Dari", "DariError", "__version__"]
