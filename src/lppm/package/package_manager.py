from pathlib import Path
from os.path import expanduser
from subprocess import run, DEVNULL
from json import load, dump, JSONDecodeError
from base64 import b64decode
from dataclasses import asdict
from github import Github, Repository, GithubException
from github.Comparison import Comparison
from .package import Package


# TODO: Allow user to install to different locations.
class PackageManager:
    def __init__(self, github: Github):
        self.github = github

        user_path = Path(expanduser("~"))
        self.installation_folder = user_path / ".lapis_packages"
        self.installed_file = self.installation_folder / "install.json"

        if not self.installation_folder.exists():
            self.installation_folder.mkdir()

    def add_new_package(self, package: Package) -> None:
        installed_packages = []
        package.path = str(package.path)
        if package in self.installed_packages():
            return
        
        if self.installed_file.exists():
            try:
                with open(self.installed_file, "r") as installed_file:
                    installed_packages = load(installed_file)
            except JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {self.installed_file}, initializing as empty: {e}")
                installed_packages = []
            except Exception as e:
                raise RuntimeError(f"Failed to read {self.installed_file}: {e}")
        else:
            try:
                with open(self.installed_file, "w") as file:
                    dump([], file, indent=2)
            except Exception as e:
                raise RuntimeError(f"Failed to create {self.installed_file}: {e}")

        installed_packages.append(asdict(package))

        try:
            with open(self.installed_file, "w") as installed_file:
                dump(installed_packages, installed_file, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to write to {self.installed_file}: {e}")

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

    def update(self) -> tuple[list[Package], list[Package]]:
        """
        Updates all locally installed packages.
        :param package:
        were updated.
        :return: Returns two lists, the first list being the updated packages, and the second list being the failed packages.
        """
        packages = self.installed_packages()
        updated_packages = []
        failed_packages = []

        for package in packages:
            commit = package.commit
            repo = self.github.get_repo(package.name)
            latest_commit = repo.get_commits()[0]
            if commit == latest_commit.sha:
                continue
            
            comparison = repo.compare(commit, latest_commit.sha)
            failed = self._update_local_files(package, repo, comparison)
            if failed == 0:
                updated_packages.append(package)
            else:
                failed_packages.append(package)

        return updated_packages, failed_packages

    def install_package(self, package_name: str) -> Package:
        repo = self.github.get_repo(package_name)
        local_package_name = repo.name.replace("/", "_").lower()
        package_path = self.installation_folder / local_package_name
        package_path.mkdir(exist_ok=True)
        command = [
            "git", "clone", repo.svn_url + ".git", str(package_path)
        ]
        run(command, stdout=DEVNULL, stderr=DEVNULL)
        package = Package(local_package_name, repo.get_commits()[0].sha, repo.svn_url, package_path)
        self.add_new_package(package)
        return package

    def remove_package(self, package_name: str):
        if package_name not in [pkg.name for pkg in self.installed_packages()]:
            return

        package_name = package_name.replace("/", "-")
        installed_packages = self.installed_packages()
        new_packages = [pkg for pkg in installed_packages if pkg.name != package_name]
        print(new_packages)


    def _write_to_file(self, repo, file, file_path) -> None:
        content = repo.get_contents(file.filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(b64decode(content.content))

    def _remove_path(self, file_path) -> None:
        if file_path.is_dir():
            file_path.rmdir()
        if file_path.exists():
            file_path.unlink()

    def _move_path(self, installation_directory, file, file_path) -> None:
        old_path = installation_directory / file.previous_filename
        if old_path.exists():
            old_path.rename(file_path)

    def _update_local_files(self, package: Package, repo: Repository, comparison: Comparison) -> int:
        installation_directory = package.path
        failed = 0

        for file in comparison.files:
            file_path = installation_directory / file.filename
            if file.status in ("added", "changed", "modified"):
                try:
                    self._write_to_file(repo, file, file_path)
                except GithubException as e:
                    print(f"Failed to download {file.filename}: {e.data}")
                    failed += 1
                except OSError as e:
                    print(f"Failed to write {file_path}: {e}")
                    failed += 1
            elif file.status == "removed":
                try:
                    self._remove_path(file_path)
                except OSError as e:
                    print(f"Failed to remove {file_path}: {e}")
                    failed += 1
            elif file.status == "renamed":
                try:
                    self._move_path(installation_directory, file, file_path)
                except OSError as e:
                    print(f"Failed to rename {file.previous_filename} to {file.filename}: {e}")
                    failed += 1
        return failed
