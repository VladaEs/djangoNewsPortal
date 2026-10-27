from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from articles.models import Article, Tag, WebsiteSettings


ARTICLE_IMAGE_PATHS = (
    "articles/images/image1.png",
    "articles/images/image2.jpg",
    "articles/images/image3.jpg",
    "articles/images/image4.jpg",
    "articles/images/image5.jpg",
)


DEMO_ARTICLES = [
    {
        "title": "Місто відкриває оновлену набережну після великої реконструкції",
        "slug": "misto-vidkryvaie-onovlenu-naberezhnu",
        "tags": [("Місто", "misto"), ("Розвиток", "rozvytok")],
        "hours_ago": 1,
        "body": """У центрі міста завершили оновлення набережної — простору, який поєднує пішохідні маршрути, велосипедну доріжку та нові зелені зони.

За задумом проєктувальників, територія має стати зручним місцем для щоденних прогулянок, невеликих культурних подій і відпочинку біля води. Під час робіт також оновили освітлення та облаштували доступні спуски.

Це демонстраційний матеріал, створений для перевірки дизайну навчального новинного порталу.""",
    },
    {
        "title": "Новий маршрут електробуса з’єднає північні квартали з центром",
        "slug": "novyi-marshrut-elektrobusa",
        "tags": [("Транспорт", "transport"), ("Місто", "misto")],
        "hours_ago": 3,
        "body": """Тестовий маршрут електробуса почне працювати наступного тижня. Він проходитиме через житлові квартали, університетський кампус і центральну площу.

На маршруті передбачено дванадцять зупинок. Інтервал руху в години пік становитиме близько десяти хвилин.

Це вигадана новина для демонстрації інтерфейсу.""",
    },
    {
        "title": "У старому депо готують простір для концертів, лекцій і виставок",
        "slug": "kulturnyi-prostir-u-staromu-depo",
        "tags": [("Культура", "kultura"), ("Події", "podii")],
        "hours_ago": 5,
        "content_type": Article.ContentType.ARTICLE,
        "body": """Колишнє трамвайне депо поступово перетворюють на відкритий культурний майданчик. Організатори планують проводити тут камерні концерти, публічні лекції та виставки місцевих художників.

Перший сезон буде експериментальним: команда збиратиме відгуки відвідувачів і коригуватиме програму.

Матеріал є частиною демонстраційного набору даних.""",
    },
    {
        "title": "Що зміниться у русі транспорту на центральних вулицях",
        "slug": "zminy-rukhu-u-tsentri",
        "tags": [("Транспорт", "transport")],
        "hours_ago": 8,
        "body": """На кількох центральних вулицях планують змінити організацію руху. Частину смуг відведуть для громадського транспорту, а біля шкіл встановлять додаткові острівці безпеки.

Міські служби радять водіям заздалегідь перевіряти маршрут і звертати увагу на нові дорожні знаки.

Це демонстраційний матеріал, а не повідомлення про реальні обмеження.""",
    },
    {
        "title": "Міські школи отримають сучасні природничі лабораторії",
        "slug": "novi-laboratorii-u-shkolakh",
        "tags": [("Освіта", "osvita"), ("Розвиток", "rozvytok")],
        "hours_ago": 12,
        "body": """У навчальних закладах готують нові кабінети для практичних занять із фізики, хімії та біології. Обладнання надходитиме поетапно.

Учителі також пройдуть короткі програми підготовки, присвячені роботі з цифровими вимірювальними приладами.

Новина створена виключно як тестовий контент.""",
    },
    {
        "title": "П’ять локальних кав’ярень, що працюють із міськими пекарнями",
        "slug": "lokalni-kaviarni-ta-pekarni",
        "tags": [("Бізнес", "biznes"), ("Місто", "misto")],
        "hours_ago": 18,
        "content_type": Article.ContentType.ARTICLE,
        "access_level": Article.AccessLevel.REGISTERED,
        "body": """Малі кав’ярні дедалі частіше формують меню разом із пекарнями зі свого району. Така співпраця скорочує логістику й допомагає локальним командам знаходити нову аудиторію.

Ми зібрали п’ять вигаданих прикладів для перевірки закритих матеріалів та відображення довгих текстів.

Повний матеріал доступний після входу на портал.""",
    },
    {
        "title": "Вихідні у місті: книжковий ярмарок, кіно просто неба та велозаїзд",
        "slug": "podii-na-vykhidni",
        "tags": [("Події", "podii"), ("Культура", "kultura")],
        "hours_ago": 24,
        "body": """Цими вихідними демонстраційний календар порталу пропонує три події: ранковий велозаїзд, книжковий ярмарок у парку та вечірній кінопоказ.

Усі назви й деталі в цьому тексті вигадані та призначені для тестування новинної сторінки.""",
    },
]


class Command(BaseCommand):
    help = "Create an idempotent set of fictional articles for the local demo."

    def handle(self, *args, **options):
        WebsiteSettings.load()
        author = get_user_model().objects.filter(is_superuser=True).first()
        now = timezone.now()
        created_count = 0

        for article_index, item in enumerate(DEMO_ARTICLES):
            tag_specs = item["tags"]
            image_path = ARTICLE_IMAGE_PATHS[
                article_index % len(ARTICLE_IMAGE_PATHS)
            ]
            defaults = {
                "body": item["body"],
                "image": image_path,
                "author": author,
                "content_type": item.get("content_type", Article.ContentType.NEWS),
                "status": Article.Status.PUBLISHED,
                "access_level": item.get(
                    "access_level",
                    Article.AccessLevel.PUBLIC,
                ),
                "published_at": now - timedelta(hours=item["hours_ago"]),
            }
            article, created = Article.objects.get_or_create(
                slug=item["slug"],
                defaults={"title": item["title"], **defaults},
            )
            if created:
                created_count += 1
            elif article.image != image_path:
                article.image = image_path
                article.save(update_fields=["image"])

            tags = []
            for name, slug in tag_specs:
                tag, _ = Tag.objects.get_or_create(name=name, defaults={"slug": slug})
                tags.append(tag)
            article.tags.add(*tags)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo news ready: {created_count} created, "
                f"{len(DEMO_ARTICLES) - created_count} already existed."
            )
        )
