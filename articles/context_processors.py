from .models import Tag, WebsiteSettings


def website_context(request):
    return {
        "website_settings": WebsiteSettings.load(),
        "navigation_tags": Tag.objects.all()[:6],
    }
