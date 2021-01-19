from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


class StaticURLTests(TestCase):
    def setUp(self):
        """ Create guest client """
        self.guest_client = Client()

    def test_about_author(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_techonologies(self):
        """Страница /about/tech/ доступна любому пользователю."""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()

        cls.author = User.objects.create(username='author')
        
        cls.group = Group.objects.create(
            slug='test_slug',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=PostURLTest.author,
            group=PostURLTest.group,    
        )
        
        cls.not_author = User.objects.create(username='not_author')

    def setUp(self):
        """ Create authorized and guest client """
        self.guest_client = Client()
        
        self.authorized_client_author = Client()
        self.authorized_client_not_author = Client()
        
        self.authorized_client_author.force_login(PostURLTest.author)
        self.authorized_client_not_author.force_login(PostURLTest.not_author)

    def test_home_url_exists_at_desired_location_for_auth_user(self):
        """Страница / доступна авторизированному пользователю."""
        response = self.authorized_client_author.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_url_exists_at_desired_location_for_guest(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_slug_url_exists_at_desired_location_for_auth_user(self):
        """Страница /group/test_slug/ доступна авторизированному 
        пользователю.
        
        """
        response = self.authorized_client_author.get('/group/test_slug')
        self.assertEqual(response.status_code, 200)

    def test_post_group_slug_url_exists_at_desired_location_for_guest(self):
        """Страница /group/test_slug/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test_slug')
        self.assertEqual(response.status_code, 200)

    def test_post_new_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client_author.get('/new/')
        self.assertEqual(response.status_code, 200)
  
    def test_post_new_url_does_not_exist_at_desired_location_for_guest(self):
        """Страница /new/ недоступна любому пользователю."""
        response = self.guest_client.get('/new/',
                                         follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/new/'))

    def test_username_for_guest(self):
        """Страница '/author/' доступна любому пользователю."""
        response = self.guest_client.get('/author/')  
        self.assertEqual(response.status_code, 200)
    
    def test_username_for_auth_user(self):
        """Страница '/author/' доступна авторизованному пользователю."""
        response = self.authorized_client_author.get('/author/')  
        self.assertEqual(response.status_code, 200)

    def test_username_post_id_for_guest(self):
        """Страница '/author/1/' доступна любому пользователю."""
        response = self.guest_client.get('/author/1/')  
        self.assertEqual(response.status_code, 200)

    def test_username_post_id_for_auth_user(self):
        """Страница '/author/1/' доступна авторизованному пользователю."""
        response = self.authorized_client_author.get('/author/1/')  
        self.assertEqual(response.status_code, 200)

    def test_username_post_id_edit_for_guest(self):
        """Страница '/author/1/edit/' недоступна любому пользователю."""
        response = self.guest_client.get('/author/1/edit/',
                                         follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/author/1/edit/'))

    def test_username_post_id_edit_for_auth_user_post_author(self):
        """Страница '/author/1/edit/' доступна авторизованному пользователю,
        автору поста.
        
        """
        response = self.authorized_client_author.get('/author/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/new_post.html': '/new/',
            'group.html': '/group/test_slug',
            'posts/new_post.html': '/author/1/edit/',
        }
        
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_redirect_from_username_post_id_edit_for_anon(self):
        """Тест редиректа со страницы '/author/1/edit/' 
        на страницу /author/1/ для авторизованного пользователя."""
        response = self.authorized_client_not_author.get('/author/1/edit/',
                                                         follow=True
        )
        self.assertRedirects(
            response, ('/author/1/')) 

    def test_techonologies(self):
        """Тест ошибки сервера 404 для несуществующей страницы"""
        response = self.guest_client.get('/false_page/')
        self.assertEqual(response.status_code, 404)
        