"""Формы приложения blog."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Category, Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    """Форма создания и редактирования публикации."""

    class Meta:
        """Настройки формы публикации."""

        model = Post
        fields = (
            'title',
            'text',
            'image',
            'pub_date',
            'category',
            'location',
        )
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }

    def __init__(self, *args, **kwargs):
        """Оставить только опубликованные категории."""
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            is_published=True,
        )


class CommentForm(forms.ModelForm):
    """Форма создания и редактирования комментария."""

    class Meta:
        """Настройки формы комментария."""

        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class RegisterForm(UserCreationForm):
    """Форма регистрации нового пользователя."""

    class Meta(UserCreationForm.Meta):
        """Настройки формы регистрации."""

        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        """Настройки формы профиля."""

        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
