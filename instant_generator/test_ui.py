from collections import Counter
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import InstantGenerator, Paraphrase


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.ids = []
        self.inputs = []
        self.labels = []
        self.links = []
        self.descriptions = []
        self.feed(content.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag in ('input', 'textarea', 'select'):
            self.inputs.append(attrs)
        if tag == 'label':
            self.labels.append(attrs.get('for'))
        if tag == 'a':
            self.links.append(attrs.get('href'))
        self.descriptions.extend(attrs.get('aria-describedby', '').split())


class WorkspaceUITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('writer', email='writer@example.com', password='StrongPass123!')

    def assert_accessible_fields(self, response):
        page = Page(response.content)
        self.assertEqual([key for key, count in Counter(page.ids).items() if count > 1], [])
        for field in page.inputs:
            if field.get('type') not in ('hidden', 'submit', 'checkbox'):
                self.assertIn(field.get('id'), page.labels)
        for target in page.descriptions:
            self.assertIn(target, page.ids)

    def test_failed_login_explains_error_and_keeps_return_destination(self):
        response = self.client.post(reverse('login'), {'username': 'writer', 'password': 'wrong', 'next': '/paraphrase/'})
        self.assertContains(response, 'Please enter a correct username and password')
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'name="next" value="/paraphrase/"')
        self.assert_accessible_fields(response)
        response = self.client.post(reverse('login'), {'username': 'writer', 'password': 'StrongPass123!', 'next': '/paraphrase/'})
        self.assertRedirects(response, '/paraphrase/')

    def test_invalid_signup_preserves_values_and_exposes_password_guidance(self):
        response = self.client.post(reverse('signup'), {'username': 'new-writer', 'email': 'invalid', 'password1': 'short', 'password2': 'short'})
        self.assertContains(response, 'value="new-writer"')
        self.assertContains(response, 'Enter a valid email address')
        self.assertContains(response, 'at least 8 characters')
        self.assert_accessible_fields(response)

    def test_empty_workspace_exposes_creation_and_history_destinations(self):
        self.client.force_login(self.user)
        for route in ('dashboard', 'my_adcopies', 'paraphrase'):
            response = self.client.get(reverse(route))
            page = Page(response.content)
            for target in ('create', 'create_paraphrase', 'my_adcopies', 'paraphrase', 'profile'):
                self.assertIn(reverse(target), page.links)
            self.assertContains(response, 'id="main-content"')
            self.assertContains(response, 'empty-state')

    def test_sales_editor_keeps_all_fields_and_validation_messages(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('create'), {'Get_Attention': 'A saved headline'})
        self.assertContains(response, 'This field is required')
        self.assert_accessible_fields(response)
        page = Page(response.content)
        names = {field.get('name') for field in page.inputs}
        for field in InstantGenerator._meta.fields:
            if field.get_internal_type() in ('CharField', 'TextField'):
                self.assertIn(field.name, names)
        self.assertFalse(InstantGenerator.objects.exists())

    def test_draft_edit_preserves_multiline_content_and_escapes_markup(self):
        self.client.force_login(self.user)
        draft = Paraphrase.objects.create(user=self.user, Title='Outline', Article='Old')
        body = 'First line\n<script>alert(1)</script>\nLast line'
        self.assertRedirects(self.client.post(reverse('edit_draft', args=[draft.pk]), {'Title': 'Revised', 'Article': body}), reverse('paraphrase_preview', args=[draft.pk]))
        page = self.client.get(reverse('paraphrase_preview', args=[draft.pk]))
        self.assertContains(page, '&lt;script&gt;')
        self.assertNotContains(page, '<script>alert(1)</script>')
        self.assertContains(page, 'First line<br>')
        self.assertContains(page, reverse('edit_draft', args=[draft.pk]))

    def test_profile_form_keeps_upload_and_disabled_email_contract(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('edit-profile'))
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assert_accessible_fields(response)
        email = next(field for field in Page(response.content).inputs if field.get('name') == 'email')
        self.assertIn('disabled', email)
