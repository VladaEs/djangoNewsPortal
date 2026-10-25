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
