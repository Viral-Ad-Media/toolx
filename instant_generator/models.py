from django.db import models
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class InstantGenerator(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    Get_Attention = models.CharField(max_length=255)
    Identify_the_Problem_Your_Audience_Have = models.TextField(validators=[MaxLengthValidator(10000)])
    Provide_the_Solution = models.TextField(validators=[MaxLengthValidator(10000)])
    Present_your_Credentials = models.TextField(validators=[MaxLengthValidator(10000)])
    Show_the_Benefits = models.TextField(validators=[MaxLengthValidator(10000)])
    Give_Social_Proof = models.TextField(validators=[MaxLengthValidator(10000)])
    Make_Your_Offer = models.TextField(validators=[MaxLengthValidator(10000)])
    Give_a_Guarantee = models.TextField(validators=[MaxLengthValidator(10000)])
    Inject_Scarcity = models.TextField(validators=[MaxLengthValidator(10000)])
    Call_to_action = models.CharField(max_length=255)
    Give_a_Warning = models.TextField(validators=[MaxLengthValidator(10000)])
    Close_with_a_Reminder = models.TextField(validators=[MaxLengthValidator(10000)])
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['user', '-created_on', '-id'], name='adcopy_user_history')]

    def __str__(self):
        return f'{self.Get_Attention}'


class Paraphrase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    Title = models.CharField(max_length=255)
    Article = models.TextField(validators=[MaxLengthValidator(10000)])
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['user', '-created_on', '-id'], name='draft_user_history')]

    def __str__(self):
        return f'{self.Title}'


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to='avatar', blank=True, default='')
    activation_pending = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def update_profile(sender, instance, created, **kwargs):
    if not kwargs.get("raw"):
        Profile.objects.get_or_create(user=instance)


class RateLimitBucket(models.Model):
    key = models.CharField(max_length=64)
    bucket = models.BigIntegerField()
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['key', 'bucket'], name='unique_rate_bucket')]
