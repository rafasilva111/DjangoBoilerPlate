# Generated by Django 5.0 on 2024-10-29 18:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0005_remove_followrequest_followed_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='company',
        ),
        migrations.RemoveField(
            model_name='invitation',
            name='company',
        ),
        migrations.DeleteModel(
            name='Company',
        ),
    ]
