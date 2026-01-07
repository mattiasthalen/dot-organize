"""dot - Data Organize Tool for validating and creating manifests using the HOOK methodology."""

try:
    from dot._version import __version__
except ImportError:
    # Fallback for editable installs before first build
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
]
