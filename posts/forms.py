from django.forms import ModelForm, Textarea

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Введите текст',
            'group': 'Выберите группу',
            'image': 'Выберите изображение'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': Textarea({'rows': 3})
        }
