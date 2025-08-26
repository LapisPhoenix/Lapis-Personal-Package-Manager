from subprocess import run, CompletedProcess
from os import name as osname
from venv import create as vcreate
from pathlib import Path


class VirtualEnvironment:
    """
    A virtual environment helper class.
    """
    def __init__(self, environment_path: Path):
        self.environment_path = environment_path

    def create(self) -> None:
        """
        Create the virtual environment.
        This will fail if it has already been created.
        """
        vcreate(self.environment_path, with_pip=True)

    def pip(
        self, command: list[str], check: bool = True, root: str | None = None
    ) -> CompletedProcess:
        """
        Run a pip command in the virtual environment.
        """
        pip_bin = (
            self.environment_path / "bin" / "pip"
            if osname != "nt"
            else self.environment_path / "Scripts" / "pip.exe"
        )
        return run([str(pip_bin.resolve().absolute()), *command], check=check, cwd=root)

    def python(
        self, command: list[str], check: bool = True, root: str | None = None
    ) -> CompletedProcess:
        """
        Run a python command in  the virtual environment.
        """
        python_bin = (
            self.environment_path / "bin" / "python"
            if osname != "nt"
            else self.environment_path / "Scripts" / "python.exe"
        )
        return run(
            [str(python_bin.resolve().absolute()), *command], check=check, cwd=root
        )
