from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse


from posts.models import Post, Group, Follow

User = get_user_model()
NUM_POSTS = 10


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description="Описание группы",
            slug='test-slug'
        )
        cls.author = User.objects.create_user(username='Author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.auth = User.objects.create_user(username='Aut')
        self.authorized = Client()
        self.authorized.force_login(self.auth)
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts:index': ({}, 'posts/index.html'),
            'posts:group_posts': ({'slug': self.group.slug},
                                  'posts/group_list.html'),
            'posts:profile': ({'username': self.author},
                              'posts/profile.html'),
            'posts:post_detail': ({'post_id': self.post.id},
                                  'posts/post_detail.html'),
            'posts:post_edit': ({'post_id': self.post.id},
                                'posts/create_post.html'),
            'posts:post_create': ({}, 'posts/create_post.html'),
        }
        for reverse_name, template in templates_pages_names.items():
            kwargs, template = template
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=kwargs))
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        post = response.context['page_obj'][0]
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_group_post_show_correct_context(self):
        """Шаблон group_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        post = response.context['page_obj'][0]
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_post_profile_page_show_correct_context(self):
        """Шаблон post_profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        contexts = {
            'page_obj', 'username', 'post_count'
        }
        for context in contexts:
            self.assertIn(context, response.context)
        post = response.context['page_obj'][0]
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIn('post', response.context)
        self.assertIn('posts', response.context)
        post = response.context['post']
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)
        self.assertIn('post', response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIn('form', response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_correct_index(self):
        post = Post.objects.create(
            author=self.author,
            text='Пост для проверки отображения',
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        page = response.context['page_obj']
        self.assertIn(post, page)

    def test_post_create_correct_group(self):
        post = Post.objects.create(
            author=self.author,
            text='Пост для проверки отображения',
            group=self.group,
        )
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}))
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        page = response.context['page_obj']
        self.assertIn(post, page)

    def test_post_create_correct_profile(self):
        post = Post.objects.create(
            author=self.author,
            text='Пост для проверки отображения',
            group=self.group,
        )
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author}))
        self.assertIn('username', response.context)
        self.assertIn('page_obj', response.context)
        self.assertIn('post_count', response.context)
        page = response.context['page_obj']
        self.assertIn(post, page)

    def test_cache_index(self):
        """Проверка кеширования"""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            author=self.author,
            text='Кеш-тест',
            group=self.group,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_old.content, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_old.content, response_new.content)

    def test_authorized_client_can_follow(self):
        """Авторизированный пользователь может подписываться на других"""
        self.authorized.get(reverse('posts:profile_follow',
                                    kwargs={'username': self.author.username}))
        follow_old = Follow.objects.all().count()
        self.assertEqual(follow_old, 1)

    def test_guest_client_can_not_follow(self):
        """Неавторизированный пользователь не может подписываться на других"""
        self.guest_client.get(reverse('posts:profile_follow',
                                      kwargs={'username':
                                              self.author.username}))
        follow_old = Follow.objects.all().count()
        self.assertEqual(follow_old, 0)

    def test_authorized_client_can_unfollow(self):
        """Авторизированный пользователь может отписываться от других"""
        self.authorized.get(reverse('posts:profile_follow',
                                    kwargs={'username':
                                            self.author.username}))
        unfollow_old = Follow.objects.all().count()
        self.authorized.get(reverse('posts:profile_unfollow',
                                    kwargs={'username': self.author.username}))
        unfollow = Follow.objects.all().count()
        self.assertEqual(unfollow_old, unfollow + 1)

    def test_guest_client_can_not_unfollow(self):
        """Неавторизированный пользователь не может отписываться от других"""
        self.guest_client.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.author.username}))
        unfollow_old = Follow.objects.all().count()
        self.assertEqual(unfollow_old, 0)

    def tearDown(self):
        cache.clear()


class PaginatorViewsTest(TestCase):
    POST_NUM = 13

    def setUp(self):
        self.guest = Client()
        self.author = User.objects.create_user(username='Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            description="Описание группы",
            slug='test-slug'
        )
        post_test = []
        for i in range(self.POST_NUM):
            post_test.append(Post.objects.create(
                author=self.author,
                text='Тестовый пост',
                group=self.group,))

    def test_index_first_page_contains_ten_records(self):
        response = self.guest.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), NUM_POSTS)

    def test_index_second_page_contains_three_records(self):
        response = self.guest.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POST_NUM - NUM_POSTS)

    def test_group_list_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), NUM_POSTS)

    def test_group_list_second_page_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POST_NUM - NUM_POSTS)

    def test_post_profile_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author}))
        self.assertEqual(len(response.context['page_obj']), NUM_POSTS)

    def test_post_profile_second_page_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POST_NUM - NUM_POSTS)
