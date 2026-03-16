"""YAML-to-document generator."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("docsmith")
except PackageNotFoundError:
    __version__ = "dev"
