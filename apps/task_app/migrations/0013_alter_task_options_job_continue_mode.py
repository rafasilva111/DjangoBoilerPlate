# Generated by Django 5.0 on 2024-11-17 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0012_rename_celeryid_celerytask_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'permissions': [('can_view_task', "Can view task's details"), ('can_view_tasks', 'Can view tasks list'), ('can_create_task', 'Can create task'), ('can_edit_task', 'Can edit task'), ('can_restart_task', 'Can restart task'), ('can_pause_task', 'Can pause task'), ('can_resume_task', 'Can resume task'), ('can_cancel_task', 'Can cancel task'), ('can_delete_task', 'Can delete task')]},
        ),
        migrations.AddField(
            model_name='job',
            name='continue_mode',
            field=models.BooleanField(default=False),
        ),
    ]
