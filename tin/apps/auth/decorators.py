from django.contrib.auth.decorators import user_passes_test

login_required = user_passes_test(lambda u: not u.is_anonymous and u.is_authenticated)

student_required = user_passes_test(lambda u: not u.is_anonymous and u.is_student)

teacher_required = user_passes_test(lambda u: not u.is_anonymous and u.is_teacher)

teacher_or_superuser_required = user_passes_test(lambda u: not u.is_anonymous and (u.is_teacher or u.is_superuser))

