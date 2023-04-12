from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, Comment

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description="Описание группы",
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            image=cls.uploaded,
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.user = PostCreateFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_guest_create(self):
        """Неавторизированный пользователь создание поста"""
        posts_count = Post.objects.count()
        form_data = {
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            'Поcт не может быть добавлен')

    def test_guest_edit(self):
        """Неавторизированный пользователь редактирование поста"""
        posts_count = Post.objects.count()
        form_data = {
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            'Поcт не может быть добавлен')

    def test_not_create_post_invalid_group(self):
        """Форма с невалидными данными"""
        posts_count = Post.objects.count()
        form_data = {
            'image': self.uploaded,
            'text': 'Тестовый пост 1',
            'group': 'Группа',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'group',
            ('Выберите корректный вариант. '
             'Вашего варианта нет среди допустимых значений.'),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'image': self.uploaded,
            'text': 'Тестовый пост 1',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост 1',
                group=self.group
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный тестовый пост',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), post_count)

        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.pk
            ).exists()
        )

    def test_comment_guest_user(self):
        """Создание комментария незарегистрированным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий 1',
        }
        response = self.guest_client.post(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Comment.objects.count(),
                            comment_count + 1,
                            'Комментарий не может быть добавлен')

    def test_create_comment(self):
        """Создание комментария"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), comment_count + 1)
