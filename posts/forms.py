from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post

        fields = ['text', 'group', 'image']
        labels = {'text': 'Введите текст', 'group': 'Выберите группу', 'image': 'Добавьте картинку'}
        help_texts = {'text': 'Заполнить', 'group':
                                  'Выбрать группу'}

class CommentForm(ModelForm):
    class Meta:
        model = Comment

        fields = ['text']
