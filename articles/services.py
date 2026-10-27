from .models import ArticleView


VIEWED_ARTICLES_SESSION_KEY = "viewed_article_ids"


def should_record_article_view(request):
    """Count GET requests except views made by portal staff."""
    if request.method != "GET":
        return False

    if request.user.is_authenticated and request.user.is_staff:
        return False

    return True


def record_article_view(request, article):
    """Store one view event per article in the current Django session."""
    if not should_record_article_view(request):
        return None

    viewed_article_ids = request.session.get(
        VIEWED_ARTICLES_SESSION_KEY,
        [],
    )
    if article.pk in viewed_article_ids:
        return None

    user = request.user if request.user.is_authenticated else None
    article_view = ArticleView.objects.create(
        article=article,
        user=user,
    )
    request.session[VIEWED_ARTICLES_SESSION_KEY] = [
        *viewed_article_ids,
        article.pk,
    ]

    return article_view
