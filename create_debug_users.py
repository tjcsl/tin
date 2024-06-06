#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

if not __file__.endswith("shell.py"):
    subprocess.call(
        [
            sys.executable,
            Path(__file__).parent / "manage.py",
            "shell",
            "-c",
            Path(__file__).read_text(encoding="utf-8"),
        ]
    )
    exit()


from tin.tests.create_users import add_users_to_database

password = input("Enter password for all users: ")

add_users_to_database(password=password, verbose=True)
