from logging import Logger
from argparse import ArgumentParser, REMAINDER
from src.lppm.package_manager import PackageManager
from src.lppm.error import BadPackage, BadPackageFormat


def program_name_check(program_name, logger) -> None:
    if program_name is None:
        logger.critical("You must provide a package name!")
        raise BadPackage("No pacakage name provided!")
    elif '/' not in program_name:
        logger.critical("Wrong Format! Example: owner/repo")
        raise BadPackageFormat("Invalid package name format")
    elif len(program_name.split('/')) != 2:
        logger.critical("Wrong Format! Example: owner/repo")
        raise BadPackageFormat("Invalid package name format")


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
        "program_arguments",
        nargs=REMAINDER,
        help="Additional arguments to pass to the program when using the 'run' command"
    )

    args = argument_parser.parse_args()
    command = args.command
    package_name = args.package_name
    program_arguments = args.program_arguments

    if command == "install":
        program_name_check(package_name, logger)
        package_manager.install_program(package_name)
        logger.debug(f"Installed program {package_name}")
    elif command == "uninstall":
        program_name_check(package_name, logger)
        package_manager.uninstall_program(package_name)
        logger.debug(f"Uninstalled program {package_name}")
    elif command == "update":
        if package_name:
            program_name_check(package_name, logger)
            package_manager.update(package_name)
            logger.debug(f"Updated program {package_name}")
        else:
            package_manager.update()
            logger.debug("Mass updated programs")
    elif command == "list":
        package_manager.list_programs()
        logger.debug("Listed installed programs")
    elif command == "run":
        program_name_check(package_name, logger)
        logger.debug(f"Running {package_name} with arguments {program_arguments}")
        package_manager.run_program(
            package_name, program_arguments
        )
    elif command == "open":
        program_name_check(package_name, logger)
        package_manager.open_program(package_name)
        logger.debug(f"Opened file location for {package_name}")