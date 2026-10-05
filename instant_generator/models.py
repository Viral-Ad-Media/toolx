from django.db import models
from tinymce.models import HTMLField
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
# User = get_user_model()


# Create your models here.
class InstantGenerator(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    Get_Attention = models.CharField(max_length=255)
    Identify_the_Problem_Your_Audience_Have = HTMLField()
    Provide_the_Solution = HTMLField()
    Present_your_Credentials = HTMLField()
    Show_the_Benefits = HTMLField()
    Give_Social_Proof = HTMLField()
    Make_Your_Offer = HTMLField()
    Give_a_Guarantee = HTMLField()
    Inject_Scarcity = HTMLField()
    Call_to_action = models.CharField(max_length=255)
    Give_a_Warning = HTMLField()
    Close_with_a_Reminder = HTMLField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='profile_pics', blank=True)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
