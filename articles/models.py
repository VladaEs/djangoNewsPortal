from django.conf import settings
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        allow_unicode=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self):
        return self.name


class Article(models.Model):
    class ContentType(models.TextChoices):
        NEWS = "news", "News"
        ARTICLE = "article", "Article"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class AccessLevel(models.TextChoices):
        PUBLIC = "public", "Public"
        REGISTERED = "registered", "Registered users only"

    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        allow_unicode=True,
    )
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles",
    )
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.NEWS,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    access_level = models.CharField(
        max_length=20,
        choices=AccessLevel.choices,
        default=AccessLevel.PUBLIC,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["status", "-published_at"],
                name="article_status_pub_idx",
            ),
            models.Index(
                fields=["author", "-published_at"],
                name="article_author_pub_idx",
            ),
        ]
        verbose_name = "article"
        verbose_name_plural = "articles"

    def __str__(self):
        return self.title
