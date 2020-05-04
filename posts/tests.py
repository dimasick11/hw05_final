from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache

from .models import Post, Group, Follow, Comment


class TestYatube(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='dmitry', email='connor.s@skynet.com', password='12345')
        User.objects.create_user(username='sarah', email='connor.s@skynet.com', password='12345'
                                 )
        # создаем новый пост
        self.post = Post.objects.create(text='Hello World', author=self.user)

    def test_profile_page(self):
        response = self.client.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_user_not_auth(self):
        response = self.client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_create_new_post(self):
        self.client.login(username='dmitry', password='12345')
        post = Post.objects.create(text='Hello test auth', author=self.user)

        # Проверяем записана ли новая запись
        self.assertTrue(Post.objects.filter(text=post.text).exists())

        # проверяем доступна ли страница с постом
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertEqual(response.status_code, 200)

        # проверем соедржание поста на всех связных страниц
        response = self.client.get('')
        self.assertContains(response, self.post.text)
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, self.post.text)

        cache.clear()

    def test_edit_post(self):
        self.client.login(username='dmitry', password='12345')

        # проверяем доступна ли страница редактирования
        response = self.client.get(f'/{self.user.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

        # меняем содержимое поста
        self.client.post(f"/{self.user.username}/{self.post.id}/edit/", {'text': 'Привет мир'})

        # проверем соедржание поста на всех связных страницах
        response = self.client.get('')
        self.assertContains(response, 'Привет мир')
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, 'Привет мир')
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, 'Привет мир')

        # если вы не автор, то редирект на страницу поста
        self.client.logout()
        self.client.login(username='sarah', password='12345')
        response = self.client.get(f'/{self.user.username}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response, f'/{self.user.username}/{self.post.id}/')

        cache.clear()

    def test_image_post(self):
        self.client.login(username='dmitry', password='12345')

        # редактируем пост и добовляем картинку
        with open('test_files/california.jpg', 'rb') as img:
            self.client.post(f'/{self.user.username}/{self.post.id}/edit/',
                             {'author': self.user, 'id': self.post.id, 'text': 'Hello image', 'image': img})

        # проверяем содердание поста на картинку
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, '<img')

    def test_image_index(self):
        self.client.login(username='sarah', password='12345')

        with open('test_files/california.jpg', 'rb') as img:
            self.client.post('/new/',
                             {'author': self.user.id, 'text': 'Hello image', 'image': img})

        # проверяем содержание поста стартовой стрнице на картинку
        response = self.client.get('')
        self.assertContains(response, '<img')

        cache.clear()

    def test_image_group(self):
        self.client.login(username='dmitry', password='12345')
        group = Group.objects.create(title='test', slug='test')

        with open('test_files/california.jpg', 'rb') as img:
            self.client.post('/new/',
                             {'author': self.user.id, 'text': 'Hello image', 'group': group.id, 'image': img})

        # Проверяем содержание поста в группе на картинку
        response = self.client.get(f'/group/{group.slug}/')
        self.assertContains(response, '<img')

    def test_protect(self):
        self.client.login(username='dmitry', password='12345')

        with open('test_files/null_file', 'rb') as file:
            response = self.client.post('/new/',
                                        {'author': self.user.id, 'text': 'Hello image', 'image': file})
            self.assertFormError(response, 'form', 'image', ['Отправленный файл пуст.'])

    def test_cache(self):
        self.client.login(username='dmitry', password='12345')
        response = self.client.get('')

        self.post = Post.objects.create(
            text='Hello Cache',
            author=self.user)

        # проверяем кешируется ли страница
        response = self.client.get('')
        self.assertNotContains(response, self.post.text)
        cache.clear()

        # проверяем, что после очистки кэша пост появился на стартовой
        response = self.client.get('')
        self.assertContains(response, self.post.text)

    def test_follow_auth(self):
        user_1 = User.objects.create_user(username='user_1', email='connor.s@skynet.com', password='12345')
        self.client.login(username='dmitry', password='12345')

        # проверяем можно ли подпиаться на юзера
        response = self.client.get(f'/{user_1.username}/follow')
        self.assertRedirects(response, '/user_1/')
        self.assertTrue(Follow.objects.filter(user=self.user, author=user_1).exists())

        # проверяем можно ли отписаться от юзера
        response = self.client.get(f'/{user_1.username}/unfollow')
        self.assertRedirects(response, '/user_1/')

    def test_new_post_other_page(self):
        self.client.login(username='dmitry', password='12345')
        user_1 = User.objects.create_user(username='user_1', email='connor.s@skynet.com', password='12345')

        post = Post.objects.create(
            text='Hello test page',
            author=user_1)

        # проверяем появился ли новый пост на всех страницах
        self.client.get(f'/{user_1.username}/follow')
        response = self.client.get(f'/follow/')
        self.assertContains(response, post.text)

        self.client.logout()
        self.client.login(username='sarah', password='12345')

        response = self.client.get(f'/follow/')
        self.assertNotContains(response, post.text)

    def test_comment_auth(self):
        self.client.login(username='dmitry', password='12345')
        
        response = self.client.post(f'/{self.user.username}/{self.post.id}/comment/', {'text': 'Новый коммент!'})

        # проверяем появился ли комментарий после создания в базе и прошел редирект
        self.assertTrue(Comment.objects.filter(author = self.user.id, text='Новый коммент!').exists())
        self.assertRedirects(response, f'/{self.user.username}/{self.post.id}/')

    def test_comment_not_auth(self):
        response = self.client.post(f'/{self.user.username}/{self.post.id}/comment/',
                                    {'text': 'Новый коммент!'}, follow=True)

        # проверяем редирект на страницу авторизации, ели юзер не авторизован
        self.assertRedirects(response, response.redirect_chain[0][0])
