from __future__ import annotations

from getpass import getpass

from django.core.management.base import BaseCommand, no_translations

import tin.tests.create_users as users


class Command(BaseCommand):
    help = "Create users for debugging"

    def add_arguments(self, parser):
        parser.add_argument("--noinput", action="store_true", help="Do not ask for password")
        parser.add_argument("--force", action="store_true", help="Force creation of users")

    @no_translations
    def handle(self, *args, **options):
        if not options["noinput"]:
            pwd = getpass("Enter password for all users: ")
        else:
            pwd = "jasongrace"

        users.add_users_to_database(
            password=pwd,
            verbose=options["verbosity"] > 0,
            force=options["force"],
        )
