from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article, Tag, WebsiteSettings


class WebsiteSettingsTests(TestCase):
    def test_load_creates_a_singleton(self):
        first = WebsiteSettings.load()
        second = WebsiteSettings.load()

        self.assertEqual(first.pk, 1)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(WebsiteSettings.objects.count(), 1)


class ArticlePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="editor",
            password="test-password",
        )
        cls.tag = Tag.objects.create(name="Місто", slug="misto")
        cls.public_article = Article.objects.create(
            title="Публічна міська новина",
            slug="public-city-news",
            body="Відкритий демонстраційний текст міської новини.",
            author=cls.user,
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        cls.public_article.tags.add(cls.tag)
        cls.restricted_article = Article.objects.create(
            title="Матеріал для читачів",
            slug="reader-only-story",
            body=("Вступний текст " * 50) + "PRIVATE_ENDING",
            author=cls.user,
            status=Article.Status.PUBLISHED,
            access_level=Article.AccessLevel.REGISTERED,
            published_at=timezone.now(),
        )

    def test_homepage_lists_published_articles(self):
        response = self.client.get(reverse("articles:article_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_article.title)

    def test_search_finds_an_article_by_title(self):
        response = self.client.get(
            reverse("articles:article_list"),
            {"q": "міська"},
        )

        self.assertContains(response, self.public_article.title)

    def test_restricted_article_hides_full_body_from_anonymous_user(self):
        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.restricted_article.slug},
            )
        )

        self.assertContains(response, "Матеріал для зареєстрованих читачів")
        self.assertNotContains(response, "PRIVATE_ENDING")

    def test_restricted_article_is_visible_after_login(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.restricted_article.slug},
            )
        )

        self.assertContains(response, "PRIVATE_ENDING")
