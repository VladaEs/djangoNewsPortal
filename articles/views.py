from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Article
from .utils import build_url


def article_list(request):
    articles = (
        Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        )
        .select_related("author")
        .prefetch_related("tags")
    )

    # SELECT *
    #FROM articles_article
    #WHERE status = 'published'
    #  AND published_at <= NOW()
    # published in the future to not fetch draft, or articles scheduled for later


    #search query and selected tag filtering
    query = request.GET.get("q", "").strip()
    selected_tag = request.GET.get("tag", "").strip()
    sort = request.GET.get("sort", "new_first")

    if sort not in {"new_first", "old_first"}:
        return redirect(build_url(request, sort="new_first"))

    if query:
        articles = articles.filter(Q(title__icontains=query) | Q(body__icontains=query))

    if selected_tag:
        articles = articles.filter(tags__slug=selected_tag)

    if sort == "old_first":
        articles = articles.order_by("published_at", "created_at")
    else:
        articles = articles.order_by("-published_at", "-created_at")

    article_list = list(articles.distinct()[:12])

    return render(
        request,
        "articles/article_list.html",
        {
            "featured_article": article_list[0] if article_list else None,
            "secondary_articles": article_list[1:3],
            "latest_articles": article_list[3:],
            "query": query,
            "selected_tag": selected_tag,
            "sort": sort,
        },
    )


def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related("author").prefetch_related("tags"),
        slug=slug,
        status=Article.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    is_locked = (
        article.access_level == Article.AccessLevel.REGISTERED
        and not request.user.is_authenticated
    )
    related_articles = (
        Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=timezone.now(),
            tags__in=article.tags.all(),
        )
        .exclude(pk=article.pk)
        .select_related("author")
        .distinct()[:3]
    )

    return render(
        request,
        "articles/article_detail.html",
        {
            "article": article,
            "is_locked": is_locked,
            "related_articles": related_articles,
        },
    )
