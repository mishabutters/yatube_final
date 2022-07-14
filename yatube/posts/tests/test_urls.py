from http import HTTPStatus
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_owner = User.objects.create_user(username='NoName')

        cls.user_new = User.objects.create_user(username='NewName')

        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug'
        )

        cls.post = Post.objects.create(
            author=cls.user_owner,
            text='Тестовая запись для создания нового поста',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_owner = Client()
        self.authorized_client_owner.force_login(self.user_owner)
        self.authorized_client_new = Client()
        self.authorized_client_new.force_login(self.user_new)

    def test_home_and_group(self):
        """Тест доступа к публичным страницам"""
        url_names = (
            '/',
            '/group/test_slug/',
            '/profile/NoName/',
            '/posts/1/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/')
        url = urljoin(reverse('login'), "?next=/create/")
        self.assertRedirects(response, url)

    def test_private_url(self):
        """Тест доступа к приватным страницам"""
        url_names = (
            '/create/',
            '/posts/1/edit/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_new_for_authorized(self):
        """Тест создания поста для авторизованного пользователя"""
        response = self.authorized_client_owner.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_for_owner(self):
        """Тест доступа редактирования поста для владельца"""
        response = self.authorized_client_owner.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_for_new_user(self):
        """Тест доступа редактирования поста для авторизованного юзера"""
        response = self.authorized_client_new.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/create/': 'posts/create_post.html',
            '/profile/NoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_owner.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        response = self.guest_client.get('/qwerty12345/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
