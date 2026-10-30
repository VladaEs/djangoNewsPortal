from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import portal_administrator_required

from .forms import CommentForm, StatisticsDateFilterForm
from .models import Article, ArticleView, Comment, SavedArticle
from .services import build_personalized_feed, record_article_view
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
        articles = articles.order_by("published_at", "created_at", "pk")
    else:
        articles = articles.order_by("-published_at", "-created_at", "-pk")

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
    feed = build_personalized_feed(request.user)

    return render(
        request,
        "articles/personalized_feed.html",
        {
            "recommendations": feed.recommendations,
            "interest_tags": feed.interest_tags,
            "is_fallback": feed.is_fallback,
            "is_personalized_feed": True,
        },
    )


@portal_administrator_required
def article_statistics(request):
    now = timezone.now()
    statistics_form = StatisticsDateFilterForm(request.GET)
    period_start = None
    period_end = None

    if statistics_form.is_valid():
        date_from = statistics_form.cleaned_data.get("date_from")
        date_to = statistics_form.cleaned_data.get("date_to")
        current_timezone = timezone.get_current_timezone()

        if date_from is not None:
            period_start = timezone.make_aware(
                datetime.combine(date_from, time.min),
                current_timezone,
            )

        if date_to is not None:
            next_date = date_to + timedelta(days=1)
            period_end = timezone.make_aware(
                datetime.combine(next_date, time.min),
                current_timezone,
            )

    view_count_filter = None
    comment_count_filter = None
    save_count_filter = None

    if period_start is not None:
        view_count_filter = Q(views__viewed_at__gte=period_start)
        comment_count_filter = Q(comments__created_at__gte=period_start)
        save_count_filter = Q(saved_by_users__saved_at__gte=period_start)

    if period_end is not None:
        view_end_filter = Q(views__viewed_at__lt=period_end)
        comment_end_filter = Q(comments__created_at__lt=period_end)
        save_end_filter = Q(saved_by_users__saved_at__lt=period_end)

        if view_count_filter is None:
            view_count_filter = view_end_filter
            comment_count_filter = comment_end_filter
            save_count_filter = save_end_filter
        else:
            view_count_filter = view_count_filter & view_end_filter
            comment_count_filter = comment_count_filter & comment_end_filter
            save_count_filter = save_count_filter & save_end_filter

    published_articles = Article.objects.filter(
        status=Article.Status.PUBLISHED,
        published_at__lte=now,
    )
    article_ranking = (
        published_articles.select_related("author")
        .annotate(
            view_count=Count(
                "views",
                filter=view_count_filter,
                distinct=True,
            ),
            comment_count=Count(
                "comments",
                filter=comment_count_filter,
                distinct=True,
            ),
            save_count=Count(
                "saved_by_users",
                filter=save_count_filter,
                distinct=True,
            ),
        )
        .order_by("-view_count", "-published_at", "title")
    )
    article_views = ArticleView.objects.filter(
        article__status=Article.Status.PUBLISHED,
        article__published_at__lte=now,
    )
    comments = Comment.objects.filter(
        article__status=Article.Status.PUBLISHED,
        article__published_at__lte=now,
    )
    saved_articles = SavedArticle.objects.filter(
        article__status=Article.Status.PUBLISHED,
        article__published_at__lte=now,
    )

    if period_start is not None:
        article_views = article_views.filter(viewed_at__gte=period_start)
        comments = comments.filter(created_at__gte=period_start)
        saved_articles = saved_articles.filter(saved_at__gte=period_start)

    if period_end is not None:
        article_views = article_views.filter(viewed_at__lt=period_end)
        comments = comments.filter(created_at__lt=period_end)
        saved_articles = saved_articles.filter(saved_at__lt=period_end)

    return render(
        request,
        "articles/article_statistics.html",
        {
            "article_ranking": article_ranking,
            "total_articles": published_articles.count(),
            "total_views": article_views.count(),
            "total_comments": comments.count(),
            "total_saves": saved_articles.count(),
            "statistics_form": statistics_form,
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
