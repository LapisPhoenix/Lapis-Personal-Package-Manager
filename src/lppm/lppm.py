from os import environ
from sys import exit as sexit
from argparse import ArgumentParser, REMAINDER
from github import Auth
from github import Github
from dotenv import load_dotenv
# from package.package_manager import PackageManager
from src.lppm.package.package_manager import PackageManager


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
        prog="lppm"
    )
    argument_parser.add_argument(
        "command",
        choices=["install", "uninstall", "list", "run"],
        help="The command to execute: 'install', 'uninstall', or 'list'"
    )
    argument_parser.add_argument(
        "package_name",
        nargs="?",
        help="The package name to install or uninstall (required for 'install' and 'uninstall'). Eg: Jhonny/Doie"
    )
    argument_parser.add_argument(
        "program_arguments",
        nargs=REMAINDER,
        help="Arguments to pass to the program"
    )

    args = argument_parser.parse_args()

    if args.command == "install":
        if args.package_name is None:
            print("You must provide a package to install!")
            sexit(1)
        package_manager.package_manager.install_program(args.package_name)
    elif args.command == "uninstall":
        if args.package_name is None:
            print("[-] You must provide a package to uninstall!")
            sexit(1)
        package_manager.package_manager.uninstall_program(args.package_name)
    elif args.command == "list":
        package_manager.package_manager.list_programs()
    elif args.command == "run":
        package_manager.package_manager.run_program(args.package_name, args.program_arguments)
    sexit(0)


if __name__ == "__main__":
    main()
