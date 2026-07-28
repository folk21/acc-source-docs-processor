"""CLI command registration and execution handlers."""

from .anonymize import register_anonymize_command
from .process import process_folder, register_process_command

__all__ = [
    "process_folder",
    "register_anonymize_command",
    "register_process_command",
]
