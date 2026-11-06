"""Вью-классы приложения blog."""
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, ProfileForm, RegisterForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_ON_PAGE = 10


def filter_published(queryset):
    """Оставить только доступные всем посетителям публикации."""
    return queryset.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )


def with_comment_count(queryset):
    """Добавить к публикациям количество комментариев."""
    return queryset.select_related(
        'author',
        'category',
        'location',
    ).annotate(
        comment_count=Count('comments'),
    )


class PostIndexView(ListView):
    """Главная страница с лентой публикаций."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_ON_PAGE

    def get_queryset(self):
        """Вернуть опубликованные публикации от новых к старым."""
        return with_comment_count(
            filter_published(Post.objects.all()),
        ).order_by('-pub_date')


class CategoryPostsView(ListView):
    """Публикации выбранной категории."""

    model = Post
    template_name = 'blog/category.html'
    paginate_by = POSTS_ON_PAGE

    def get_queryset(self):
        """Вернуть публикации категории от новых к старым."""
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        queryset = self.category.posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
        )
        return with_comment_count(queryset).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        """Добавить в контекст категорию."""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostDetailView(DetailView):
    """Страница отдельной публикации."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_queryset(self):
        """Вернуть публикации, доступные текущему пользователю."""
        queryset = Post.objects.select_related(
            'author',
            'category',
            'location',
        )
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(author=self.request.user) | Q(
                    is_published=True,
                    pub_date__lte=timezone.now(),
                    category__is_published=True,
                ),
            )
        return filter_published(queryset)

    def get_context_data(self, **kwargs):
        """Добавить комментарии и форму для нового комментария."""
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related(
            'author',
        ).order_by('created_at', 'pk')
        context['form'] = CommentForm()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание новой публикации."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Назначить автора и вернуть на страницу профиля."""
        form.instance.author = self.request.user
        self.object = form.save()
        return redirect(
            'blog:profile',
            username=self.request.user.username,
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование публикации."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """Пропустить к редактированию только автора публикации."""
        if request.user.is_authenticated:
            post = self.get_object()
            if post.author != request.user:
                return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Вернуть адрес отредактированной публикации."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk},
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление публикации после подтверждения."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        """Пропустить к удалению только автора и администратора."""
        if request.user.is_authenticated:
            self.object = self.get_object()
            if (self.object.author != request.user
                    and not request.user.is_staff):
                return redirect(
                    'blog:post_detail',
                    post_id=self.object.pk,
                )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Показать публикацию на странице подтверждения."""
        kwargs.setdefault('form', PostForm(instance=self.object))
        return super().get_context_data(**kwargs)


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавление комментария к публикации."""

    model = Comment
    form_class = CommentForm
    http_method_names = ['post']

    def get_post(self):
        """Вернуть публикацию, к которой можно оставить комментарий."""
        queryset = Post.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(author=self.request.user) | Q(
                    is_published=True,
                    pub_date__lte=timezone.now(),
                    category__is_published=True,
                ),
            )
        else:
            queryset = filter_published(queryset)
        return get_object_or_404(queryset, pk=self.kwargs['post_id'])

    def form_valid(self, form):
        """Назначить автора и публикацию комментария."""
        form.instance.author = self.request.user
        form.instance.post = self.get_post()
        return super().form_valid(form)

    def form_invalid(self, form):
        """Вернуть пользователя к публикации, если комментарий пуст."""
        return redirect(
            'blog:post_detail',
            post_id=self.kwargs['post_id'],
        )

    def get_success_url(self):
        """Вернуть адрес публикации с комментариями."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование собственного комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'

    def get_queryset(self):
        """Искать комментарий только среди комментариев публикации."""
        return Comment.objects.filter(post_id=self.kwargs['post_id'])

    def dispatch(self, request, *args, **kwargs):
        """Пропустить к редактированию только автора комментария."""
        if request.user.is_authenticated:
            comment = self.get_object()
            if comment.author != request.user:
                return redirect(
                    'blog:post_detail',
                    post_id=self.kwargs['post_id'],
                )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Вернуть адрес публикации с комментариями."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post_id},
        )


class CommentDeleteView(DeleteView):
    """Удаление комментария после подтверждения."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'

    def get_queryset(self):
        """Искать комментарий только среди комментариев публикации."""
        return Comment.objects.filter(post_id=self.kwargs['post_id'])

    def get_success_url(self):
        """Вернуть адрес публикации с комментариями."""
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )

    def post(self, request, *args, **kwargs):
        """Удалить комментарий, если это разрешено пользователю."""
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        self.object = self.get_object()
        if (self.object.author != request.user
                and not request.user.is_staff):
            return redirect(
                'blog:post_detail',
                post_id=self.object.post_id,
            )
        return super().post(request, *args, **kwargs)


class ProfileListView(ListView):
    """Страница пользователя с его публикациями."""

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_ON_PAGE

    def get_queryset(self):
        """Вернуть публикации пользователя от новых к старым."""
        self.profile_user = get_object_or_404(
            User,
            username=self.kwargs['username'],
        )
        queryset = Post.objects.filter(author=self.profile_user)
        if self.request.user != self.profile_user:
            queryset = filter_published(queryset)
        return with_comment_count(queryset).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        """Добавить в контекст владельца страницы."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile_user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование собственного профиля."""

    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        """Редактировать можно только собственный профиль."""
        return self.request.user

    def get_success_url(self):
        """Вернуть на страницу профиля после сохранения."""
        return reverse(
            'blog:profile',
            kwargs={'username': self.object.username},
        )


class RegisterView(CreateView):
    """Регистрация нового пользователя."""

    form_class = RegisterForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')
