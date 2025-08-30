from os import environ
from logging import getLogger, basicConfig
from dotenv import load_dotenv
from github import Auth
from github import Github
from src.lppm.argument_handler import parse_args
from src.lppm.package_manager import PackageManager


class LapisPersonPackageManager:
    """
    Lapis' Personal Package Manager is a small CLI tool that helps simplify the process of installing and using my scripts.
    """
    def __init__(self):
        auth = Auth.Token(environ["TOKEN"])
        self.github = Github(auth=auth)
        basicConfig(
            format="[%(name)s] %(levelname)s: %(message)s"
        )
        self.logger = getLogger("LPPM")
        self.package_manager = PackageManager(self.github, self.logger)

    def execute(self):
        parse_args(self.package_manager, self.logger)


def main():
    load_dotenv()
    lppm = LapisPersonPackageManager()
    lppm.execute()


if __name__ == "__main__":
    main()
