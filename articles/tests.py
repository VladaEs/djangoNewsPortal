from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article, Tag, WebsiteSettings
from .utils import build_url


class BuildUrlTests(TestCase):
    def test_build_url_replaces_values_and_preserves_all_other_parameters(self):
        request = RequestFactory().get(
            "/?q=qwerty&tag=news&tag=business&page=2"
        )

        url = build_url(request, sort="new_first", page=None)

        self.assertEqual(
            url,
            "/?sort=new_first&q=qwerty&tag=news&tag=business",
        )


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
        cls.old_article = Article.objects.create(
            title="Стара міська новина",
            slug="old-city-news",
            body="Архівний текст міської новини.",
            author=cls.user,
            status=Article.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=30),
        )
        cls.old_article.tags.add(cls.tag)
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

    def test_articles_are_sorted_newest_first_by_default(self):
        response = self.client.get(reverse("articles:article_list"))

        self.assertEqual(response.context["sort"], "new_first")
        self.assertEqual(response.context["featured_article"], self.restricted_article)

    def test_articles_can_be_sorted_oldest_first_with_get(self):
        response = self.client.get(
            reverse("articles:article_list"),
            {"sort": "old_first"},
        )

        self.assertEqual(response.context["sort"], "old_first")
        self.assertEqual(response.context["featured_article"], self.old_article)
        self.assertContains(response, 'option value="old_first" selected')

    def test_invalid_sort_value_redirects_to_preserved_canonical_url(self):
        response = self.client.get(
            reverse("articles:article_list"),
            {"sort": "not-allowed", "q": "міська"},
        )

        self.assertRedirects(
            response,
            "/?sort=new_first&q=%D0%BC%D1%96%D1%81%D1%8C%D0%BA%D0%B0",
        )

    def test_sort_form_preserves_all_existing_get_parameters(self):
        response = self.client.get(
            reverse("articles:article_list"),
            {"sort": "new_first", "q": "міська", "page": "2"},
        )

        self.assertContains(response, 'name="q" value="міська"')
        self.assertContains(response, 'name="page" value="2"')

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
