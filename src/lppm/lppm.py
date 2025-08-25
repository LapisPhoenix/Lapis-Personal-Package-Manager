from os import environ
from sys import exit as sexit
from argparse import ArgumentParser
from github import Auth
from github import Github
from dotenv import load_dotenv
from package.package_manager import PackageManager


class LapisPersonPackageManager:
    def __init__(self):
        auth = Auth.Token(environ["TOKEN"])
        self.github = Github(auth=auth)
        self.package_manager = PackageManager(self.github)


def main() -> None:
    load_dotenv()
    package_manager = LapisPersonPackageManager()
    argument_parser = ArgumentParser(
        description="Lapis' Personal Package Manager",
        prog="xyz"
    )
    argument_parser.add_argument(
        "command",
        choices=["install", "uninstall", "list"],
        help="The command to execute: 'install', 'uninstall', or 'list'"
    )
    argument_parser.add_argument(
        "package_name",
        nargs="?",
        help="The package name to install or uninstall (required for 'install' and 'uninstall'). Eg: Jhonny/Doie"
    )

    args = argument_parser.parse_args()

    if args.command == "install":
        if args.package_name is None:
            print("[-] You must provide a package to install!")
            return
        package_manager.package_manager.install_package(args.package_name)
    elif args.command == "uninstall":
        if args.package_name is None:
            print("[-] You must provide a package to uninstall!")
            return
        package_manager.package_manager.remove_package(args.package_name)
    elif args.command == "list":
        if args.package_name is not None:
            print("[-] The 'list' command does not accept a package name!")
            return
        packages = package_manager.package_manager.installed_packages()
        for package in packages:
            lines = [
                "======================",
                f"{package.name.title()}",
                f"  > Commit: {package.commit}",
                f"  > Source: {package.url}",
                f"  > Installed: {package.path}",
                "======================"
            ]
            print('\n'.join(lines))


if __name__ == "__main__":
    main()
