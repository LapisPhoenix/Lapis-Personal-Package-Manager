from sys import exit as sexit
from argparse import ArgumentParser, REMAINDER


def parse_args(package_manager) -> None:
    argument_parser = ArgumentParser(
        description="Lapis' Personal Package Manager", prog="lppm"
    )
    argument_parser.add_argument(
        "command",
        choices=["install", "uninstall", "list", "run", "update"],
        help="The command to execute: 'install', 'uninstall', or 'list'",
    )
    argument_parser.add_argument(
        "package_name",
        nargs="?",
        help="The package name to install or uninstall (required for 'install' and 'uninstall'). Eg: Jhonny/Doie",
    )
    argument_parser.add_argument(
        "program_arguments", nargs=REMAINDER, help="Arguments to pass to the program"
    )

    args = argument_parser.parse_args()

    if args.command == "install":
        if args.package_name is None:
            print("You must provide a package to install!")
            sexit(1)
        package_manager.install_program(args.package_name)
        print(f"Installed {args.package_name}!")
    elif args.command == "uninstall":
        if args.package_name is None:
            print("[-] You must provide a package to uninstall!")
            sexit(1)
        package_manager.uninstall_program(args.package_name)
        print(f"Uninstalled {args.package_name}!")
    elif args.command == "update":
        if args.package_name:
            package_manager.update(args.package_name)
        else:
            package_manager.update()
    elif args.command == "list":
        package_manager.list_programs()
    elif args.command == "run":
        package_manager.run_program(
            args.package_name, args.program_arguments
        )
    sexit(0)
