from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Enter a color in #RRGGBB format.",
)


class WebsiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Міський Вісник")
    tagline = models.CharField(
        max_length=200,
        default="Новини, що тримають місто разом",
    )
    background_color = models.CharField(
        max_length=7,
        default="#F4F1EA",
        validators=[hex_color_validator],
    )
    text_color = models.CharField(
        max_length=7,
        default="#171717",
        validators=[hex_color_validator],
    )
    accent_color = models.CharField(
        max_length=7,
        default="#A51C30",
        validators=[hex_color_validator],
    )
    base_font_size = models.PositiveSmallIntegerField(
        default=16,
        validators=[MinValueValidator(14), MaxValueValidator(22)],
        help_text="Base font size in pixels (14–22).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "website settings"
        verbose_name_plural = "website settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.site_name


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
        NEWS = "news", "Новина"
        ARTICLE = "article", "Стаття"

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опубліковано"
        ARCHIVED = "archived", "В архіві"

    class AccessLevel(models.TextChoices):
        PUBLIC = "public", "Публічний"
        REGISTERED = "registered", "Лише для зареєстрованих"

    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        allow_unicode=True,
    )
    body = models.TextField()
    image = models.CharField(
        max_length=255,
        default="articles/images/image1.png",
    )
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


class SavedArticle(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_articles",
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="saved_by_users",
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "article"],
                name="unique_saved_article_per_user",
            ),
        ]
        verbose_name = "saved article"
        verbose_name_plural = "saved articles"

    def __str__(self):
        return f"{self.user} — {self.article}"


class Comment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Очікує модерації"
        APPROVED = "approved", "Схвалено"
        REJECTED = "rejected", "Відхилено"

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField(max_length=2000)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["article", "status", "-created_at"],
                name="comment_article_status_idx",
            ),
        ]
        verbose_name = "comment"
        verbose_name_plural = "comments"

    def __str__(self):
        return f"{self.user}: {self.body[:50]}"


class ArticleView(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="views",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="article_views",
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(
                fields=["article", "-viewed_at"],
                name="article_view_article_idx",
            ),
            models.Index(
                fields=["user", "-viewed_at"],
                name="article_view_user_idx",
            ),
        ]
        verbose_name = "article view"
        verbose_name_plural = "article views"

    def __str__(self):
        viewer = self.user if self.user_id else "anonymous"
        return f"{viewer} — {self.article}"
