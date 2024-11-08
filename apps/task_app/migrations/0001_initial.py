# Generated by Django 5.0 on 2024-10-29 16:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('django_celery_beat', '0019_alter_periodictasks_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MaxRecordsCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_records', models.IntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(choices=[('EXTRACT', 'Extract'), ('TRANSFORM', 'Transform'), ('LOAD', 'Load'), ('FULL_PROCESS', 'Full Process')], default=None, max_length=12, null=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Job Name')),
                ('log_path', models.CharField(max_length=255)),
                ('enabled', models.BooleanField(default=True)),
                ('starting_condition_id', models.PositiveIntegerField(null=True)),
                ('stopping_condition_id', models.PositiveIntegerField(null=True)),
                ('debug_mode', models.BooleanField(default=False)),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to=settings.AUTH_USER_MODEL, verbose_name='Company')),
                ('parent_job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_jobs', to='task_app.job')),
                ('starting_condition_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='start_condition_type', to='contenttypes.contenttype')),
                ('stopping_condition_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stop_condition_type', to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(choices=[('EXTRACT', 'Extract'), ('TRANSFORM', 'Transform'), ('LOAD', 'Load'), ('FULL_PROCESS', 'Full Process')], default=None, max_length=12, null=True)),
                ('started_at', models.DateTimeField(auto_now=True)),
                ('paused_at', models.DateTimeField(null=True)),
                ('resumed_at', models.DateTimeField(null=True)),
                ('finished_at', models.DateTimeField(null=True)),
                ('log_path', models.CharField(blank=True, max_length=255, null=True)),
                ('sql_file', models.CharField(blank=True, max_length=255, null=True)),
                ('celery_task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stopping_condition_max_records', models.IntegerField(blank=True, default=None, null=True)),
                ('extract_sql_file', models.CharField(blank=True, max_length=255, null=True)),
                ('transform_sql_file', models.CharField(blank=True, max_length=255, null=True)),
                ('debug_mode', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('STARTING', 'Starting'), ('RUNNING', 'Running'), ('PAUSED', 'Paused'), ('CANCELED', 'Canceled'), ('FAILED', 'Failed'), ('FINISHED', 'Finished')], default='STARTING', max_length=10)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='task_app.job')),
                ('parent_task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subtasks', to='task_app.task')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='job',
            name='parent_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='task_app.task'),
        ),
        migrations.CreateModel(
            name='TimeCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crontab', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.crontabschedule')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]