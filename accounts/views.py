from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from articles.models import Article, SavedArticle

from .forms import UserRegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form, "next": next_url},
    )


'''
    @login_required - flag which is used to indicate that only logged in users can access the view.
    If a user is not logged in - they will be redirected to the login page.
'''


# we can access user like this -> request.user

@login_required
def profile(request):
    saved_articles = (
        SavedArticle.objects.filter(
            user=request.user,
            article__status=Article.Status.PUBLISHED,
            article__published_at__lte=timezone.now(),
        )
        .select_related("article", "article__author")
    )

    return render(
        request,
        "accounts/profile.html",
        {"saved_articles": saved_articles},
    )
