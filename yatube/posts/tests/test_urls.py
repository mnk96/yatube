from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description="Описание группы",
            slug='test-slug'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized = Client()
        self.people = User.objects.create_user(username='NoName')
        self.authorized.force_login(self.people)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )

    def test_guest_redirect(self):
        response = self.guest_client.get(f'/posts/{self.post.id}/edit',
                                         follow=True)
        print(response.status_code)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/',
            HTTPStatus.MOVED_PERMANENTLY
        )

    def test_authorized_not_author(self):
        response = self.authorized.get(f'/posts/{self.post.id}/edit',
                                       follow=True)
        print(response.status_code)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/',
            HTTPStatus.MOVED_PERMANENTLY
        )

    def test_authorized_redirect(self):
        response = self.authorized.get(f'/posts/{self.post.id}/edit',
                                       follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': f'/profile/{self.user}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, address in templates_url.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location(self):
        response = self.guest_client.get('/unexsiting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def tearDown(self):
        cache.clear()
