from django.contrib import admin

from .models import Article, Tag, WebsiteSettings


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
