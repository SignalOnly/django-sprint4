"""Страницы приложения pages и обработчики ошибок."""
from django.shortcuts import render
from django.views.generic import TemplateView


class AboutPageView(TemplateView):
    """Статичная страница «О проекте»."""

    template_name = 'pages/about.html'


class RulesPageView(TemplateView):
    """Статичная страница «Наши правила»."""

    template_name = 'pages/rules.html'


def csrf_failure(request, reason=''):
    """Страница ошибки проверки CSRF-токена."""
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    """Страница несуществующего адреса."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Страница внутренней ошибки сервера."""
    return render(request, 'pages/500.html', status=500)
