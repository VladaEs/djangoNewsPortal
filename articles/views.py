from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CommentForm
from .models import Article, ArticleView, Comment, SavedArticle
from .services import record_article_view
from .utils import build_url


COMMENTS_PER_PAGE = 10


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


@login_required
def personalized_feed(request):
    history_queryset = (
        ArticleView.objects.filter(
            user=request.user,
            article__status=Article.Status.PUBLISHED,
            article__published_at__lte=timezone.now(),
        )
        .select_related("article", "article__author")
        .order_by("-viewed_at")[:100]
    )

    view_history = []
    seen_article_ids = set()
    for article_view in history_queryset:
        if article_view.article_id in seen_article_ids:
            continue

        seen_article_ids.add(article_view.article_id)
        view_history.append(article_view)
        if len(view_history) == 12:
            break

    latest_articles = []
    if not view_history:
        latest_articles = list(
            Article.objects.filter(
                status=Article.Status.PUBLISHED,
                published_at__lte=timezone.now(),
            )
            .select_related("author")
            .order_by("-published_at", "-created_at")[:8]
        )

    return render(
        request,
        "articles/personalized_feed.html",
        {
            "view_history": view_history,
            "latest_articles": latest_articles,
            "is_personalized_feed": True,
        },
    )


def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related("author").prefetch_related("tags"),
        slug=slug,
        status=Article.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    record_article_view(request, article)
    view_count = article.views.count()
    is_locked = (
        article.access_level == Article.AccessLevel.REGISTERED
        and not request.user.is_authenticated
    )
    is_saved = (
        request.user.is_authenticated
        and SavedArticle.objects.filter(
            user=request.user,
            article=article,
        ).exists()
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
    comments = article.comments.filter(
        status=Comment.Status.APPROVED,
    ).select_related("user")
    comments_page = Paginator(
        comments,
        COMMENTS_PER_PAGE,
    ).get_page(request.GET.get("comments_page"))

    return render(
        request,
        "articles/article_detail.html",
        {
            "article": article,
            "view_count": view_count,
            "is_locked": is_locked,
            "is_saved": is_saved,
            "related_articles": related_articles,
            "comments_page": comments_page,
            "comment_form": CommentForm(),
        },
    )


@login_required
@require_POST
def article_comment_create(request, slug):
    article = get_object_or_404(
        Article,
        slug=slug,
        status=Article.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.user = request.user
        comment.save()
        messages.success(
            request,
            "Ваш коментар надіслано на модерацію.",
        )

        article_url = reverse(
            "articles:article_detail",
            kwargs={"slug": article.slug},
        )
        return redirect(f"{article_url}#comments")

    messages.error(
        request,
        "Не вдалося додати коментар. Перевірте введений текст.",
    )
    article_url = reverse(
        "articles:article_detail",
        kwargs={"slug": article.slug},
    )
    return redirect(f"{article_url}#comment-form")


@login_required
@require_POST
def article_save_for_later(request, slug):
    article = get_object_or_404(
        Article,
        slug=slug,
        status=Article.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    SavedArticle.objects.get_or_create(
        article=article,
        user=request.user,
    )

    return redirect("articles:article_detail", slug=article.slug)


@login_required
@require_POST
def article_remove_from_saved(request, slug):
    article = get_object_or_404(
        Article,
        slug=slug,
        status=Article.Status.PUBLISHED,
        published_at__lte=timezone.now(),
    )
    SavedArticle.objects.filter(
        article=article,
        user=request.user,
    ).delete()

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect("articles:article_detail", slug=article.slug)
