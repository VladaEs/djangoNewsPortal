from django.contrib.auth import get_user_model
from django.contrib.auth import SESSION_KEY
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from articles.models import Article, SavedArticle


class AuthenticationPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="reader",
            email="reader@example.com",
            password="reader-password",
        )

    def test_login_page_is_available_to_anonymous_users(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Увійти до порталу")

    def test_normal_user_can_log_in_and_return_to_requested_page(self):
        next_url = reverse("articles:article_list")

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": "reader-password",
                "next": next_url,
            },
        )

        self.assertRedirects(response, next_url)
        self.assertEqual(
            self.client.session[SESSION_KEY],
            str(self.user.pk),
        )
        self.assertFalse(self.user.is_staff)

    def test_normal_login_without_next_redirects_to_personalized_feed(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": "reader-password",
            },
        )

        self.assertRedirects(
            response,
            reverse("articles:personalized_feed"),
        )

    def test_invalid_credentials_show_an_error(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.username, "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неправильне ім’я користувача або пароль")

    def test_authenticated_user_can_log_out_with_post(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("articles:article_list"))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_registration_page_is_available(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Створити обліковий запис")

    def test_user_can_register_and_return_to_requested_page(self):
        next_url = reverse("articles:article_list")

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-reader",
                "email": "new-reader@example.com",
                "password1": "Safe-reader-password-4829",
                "password2": "Safe-reader-password-4829",
                "next": next_url,
            },
        )

        self.assertRedirects(response, next_url)
        user = get_user_model().objects.get(username="new-reader")
        self.assertTrue(user.check_password("Safe-reader-password-4829"))
        self.assertFalse(user.is_staff)
        self.assertEqual(self.client.session[SESSION_KEY], str(user.pk))

    def test_registration_rejects_duplicate_email_ignoring_case(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "another-reader",
                "email": "READER@example.com",
                "password1": "Safe-reader-password-4829",
                "password2": "Safe-reader-password-4829",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Користувач із таким email уже існує")
        self.assertFalse(
            get_user_model().objects.filter(username="another-reader").exists()
        )

    def test_registration_rejects_external_next_url(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "safe-reader",
                "email": "safe-reader@example.com",
                "password1": "Safe-reader-password-4829",
                "password2": "Safe-reader-password-4829",
                "next": "https://example.com/unsafe-redirect",
            },
        )

        self.assertRedirects(
            response,
            reverse("articles:personalized_feed"),
        )


class ProfilePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="profile-reader",
            password="reader-password",
        )
        cls.other_user = get_user_model().objects.create_user(
            username="other-reader",
            password="reader-password",
        )
        cls.article = Article.objects.create(
            title="Збережена міська стаття",
            slug="saved-city-article",
            body="Текст збереженої статті.",
            author=cls.other_user,
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_profile_keeps_empty_state_without_saved_articles(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertContains(
            response,
            "Тут пізніше з’являться матеріали, збережені для читання.",
        )

    def test_profile_displays_current_users_saved_articles(self):
        SavedArticle.objects.create(
            user=self.user,
            article=self.article,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertContains(response, self.article.title)
        self.assertContains(response, "Видалити зі збережених")
        self.assertContains(
            response,
            reverse(
                "articles:article_detail",
                kwargs={"slug": self.article.slug},
            ),
        )
        self.assertNotContains(
            response,
            "Тут пізніше з’являться матеріали, збережені для читання.",
        )

    def test_profile_remove_button_returns_to_profile(self):
        SavedArticle.objects.create(
            user=self.user,
            article=self.article,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "articles:article_remove_from_saved",
                kwargs={"slug": self.article.slug},
            ),
            {"next": reverse("accounts:profile")},
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertFalse(
            SavedArticle.objects.filter(
                user=self.user,
                article=self.article,
            ).exists()
        )

    def test_profile_does_not_display_another_users_saved_articles(self):
        SavedArticle.objects.create(
            user=self.other_user,
            article=self.article,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertNotContains(response, self.article.title)
