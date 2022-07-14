import tempfile
from http import HTTPStatus
from shutil import rmtree

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_name')

        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug'
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания поста',
            group=cls.group,
            image=uploaded,
        )
        cls.templates_page_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse('posts:group_list', kwargs={'slug': 'test_slug'}),
                'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': 'test_name'}),
                'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={'post_id': '1'}),
                'posts/post_detail.html'),
            (reverse('posts:post_edit', kwargs={'post_id': '1'}),
                'posts/create_post.html'),
        ]

    @classmethod
    def tearDownClass(cls):
        rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = PostTests.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует правильный шаблон."""
        for reverse_name, template in PostTests.templates_page_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        index_group_profile_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page in index_group_profile_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                first_object = response.context["page_obj"][0]
                post_group = first_object.group
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.author, self.post.author)
                self.assertEqual(post_group.title, self.post.group.title)
                self.assertEqual(post_group.slug, self.post.group.slug)
                self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        first_object = response.context["post"]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_form_show_correct_context(self):
        """Шаблон post_create/post_edit сформирован
        с правильным контекстом."""
        create_edit_pages = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        ]
        for page in create_edit_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        self.assertIn('form', response.context)
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)

    def test_post_get_right_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Тестовая запись для создания поста')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(settings.POSTS_FOR_ONE_PAGE + 1):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

        cls.list_urls = {
            reverse("posts:index"): "index",
            reverse(
                "posts:group_list", kwargs={"slug": "test_slug2"}
            ): "group",
            reverse(
                "posts:profile",
                kwargs={"username": "test_name"}
            ): "profile",
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        for tested_url in self.list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                settings.POSTS_FOR_ONE_PAGE
            )

    def test_second_page_contains_other_posts(self):
        for tested_url in self.list_urls.keys():
            response = self.client.get(tested_url + "?page=2")
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 1
            )


class FollowTests(TestCase):
    def setUp(self):
        self.user_follower = Client()
        self.author_following = Client()
        self.user_1 = User.objects.create_user(username='follower')
        self.author_1 = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.author_1,
            text='Тестовая запись для тестирования ленты'
        )
        self.user_follower.force_login(self.user_1)
        self.author_following.force_login(self.author_1)

    def test_user_can_follow_author(self):
        self.user_follower.get(
            reverse('posts:profile_follow', args=(self.author_1.username,)))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_user_can_unfollow_author(self):
        self.user_follower.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.author_1.username
            }))
        self.user_follower.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.author_1.username
            }))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_following_authors_posts_appends_on_follow_page(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_1,
                              author=self.author_1)
        response = self.user_follower.get('/follow/')
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, self.post.text)

    def test_authorized_client_can_add_comment(self):
        response = self.author_following.post(
            f'/posts/{self.post.id}/comment/', {
                'text': "тестовый комментарий"
            }, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.author_following.get(f'/posts/{self.post.id}/')
        self.assertContains(response, 'тестовый комментарий')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания поста')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        first_step = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_step = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_step.content, second_step.content)
        cache.clear()
        third_step = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_step.content, third_step.content)
        cache.clear()
