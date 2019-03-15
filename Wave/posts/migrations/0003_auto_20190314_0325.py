# Generated by Django 2.1.5 on 2019-03-14 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20190314_0319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='content_type',
            field=models.CharField(choices=[('text/plain', 'text/plain'), ('text/markdown', 'text/markdown'), ('application/base64', 'application/base64'), ('image/jpeg;base64', 'image/jpeg;base64'), ('image/png;base64', 'image/png;base64')], default='text/plain', max_length=18),
        ),
    ]