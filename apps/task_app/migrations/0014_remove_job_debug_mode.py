# Generated by Django 5.0 on 2024-11-17 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0013_alter_task_options_job_continue_mode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='debug_mode',
        ),
    ]