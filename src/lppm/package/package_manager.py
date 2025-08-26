from pathlib import Path
from os.path import expanduser
from shutil import rmtree
from sqlite3 import connect
from subprocess import run, DEVNULL
from github import Github
# from environment.virtual import VirtualEnvironment
from src.lppm.environment.virtual import VirtualEnvironment


class PackageManager:
    def __init__(self, github: Github):
        self.github = github
        user_path = Path(expanduser("~"))
        self.installation_folder = user_path / ".lapis_packages"
        self.installed_database = self.installation_folder / "applications.db"
        self.virtual_environments = self.installation_folder / "environments"
        self._verify_file_integrity(folders=[self.installation_folder, self.virtual_environments])

        self.connection = connect(self.installed_database)
        self.cursor = self.connection.cursor()
        self._database_setup()

    def run_program(self, name: str, *args) -> None:
        self.cursor.execute("SELECT root, environment FROM programs WHERE name=?", (name,))
        program = self.cursor.fetchone()

        if not program:
            print(f"{name} not found!")
            return
        
        program_path = Path(program[0])
        env_path = Path(program[1])
        main_file = program_path / "main.py"
        
        venv = VirtualEnvironment(env_path)
        command = [str(main_file)]
        command.extend(map(str, args))

        venv.python(command, False, str(program_path))

    def update(self, program: str | None = None) -> None:
        if program:
            self.cursor.execute("SELECT commit_hash, root, environment FROM programs WHERE name=?", (program,))
            program_info = self.cursor.fetchone()

            if not program_info:
                print(f"{program} not found!")
                return
            repo = self.github.get_repo(program)
            latest_commit_hash = repo.get_commits()[0].sha
            local_commit_hash = program_info[0]

            if latest_commit_hash == local_commit_hash:
                print(f"{program} already up to date!")
                return
            
            program_root = program_info[1]
            environment = program_info[2]
            venv = VirtualEnvironment(environment)

            command = [
                "git", "pull", "origin", "main"
            ]

            run(command, cwd=program_root, check=True)

            venv.pip(["install", "-r", program_root + "/requirements.txt"])

    def install_program(self, program_name: str) -> None:
        # Verify it isnt already installed
        self.cursor.execute("SELECT * FROM programs WHERE name=?", (program_name,))
        found = self.cursor.fetchone()

        if found:
            print(f"[Install]  Already found {program_name} installed!")
            return

        # Create needed paths
        program_root_path = self.installation_folder / program_name.split("/")[1]
        environment_path = self.virtual_environments / program_name.split("/")[1]
        environment_path.mkdir()
        
        # Clone the Repo
        repo = self.github.get_repo(program_name)
        command = [
            "git", "clone", repo.svn_url, program_root_path
        ]
        run(command, stdout=DEVNULL, stderr=DEVNULL, check=True)

        # File entry point & requirements
        main_file = program_root_path / "main.py"
        requirements_file = program_root_path / "requirements.txt"

        if not main_file.exists():
            print("Unable to locate entry point! Exiting!!")
            return
        elif not requirements_file.exists():
            print("Unable to find requirements! Exiting!!")
            return
        
        # Create Environment for Program
        venv = VirtualEnvironment(environment_path)
        venv.create()
        venv.pip(["install", "-r", str(requirements_file)])
        
        # Add program to database
        self.cursor.execute("INSERT INTO programs VALUES (?, ?, ?, ?, ?)", (program_name, repo.get_commits()[0].sha, repo.svn_url, str(program_root_path.resolve().absolute()), str(environment_path.resolve().absolute())))
        self.connection.commit()
    
    def uninstall_program(self, program_name: str) -> None:
        self.cursor.execute("SELECT root, environment FROM programs WHERE name=?", (program_name,))
        program = self.cursor.fetchone()

        if not program:
            print(f"{program_name} not found!")
            return

        installed_path = program[0]
        environment_path = program[1]
        
        rmtree(installed_path)
        rmtree(environment_path)
        self.cursor.execute("DELETE FROM programs WHERE name=?", (program_name,))
        self.connection.commit()

    def list_programs(self) -> None:
        self.cursor.execute("SELECT * FROM programs")
        programs = self.cursor.fetchall()

        print(f"{'Name':<40} {'Commit':<40} {'URL':<40}")
        print('-' * 120)

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
        self.connection.execute("CREATE TABLE IF NOT EXISTS programs (name, commit_hash, url, root, environment)")