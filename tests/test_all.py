import os

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from posts.models import Follow, Group, Post

User = get_user_model()


# Create your tests here.

class TestPostsApp(TestCase):
    def setUp(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded = SimpleUploadedFile(
            'small.gif', self.small_gif, content_type='image/gif')
        self.client = Client()
        self.user = User.objects.create(
            username='test', email='alice@spam.eggs', password='!1Qazerfc')
        cache.clear()

    def test_registration(self):
        self.client.post("/auth/signup/", {'username': 'kekekeke',
                                           'first_name': 'spam',
                                           'last_name': 'eggs',
                                           'email': 'alice@spam.eggs',
                                           'password1': '!1Qazerfc',
                                           'password2': '!1Qazerfc'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         'Подтверждение регистрации YABE')

    def test_profile_page(self):
        self.assertEqual(self.client.get("/test/").status_code, 200)

    def test_new_post(self):
        self.client.force_login(self.user)
        self.client.post("/new/", {'text': 'Awesome meme'})
        response = self.client.get("/test/")
        self.assertEqual(len(response.context["page"]), 1)

    def test_unauthorized(self):
        self.assertRedirects(self.client.get("/new/"), '/auth/login/?next=/new/',
                             status_code=302, target_status_code=200, fetch_redirect_response=True)

    def test_post_show(self):
        post = Post.objects.create(text="Awesome meme", author=self.user)
        self.assertContains(self.client.get(""), "Awesome meme")
        self.assertContains(self.client.get("/test/"), "Awesome meme")
        self.assertContains(self.client.get(
            f"/test/{post.pk}/"), "Awesome meme")

    def test_post_edit(self):
        post = Post.objects.create(text="Awesome meme", author=self.user)
        self.client.force_login(self.user)
        self.client.post(f"/test/{post.pk}/edit/", {'text': 'Not awesome'})
        self.assertContains(self.client.get(""), "Not awesome")
        self.assertContains(self.client.get("/test/"), "Not awesome")
        self.assertContains(self.client.get(
            f"/test/{post.pk}/"), "Not awesome")

    def test_404(self):
        self.assertEqual(self.client.get(
            "/awesome-test-page/").status_code, 404)

    def test_show_img(self):
        self.client.force_login(self.user)
        self.client.post('/new/', {'text': 'fred', 'image': self.uploaded})
        self.assertContains(self.client.get("/test/1/"),  "<img")

    def test_img_on_all_pages(self):
        group = Group.objects.create(
            title='memes', slug='memes', description='Also memes')
        self.client.force_login(self.user)
        self.client.post(
            '/new/', {'text': 'fred', 'group': group.id, 'image': self.uploaded})
        self.assertContains(self.client.get(""), "<img")
        self.assertContains(self.client.get("/test/"), "<img")
        self.assertContains(self.client.get(
            f"/group/{group.slug}/"), "<img")

    def test_upload_non_img(self):
        self.client.force_login(self.user)
        with open('manage.py', 'rb') as fp:
            response = self.client.post('/new/', {'text': 'fred', 'image': fp})
            self.assertFalse(response.context['form'].is_valid())

    def test_cache(self):
        key = make_template_fragment_key('index_page', [1])
        self.assertFalse(cache.get(key))
        self.client.get("")
        self.assertTrue(cache.get(key))

    def test_follow(self):
        user = User.objects.create(
            username='test2', email='alice@spam.eggs', password='!1Qazerfc')
        self.client.force_login(self.user)
        self.client.get(f"/{user.username}/follow/")
        self.assertTrue(self.client.get(
            f"/{user.username}/").context['following'])

    def test_unfollow(self):
        user = User.objects.create(
            username='test2', email='alice@spam.eggs', password='!1Qazerfc')
        self.client.force_login(self.user)
        Follow.objects.create(user=self.user, author=user)
        self.client.get(f"/{user.username}/unfollow/")
        self.assertFalse(self.client.get(
            f"/{user.username}/").context['following'])


    def test_following_read_feed(self):
        follower_user = self.user
        writer_user = User.objects.create(
            username='test2', email='alice@spam.eggs', password='!1Qazerfc')
        dummy_user = User.objects.create(
            username='test3', email='alice@spam.eggs', password='!1Qazerfc')

        follower_client = self.client
        writer_client = Client()
        dummy_client = Client()

        follower_client.force_login(follower_user)
        writer_client.force_login(writer_user)
        dummy_client.force_login(dummy_user)

        follower_client.get(f"/{writer_user.username}/follow/")
        writer_client.post("/new/", {'text': 'Awesome meme'})
        self.assertContains(follower_client.get("/follow/"), 'Awesome meme')
        self.assertNotContains(
            dummy_client.get("/follow/"), 'Awesome meme')

    def test_comments(self):
        self.unauth_client = Client()
        self.client.force_login(self.user)
        self.client.post("/new/", {'text': 'Good meme'})
        self.client.post("/test/1/comment/", {'text': 'Comment'})
        self.assertContains(self.client.get(
            f"/{self.user.username}/1/"), 'Comment')
        self.assertRedirects(self.unauth_client.post(
            "/test/1/comment/", {'text': 'Forbidden'}), f"/auth/login/?next=/{self.user.username}/1/comment/",  status_code=302, target_status_code=200,)
