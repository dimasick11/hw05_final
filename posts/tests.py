import time

from django.test import TestCase, Client
from django.core.cache import cache
from django.contrib.auth.models import User

from .models import Post, Group


class TestYatube(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dmitry', email='connor.s@skynet.com', password='12345'
        )
        User.objects.create_user(
            username='sarah', email='connor.s@skynet.com', password='12345'
        )
        # создаем новый пост
        self.post = Post.objects.create(
            text='Hello World',
            author=self.user)

    def test_profile_page(self):
        response = self.client.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_user_not_auth(self):
        response = self.client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_new_post_user_auth(self):
        auth_user = self.client.login(username='dmitry', password='12345')
        self.assertTrue(auth_user)
        response = self.client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_create_new_post(self):
        self.client.login(username='dmitry', password='12345')
        # проверяем доступна ли страница с постом
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertEqual(response.status_code, 200)
        # проверем соедржание поста на всех связных страниц
        response = self.client.get('')
        self.assertContains(response, self.post.text)
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, self.post.text)
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, self.post.text)

    def test_edit_Post(self):
        self.client.login(username='dmitry', password='12345')
        # проверяем доступна ли страница редактирования
        response = self.client.get(f'/{self.user.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)
        cache.clear()
        # меняем содержимое поста
        self.post.text = 'Привет мир'
        self.post.save()
        # проверем соедржание поста на всех связных страницах
        response = self.client.get('')
        self.assertContains(response, self.post.text)
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, self.post.text)
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, self.post.text)
        # если вы не автор, то редирект на страницу поста
        self.client.logout()
        self.client.login(username='sarah', password='12345')
        response = self.client.get(f'/{self.user.username}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response, f'/{self.user.username}/{self.post.id}/')
        cache.clear()

    def test_image_post(self):
        self.client.login(username='dmitry', password='12345')
        # редактируем пост и добовляем картинку
        with open('posts/california.jpg', 'rb') as img:
            self.client.post(f'/{self.user.username}/{self.post.id}/edit/',
                             {'author': self.user, 'id': self.post.id, 'text': 'Hello image', 'image': img})
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')
        self.assertContains(response, '<img')

    def test_image_index(self):
        self.client.login(username='dmitry', password='12345')
        with open('posts/california.jpg', 'rb') as img:
            self.client.post('/new/',
                             {'author': self.user.id, 'text': 'Hello image', 'image': img})
        response = self.client.get('')
        self.assertContains(response, '<img')

    def test_image_group(self):
        self.client.login(username='dmitry', password='12345')
        group = Group.objects.create(title='test', slug='test')
        with open('posts/california.jpg', 'rb') as img:
            self.client.post('/new/',
                             {'author': self.user.id, 'text': 'Hello image', 'group': group.id, 'image': img})
        response = self.client.get(f'/group/{group.slug}/')
        self.assertContains(response, '<img')

    def test_protect(self):
        self.client.login(username='dmitry', password='12345')
        with open('posts/null_file', 'rb') as file:
            response = self.client.post('/new/',
                                        {'author': self.user.id, 'text': 'Hello image', 'image': file})
            self.assertFormError(response, 'form', 'image', ['Отправленный файл пуст.'])

    def test_cache(self):
        self.client.login(username='dmitry', password='12345')
        response = self.client.get('')
        self.post = Post.objects.create(
            text='Hello Cache',
            author=self.user)
        response = self.client.get('')
        self.assertNotContains(response, self.post.text)
        time.sleep(20)
        response = self.client.get('')
        self.assertContains(response, self.post.text)
        cache.clear()

    def test_follow_auth(self):
        user_1 = User.objects.create_user(
            username='user_1', email='connor.s@skynet.com', password='12345')

        self.client.login(username='dmitry', password='12345')

        response = self.client.get(f'/{user_1.username}/follow')
        self.assertRedirects(response, '/user_1/')
        response = self.client.get(f'/{user_1.username}/unfollow')
        self.assertRedirects(response, '/user_1/')

    def test_new_post_other_page(self):
        self.client.login(username='dmitry', password='12345')
        user_1 = User.objects.create_user(
            username='user_1', email='connor.s@skynet.com', password='12345')
        post = Post.objects.create(
            text='Hello test page',
            author=user_1)
        self.client.get(f'/{user_1.username}/follow')
        response = self.client.get(f'/follow/')
        self.assertContains(response, post.text)
        self.client.logout()
        self.client.login(username='sarah', password='12345')
        response = self.client.get(f'/follow/')
        self.assertNotContains(response, post.text)

    def test_comment_auth(self):
        self.client.login(username='sarah', password='12345')

        response = self.client.post(f'/{self.user.username}/{self.post.id}/comment/', data={'text': 'Новый коммент!'} )
        self.assertRedirects(response, f'/{self.user.username}/{self.post.id}/')

    def test_comment_not_auth(self):
        response = self.client.post(f'/{self.user.username}/{self.post.id}/comment/', data={'text': 'Новый коммент!'} )
        self.assertRedirects(response, '/auth/login/?next=%2Fdmitry%2F1%2Fcomment%2F')


