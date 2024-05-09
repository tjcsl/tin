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

from tin.apps.users.models import User

password = input("Enter password for all users: ")

# fmt: off
users = [
    #[username, id, full_name, first_name, last_name, email, is_teacher, is_student, is_staff, is_superuser]
    ["2020jbeutner", 33538, "John Beutner", "John", "Beutner", "2020jbeutner@tjhsst.edu", False, True, False, False],
    ["2020fouzhins", 33797, "Theo Ouzhinski", "Theo", "Ouzhinski", "2020fouzhins@tjhsst.edu", False, True, False, False],
    ["2024kshankar", 1000891, "Krishnan Shankar", "Krishnan", "Shankar", "2024kshankar@tjhsst.edu", False, True, False, False],
    ["pcgabor", None, "Peter Gabor", "Peter", "Gabor", "pcgabor@fcps.edu", True, False, False, False],
    ["admin", None, "Admin", "Admin", "Admin", "admin@example.com", False, False, True, True],
]
# fmt: on

for user_info in users:
    print("Creating user {}".format(user_info[0]))
    if user_info[1] is None:
        user = User.objects.get_or_create(username=user_info[0])[0]
    else:
        user = User.objects.get_or_create(id=user_info[1])[0]
        user.username = user_info[0]

    user.full_name = user_info[2]
    user.first_name = user_info[3]
    user.last_name = user_info[4]
    user.email = user_info[5]
    user.is_teacher = user_info[6]
    user.is_student = user_info[7]
    user.is_staff = user_info[8]
    user.is_superuser = user_info[9]
    user.set_password(password)
    user.save()
