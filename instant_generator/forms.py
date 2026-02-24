from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.files.images import get_image_dimensions

from .models import InstantGenerator, Paraphrase, Profile

User = get_user_model()


class InstantGeneratorForm(forms.ModelForm):
    class Meta:
        model = InstantGenerator
        fields = ('Get_Attention', 'Identify_the_Problem_Your_Audience_Have', 'Provide_the_Solution',
                  'Present_your_Credentials', 'Show_the_Benefits', 'Give_Social_Proof', 'Make_Your_Offer',
                  'Give_a_Guarantee', 'Inject_Scarcity', 'Call_to_action', 'Give_a_Warning', 'Close_with_a_Reminder')


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class UserForm(forms.ModelForm):
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

        main, sub = avatar.content_type.split('/')
        if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'gif', 'png']):
            raise forms.ValidationError('Please use a JPEG, GIF or PNG image.')

        if len(avatar) > (20 * 1024):
            raise forms.ValidationError('Avatar file size may not exceed 20k.')

        return avatar


class ParaphraseForm(forms.ModelForm):
    class Meta:
        model = Paraphrase
        fields = ('Title', 'Article',)
