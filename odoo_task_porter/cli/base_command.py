"""Base abstractions for CLI commands."""
from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandHelper:
    """Command helper entry used by the general helper renderer."""

    name: str
    summary: str
    usage: str


class BaseCommand(ABC):
    """Base class for all CLI commands."""

    name: str
    summary: str

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(self.name, help=self.summary)
        self.configure(parser)
        parser.set_defaults(_handler=self.execute)

    @abstractmethod
    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Attach command-specific arguments to parser."""

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command and return an exit code."""

    @abstractmethod
    def helper(self) -> CommandHelper:
        """Return command-specific helper details."""
