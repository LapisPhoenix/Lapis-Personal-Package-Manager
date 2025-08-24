from dataclasses import dataclass
from pathlib import Path


@dataclass()
class Package:
    """
    Represents a package.
    """
    name: str
    commit: str
    url: str
    path: Path
