from __future__ import annotations

import logging

import requests
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone
from social_django.utils import load_strategy

logger = logging.getLogger(__name__)


class UserManager(DjangoUserManager):
    """The Manager for :class:`~User`"""


class User(AbstractBaseUser, PermissionsMixin):
    """A Tin user"""

    id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=32)
    full_name = models.CharField(max_length=105)
    nickname = models.CharField(max_length=35, blank=True)
    first_name = models.CharField(max_length=35)
    last_name = models.CharField(max_length=70)
    email = models.CharField(max_length=50)
    is_staff = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    # 0 = Light mode, 1 = Dark Mode
    dark_mode = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(1)])

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    @property
    def short_name(self):
        return self.username

    def api_request(self, url, params=None, *, refresh=True):
        """Log in to Tin via Ion"""
        if params is None:
            params = {}

        social_auth = self.get_social_auth()
        params.update({"format": "json"})
        params.update({"access_token": social_auth.access_token})
        res = requests.get(f"https://ion.tjhsst.edu/api/{url}", params=params)
        if res.status_code == 401:
            if refresh:
                try:
                    self.get_social_auth().refresh_token(load_strategy())
                except BaseException as ex:  # pylint: disable=broad-except
                    logger.exception(str(ex))
                return self.api_request(url, params, refresh=False)
            else:
                logger.error("Ion API Request Failure: %s %s", res.status_code, res.json())
        return res.json()

    def get_social_auth(self):
        """Get social auth information from Ion"""
        return self.social_auth.get(provider="ion")
