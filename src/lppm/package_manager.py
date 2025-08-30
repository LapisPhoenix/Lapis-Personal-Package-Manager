from pathlib import Path
from time import perf_counter
from logging import Logger
from platform import system
from os.path import expanduser, abspath
from shutil import rmtree
from sqlite3 import connect
from subprocess import run, DEVNULL, CalledProcessError
from github import Github
from src.lppm.virtual_environment import VirtualEnvironment


class PackageManager:
    """
    Handles the internal logic.
    """

    def __init__(self, github: Github, logger: Logger):
        self.logger = logger
        self.github = github
        user_path = Path(expanduser("~"))
        self.installation_folder = user_path / ".lapis_packages"
        self.installed_database = self.installation_folder / "applications.db"
        self.virtual_environments = self.installation_folder / "environments"
        self._verify_file_integrity(
            folders=[self.installation_folder, self.virtual_environments]
        )

        self.connection = connect(self.installed_database)
        self.cursor = self.connection.cursor()
        self._database_setup()

    def __del__(self):
        self.connection.close()

    def open_program(self, name: str) -> None:
        """
        Open the file location of where a program has been installed.
        """
        self.cursor.execute(
            "SELECT root FROM programs WHERE name=?", (name,)
        )
        program_root = self.cursor.fetchone()

        if not program_root:
            self.logger.critical(f"{name} not found!")
            return
        
        program_root = program_root[0]
        failed = self._open_file_manager(program_root)

        if failed:
            self.logger.info(f"Program Directory: {program_root}")

    def run_program(self, name: str, args) -> None:
        """
        Runs a installed program. Chroots into the directory where its installed.
        """
        self.cursor.execute(
            "SELECT root, environment FROM programs WHERE name=?", (name,)
        )
        program = self.cursor.fetchone()

        if not program:
            self.logger.critical(f"{name} not found!")
            return

        program_path = Path(program[0]).resolve()
        env_path = Path(program[1]).resolve()

        if not str(program_path).startswith(str(self.installation_folder.resolve())):
            self.logger.critical(f"Untrusted Program Detected! {name}")
            exit(1)

        main_file = program_path / "main.py"

        venv = VirtualEnvironment(env_path)
        command = [str(main_file)]
        if args is not None:
            command.extend(map(str, args))

        venv.python(command, False, str(program_path))

    def update(self, program_name: str | None = None) -> None:
        """
        Update either a specific program or all programs at once.
        """
        start_time = perf_counter()
        if program_name:
            self.cursor.execute(
                "SELECT commit_hash, root, environment FROM programs WHERE name=?",
                (program_name,),
            )
            program_info = self.cursor.fetchone()

            if not program_info:
                self.logger.critical(f"{program_name} not found!")
                return
            repo = self.github.get_repo(program_name)
            latest_commit_hash = repo.get_commits()[0].sha
            local_commit_hash = program_info[0]

            if latest_commit_hash == local_commit_hash:
                self.logger.info(f"{program_name} is already up to date!")
                return

            program_root = Path(program_info[1]).resolve()
            environment = Path(program_info[2]).resolve()
            venv = VirtualEnvironment(environment)

            command = ["git", "pull", "origin", "main"]

            try:
                run(command, stdout=DEVNULL, stderr=DEVNULL, check=True)
            except CalledProcessError as e:
                self.logger.critical(f"Failed to clone repository {program_name}: {e}")
                return

            venv.pip(["install", "-r", str(program_root / "requirements.txt")])
            self.logger.info(f"Updated {program_name} in {perf_counter() - start_time:.2f} seconds.")
            return

        self.cursor.execute("SELECT name, commit_hash, root, environment FROM programs")
        info = self.cursor.fetchall()

        programs = 0
        for installed_program in info:
            name, commit, root, env = installed_program
            root = Path(root).resolve()
            repo = self.github.get_repo(name)
            latest_commit_hash = repo.get_commits()[0].sha
            local_commit_hash = commit

            if latest_commit_hash == local_commit_hash:
                self.logger.info(f"Ignoring {name}...")
                continue

            venv = VirtualEnvironment(Path(env))

            command = ["git", "pull", "origin", "main"]

            try:
                run(command, stdout=DEVNULL, stderr=DEVNULL, check=True)
            except CalledProcessError as e:
                self.logger.critical(f"Failed to clone repository {program_name}: {e}")
                return

            venv.pip(["install", "-r", str(root / "requirements.txt")])
            self.cursor.execute(
                "UPDATE programs SET commit_hash=? WHERE name=?",
                (latest_commit_hash, name),
            )
            programs += 1
        self.connection.commit()
        self.logger.info(f"Updated {programs} program{'s' if programs != 1 else None} in {perf_counter() - start_time:.2f} seconds.")

    def install_program(self, program_name: str) -> None:
        """
        Install a program/repo. Expects a `main.py` and `requirements.txt` file in the root directory.
        """
        start_time = perf_counter()
        # Verify it isnt already installed
        self.cursor.execute("SELECT * FROM programs WHERE name=?", (program_name,))
        found = self.cursor.fetchone()

        if found:
            self.logger.info(f"Already found {program_name} installed!")
            return

        # Create needed paths
        program_root_path = self.installation_folder / program_name.split("/")[1]
        environment_path = self.virtual_environments / program_name.split("/")[1]
        program_root_path.mkdir(exist_ok=True)
        environment_path.mkdir(exist_ok=True)

        # Clone the Repo
        repo = self.github.get_repo(program_name)
        command = ["git", "clone", repo.svn_url, program_root_path]
        try:
            run(command, stdout=DEVNULL, stderr=DEVNULL, check=True)
        except CalledProcessError as e:
            self.logger.critical(f"Failed to clone repository {program_name}: {e}")
            return

        # File entry point & requirements
        main_file = program_root_path / "main.py"
        requirements_file = program_root_path / "requirements.txt"

        if not main_file.exists():
            self.logger.critical("Unable to locate entry point! Exiting!!")
            return
        elif not requirements_file.exists():
            self.logger.critical("Unable to find requirements! Exiting!!")
            return

        # Create Environment for Program
        venv = VirtualEnvironment(environment_path)
        venv.create()
        venv.pip(["install", "-r", str(requirements_file)])

        # Add program to database
        self.cursor.execute(
            "INSERT INTO programs VALUES (?, ?, ?, ?, ?)",
            (
                program_name,
                repo.get_commits()[0].sha,
                repo.svn_url,
                str(program_root_path.resolve().absolute()),
                str(environment_path.resolve().absolute()),
            ),
        )
        self.connection.commit()
        self.logger.info(f"Installed {program_name} in {perf_counter() - start_time:.2f} seconds.")

    def uninstall_program(self, program_name: str) -> None:
        """
        Uninstall a program via it's name.
        """
        start_time = perf_counter()
        self.cursor.execute(
            "SELECT root, environment FROM programs WHERE name=?", (program_name,)
        )
        program = self.cursor.fetchone()

        if not program:
            # Attempt to find it in the files
            installed_path = self.installation_folder / program_name.split("/")[1]
            environment_path = self.virtual_environments / program_name.split("/")[1]
        else:
            installed_path = program[0]
            environment_path = program[1]

        rmtree(installed_path, ignore_errors=True)
        rmtree(environment_path, ignore_errors=True)
        self.cursor.execute("DELETE FROM programs WHERE name=?", (program_name,))
        self.connection.commit()
        self.logger.info(f"Uninstalled {program_name} in {perf_counter() - start_time:.2f} seconds.")

    def list_programs(self) -> None:
        """
        List all installed programs.
        """
        self.cursor.execute("SELECT * FROM programs")
        programs = self.cursor.fetchall()

        print(f"{'Name':<40} {'Commit':<40} {'URL':<40}")
        print("-" * 120)

        for program in programs:
            name, commit, url, _, _ = program
            print(f"{name:<40} {commit:<40} {url:<40}")

    def _verify_file_integrity(self, folders: list[Path]) -> None:
        """
        Verified that all the folders needed to operate exist.
        """
        for folder in folders:
            if not folder.exists():
                folder.mkdir(parents=True)
            elif not folder.is_dir():
                raise OSError(f"{folder} must be a directory, not a file or otherwise!")

    def _database_setup(self) -> None:
        """
        Creates the programs database table if it doesnt exist.
        """
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS programs (name, commit_hash, url, root, environment)"
        )

    def _open_file_manager(self, path) -> bool:
        """
        Attempts to open the file manager. If it cannot it'll return True, for failed. If it can then False.
        """
        system_name = system()

        if system_name == "Windows":
            # Windows: use explorer
            run(["explorer", abspath(path)])
        elif system_name == "Darwin":
            # macOS: use open
            run(["open", path])
        elif system_name == "Linux":
            # Linux: use xdg-open (most universal)
            run(["xdg-open", path])
        else:
            return True
        return False
