from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
TEXT_NUM = 15


class Group(models.Model):
    title = models.CharField("Group name", max_length=200)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Description group")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        max_length=1000,
        help_text='Введите текст поста')
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'group', blank=True, null=True,
        related_name='posts',
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        help_text='Группа, к которой будет относиться пост')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:TEXT_NUM]

    class Meta:
        ordering = ["-pub_date"]


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        'Текст комментария',
        max_length=1000,
        help_text='Введите текст комментария')
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
