from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
User = get_user_model()


# Create your models here.
class Question(models.Model):
    question_no = models.IntegerField(default=0)
    question_name = models.CharField(max_length=20, unique=True, default=' ')
    question_text = models.TextField(blank=True, max_length=100)

    def __str__(self):
        return str(self.question_name)

    class Meta:
        ordering = ["question_no"]


class Answer(models.Model):
    question_relation = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.answer


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
    Call_to_action = models.TextField()
    Give_a_Warning = models.TextField()
    Close_with_a_Reminder = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('view_request', 'Can view request'),
            ("can_approve_request", "Can approve a request"),
        )

    def __str__(self):
        return f'{self.user.username} fundrequest'


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
