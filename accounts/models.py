from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property


PORTAL_ADMINISTRATORS_GROUP_NAME = "Portal Administrators"


class User(AbstractUser):
    @cached_property
    def is_portal_administrator(self):
        if not self.is_active or not self.is_staff:
            return False

        if self.is_superuser:
            return True

        return self.groups.filter(
            name=PORTAL_ADMINISTRATORS_GROUP_NAME,
        ).exists()


class UserBan(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bans",
    )
    reason = models.TextField()
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_bans",
    )

    class Meta:
        ordering = ["-starts_at"]
        indexes = [
            models.Index(
                fields=["user", "-starts_at"],
                name="user_ban_user_start_idx",
            ),
        ]
        verbose_name = "user ban"
        verbose_name_plural = "user bans"

    @property
    def is_active(self):
        now = timezone.now()

        if self.starts_at > now:
            return False

        if self.ends_at is None:
            return True

        return self.ends_at > now

    def clean(self):
        super().clean()

        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValidationError(
                {"ends_at": "Ban end date must be later than start date."}
            )

    def __str__(self):
        return f"Ban for {self.user}"
