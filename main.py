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
    def __init__(self, github_token: str):
        auth = Auth.Token(github_token)
        try:
            self.github = Github(auth=auth)
        except Exception as e:
            self.logger.critical(f"Failed to initialize GitHub client: {e}")
            raise
        self.logger = getLogger("LPPM")
        self.package_manager = PackageManager(self.github, self.logger)

    def execute(self):
        parse_args(self.package_manager, self.logger)


def main():
    load_dotenv()
    basicConfig(level="INFO", format="[%(name)s] %(levelname)s: %(message)s")
    token = environ.get("TOKEN")
    if not token:
        raise RuntimeError("TOKEN not found in environment.")

    lppm = LapisPersonPackageManager(token)
    lppm.execute()


if __name__ == "__main__":
    main()
