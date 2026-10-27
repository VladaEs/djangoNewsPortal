from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Article, ArticleView, Tag
from .services import build_personalized_feed


class RecommendationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="recommendation-reader",
            password="test-password",
        )
        cls.other_user = get_user_model().objects.create_user(
            username="other-recommendation-reader",
            password="test-password",
        )
        cls.transport = Tag.objects.create(
            name="Транспорт",
            slug="recommendation-transport",
        )
        cls.culture = Tag.objects.create(
            name="Культура",
            slug="recommendation-culture",
        )

        now = timezone.now()
        cls.viewed_article = Article.objects.create(
            title="Міський електробус вийшов на новий маршрут",
            slug="recommendation-viewed-electric-bus",
            body=(
                "Електробус працює на міському маршруті та з’єднує "
                "віддалені райони громадським транспортом."
            ),
            status=Article.Status.PUBLISHED,
            published_at=now - timedelta(days=1),
        )
        cls.viewed_article.tags.add(cls.transport)

        cls.tag_match = Article.objects.create(
            title="Автобусний маршрут отримає додаткові рейси",
            slug="recommendation-tag-match",
            body="Громадський транспорт частіше курсуватиме між районами.",
            status=Article.Status.PUBLISHED,
            published_at=now - timedelta(days=8),
        )
        cls.tag_match.tags.add(cls.transport)

        cls.text_match = Article.objects.create(
            title="Електробус змінює маршрут між районами",
            slug="recommendation-text-match",
            body="Новий маршрут допоможе пасажирам швидше дістатися центру.",
            status=Article.Status.PUBLISHED,
            published_at=now - timedelta(days=20),
        )

        cls.fresh_irrelevant = Article.objects.create(
            title="У галереї відкрилася виставка живопису",
            slug="recommendation-fresh-culture",
            body="Художники представили картини та графічні роботи.",
            status=Article.Status.PUBLISHED,
            published_at=now,
        )
        cls.fresh_irrelevant.tags.add(cls.culture)

        cls.future_article = Article.objects.create(
            title="Майбутній транспортний матеріал",
            slug="recommendation-future-transport",
            body="Матеріал ще не опублікований.",
            status=Article.Status.PUBLISHED,
            published_at=now + timedelta(days=1),
        )
        cls.future_article.tags.add(cls.transport)

    def test_tags_are_analyzed_and_viewed_articles_are_excluded(self):
        ArticleView.objects.create(
            user=self.user,
            article=self.viewed_article,
        )

        feed = build_personalized_feed(self.user)
        recommended_ids = {
            recommendation.article.pk
            for recommendation in feed.recommendations
        }

        self.assertFalse(feed.is_fallback)
        self.assertEqual(feed.interest_tags[0], self.transport)
        self.assertEqual(feed.interest_tags[0].weight, 1)
        self.assertNotIn(self.viewed_article.pk, recommended_ids)
        self.assertNotIn(self.future_article.pk, recommended_ids)
        self.assertIn(self.tag_match.pk, recommended_ids)

    def test_repeated_history_strengthens_tag_interest(self):
        ArticleView.objects.create(
            user=self.user,
            article=self.viewed_article,
        )
        ArticleView.objects.create(
            user=self.user,
            article=self.viewed_article,
        )
        ArticleView.objects.create(
            user=self.other_user,
            article=self.fresh_irrelevant,
        )

        feed = build_personalized_feed(self.user)

        self.assertEqual(len(feed.interest_tags), 1)
        self.assertEqual(feed.interest_tags[0], self.transport)
        self.assertEqual(feed.interest_tags[0].weight, 2)

    def test_article_with_popular_tag_scores_above_text_match(self):
        ArticleView.objects.create(
            user=self.user,
            article=self.viewed_article,
        )

        feed = build_personalized_feed(self.user)
        recommendations = {
            recommendation.article.pk: recommendation
            for recommendation in feed.recommendations
        }

        self.assertEqual(recommendations[self.tag_match.pk].score, 1)
        self.assertEqual(recommendations[self.text_match.pk].score, 0)
        self.assertGreater(
            recommendations[self.tag_match.pk].score,
            recommendations[self.text_match.pk].score,
        )

    def test_recommendations_are_sorted_by_score(self):
        ArticleView.objects.create(
            user=self.user,
            article=self.viewed_article,
        )

        feed = build_personalized_feed(self.user)
        scores = [
            recommendation.score
            for recommendation in feed.recommendations
        ]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(feed.recommendations[0].article, self.tag_match)

    def test_new_user_receives_latest_articles_as_fallback(self):
        feed = build_personalized_feed(self.user)

        self.assertTrue(feed.is_fallback)
        self.assertFalse(feed.interest_tags)
        self.assertTrue(feed.recommendations)
        self.assertEqual(
            feed.recommendations[0].article,
            self.fresh_irrelevant,
        )
