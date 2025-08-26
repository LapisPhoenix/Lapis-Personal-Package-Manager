from subprocess import run, CompletedProcess
from os import name as osname
from venv import create as vcreate
from pathlib import Path


class VirtualEnvironment:
    def __init__(self, environment_path: Path):
        self.environment_path = environment_path
    
    def create(self) -> None:
        vcreate(self.environment_path, with_pip=True)

    def pip(self, command: list[str], check: bool = True, root: str | None = None) -> CompletedProcess:
        pip_bin = self.environment_path / "bin" / "pip" if osname != "nt" else self.environment_path / "Scripts" / "pip.exe"
        return run([str(pip_bin.resolve().absolute()), *command], check=check, cwd=root)

    def python(self, command: list[str], check: bool = True, root: str | None = None) -> CompletedProcess:
        python_bin = self.environment_path / "bin" / "python" if osname != "nt" else self.environment_path / "Scripts" / "python.exe"
        return run([str(python_bin.resolve().absolute()), *command], check=check, cwd=root)
