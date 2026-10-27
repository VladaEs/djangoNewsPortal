from django.db import migrations, models


ARTICLE_IMAGE_PATHS = (
    "articles/images/image1.png",
    "articles/images/image2.jpg",
    "articles/images/image3.jpg",
    "articles/images/image4.jpg",
    "articles/images/image5.jpg",
)


def assign_article_images(apps, schema_editor):
    Article = apps.get_model("articles", "Article")

    for index, article in enumerate(Article.objects.order_by("pk").iterator()):
        article.image = ARTICLE_IMAGE_PATHS[index % len(ARTICLE_IMAGE_PATHS)]
        article.save(update_fields=["image"])


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0006_articleview"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="image",
            field=models.CharField(
                default="articles/images/image1.png",
                max_length=255,
            ),
        ),
        migrations.RunPython(
            assign_article_images,
            migrations.RunPython.noop,
        ),
    ]
