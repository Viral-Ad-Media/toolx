from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import InstantGenerator, Paraphrase, Profile

User = get_user_model()


class InstantGeneratorViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='strong-pass-1')
        self.other_user = User.objects.create_user(username='other', password='strong-pass-2')

        self.owner_adcopy = InstantGenerator.objects.create(
            user=self.owner,
            Get_Attention='Attention',
            Identify_the_Problem_Your_Audience_Have='Problem',
            Provide_the_Solution='Solution',
            Present_your_Credentials='Credentials',
            Show_the_Benefits='Benefits',
            Give_Social_Proof='Proof',
            Make_Your_Offer='Offer',
            Give_a_Guarantee='Guarantee',
            Inject_Scarcity='Scarcity',
            Call_to_action='Act now',
            Give_a_Warning='Warning',
            Close_with_a_Reminder='Reminder',
        )
        self.owner_paraphrase = Paraphrase.objects.create(
            user=self.owner,
            Title='Example',
            Article='Original article text.',
        )

    def test_preview_requires_login(self):
        response = self.client.get(reverse('preview', args=[self.owner_adcopy.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_preview_blocks_non_owner(self):
        self.client.login(username='other', password='strong-pass-2')
        response = self.client.get(reverse('preview', args=[self.owner_adcopy.pk]))
        self.assertEqual(response.status_code, 404)

    def test_preview_allows_owner(self):
        self.client.login(username='owner', password='strong-pass-1')
        response = self.client.get(reverse('preview', args=[self.owner_adcopy.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['generated'].pk, self.owner_adcopy.pk)

    def test_paraphrase_preview_blocks_non_owner(self):
        self.client.login(username='other', password='strong-pass-2')
        response = self.client.get(reverse('paraphrase_preview', args=[self.owner_paraphrase.pk]))
        self.assertEqual(response.status_code, 404)


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='strong-pass-3')

    def test_edit_profile_updates_user_and_avatar(self):
        self.client.login(username='alice', password='strong-pass-3')
        avatar = SimpleUploadedFile(
            'avatar.gif',
            (
                b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!'
                b'\xf9\x04\x01\n\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00'
                b'\x00\x02\x02L\x01\x00;'
            ),
            content_type='image/gif',
        )
        response = self.client.post(
            reverse('edit-profile'),
            {
                'username': 'alice-updated',
                'email': 'alice@example.com',
                'first_name': 'Alice',
                'last_name': 'Updated',
                'avatar': avatar,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alice-updated')
        self.assertEqual(self.user.email, 'alice@example.com')
        self.assertEqual(self.user.first_name, 'Alice')
        self.assertEqual(self.user.last_name, 'Updated')

        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar.name.startswith('avatar/'))


class SignUpTests(TestCase):
    def test_signup_creates_inactive_user(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'new-user',
                'email': 'new@example.com',
                'first_name': 'New',
                'last_name': 'User',
                'password1': 'VeryStrongPass123!',
                'password2': 'VeryStrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('activation_sent'))
        user = User.objects.get(username='new-user')
        self.assertFalse(user.is_active)
