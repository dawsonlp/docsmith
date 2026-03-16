"""YAML-to-document generator."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("docsmith")
except PackageNotFoundError:
    __version__ = "dev"