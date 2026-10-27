from django.urls import path

from . import views


app_name = "articles"

urlpatterns = [
    path("", views.article_list, name="article_list"),
    path("feed/", views.personalized_feed, name="personalized_feed"),
    path(
        "articles/<str:slug>/save/",
        views.article_save_for_later,
        name="article_save_for_later",
    ),
    path(
        "articles/<str:slug>/remove-from-saved/",
        views.article_remove_from_saved,
        name="article_remove_from_saved",
    ),
    path(
        "articles/<str:slug>/comments/add/",
        views.article_comment_create,
        name="article_comment_create",
    ),
    path("articles/<str:slug>/", views.article_detail, name="article_detail"),
]
