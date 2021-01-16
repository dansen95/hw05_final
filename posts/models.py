from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Группа', 
                            help_text='Выбрать группу')
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст', help_text='Заполнить')
    pub_date = models.DateTimeField('date published',
                                    auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              blank=True, null=True,
                              related_name='posts')
    image = models.ImageField(upload_to='posts/', blank=True, null=True) 

    def __str__(self):
       return self.text[:15]

    class Meta:
        ordering = ['-pub_date']

class Comment(models.Model):
    post = models.ForeignKey(Post, blank=False, null=False,
                             on_delete=models.CASCADE,
                             related_name='comments',)
    author = models.ForeignKey(User, blank=False, null=False,
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(blank=False, null=False,
                            help_text='Ваш комментарий')
    created = models.DateTimeField(auto_now_add=True)  

class Follow(models.Model):
    user = models.ForeignKey(User, 
                             on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, 
                               on_delete=models.CASCADE,
                               related_name='following')

    def __str__(self):
        return f"follower - {self.user} following - {self.author}"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"