import tempfile
from shutil import rmtree
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug5',
            description='Тестовое описание'
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }

    @classmethod
    def tearDownClass(cls):
        rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_authorized_user_can_create_post(self):
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=1)
        self.assertEqual(Post.objects.count(), 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'NoName'})
        )
        self.assertEqual(post_1.text, 'Данные из формы')
        self.assertEqual(post_1.author.username, 'NoName')
        self.assertEqual(post_1.group.title, 'Заголовок для тестовой группы')

    def test_guest_user_cant_create_post(self):
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        url = urljoin(reverse('login'), "?next=/create/")
        self.assertRedirects(response, url)

    def test_authorized_user_can_edit_post(self):
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=1)
        self.client.get(reverse(
            'posts:post_edit', kwargs={'post_id': post_1.pk})
        )
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': post_1.id}),
            data=form_data,
            follow=True,
        )
        modified_post = Post.objects.get(id=1)
        self.assertEqual(response_edit.status_code, 200)
        self.assertEqual(modified_post.text, 'Измененный текст')

    def test_user_can_upload_post_with_picture(self):
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
        form_data = {
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(post.image)
