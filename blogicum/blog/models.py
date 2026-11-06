"""Модели приложения blog."""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class BasePostModel(models.Model):
    """Общие поля публикаций, категорий и местоположений."""

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено',
    )

    class Meta:
        """Настройки абстрактной модели."""

        abstract = True


class Category(BasePostModel):
    """Тематическая категория."""

    title = models.CharField(
        max_length=256,
        verbose_name='Заголовок',
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        ),
    )

    class Meta:
        """Метаданные категории."""

        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        """Вернуть название категории."""
        return self.title


class Location(BasePostModel):
    """Географическая метка."""

    name = models.CharField(
        max_length=256,
        verbose_name='Название места',
    )

    class Meta:
        """Метаданные местоположения."""

        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        """Вернуть название места."""
        return self.name


class Post(BasePostModel):
    """Публикация."""

    title = models.CharField(
        max_length=256,
        verbose_name='Заголовок',
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    image = models.ImageField(
        upload_to='posts/',
        null=True,
        blank=True,
        verbose_name='Изображение',
        help_text='Картинка, которая будет показана вместе с публикацией.',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — можно делать '
            'отложенные публикации.'
        ),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
        related_name='posts',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        verbose_name='Категория',
        related_name='posts',
    )

    class Meta:
        """Метаданные публикации."""

        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def __str__(self):
        """Вернуть заголовок публикации."""
        return self.title


class Comment(models.Model):
    """Комментарий к публикации."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Публикация',
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено',
    )

    class Meta:
        """Метаданные комментария."""

        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at', 'pk')

    def __str__(self):
        """Вернуть начало текста комментария."""
        return self.text[:50]
