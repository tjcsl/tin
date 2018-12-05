from django.contrib.auth.decorators import user_passes_test

sysadmin_required = user_passes_test(lambda u: not u.is_anonymous and u.is_sysadmin)
