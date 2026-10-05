from django.db import models
# from tinymce.models import HTMLField
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class InstantGenerator(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    Get_Attention = models.CharField(max_length=255)
    Identify_the_Problem_Your_Audience_Have = models.TextField()
    Provide_the_Solution = models.TextField()
    Present_your_Credentials = models.TextField()
    Show_the_Benefits = models.TextField()
    Give_Social_Proof = models.TextField()
    Make_Your_Offer = models.TextField()
    Give_a_Guarantee = models.TextField()
    Inject_Scarcity = models.TextField()
    Call_to_action = models.CharField(max_length=255)
    Give_a_Warning = models.TextField()
    Close_with_a_Reminder = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.Get_Attention}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatar', blank=True, default='media/avatar/default.png')
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
