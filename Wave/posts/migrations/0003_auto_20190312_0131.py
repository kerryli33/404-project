# Generated by Django 2.1.5 on 2019-03-12 01:31

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('posts', '0002_post_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='accessible_users',
            field=models.ManyToManyField(blank=True, related_name='accessible_posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='post',
            name='privacy',
            field=models.IntegerField(choices=[(0, 'PUBLIC'), (1, 'PRIVATE'), (2, 'ONLY FRIENDS'), (3, 'FRIEND OF A FRIEND'), (4, 'SERVER ONLY'), (5, 'ONLY ME')], default=0),
        ),
    ]
