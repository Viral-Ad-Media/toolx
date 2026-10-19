from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.conf import settings
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
from django.core.files.images import get_image_dimensions

from .models import InstantGenerator, Paraphrase, Profile
from .text_validation import validate_document_text

User = get_user_model()


class DocumentTextForm(forms.ModelForm):
    def clean(self):
        cleaned = super().clean()
        for name, value in list(cleaned.items()):
            if isinstance(value, str):
                try:
                    validate_document_text(value)
                except ValidationError as error:
                    self.add_error(name, error)
        return cleaned


class CanonicalPasswordResetForm(PasswordResetForm):
    def save(self, **kwargs):
        origin = urlparse(settings.PUBLIC_ORIGIN)
        kwargs['domain_override'] = origin.netloc
        kwargs['use_https'] = origin.scheme == 'https'
        return super().save(**kwargs)


class InstantGeneratorForm(DocumentTextForm):
    class Meta:
        model = InstantGenerator
        fields = ('Get_Attention', 'Identify_the_Problem_Your_Audience_Have', 'Provide_the_Solution',
                  'Present_your_Credentials', 'Show_the_Benefits', 'Give_Social_Proof', 'Make_Your_Offer',
                  'Give_a_Guarantee', 'Inject_Scarcity', 'Call_to_action', 'Give_a_Warning', 'Close_with_a_Reminder')


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account already uses this email address.')
        return email

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class UserForm(forms.ModelForm):
    # Changing the confirmed destination requires a separate verification flow.
    email = forms.EmailField(disabled=True, required=False, help_text='Email changes are currently unavailable.')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar',)

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        if not hasattr(avatar, 'content_type'):
            return avatar

        w, h = get_image_dimensions(avatar)

        max_width = max_height = 100
        if w > max_width or h > max_height:
            raise forms.ValidationError(
                'Please use an image that is %s x %s pixels or smaller.' % (max_width, max_height)
            )

        main, _, sub = avatar.content_type.partition('/')
        if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'gif', 'png']):
            raise forms.ValidationError('Please use a JPEG, GIF or PNG image.')

        if len(avatar) > (20 * 1024):
            raise forms.ValidationError('Avatar file size may not exceed 20k.')

        return avatar


class ParaphraseForm(DocumentTextForm):
    class Meta:
        model = Paraphrase
        fields = ('Title', 'Article',)


class ActivationResendForm(forms.Form):
    email = forms.EmailField()
