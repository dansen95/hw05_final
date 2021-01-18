from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(username='testuser')
        
        cls.group = Group.objects.create(
            title='тестовый заголовок',
            slug='test_slug',
        )
        
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=ModelsTest.user,
            group=ModelsTest.group,
        )

    def setUp(self):
        """ Create authorized client """
        self.authorized_client = Client()
        self.authorized_client.force_login(ModelsTest.user)
        
    def test_verbose_name_post(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post_model = ModelsTest.post
        field_verboses = {
            'text': 'Текст',
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post_model._meta.get_field(value).verbose_name, expected)

    def test_help_text_post(self):
        """help_text в полях совпадает с ожидаемым."""
        post_model = ModelsTest.post
        field_help_texts = {
            'text': 'Заполнить',
        }

        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post_model._meta.get_field(value).help_text, expected)

    def test_object_name_is_text_field_post(self):
        """__str__  post_model - это строчка с содержимым post."""
        post_model = ModelsTest.post
        expected_object_name = post_model.text
        self.assertEquals(expected_object_name, str(post_model))

    def test_verbose_name_group(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post_group = ModelsTest.group
        field_verboses = {
            'title': 'Группа',
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post_group._meta.get_field(value).verbose_name, expected)

    def test_help_text_group(self):
        """help_text в полях совпадает с ожидаемым."""
        post_group = ModelsTest.group
        field_help_texts = {
            'title': 'Выбрать группу',
        }

        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post_group._meta.get_field(value).help_text, expected)
        
    def test_object_name_is_title_field_group(self):
        """__str__  post_group - это строчка с содержимым group."""
        post_group = ModelsTest.group
        expected_object_name = post_group.title
        self.assertEquals(expected_object_name, str(post_group))
        