from django import forms

from .models import Comment


class StatisticsDateFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label="Від",
        widget=forms.DateInput(
            attrs={
                "class": "form-control rounded-0",
                "type": "date",
            }
        ),
    )
    date_to = forms.DateField(
        required=False,
        label="До",
        widget=forms.DateInput(
            attrs={
                "class": "form-control rounded-0",
                "type": "date",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from is not None and date_to is not None:
            if date_from > date_to:
                self.add_error(
                    "date_to",
                    "Дата завершення має бути не раніше дати початку.",
                )

        return cleaned_data


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
