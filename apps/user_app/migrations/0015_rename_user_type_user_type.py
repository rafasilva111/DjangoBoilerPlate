# Generated by Django 5.0 on 2024-12-05 17:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0014_alter_user_options_alter_user_user_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='user_type',
            new_name='type',
        ),
    ]
