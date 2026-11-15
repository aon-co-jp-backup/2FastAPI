"""2FastAPI (to FastAPI): convert Flask / Django code to FastAPI-compatible code (MFastAPI compatible)."""
__version__ = "0.1.0"

from .common import Result, Warn  # noqa: F401
from .flask_conv import convert_source as convert_flask  # noqa: F401
