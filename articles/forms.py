from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        labels = {"body": "Ваш коментар"}
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "form-control rounded-0",
                    "rows": 5,
                    "placeholder": "Напишіть коментар...",
                }
            ),
        }
        error_messages = {
            "body": {
                "required": "Введіть текст коментаря.",
                "max_length": "Коментар не може перевищувати 2000 символів.",
            },
        }
