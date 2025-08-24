from pathlib import Path
from os.path import expanduser
from json import load, dump
from base64 import b64decode
from github import Github, Repository
from github.Comparison import Comparison
from .package import Package


# TODO: Allow user to install to different locations.
class FileHandler:
    def __init__(self, github: Github):
        self.github = github

        user_path = Path(expanduser("~"))
        self.installation_folder = user_path / ".lapis_packages"
        self.installed_file = self.installation_folder / "install.json"

        if not self.installation_folder.exists():
            self.installation_folder.mkdir()

    def installed_packages(self) -> list[Package]:
        packages = []

        if not self.installed_file.exists():
            try:
                with open(self.installed_file, "w") as file:
                    dump([], file, indent=2)
            except Exception as e:
                raise RuntimeError(f"Failed to create {self.installed_file}: {e}")
            return packages

        try:
            with open(self.installed_file, "r") as file:
                data = load(file)
                for pkg in data:
                    try:
                        packages.append(Package(pkg["name"], pkg["commit"], pkg["url"], Path(pkg["path"])))
                    except KeyError as e:
                        print(f"Skipping invalid package entry, missing key: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to read {self.installed_file}: {e}")

        return packages

    def download_new_files(self, package: Package, repo: Repository, comparison: Comparison) -> None:
        installation_directory = package.path

        for file in comparison.files:
            file_path = installation_directory / file.filename
            if file.status == "removed":
                if file_path.is_dir():
                    file_path.rmdir()
                else:
                    file_path.unlink()
                continue

            # TODO: handle when a directory is updated
            # TODO: handle when a file is renamed
            with open(file_path, "wb") as f:
                f.write(b64decode(repo.get_contents(file.filename).content))

    def update(self) -> list[Package]:
        """
        Updates all locally installed packages.
        :param package: Returns a list of updated packages. Empty if none
        were updated.
        :return:
        """
        packages = self.installed_packages()
        updated = []

        for package in packages:
            commit = package.commit
            repo = self.github.get_repo(package.name)
            latest_commit = repo.get_commits()[0]
            if commit == latest_commit.sha:
                continue
            
            comparison = repo.compare(commit, latest_commit.sha)
            