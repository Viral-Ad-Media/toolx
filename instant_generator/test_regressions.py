from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import InstantGeneratorForm, SignUpForm
from .models import InstantGenerator, Paraphrase, Profile
from .tokens import account_activation_token

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', PUBLIC_ORIGIN='https://toolx.example.com')
class ActivationTests(TestCase):
    def pending_user(self):
        user = User.objects.create_user('pending', email='pending@example.com', password='StrongPass123!', is_active=False)
        Profile.objects.filter(user=user).update(activation_pending=True)
        user.refresh_from_db()
        return user

    def link(self, user, token=None):
        return reverse('activate', args=[urlsafe_base64_encode(force_bytes(user.pk)), token or account_activation_token.make_token(user)])

    def test_activation_is_single_use_and_does_not_login(self):
        user = self.pending_user()
        link = self.link(user)
        self.assertRedirects(self.client.get(link), reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.profile.email_confirmed)
        self.assertFalse(user.profile.activation_pending)
        user.is_active = False
        user.set_password('ChangedPass123!')
        user.save()
        self.assertEqual(self.client.get(link).status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_password_email_and_pending_changes_invalidate_token(self):
        for field, value in [('password', 'changed'), ('email', 'changed@example.com'), ('is_active', True)]:
            user = self.pending_user()
            link = self.link(user)
            setattr(user, field, value)
            user.save()
            self.assertEqual(self.client.get(link).status_code, 400)
            user.delete()
        user = self.pending_user()
        link = self.link(user)
        Profile.objects.filter(user=user).update(activation_pending=False)
        self.assertEqual(self.client.get(link).status_code, 400)

    def test_expired_token_and_bad_uid_are_rejected(self):
        user = self.pending_user()
        with patch.object(account_activation_token, '_now', return_value=timezone.now().replace(tzinfo=None) - timedelta(hours=2)):
            link = self.link(user)
        self.assertEqual(self.client.get(link).status_code, 400)
        self.assertEqual(self.client.get(reverse('activate', args=['_w', 'bad'])).status_code, 400)

    def test_signup_requires_email_and_rejects_duplicate_case(self):
        data = {'username': 'new', 'password1': 'StrongNewPass123!', 'password2': 'StrongNewPass123!'}
        self.assertFalse(SignUpForm(data).is_valid())
        User.objects.create_user('existing', email='Known@example.com')
        self.assertFalse(SignUpForm({**data, 'email': 'known@example.com'}).is_valid())

    def test_signup_sends_canonical_https_link_and_marks_pending(self):
        response = self.client.post(reverse('signup'), {'username': 'new', 'email': 'new@example.com', 'password1': 'StrongNewPass123!', 'password2': 'StrongNewPass123!'})
        self.assertRedirects(response, reverse('activation_sent'))
        self.assertTrue(User.objects.get(username='new').profile.activation_pending)
        self.assertIn('https://toolx.example.com/activate/', mail.outbox[0].body)

    def test_mail_failure_rolls_back_registration(self):
        with patch('instant_generator.views.send_mail', side_effect=SMTPException('failed')):
            response = self.client.post(reverse('signup'), {'username': 'new', 'email': 'new@example.com', 'password1': 'StrongNewPass123!', 'password2': 'StrongNewPass123!'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='new').exists())
        self.assertContains(response, 'could not send')

    def test_resend_only_pending_and_has_same_response(self):
        user = self.pending_user()
        first = self.client.post(reverse('activation_resend'), {'email': user.email})
        other = self.client.post(reverse('activation_resend'), {'email': 'absent@example.com'})
        self.assertEqual(first.status_code, other.status_code)
        self.assertEqual(first.url, other.url)
        self.assertEqual(len(mail.outbox), 1)
        Profile.objects.filter(user=user).update(activation_pending=False)
        self.client.post(reverse('activation_resend'), {'email': user.email})
        self.assertEqual(len(mail.outbox), 1)

    def test_csrf_is_required_for_signup(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('signup'), {}).status_code, 403)


class ContentTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='StrongPass123!')
        self.other = User.objects.create_user('other', password='StrongPass123!')
        self.fields = {f.name: 'Plain text' for f in InstantGenerator._meta.fields if f.get_internal_type() in ('CharField', 'TextField')}
        self.record = InstantGenerator.objects.create(user=self.owner, **self.fields)
        self.client.force_login(self.owner)

    def test_pdf_escapes_markup_without_loading_external_image(self):
        self.record.Provide_the_Solution = 'Use <b> in HTML & <img src="https://invalid.example/image.png">\nNext line'
        self.record.save()
        with patch('reportlab.lib.utils.ImageReader', side_effect=AssertionError('No images should be loaded')):
            response = self.client.get(reverse('pdf', args=[self.record.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_exports_enforce_ownership(self):
        self.client.force_login(self.other)
        for route in ('pdf', 'docx'):
            self.assertEqual(self.client.get(reverse(route, args=[self.record.pk])).status_code, 404)

    def test_docx_and_legacy_export_size_limit(self):
        response = self.client.get(reverse('docx', args=[self.record.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'PK'))
        self.record.Provide_the_Solution = 'x' * 10001
        self.record.save()
        for route in ('pdf', 'docx'):
            self.assertEqual(self.client.get(reverse(route, args=[self.record.pk])).status_code, 400)
        self.assertFalse(InstantGeneratorForm({**self.fields, 'Provide_the_Solution': 'x' * 10001}).is_valid())

    def test_creation_uses_current_user_and_rejects_invalid_input(self):
        response = self.client.post(reverse('create'), {**self.fields, 'user': self.other.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(InstantGenerator.objects.latest('pk').user_id, self.owner.pk)
        response = self.client.post(reverse('create'), {**self.fields, 'Provide_the_Solution': 'x' * 10001})
        self.assertEqual(response.status_code, 200)

    def test_history_pagination_and_dashboard_bounds(self):
        for i in range(24):
            InstantGenerator.objects.create(user=self.owner, **{**self.fields, 'Get_Attention': f'Entry {i}'})
            Paraphrase.objects.create(user=self.owner, Title=f'Draft {i}', Article='Draft body')
        self.assertEqual(len(self.client.get(reverse('my_adcopies')).context['adcopies']), 20)
        self.assertEqual(len(self.client.get(reverse('my_adcopies') + '?page=2').context['adcopies']), 5)
        self.assertEqual(len(self.client.get(reverse('paraphrase')).context['my_paraphrase']), 20)
        dashboard = self.client.get(reverse('dashboard'))
        self.assertEqual(len(dashboard.context['adcopies']), 6)
        self.assertEqual(len(dashboard.context['my_paraphrase']), 6)

    def test_draft_edit_and_preview_are_honest_and_owned(self):
        draft = Paraphrase.objects.create(user=self.owner, Title='Draft', Article='Original text')
        response = self.client.get(reverse('paraphrase_preview', args=[draft.pk]))
        self.assertContains(response, 'Original text', count=1)
        self.assertNotIn('generated', response.context)
        self.client.post(reverse('edit_draft', args=[draft.pk]), {'Title': 'Edited', 'Article': 'Updated text'})
        draft.refresh_from_db()
        self.assertEqual(draft.Article, 'Updated text')
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('edit_draft', args=[draft.pk]), {'Title': 'Unauthorized', 'Article': 'Bad'}).status_code, 404)

    def test_profile_fallback_and_immutable_email(self):
        self.assertContains(self.client.get(reverse('profile')), 'default-avatar')
        self.client.post(reverse('edit-profile'), {'username': 'owner', 'email': 'unverified@example.com', 'first_name': 'Owner', 'last_name': ''})
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.email, '')

    def test_logout_requires_csrf_post(self):
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('index'))

    def test_limits_are_shared_and_return_retry_after(self):
        with patch('instant_generator.middleware.time.time', return_value=1800000040):
            for _ in range(20):
                self.assertEqual(self.client.get(reverse('docx', args=[self.record.pk])).status_code, 200)
            response = self.client.get(reverse('pdf', args=[self.record.pk]))
            self.assertEqual(response.status_code, 429)
            self.assertIn('Retry-After', response)
            second = Client()
            second.force_login(self.owner)
            self.assertEqual(second.get(reverse('docx', args=[self.record.pk])).status_code, 429)
        with patch('instant_generator.middleware.time.time', return_value=1800000061):
            self.assertEqual(self.client.get(reverse('docx', args=[self.record.pk])).status_code, 200)

    def test_login_throttle(self):
        self.client.logout()
        with patch('instant_generator.middleware.time.time', return_value=1800000040):
            for _ in range(10):
                self.assertEqual(self.client.post(reverse('login'), {'username': 'no-user', 'password': 'wrong'}).status_code, 200)
            self.assertEqual(self.client.post(reverse('login'), {}).status_code, 429)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', PUBLIC_ORIGIN='https://toolx.example.com')
class FollowUpReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('reader', email='reader@example.com', password='StrongPass123!')

    def test_password_reset_uses_canonical_origin_and_remains_single_use(self):
        from django.contrib.auth.tokens import default_token_generator
        self.assertEqual(self.client.get(reverse('password_reset')).status_code, 200)
        response = self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertIn('https://toolx.example.com/reset/', mail.outbox[0].body)
        self.assertNotIn('testserver', mail.outbox[0].body)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        start = self.client.get(reverse('password_reset_confirm', args=[uid, token]))
        self.assertEqual(start.status_code, 302)
        self.assertRedirects(self.client.post(start.url, {'new_password1': 'NewStrongPass123!', 'new_password2': 'NewStrongPass123!'}), reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass123!'))
        self.assertFalse(default_token_generator.check_token(self.user, token))

    def test_password_change_screen_and_logout_work_for_nonstaff(self):
        self.client.force_login(self.user)
        page = self.client.get(reverse('password_change'))
        self.assertContains(page, 'Back to profile')
        self.assertNotContains(page, '/admin/')
        response = self.client.post(reverse('password_change'), {'old_password': 'StrongPass123!', 'new_password1': 'NewStrongPass123!', 'new_password2': 'NewStrongPass123!'})
        self.assertRedirects(response, reverse('password_change_done'))
        self.assertContains(self.client.get(reverse('password_change_done')), 'Back to dashboard')
        self.assertRedirects(self.client.post(reverse('logout')), reverse('index'))

    def test_public_pages_describe_supported_features_and_working_links(self):
        self.assertContains(self.client.get(reverse('features')), 'Sales letters')
        home = self.client.get(reverse('index'))
        self.assertNotContains(home, '100,000')
        self.assertContains(home, reverse('features'))
        pricing = self.client.get(reverse('pricing'))
        self.assertContains(pricing, 'no paid plans or checkout')
        self.assertNotContains(pricing, '$15')
        self.assertNotContains(pricing, 'href="#!"')
        self.assertNotContains(pricing, 'href="/about"')

    def test_control_characters_cannot_be_saved_or_exported(self):
        from .forms import ParaphraseForm
        fields = {f.name: 'Text' for f in InstantGenerator._meta.fields if f.get_internal_type() in ('CharField', 'TextField')}
        for control in ('\x01', '\x0b', '\ufffe'):
            invalid = {**fields, 'Provide_the_Solution': 'Text' + control + 'more'}
            self.assertFalse(InstantGeneratorForm(invalid).is_valid())
            self.assertFalse(ParaphraseForm({'Title': 'Draft', 'Article': 'Text' + control + 'more'}).is_valid())
            record = InstantGenerator.objects.create(user=self.user, **invalid)
            self.client.force_login(self.user)
            for route in ('pdf', 'docx'):
                self.assertContains(self.client.get(reverse(route, args=[record.pk])), 'unsupported control', status_code=400)
        valid = {**fields, 'Provide_the_Solution': 'Text\twith\nline\rbreaks'}
        self.assertTrue(InstantGeneratorForm(valid).is_valid())
        record = InstantGenerator.objects.create(user=self.user, **valid)
        self.assertEqual(self.client.get(reverse('docx', args=[record.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('pdf', args=[record.pk])).status_code, 200)

    def test_signup_conflict_rolls_back_and_returns_form_error(self):
        # Emulate another request reserving the username after form validation.
        conflicting = User(username=self.user.username, email='new@example.com')
        with patch.object(SignUpForm, 'save', return_value=conflicting):
            response = self.client.post(reverse('signup'), {'username': 'available', 'email': 'new@example.com', 'password1': 'StrongNewPass123!', 'password2': 'StrongNewPass123!'})
        self.assertContains(response, 'Registration could not be completed')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
