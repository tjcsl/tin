from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager as DjangoUserManager
from django.utils import timezone

from social_django.utils import load_strategy

import requests
import logging

logger = logging.getLogger(__name__)


class UserManager(DjangoUserManager):
    pass


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=32)
    full_name = models.CharField(max_length=105)
    nickname = models.CharField(max_length=35)
    first_name = models.CharField(max_length=35)
    last_name = models.CharField(max_length=70)
    email = models.CharField(max_length=50)
    is_staff = models.BooleanField(default=False)
    is_sysadmin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    @property
    def short_name(self):
        return self.username

    def api_request(self, url, params={}, refresh=True):
        s = self.get_social_auth()
        params.update({"format": "json"})
        params.update({"access_token": s.access_token})
        r = requests.get("https://ion.tjhsst.edu/api/{}".format(url),
                         params=params)
        if r.status_code == 401:
            if refresh:
                try:
                    self.get_social_auth().refresh_token(load_strategy())
                except BaseException as e:
                    logger.exception(str(e))
                return self.api_request(url, params, False)
            else:
                logger.error(
                    "Ion API Request Failure: {} {}".format(r.status_code,
                                                            r.json()))
        return r.json()

    def get_social_auth(self):
        return self.social_auth.get(provider="ion")
