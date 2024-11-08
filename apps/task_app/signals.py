###
# General imports
##

## Django Signals
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

## Celery Signals
from celery.signals import task_failure

## Models
from apps.task_app.models import Task


@receiver(post_save, sender=Task)
def post_create_task_handler(sender, instance, created, **kwargs):
    """
    Signal handler triggered after a Task instance is saved.

    - If the instance is newly created, it will automatically launch the task.

    Args:
        sender (Model): The model class that sent the signal (Task).
        instance (Task): The instance of the model that was saved.
        created (bool): A boolean indicating if a new instance was created.
        kwargs (dict): Additional keyword arguments.
    """
    if created:
        instance.launch()


@receiver(post_delete, sender=Task)
def post_delete_task_handler(sender, instance, **kwargs):
    """
    Signal handler triggered after a Task instance is deleted.

    - This will automatically purge the task's logs and related data.

    Args:
        sender (Model): The model class that sent the signal (Task).
        instance (Task): The instance of the model that was deleted.
        kwargs (dict): Additional keyword arguments.
    """
    instance.purge()


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """
    Signal handler for Celery task failure events.

    - Sets the status of the Task to FAILED if the task fails during execution.

    Args:
        sender (Task): The task class that failed.
        task_id (str): ID of the failed Celery task.
        exception (Exception): The exception raised by the task.
        args (tuple): Positional arguments passed to the task.
        kwargs (dict): Keyword arguments passed to the task.
        traceback (Traceback): Traceback of the exception.
        einfo (ExceptionInfo): Exception information.
        extra (dict): Additional keyword arguments.
    """
    print(f'Failure: {task_id}')
    if task_id:
        task = Task.objects.get(celery_task_id=task_id)
        task.status = Task.Status.FAILED
        task.save()
