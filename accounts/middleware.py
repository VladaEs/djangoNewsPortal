from django.contrib import messages
from django.contrib.auth import logout


class UserBanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            active_ban = None

            for ban in request.user.bans.all():
                if ban.is_active:
                    active_ban = ban
                    break

            if active_ban is not None:
                logout(request)
                messages.error(
                    request,
                    "Ваш обліковий запис тимчасово заблоковано.",
                )

        response = self.get_response(request)
        return response