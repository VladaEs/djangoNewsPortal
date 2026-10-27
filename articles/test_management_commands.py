from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from .management.commands.seed_news import (
    ARTICLE_DATA,
    ARTICLE_IMAGE_PATHS,
    TAG_DATA,
)
from .models import Article, Tag


class SeedNewsCommandTests(TestCase):
    def run_command(self):
        output = StringIO()
        call_command("seed_news", stdout=output)
        return output.getvalue()

    def test_seed_news_creates_demo_content(self):
        output = self.run_command()

        demo_articles = Article.objects.filter(slug__startswith="demo-")
        self.assertEqual(demo_articles.count(), len(ARTICLE_DATA))
        self.assertEqual(
            Tag.objects.filter(
                slug__in=[slug for _, slug in TAG_DATA],
            ).count(),
            len(TAG_DATA),
        )
        self.assertFalse(
            get_user_model()
            .objects.get(username="demo-editor")
            .has_usable_password()
        )
        self.assertTrue(
            all(article.tags.exists() for article in demo_articles)
        )
        self.assertTrue(
            all(
                article.image in ARTICLE_IMAGE_PATHS
                for article in demo_articles
            )
        )
        self.assertIn("24 created", output)

    def test_seed_news_is_idempotent(self):
        self.run_command()
        article_count = Article.objects.filter(
            slug__startswith="demo-",
        ).count()

        output = self.run_command()

        self.assertEqual(
            Article.objects.filter(slug__startswith="demo-").count(),
            article_count,
        )
        self.assertIn("0 created", output)
        self.assertIn("24 updated", output)
