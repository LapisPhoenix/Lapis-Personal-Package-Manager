from sys import exit as sexit
from logging import Logger
from argparse import ArgumentParser, REMAINDER
from src.lppm.package_manager import PackageManager


def program_name_check(program_name, logger) -> None:
    if program_name is None:
        logger.critical("You must provide a package name!")
        sexit(1)
    elif '/' not in program_name:
        logger.critical("Wrong Format! Example: LapisPhoenix/Lapis-Personal-Package-Manager")
        sexit(1)


def parse_args(package_manager: PackageManager, logger: Logger) -> None:
    """
    Parses the arguments given and runs the package manager.
    """
    argument_parser = ArgumentParser(
        description="Lapis' Personal Package Manager", prog="lppm"
    )
    argument_parser.add_argument(
        "command",
        choices=["install", "update", "uninstall", "list", "run", "open"],
        help="The command to execute: 'install', 'update', 'uninstall', 'list', 'run', or 'open'.",
    )
    argument_parser.add_argument(
        "package_name",
        nargs="?",
        help="The package name to install or uninstall (required for 'install', 'run', 'open' and 'uninstall'). Eg: Jhonny/Doie",
    )
    argument_parser.add_argument(
        "program_arguments", nargs=REMAINDER, help="Arguments to pass to the program"
    )

    args = argument_parser.parse_args()
    command = args.command
    package_name = args.package_name
    program_arguments = args.program_arguments

    if command == "install":
        program_name_check(package_name, logger)
        package_manager.install_program(package_name)
    elif command == "uninstall":
        program_name_check(package_name, logger)
        package_manager.uninstall_program(package_name)
    elif command == "update":
        if package_name:
            program_name_check(package_name, logger)
            package_manager.update(package_name)
            sexit(0)
        package_manager.update()
    elif command == "list":
        package_manager.list_programs()
    elif command == "run":
        program_name_check(package_name, logger)
        package_manager.run_program(
            package_name, program_arguments
        )
    elif command == "open":
        program_name_check(package_name, logger)
        package_manager.open_program(package_name)
    sexit(0)
