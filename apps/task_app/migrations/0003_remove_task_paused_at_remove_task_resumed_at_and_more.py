# Generated by Django 5.0 on 2024-11-12 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0002_remove_task_company_remove_task_extract_sql_file_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='paused_at',
        ),
        migrations.RemoveField(
            model_name='task',
            name='resumed_at',
        ),
        migrations.AlterField(
            model_name='job',
            name='type',
            field=models.CharField(choices=[('EMPTY', 'Empty'), ('SMALL', 'Small'), ('MEDIUM', 'Medium'), ('LARGE', 'Large'), ('FAILURE', 'Failure')], default=None, max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('STARTING', 'Starting'), ('RUNNING', 'Running'), ('CANCELED', 'Canceled'), ('FAILED', 'Failed'), ('FINISHED', 'Finished')], default='STARTING', max_length=10),
        ),
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.CharField(choices=[('EMPTY', 'Empty'), ('SMALL', 'Small'), ('MEDIUM', 'Medium'), ('LARGE', 'Large'), ('FAILURE', 'Failure')], default=None, max_length=12, null=True),
        ),
    ]
