"""Конфигурация приложения pages."""
from django.apps import AppConfig


class PagesConfig(AppConfig):
    """Конфигурация приложения pages."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
    verbose_name = 'Страницы'
