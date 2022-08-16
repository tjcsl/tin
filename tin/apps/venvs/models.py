import os
import subprocess
import sys

from django.conf import settings
from django.db import IntegrityError, models

from ... import sandboxing

# Create your models here.


class VirtualenvCreationError(Exception):
    pass


class VirtualenvExistsError(VirtualenvCreationError):
    pass


class VenvQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(assignment__course__teacher=user).distinct()

    def filter_editable(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(assignment__course__teacher=user).distinct()


class Virtualenv(models.Model):
    objects = VenvQuerySet.as_manager()

    assignment = models.OneToOneField(
        "assignments.Assignment", on_delete=models.CASCADE, related_name="venv", null=False
    )

    fully_created = models.BooleanField(null=False)

    installing_packages = models.BooleanField(default=False, null=False)

    package_installation_output = models.CharField(
        max_length=16 * 1024, default="", null=False, blank=True
    )

    def get_full_path(self):
        assert self.assignment.grader_file.name
        return os.path.join(
            settings.MEDIA_ROOT, os.path.dirname(self.assignment.grader_file.name), "venv"
        )

    @classmethod
    def create_venv_for_assignment(cls, assignment):
        try:
            venv = cls.objects.create(assignment=assignment, fully_created=False)
        except IntegrityError:
            raise VirtualenvExistsError

        success = False

        try:
            if os.path.exists(venv.get_full_path()):
                raise VirtualenvCreationError(
                    "Virtualenv directory for assignment #{} exists".format(assignment.id)
                )

            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "virtualenv",
                    "-p",
                    settings.SUBMISSION_PYTHON,
                    "--",
                    venv.get_full_path(),
                ],
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            if res.returncode != 0:
                raise VirtualenvCreationError(
                    "Error creating virtual environment (return code {}): {}".format(
                        res.returncode, res.stdout
                    )
                )

            venv.fully_created = True
            venv.save()
            success = True
        finally:
            if not success:
                venv.delete()

        return venv

    def get_activation_env(self):
        venv_path = self.get_full_path()

        return {
            "VIRTUAL_ENV": venv_path,
            "PATH": os.path.join(venv_path, "bin") + os.pathsep + os.environ["PATH"],
        }

    def list_packages(self):
        env = dict(os.environ)
        env.update(self.get_activation_env())

        args = sandboxing.get_assignment_sandbox_args(
            ["pip", "freeze"],
            network_access=False,
            read_only=[self.get_full_path()],
            extra_firejail_args=["--rlimit-fsize=209715200"],
        )

        res = subprocess.run(
            args,
            check=False,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        if res.returncode != 0 or res.stderr:
            return None
        else:
            pkgs = []
            for line in res.stdout.splitlines():
                pkgs.append(line.split("==", 1))

            return pkgs

    def install_packages(self, pkgs):
        self.installing_packages = True
        self.save()

        try:
            env = dict(os.environ)
            env.update(self.get_activation_env())

            args = sandboxing.get_assignment_sandbox_args(
                ["pip", "install", "--upgrade", "--", *pkgs],
                network_access=True,
                whitelist=[self.get_full_path()],
                extra_firejail_args=["--rlimit-fsize=209715200"],
            )

            res = subprocess.run(
                args,
                check=False,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            try:
                self.package_installation_output = res.stdout.decode()[-16 * 1024:]
            except UnicodeDecodeError:
                self.package_installation_output = str(res.stdout)[-16 * 1024:]
        finally:
            self.installing_packages = False
            self.save()
