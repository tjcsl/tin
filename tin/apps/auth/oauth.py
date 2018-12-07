from social_core.backends.oauth import BaseOAuth2
from social_core.pipeline.user import get_username as social_get_username


def get_username(strategy, details, user=None, *args, **kwargs):
    result = social_get_username(strategy, details, user=user, *args, **kwargs)
    #if not hasattr(user, 'social_user'):
    #    user.social_user
    return result


class IonOauth2(BaseOAuth2):
    name = 'ion'
    AUTHORIZATION_URL = 'https://ion.tjhsst.edu/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://ion.tjhsst.edu/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires')
    ]

    def get_scope(self):
        return ["read"]

    def get_user_details(self, response):
        profile = self.get_json('https://ion.tjhsst.edu/api/profile',
                                params={'access_token': response['access_token']})
        # fields used to populate/update User model
        return {
            'id': profile['id'],
            'username': profile['ion_username'],
            'full_name': profile['full_name'],
            'first_name': profile['first_name'],
            'last_name': profile['last_name'],
            'nickname': profile['nickname'],
            'email': profile['tj_email'],
            'is_student': profile['is_student'],
            'is_teacher': profile['is_teacher'],
        }

    def get_user_id(self, details, response):
        return details["id"]
