# Generated by Django 5.0 on 2024-11-15 17:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0009_rename_counter_task_step'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='celery_task_id',
        ),
        migrations.CreateModel(
            name='CeleryId',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('celery_task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('task_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='celelry_ids', to='task_app.task')),
            ],
        ),
    ]
