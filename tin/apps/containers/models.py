import getpass
import os
import subprocess
import time
from typing import List, Optional
import uuid

from django.db import models
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone

from ..assignments.models import Assignment
from ..submissions.models import Submission

# Create your models here.

class Container(models.Model):
    assignment = models.ForeignKey(Assignment, related_name = "containers", on_delete = models.CASCADE)

    name = models.CharField(max_length = 40, unique = True)

    last_upgrade = models.DateTimeField()
    installed_packages = models.ManyToManyField("ContainerPackage", related_name = "containers")

    @classmethod
    def create_container_for_assignment(cls, assignment: Assignment):
        while True:
            while True:
                name = "tin-{}-{}".format(assignment.id, uuid.uuid1().hex[:10])
                if not cls.objects.filter(name = name):
                    break

            container = cls(assignment = assignment, name = name)

            subprocess.call(["lxc", "launch", "ubuntu:18.04", name])
            container.ensure_started()
            subprocess.call(container.get_run_args(["useradd", "-m", "-u", str(os.getuid()), getpass.getuser()], root = True))
            container.system_upgrade()
            container.install_packages()
            container.ensure_stopped()

            try:
                container.save()
            except IntegrityError:
                subprocess.call(container.delete_command)
            else:
                return container

    def has_task(self) -> bool:
        return hasattr(self, "task")

    def check_running(self) -> bool:
        output = subprocess.getoutput(subprocess.list2cmdline(["lxc", "info", self.name]))
        for line in output.splitlines():
            if line.lower().startswith("status:"):
                return "running" in line.lower()

        return None

    def check_has_ip(self) -> bool:
        output = subprocess.getoutput(subprocess.list2cmdline(["lxc", "info", self.name]))
        for line in output.splitlines():
            if line.lower().strip().startswith("eth0:"):
                return "inet" in line.lower().split()

        return None

    def ensure_started(self):
        if not self.check_running():
            subprocess.call(["lxc", "start", self.name])

        while not self.check_has_ip():
            time.sleep(1)

    def ensure_stopped(self):
        if self.check_running():
            subprocess.call(["lxc", "stop", self.name])

    def install_packages(self):
        self._install_packages(["python3", "firejail"], "apt")
        for package in ContainerPackage.query_for_assignment(self.assignment).exclude(containers = self):
            if self._install_packages([package.name], package.package_type):
                self.installed_packages.add(package)

    def _install_packages(self, package_names: List[str], package_type: str) -> bool:
        install_prefix = {
            "apt": ["apt-get", "-y", "install", "--"],
            "pip": ["pip3", "install", "--"],
        }[package_type]

        args = self.get_run_args([*install_prefix, *package_names], root = True)
        return subprocess.call(args) == 0

    def system_upgrade(self):
        subprocess.run(self.get_run_args(["apt-get", "-y", "update"], root = True))
        subprocess.run(self.get_run_args(["apt-get", "-y", "upgrade"], root = True))

        self.last_upgrade = timezone.now()
        if self.pk is not None:
            self.save(fields=["last_upgrade"])

    def post_task_cleanup(self):
        if timezone.localtime() >= self.assignment.due + datetime.timedelta(days = 2):
            self.ensure_stopped()

    def get_run_args(self, args: List[str], *, root: bool = False) -> List[str]:
        run_args = ["lxc", "exec", self.name, "--"]

        if not root:
            run_args.extend(["sudo", "-u", "#{}".format(os.getuid())])

        run_args.extend(args)

        return run_args

    def mount_path(self, disk_name: str, source: str, dest: str):
        subprocess.call(["lxc", "config", "device", "add", self.name, disk_name, "disk",
                         "source={}".format(source), "path={}".format(dest)])

    def unmount_path(self, disk_name):
        subprocess.call(["lxc", "config", "device", "remove", self.name, disk_name])

    @property
    def delete_command(self) -> List[str]:
        return ["lxc", "delete", self.name]


class ContainerTask(models.Model):
    container = models.OneToOneField(Container, related_name = "task", null = False,
                                     on_delete = models.PROTECT)
    submission = models.OneToOneField(Submission, related_name = "container_task", null = True,
                                      on_delete = models.CASCADE)

    @classmethod
    def create_task_for_submission(cls, submission: Submission):
        """Creates a ContainerTask for the given submission, waiting until a Container is available
        if necessary. If the submission is deleted while waiting, returns None.

        Args:
            submission: The submission to create a ContainerTask for.

        Returns:
            Optional[ContainerTask]: The created ContainerTask, or None if the submission was deleted.

        """
        submission_id = submission.id
        assignment = submission.assignment

        while True:
            for container in assignment.containers.all():
                if not container.has_task:
                    try:
                        return cls.objects.create(container = container, submission = submission)
                    except IntegrityError:
                        pass

            time.sleep(10)

            if not Submission.objects.filter(id = submission_id).exists():
                return None


class ContainerPackage(models.Model):
    TYPE_CHOICES = (("apt", "Apt"), ("pip", "Pip"))

    name = models.CharField(max_length = 100, null = False, unique = True, blank = False)

    package_type = models.CharField(max_length = 6, choices = TYPE_CHOICES, null = False, blank = False)

    install_globally = models.BooleanField(default = False, null = False)
    assignments = models.ManyToManyField(Assignment, related_name = "packages", blank = True)

    @classmethod
    def query_for_assignment(cls, assignment: Assignment):
        return cls.objects.filter(Q(install_globally = True) | Q(assignments = assignment))

