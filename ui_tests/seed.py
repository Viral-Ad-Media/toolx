import json
import django

django.setup()
from django.contrib.auth import get_user_model
from django.test import Client
from instant_generator.models import InstantGenerator, Paraphrase

user = get_user_model().objects.create_user('example_writer', email='writer@example.com')
empty = get_user_model().objects.create_user('example_empty', email='empty@example.com')
fields = {field.name: 'Example copy for a neighborhood writing workshop.'
          for field in InstantGenerator._meta.fields if field.get_internal_type() in ('CharField', 'TextField')}
for index in range(22):
    letter = InstantGenerator.objects.create(user=user, **{**fields, 'Get_Attention': f'Example workshop invitation {index + 1}'})
    draft = Paraphrase.objects.create(user=user, Title=f'Example article outline {index + 1}', Article='First paragraph.\n\nA place to revise your ideas.')
client = Client()
client.force_login(user)
writer_cookie = client.cookies['sessionid'].value
empty_client = Client()
empty_client.force_login(empty)
# Only the local browser runner consumes this output; it is never written to artifacts.
print(json.dumps({'writer': writer_cookie, 'empty': empty_client.cookies['sessionid'].value, 'letter': letter.pk, 'draft': draft.pk}))
