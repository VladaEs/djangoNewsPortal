from django.contrib.auth.decorators import user_passes_test


def is_portal_administrator(user):
    if not user.is_authenticated:
        return False

    return user.is_portal_administrator


portal_administrator_required = user_passes_test(
    is_portal_administrator,
    login_url="admin:login",
)
