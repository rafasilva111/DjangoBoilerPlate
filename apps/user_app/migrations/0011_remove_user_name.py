# Generated by Django 5.0 on 2024-11-13 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0010_alter_user_managers_remove_user_birth_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='name',
        ),
    ]
