#!/usr/bin/env python3
import os
import subprocess
import sys

if not __file__.endswith("shell.py"):
    subprocess.call(
        [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "manage.py"),
            "shell",
            "-c",
            open(__file__).read(),
        ]
    )
    exit()



from tin.tests.create_users import make_users

password = input("Enter password for all users: ")

make_users(password)
