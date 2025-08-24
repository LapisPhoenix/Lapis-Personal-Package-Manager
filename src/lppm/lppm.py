from os import environ
from github import Auth
from github import Github
from github import GithubIntegration
from dotenv import load_dotenv
from package.file_handler import FileHandler


class LapisPersonPackageManager:
    def __init__(self):
        auth = Auth.Token(environ["TOKEN"])
        self.github = Github(auth=auth)
        self.file_handler = FileHandler(self.github)


if __name__ == "__main__":
    def main() -> None:
        package_manager = LapisPersonPackageManager()
        print(package_manager.file_handler.update())

    load_dotenv()
    main()
