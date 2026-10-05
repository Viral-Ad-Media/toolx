from django.db import migrations


def normalize(apps, schema_editor):
    apps.get_model('instant_generator', 'Profile').objects.filter(
        avatar__in=['media/avatar/default.png', 'media/avarta/default.png', 'avatar/default.png']
    ).update(avatar='')


class Migration(migrations.Migration):
    dependencies = [('instant_generator', '0015_ratelimitbucket_profile_activation_pending_and_more')]
    operations = [migrations.RunPython(normalize, migrations.RunPython.noop)]
