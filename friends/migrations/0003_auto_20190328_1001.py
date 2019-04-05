# Generated by Django 2.1.5 on 2019-03-28 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0002_auto_20190314_2028'),
    ]

    operations = [
        migrations.AddField(
            model_name='follow',
            name='user1_server',
            field=models.CharField(default='000', max_length=200),
        ),
        migrations.AddField(
            model_name='follow',
            name='user2_server',
            field=models.CharField(default='000', max_length=200),
        ),
        migrations.AddField(
            model_name='friendrequest',
            name='recipient_server',
            field=models.CharField(default='000', max_length=200),
        ),
        migrations.AddField(
            model_name='friendrequest',
            name='requestor_server',
            field=models.CharField(default='000', max_length=200),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user1',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user2',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='friendrequest',
            name='recipient',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='friendrequest',
            name='requestor',
            field=models.UUIDField(),
        ),
    ]