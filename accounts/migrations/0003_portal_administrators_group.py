from django.db import migrations


PORTAL_ADMINISTRATORS_GROUP_NAME = "Portal Administrators"


def create_portal_administrators_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name=PORTAL_ADMINISTRATORS_GROUP_NAME)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_userban"),
    ]

    operations = [
        migrations.RunPython(
            create_portal_administrators_group,
            migrations.RunPython.noop,
        ),
    ]
