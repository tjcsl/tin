import logging
import os
import subprocess
from collections.abc import Iterable

from django.conf import settings
from django.db import models
from django.urls import reverse

from ... import sandboxing

logger = logging.getLogger(__name__)


class VenvCreationError(Exception):
    pass


class VenvExistsError(VenvCreationError):
    pass


class VenvQuerySet(models.query.QuerySet):
    def filter_visible(self, user):
        """Only superusers and teachers can see Venvs"""
        if user.is_superuser or user.is_teacher:
            return self.all()
        return self.none()

    def filter_editable(self, user):
        """Only admin can edit a venv"""
        if user.is_superuser:
            return self.all()
        return self.none()


class Venv(models.Model):
    """A Python Virtual Environment."""

    name = models.CharField(max_length=255, null=False, blank=False)

    fully_created = models.BooleanField(null=False)

    installing_packages = models.BooleanField(default=False, null=False)

    OUTPUT_MAX_LENGTH = 16 * 1024
    package_installation_output = models.CharField(
        max_length=OUTPUT_MAX_LENGTH, default="", null=False, blank=True
    )

    language = models.ForeignKey(
        "assignments.Language",
        on_delete=models.CASCADE,
        related_name="venv_set",
        null=False,
    )

    objects = VenvQuerySet.as_manager()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Virtualenv: {self.name}>"

    def get_absolute_url(self):
        return reverse("venvs:show", args=[self.id])

    @property
    def path(self):
        return os.path.join(settings.MEDIA_ROOT, "venvs", f"venv-{self.id}")

    def get_activation_env(self) -> dict[str, str]:
        """Returns information about the virtual environment.

        Returns:
            A dictionary with the keys

            * ``VIRTUAL_ENV``: the path to the virtual environment
            * ``PATH``: the modified ``$PATH`` variable
        """
        venv_path = self.path

        return {
            "VIRTUAL_ENV": venv_path,
            "PATH": os.path.join(venv_path, "bin") + os.pathsep + os.environ["PATH"],
        }

    def list_packages(self) -> list[list[str]] | None:
        """List all packages in a virtual environment.

        .. admonition:: TODO

            This parses the output from ``pip freeze``.
            Ideally, there should be a better way to do this.
        """
        env = dict(os.environ)
        env.update(self.get_activation_env())

        args = sandboxing.get_assignment_sandbox_args(
            ["pip", "freeze"],
            network_access=False,
            read_only=[self.path],
            extra_firejail_args=[f"--rlimit-fsize={settings.VENV_FILE_SIZE_LIMIT}"],
        )

        try:
            res = subprocess.run(
                args,
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as e:
            logger.error("Cannot run processes: %s", e)
            raise FileNotFoundError from e

        if res.returncode != 0 or res.stderr:
            return None
        else:
            pkgs = []
            for line in res.stdout.splitlines():
                pkgs.append(line.split("==", 1))

            return pkgs

    def install_packages(self, pkgs: Iterable[str]) -> None:
        """Install packages"""
        self.installing_packages = True
        self.save()

        try:
            env = dict(os.environ)
            env.update(self.get_activation_env())

            args = sandboxing.get_assignment_sandbox_args(
                ["pip", "install", "--upgrade", "--", *pkgs],
                network_access=True,
                whitelist=[self.path],
                extra_firejail_args=[f"--rlimit-fsize={settings.VENV_FILE_SIZE_LIMIT}"],
            )

            try:
                res = subprocess.run(
                    args,
                    check=False,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except FileNotFoundError as e:
                logger.error("Cannot run processes: %s", e)
                raise FileNotFoundError from e

            try:
                self.package_installation_output = res.stdout.decode()[-self.OUTPUT_MAX_LENGTH :]
            except UnicodeDecodeError:
                self.package_installation_output = str(res.stdout)[-self.OUTPUT_MAX_LENGTH :]
        finally:
            self.installing_packages = False
            self.save()
