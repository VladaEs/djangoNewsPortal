from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class UserLoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label = "Ім’я користувача"
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control form-control-lg rounded-0",
                "autocomplete": "username",
                "placeholder": "Ваш логін",
            }
        )
        self.fields["password"].label = "Пароль"
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control form-control-lg rounded-0",
                "autocomplete": "current-password",
                "placeholder": "Ваш пароль",
            }
        )


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-lg rounded-0",
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_settings = {
            "username": {
                "label": "Ім’я користувача",
                "autocomplete": "username",
                "placeholder": "Оберіть логін",
            },
            "password1": {
                "label": "Пароль",
                "autocomplete": "new-password",
                "placeholder": "Створіть пароль",
            },
            "password2": {
                "label": "Повторіть пароль",
                "autocomplete": "new-password",
                "placeholder": "Введіть пароль ще раз",
            },
        }

        for field_name, settings in field_settings.items():
            field = self.fields[field_name]
            field.label = settings.pop("label")
            field.widget.attrs.update(
                {
                    "class": "form-control form-control-lg rounded-0",
                    **settings,
                }
            )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Користувач із таким email уже існує.")
        return email
