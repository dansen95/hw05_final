import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse, resolve

from posts.forms import PostForm
from posts.models import Group, Post
from posts import views
from urllib.parse import urlparse

class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        User = get_user_model()
        cls.user = User.objects.create(username='testuser')
        
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
        )
        
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=PostCreateFormTests.user,
            group=PostCreateFormTests.group,
        )
        
        cls.form = PostForm()    
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """ Create authorized client """
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
    
    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

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
            'text': 'Какой-то длинный, интересный текст',
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(response, reverse('index'))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(Post.objects.filter(
            text='Какой-то длинный, интересный текст').exists()
        )

        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())

    def test_post_edit_create_post_end_redirect(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': "Новый текст",
        }

        response = self.authorized_client.post(
            reverse('post_edit', kwargs={'username': PostCreateFormTests.user,
                                         'post_id': PostCreateFormTests.post.id}),
            data=form_data, follow=True
        )

        self.assertEqual(response.status_code, 200)

        PostCreateFormTests.post.refresh_from_db()
        self.assertEqual(PostCreateFormTests.post.text, form_data['text'])

        self.assertRedirects(
            response,
            reverse('post', 
                    kwargs={'username': PostCreateFormTests.user,
                            'post_id': PostCreateFormTests.post.id}
            )
        )

        self.assertTrue(Post.objects.filter(text='Новый текст').exists())

    def test_invalid_form_does_not_create_post(self):
        """Невалидная форма не создает в базе данных пост."""
        posts_count = Post.objects.count() 
        form_data = {
            'text': '',
            'group': PostCreateFormTests.group.id,
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )

        self.assertEqual(Post.objects.count(), posts_count)

        self.assertFormError(
            response, 'form', 'text', 'Обязательное поле.'
        )
