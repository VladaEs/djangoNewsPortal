from django.contrib import admin

from .models import Article, Comment, Tag, WebsiteSettings


@admin.register(WebsiteSettings)
class WebsiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("site_name", "tagline")}),
        (
            "Appearance",
            {
                "fields": (
                    "background_color",
                    "text_color",
                    "accent_color",
                    "base_font_size",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not WebsiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "content_type",
        "status",
        "access_level",
        "author",
        "published_at",
    )
    list_filter = ("content_type", "status", "access_level", "tags")
    list_select_related = ("author",)
    search_fields = ("title", "body")
    autocomplete_fields = ("author", "tags")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    list_select_related = ("article", "user")
    search_fields = ("body", "article__title", "user__username")
    autocomplete_fields = ("article", "user")
    readonly_fields = ("created_at",)
    actions = ("approve_comments", "reject_comments")

    @admin.action(description="Схвалити вибрані коментарі")
    def approve_comments(self, request, queryset):
        queryset.update(status=Comment.Status.APPROVED)

    @admin.action(description="Відхилити вибрані коментарі")
    def reject_comments(self, request, queryset):
        queryset.update(status=Comment.Status.REJECTED)
