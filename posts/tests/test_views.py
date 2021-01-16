import shutil
import tempfile
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Group, Post, Comment


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):        
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)   
        User = get_user_model()
        cls.user = User.objects.create(username='testuser')
        cls.user_1 = User.objects.create(username='testuser_1')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
        )

        cls.group_1 = Group.objects.create(
            title='Тестовый заголовок 1',
            slug='test_slug_1',
        )

        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
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

        posts = []
        for i in range(1, 12):
            posts.append(Post(
                text='text' + str(i),
                author=cls.user,
                group=cls.group,
                image=uploaded
            ))
        Post.objects.bulk_create(posts)

        posts = []
        for x in range(1, 12):
            posts.append(Post(
                text='text new' + str(x),
                author=cls.user,
                group=cls.group_1,
            ))
        Post.objects.bulk_create(posts)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """ Create authorized and guest client """
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(PostViewsTest.user_1)
    
    def test_pages_uses_correct_template(self):
        """URL-адреса используют соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/new_post.html': reverse('new_post'),
            'group.html': reverse('group', kwargs={'slug': 'test_slug'}),
            'users/profile.html': reverse('profile', 
                                  kwargs={'username': 'testuser'}),
            'misc/404.html': reverse('404'),
            'misc/500.html': reverse('500'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    @override_settings(
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
            }
        )            
    def test_home_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(response.context.get('page').object_list,
                        list(PostViewsTest.user.posts.all()[:10]))

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    @override_settings(
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
            }
        )
    def test_second_page_of_index(self):
        """Проверка второй страницы шаблона index."""
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(response.context.get('page').object_list,
                         list(Post.objects.all()[10:20]))

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', 
            kwargs={'slug':
            'test_slug'})
        )
        self.assertEqual(response.context.get('page').object_list, 
                        list(PostViewsTest.group.posts.all()[:10]))
        self.assertEqual(response.context.get('group'), PostViewsTest.group)
    
    def test_username_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('profile',
                               kwargs={'username': 'testuser'}))
        self.assertEqual(response.context.get('page').object_list, 
                        list(PostViewsTest.user.posts.all()[:10]))
    
    def test_new_post_that_is_not_in_group_1(self):
        """Проверка: пост не находится в другой группе."""
        group = Group.objects.first()
        posts_out_of_group = Post.objects.exclude(group=group)
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test_slug'}))
        self.assertTrue(set(posts_out_of_group).isdisjoint(
            response.context.get('paginator').object_list)
        )

    def test_username_post_id_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        for post in Post.objects.all():
            with self.subTest(post=post):
                response = self.authorized_client.get(reverse('post',
                              kwargs={'username': PostViewsTest.user,
                                      'post_id': post.id}))
                self.assertEqual(response.context.get('post'), post)      

    def test_username_post_id_edit_page_show_correct_context(self):
        """Шаблон new_post для редактирования
        сформирован с правильным контекстом."""
        for post in Post.objects.all():
            with self.subTest(post=post):
                response = self.authorized_client.get(reverse('post_edit', 
                                   kwargs={'username': PostViewsTest.user,
                                            'post_id': post.id}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected) 

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)  

    def test_about_author_page_accessible_by_name(self):
        """URL, генерируемые при помощи имен
        about:author и 'about:tech', доступны."""
        for status_code in range(200, 201):
            with self.subTest(status_code=status_code):
                self.assertEqual(self.guest_client.get(
                     reverse('about:author')).status_code, status_code)
                self.assertEqual(self.guest_client.get(
                     reverse('about:tech')).status_code, status_code)

    def test_about_author_about_tech_pages_use_correct_template(self):
        """При запросе к about:tech
        применяется шаблон about/tech.html.
        При запросе к about:author
        применяется шаблон about/author.html."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_cache_index_page(self):
        """Тестируем cache"""
        index_1 = self.client.get(reverse('index'))
        Post.objects.create(
                text='Test-cache',
                author=PostViewsTest.user
        )
        index_2 = self.client.get(reverse('index'))
        self.assertHTMLEqual(str(index_1.content), str(index_2.content))

    def test_profile_follow(self):
        """authorized_client может подписываться"""
        users_followed_before = self.user.follower.count()
        self.authorized_client.get(reverse(
            "profile_follow", kwargs={"username": self.user_1.username})
        )
        users_followed_after = self.user.follower.count()
        self.assertEqual(users_followed_after, users_followed_before + 1)

    def test_profile_unfollow(self):
        """authorized_client может отписываться"""
        self.authorized_client.get(reverse(
            "profile_follow",
            kwargs={"username": self.user_1.username})
        )
        users_follower_before = self.user.follower.count()
        self.authorized_client.get(reverse(
            "profile_unfollow",
            kwargs={"username": self.user_1.username})
        )
        users_follower_after = self.user.follower.count()
        self.assertEqual(users_follower_after, users_follower_before - 1)

    def test_follow_index(self):
        """Запись появляется в ленте подписчиков"""
        self.authorized_client.get(
            reverse("profile_follow",
                    kwargs={"username": self.user_1.username}))
        self.authorized_client_1.post(
            reverse("new_post"),
            {"text": "Текст поста",
             "group": PostViewsTest.group.id
             }
        )
        response = self.authorized_client.get(reverse("follow_index"))
        self.assertContains(
            response, "Текст поста")

    def test_view_post_without_follow(self):
        """Запись не появляется в ленте подписчиков"""
        self.authorized_client_1.post(
            reverse("new_post"),
            {"text": "Текст поста",
             "group": PostViewsTest.group.id
             }
        )
        response = self.authorized_client_1.get(reverse("follow_index"))
        self.assertNotContains(
            response, "Текст поста")

    def test_authorized_user_may_add_comment(self):
        """authorized_client может комментировать"""
        post = Post.objects.create(author=self.user, text="Текст поста")
        response = self.authorized_client.post(
            reverse("add_comment", args=[self.user.username, post.id]),
            {"text": "Текст комментария"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)

    def test_unauthorized_user_not_comment(self):
        """guest_client не может комментировать"""
        post = Post.objects.create(author=self.user, text="Текст поста")
        response = self.guest_client.post(
            reverse("add_comment", args=[self.user.username, post.id]),
            {"text": "Текст комментария"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)
