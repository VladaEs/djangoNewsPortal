from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserBan


admin.site.register(User, UserAdmin)


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "starts_at",
        "ends_at",
        "is_active",
        "created_by",
    )
    list_filter = (
        "starts_at",
        "ends_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "reason",
    )
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if obj.created_by is None:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)