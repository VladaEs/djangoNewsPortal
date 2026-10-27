from dataclasses import dataclass

from django.db.models import Count
from django.utils import timezone

from .models import Article, ArticleView, Tag


VIEWED_ARTICLES_SESSION_KEY = "viewed_article_ids"
RECOMMENDATION_CANDIDATE_LIMIT = 200


@dataclass(frozen=True)
class ArticleRecommendation:
    article: Article
    score: int
    matched_tags: tuple[Tag, ...]


@dataclass(frozen=True)
class PersonalizedFeed:
    recommendations: tuple[ArticleRecommendation, ...]
    interest_tags: tuple[Tag, ...]
    is_fallback: bool


def get_recommendation_sort_key(recommendation):
    return (
        recommendation.score,
        recommendation.article.published_at,
        recommendation.article.pk,
    )


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


def build_personalized_feed(user, limit=12):
    """Build a personalized feed based on the user's tag views."""
    now = timezone.now()

    # Keep track of viewed articles so they are not recommended again.
    viewed_article_ids = set(
        ArticleView.objects.filter(user=user).values_list(
            "article_id",
            flat=True,
        )
    )

    # Get published articles and load their authors and tags in advance.
    candidate_articles = list(
        Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=now,
        )
        .select_related("author")
        .prefetch_related("tags")
        .order_by("-published_at", "-created_at")[
            :RECOMMENDATION_CANDIDATE_LIMIT
        ]
    )

    # If the user has no viewing history, show the latest articles instead.
    if not viewed_article_ids:
        recommendations = []

        for article in candidate_articles[:limit]:
            recommendation = ArticleRecommendation(
                article=article,
                score=0,
                matched_tags=(),
            )
            recommendations.append(recommendation)

        return PersonalizedFeed(
            recommendations=tuple(recommendations),
            interest_tags=(),
            is_fallback=True,
        )

    # A tag gets more weight each time the user views an article with that tag.
    interest_tags = tuple(
        Tag.objects.filter(articles__views__user=user)
        .annotate(weight=Count("articles__views"))
        .order_by("-weight", "name")
    )
    tag_weights = {}

    for tag in interest_tags:
        tag_weights[tag.pk] = tag.weight

    # An article's score is the sum of its tags' weights in the user's interests.
    recommendations = []

    for article in candidate_articles:
        if article.pk in viewed_article_ids:
            continue

        matched_tags = []
        score = 0

        for tag in article.tags.all():
            if tag.pk in tag_weights:
                matched_tags.append(tag)
                score = score + tag_weights[tag.pk]

        recommendations.append(
            ArticleRecommendation(
                article=article,
                score=score,
                matched_tags=tuple(matched_tags),
            )
        )

    # Rank by score first, then put newer articles first when scores are equal.
    recommendations.sort(
        key=get_recommendation_sort_key,
        reverse=True,
    )

    return PersonalizedFeed(
        recommendations=tuple(recommendations[:limit]),
        interest_tags=interest_tags[:8],
        is_fallback=False,
    )
