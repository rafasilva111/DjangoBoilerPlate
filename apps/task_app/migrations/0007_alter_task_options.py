# Generated by Django 5.0 on 2024-11-13 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0006_alter_task_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'permissions': [('can_view_task', "Can view task's details"), ('can_view_tasks', 'Can view tasks list'), ('can_create_task', 'Can create task'), ('can_edit_task', 'Can edit task'), ('can_restart_task', 'Can restart task'), ('can_cancel_task', 'Can cancel task'), ('can_delete_task', 'Can delete task')]},
        ),
    ]
