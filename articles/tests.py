from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article, ArticleView, Comment, SavedArticle, Tag, WebsiteSettings
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


class ArticleViewModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="history-reader",
            password="test-password",
        )
        cls.article = Article.objects.create(
            title="Стаття з історією переглядів",
            slug="article-with-view-history",
            body="Текст статті.",
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )

    def test_view_can_be_linked_to_user_and_article(self):
        article_view = ArticleView.objects.create(
            article=self.article,
            user=self.user,
        )

        self.assertEqual(article_view.article, self.article)
        self.assertEqual(article_view.user, self.user)
        self.assertEqual(self.article.views.get(), article_view)
        self.assertEqual(self.user.article_views.get(), article_view)

    def test_anonymous_view_can_be_recorded(self):
        article_view = ArticleView.objects.create(article=self.article)

        self.assertIsNone(article_view.user)

    def test_deleting_user_preserves_view_for_statistics(self):
        article_view = ArticleView.objects.create(
            article=self.article,
            user=self.user,
        )

        self.user.delete()
        article_view.refresh_from_db()

        self.assertIsNone(article_view.user)


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
            image="articles/images/image2.jpg",
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
            image="articles/images/image5.jpg",
            author=cls.user,
            status=Article.Status.PUBLISHED,
            access_level=Article.AccessLevel.REGISTERED,
            published_at=timezone.now(),
        )

    def test_homepage_lists_published_articles(self):
        response = self.client.get(reverse("articles:article_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_article.title)
        self.assertContains(
            response,
            "/static/articles/images/image5.jpg",
        )

    def test_article_detail_uses_its_own_image(self):
        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertContains(
            response,
            "/static/articles/images/image2.jpg",
        )

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

    def test_personalized_feed_requires_authentication(self):
        response = self.client.get(reverse("articles:personalized_feed"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertIn("next=/feed/", response.url)

    def test_personalized_feed_uses_only_current_users_history(self):
        other_user = get_user_model().objects.create_user(
            username="feed-outsider",
            password="test-password",
        )
        ArticleView.objects.create(
            user=self.user,
            article=self.public_article,
        )
        ArticleView.objects.create(
            user=self.user,
            article=self.public_article,
        )
        ArticleView.objects.create(
            user=other_user,
            article=self.old_article,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("articles:personalized_feed"))

        self.assertEqual(response.status_code, 200)
        recommended_ids = {
            recommendation.article.pk
            for recommendation in response.context["recommendations"]
        }
        self.assertNotIn(self.public_article.pk, recommended_ids)
        self.assertIn(self.old_article.pk, recommended_ids)
        self.assertEqual(response.context["interest_tags"][0], self.tag)
        self.assertEqual(response.context["interest_tags"][0].weight, 2)

    def test_personalized_feed_falls_back_to_latest_articles(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("articles:personalized_feed"))

        self.assertTrue(response.context["is_fallback"])
        self.assertTrue(response.context["recommendations"])
        self.assertContains(response, "Свіжі матеріали")
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

    def test_authenticated_article_view_saves_user_article_and_time(self):
        self.client.force_login(self.user)
        before_request = timezone.now()

        self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        article_view = ArticleView.objects.get()
        self.assertEqual(article_view.user, self.user)
        self.assertEqual(article_view.article, self.public_article)
        self.assertGreaterEqual(article_view.viewed_at, before_request)
        self.assertLessEqual(article_view.viewed_at, timezone.now())

    def test_anonymous_article_view_is_recorded_without_user(self):
        self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        article_view = ArticleView.objects.get()
        self.assertIsNone(article_view.user)
        self.assertEqual(article_view.article, self.public_article)

    def test_page_refresh_does_not_create_another_view_in_same_session(self):
        article_url = reverse(
            "articles:article_detail",
            kwargs={"slug": self.public_article.slug},
        )

        self.client.get(article_url)
        self.client.get(article_url)

        self.assertEqual(
            ArticleView.objects.filter(article=self.public_article).count(),
            1,
        )

    def test_new_session_creates_another_article_view(self):
        article_url = reverse(
            "articles:article_detail",
            kwargs={"slug": self.public_article.slug},
        )
        first_session_client = Client()
        second_session_client = Client()

        first_session_client.get(article_url)
        second_session_client.get(article_url)

        self.assertEqual(
            ArticleView.objects.filter(article=self.public_article).count(),
            2,
        )

    def test_bot_article_view_is_recorded(self):
        self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            ),
            HTTP_USER_AGENT="Mozilla/5.0 (compatible; Googlebot/2.1)",
        )

        self.assertEqual(
            ArticleView.objects.filter(article=self.public_article).count(),
            1,
        )

    def test_staff_article_view_is_not_recorded(self):
        staff_user = get_user_model().objects.create_user(
            username="staff-reader",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertFalse(ArticleView.objects.exists())

    def test_article_page_displays_current_view_count(self):
        ArticleView.objects.create(article=self.public_article)
        ArticleView.objects.create(article=self.public_article, user=self.user)

        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertEqual(response.context["view_count"], 3)
        self.assertContains(response, "Перегляди: 3")

    def test_authenticated_user_can_save_article_for_later(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "articles:article_save_for_later",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            ),
        )
        self.assertTrue(
            SavedArticle.objects.filter(
                user=self.user,
                article=self.public_article,
            ).exists()
        )

    def test_saving_the_same_article_twice_does_not_create_duplicate(self):
        self.client.force_login(self.user)
        save_url = reverse(
            "articles:article_save_for_later",
            kwargs={"slug": self.public_article.slug},
        )

        self.client.post(save_url)
        self.client.post(save_url)

        self.assertEqual(
            SavedArticle.objects.filter(
                user=self.user,
                article=self.public_article,
            ).count(),
            1,
        )

    def test_anonymous_user_cannot_save_article(self):
        response = self.client.post(
            reverse(
                "articles:article_save_for_later",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertFalse(SavedArticle.objects.exists())

    def test_saved_article_page_shows_saved_state(self):
        SavedArticle.objects.create(
            user=self.user,
            article=self.public_article,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertContains(response, "Видалити зі збережених")

    def test_authenticated_user_can_remove_article_from_saved(self):
        SavedArticle.objects.create(
            user=self.user,
            article=self.public_article,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "articles:article_remove_from_saved",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            ),
        )
        self.assertFalse(
            SavedArticle.objects.filter(
                user=self.user,
                article=self.public_article,
            ).exists()
        )

    def test_removing_article_does_not_delete_another_users_save(self):
        other_user = get_user_model().objects.create_user(
            username="another-reader",
            password="test-password",
        )
        SavedArticle.objects.create(
            user=self.user,
            article=self.public_article,
        )
        SavedArticle.objects.create(
            user=other_user,
            article=self.public_article,
        )
        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "articles:article_remove_from_saved",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertTrue(
            SavedArticle.objects.filter(
                user=other_user,
                article=self.public_article,
            ).exists()
        )

    def test_article_displays_only_approved_comments(self):
        approved_comment = Comment.objects.create(
            article=self.public_article,
            user=self.user,
            body="Схвалений коментар до статті.",
            status=Comment.Status.APPROVED,
        )
        pending_comment = Comment.objects.create(
            article=self.public_article,
            user=self.user,
            body="Коментар, який очікує модерації.",
        )
        rejected_comment = Comment.objects.create(
            article=self.public_article,
            user=self.user,
            body="Відхилений коментар.",
            status=Comment.Status.REJECTED,
        )

        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            )
        )

        self.assertContains(response, approved_comment.body)
        self.assertNotContains(response, pending_comment.body)
        self.assertNotContains(response, rejected_comment.body)

    def test_authenticated_user_can_submit_comment_for_moderation(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "articles:article_comment_create",
                kwargs={"slug": self.public_article.slug},
            ),
            {"body": "Новий коментар читача."},
        )

        expected_url = reverse(
            "articles:article_detail",
            kwargs={"slug": self.public_article.slug},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{expected_url}#comments")
        comment = Comment.objects.get()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.article, self.public_article)
        self.assertEqual(comment.body, "Новий коментар читача.")
        self.assertEqual(comment.status, Comment.Status.PENDING)

    def test_anonymous_user_cannot_submit_comment(self):
        response = self.client.post(
            reverse(
                "articles:article_comment_create",
                kwargs={"slug": self.public_article.slug},
            ),
            {"body": "Анонімний коментар."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertFalse(Comment.objects.exists())

    def test_comment_form_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(
            reverse(
                "articles:article_comment_create",
                kwargs={"slug": self.public_article.slug},
            ),
            {"body": "Коментар без CSRF-токена."},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Comment.objects.exists())

    def test_approved_comments_are_paginated(self):
        for number in range(11):
            Comment.objects.create(
                article=self.public_article,
                user=self.user,
                body=f"Схвалений коментар номер {number}.",
                status=Comment.Status.APPROVED,
            )

        response = self.client.get(
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.public_article.slug},
            ),
            {"comments_page": 2},
        )

        comments_page = response.context["comments_page"]
        self.assertEqual(comments_page.paginator.count, 11)
        self.assertEqual(comments_page.paginator.num_pages, 2)
        self.assertEqual(len(comments_page.object_list), 1)

    def test_comment_admin_allows_superuser_to_delete_comments(self):
        superuser = get_user_model().objects.create_superuser(
            username="portal-admin",
            email="admin@example.com",
            password="admin-password",
        )
        request = RequestFactory().get("/admin/articles/comment/")
        request.user = superuser

        self.assertIn(Comment, admin.site._registry)
        self.assertTrue(
            admin.site._registry[Comment].has_delete_permission(request)
        )
