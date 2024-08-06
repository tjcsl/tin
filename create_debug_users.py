#!/usr/bin/env python3

from __future__ import annotations

import os
from getpass import getpass

import django

import tin.tests.create_users as users


def main():
    # hide user password from showing on terminal
    password = getpass("Enter password for all users: ")
    users.add_users_to_database(password=password, verbose=True)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tin.settings")
    django.setup()
    main()
