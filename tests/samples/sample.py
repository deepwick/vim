"""Deepwick sample: exercises the syntax roles in the palette spec."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

MAX_RETRIES = 3
GREETING_PATTERN = re.compile(r"^hello,\s+(\w+)!$")


class Mood(Enum):
    CALM = 1
    STORMY = 2


class Greeter(Protocol):
    def greet(self, name: str) -> str: ...


@dataclass
class Developer:
    """A developer who says hello."""

    name: str
    mood: Mood = Mood.CALM

    def greet(self, name: str) -> str:
        # Escape sequences and f-strings
        message = f"Hello, {name}!\n\tFrom {self.name}"
        if self.mood is Mood.STORMY and not name:
            raise ValueError("no one to greet")
        return message


def say_hello(greeter: Greeter, names: list[str]) -> int:
    count = 0.0
    for attempt in range(MAX_RETRIES):
        for name in names:
            print(greeter.greet(name))
            count += 1 + attempt * 0.5
    return int(count)


if __name__ == "__main__":
    say_hello(Developer("Ada"), ["world", "Deepwick"])
