###
# General imports
##

## Default
import json

## Django
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

## Celery
from celery.result import AsyncResult
from celery.app.control import Control

## Django Celery Beat
from django_celery_beat.models import CrontabSchedule

### App-specific imports

## Models
from apps.common.models import BaseModel
from apps.user_app.models import User

## Tasks and Functions
from apps.task_app.tasks import _launch_task
from apps.task_app.functions import delete_task_logs
from config.celery import app

### Models

class BaseTask(BaseModel):
    """
    Abstract base model for tasks with a specific task type.

    Attributes:
        type (str): The type of task, chosen from 'EMPTY', 'SMALL', 'MEDIUM', or 'LARGE'.
    """

    class TaskType(models.TextChoices):
        EMPTY = 'EMPTY', 'Empty'
        SMALL = 'SMALL', 'Small'
        MEDIUM = 'MEDIUM', 'Medium'
        LARGE = 'LARGE', 'Large'
        FAILURE = 'FAILURE', 'Failure'
    
    type = models.CharField(
        max_length=12,
        choices=TaskType.choices,
        default=None,
        null=True
    )

    class Meta:
        abstract = True


class Condition(models.Model):
    """
    Abstract base class for conditions used to control job/task execution.

    This is meant to be inherited by specific condition types like
    `TimeCondition` and `MaxRecordsCondition`.
    """
    
    class Meta:
        abstract = True 


class TimeCondition(Condition):
    """
    Condition based on a time schedule, using `CrontabSchedule` for scheduling.

    Attributes:
        crontab (ForeignKey): Foreign key to a `CrontabSchedule` instance.
    """
    crontab = models.ForeignKey(
        CrontabSchedule,
        on_delete=models.CASCADE,
    )
    
    def __str__(self):
        return f"{self.id} - Crontab: {self.crontab}"



class Job(BaseTask):
    """
    Represents a job within the system, inheriting from `BaseTask`.

    Attributes:
        name (str): The name of the job, must be unique.
        company (ForeignKey): The associated company user.
        log_path (str): Path for log storage.
        enabled (bool): Whether the job is enabled.
        parent_task (ForeignKey): The task related to this job.
        parent_job (ForeignKey): Reference to a parent job.
        starting_condition (GenericForeignKey): Condition to start the job.
        stopping_condition (GenericForeignKey): Condition to stop the job.
        debug_mode (bool): Whether the job is in debug mode.
        last_run (DateTime): Last run time of the job.
    """
    name = models.CharField(max_length=255, verbose_name="Job Name", unique=True)
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs', verbose_name="Company")
    log_path = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    parent_task = models.ForeignKey('Task', on_delete=models.SET_NULL, blank=True, null=True, related_name='jobs')
    parent_job = models.ForeignKey('Job', on_delete=models.SET_NULL, blank=True, null=True, related_name='child_jobs')
    
    starting_condition_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='start_condition_type', null=True)
    starting_condition_id = models.PositiveIntegerField(null=True)
    starting_condition = GenericForeignKey('starting_condition_type', 'starting_condition_id')
    
    stopping_condition_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='stop_condition_type', null=True)
    stopping_condition_id = models.PositiveIntegerField(null=True)
    stopping_condition = GenericForeignKey('stopping_condition_type', 'stopping_condition_id')

    continue_mode = models.BooleanField(default=False)
    last_run = models.DateTimeField(null=True, blank=True)
        
    def delete(self, *args, **kwargs):
        """
        Deletes the job and its associated conditions if they exist.
        """
        if self.stopping_condition:
            self.stopping_condition.delete()
        if self.starting_condition:
            self.starting_condition.delete()
        
        super().delete(*args, **kwargs)

    def pause_task(self):
        """
        Pauses the periodic task associated with this job.
        """
        if self.periodic_task:
            self.periodic_task.enabled = False
            self.periodic_task.save()

    def resume_task(self):
        """
        Resumes the periodic task associated with this job.
        """
        if self.periodic_task:
            self.periodic_task.enabled = True
            self.periodic_task.save()





class Task(BaseTask):
    """
    Represents an individual task within a job, inheriting from `BaseTask`.

    Attributes:
        started_at (DateTime): The start time of the task.
        paused_at (DateTime): The time when the task was paused.
        resumed_at (DateTime): The time when the task was resumed.
        finished_at (DateTime): The time when the task was finished.
        log_path (str): Path for log storage.
        sql_file (str): SQL file path for the task.
        celery_task_id (str): Celery task ID.
        job (ForeignKey): The job associated with this task.
        debug_mode (bool): Whether the task is in debug mode.
        status (str): Status of the task, e.g., STARTING, RUNNING, CANCELED.
    """
    started_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True)
    log_path = models.CharField(max_length=255, null=True, blank=True)
    sql_file = models.CharField(max_length=255, null=True, blank=True)
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, blank=True, null=True, related_name='tasks')
    debug_mode = models.BooleanField(default=False)
    step = models.IntegerField(default=1)
    
    class Status(models.TextChoices):
        STARTING = 'STARTING', 'Starting'
        PAUSED = 'PAUSED', 'Paused'
        RUNNING = 'RUNNING', 'Running'
        CANCELED = 'CANCELED', 'Canceled'
        FAILED = 'FAILED', 'Failed'
        FINISHED = 'FINISHED', 'Finished'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.STARTING,
    )
    
    
    class Meta:
        permissions = [
            ("can_view_task", "Can view task's details"),
            ("can_view_tasks", "Can view tasks list"),
            ("can_create_task", "Can create task"),
            ("can_edit_task", "Can edit task"),
            
            ("can_restart_task", "Can restart task"),
            ("can_pause_task", "Can pause task"),
            ("can_resume_task", "Can resume task"),
            ("can_cancel_task", "Can cancel task"),
            ("can_delete_task", "Can delete task"),
        ]
    
    def __str__(self):
        return f"Task: {self.id} - {self.type}"

    def launch(self, continue_mode= False):
        """
        Launches the task by setting its status and initiating a Celery task.
        """
        
        self.status = Task.Status.STARTING
        self.save()
        
        if self.debug_mode:
            _launch_task(self.id, continue_mode)
        else:
            celery_id = CeleryTask.objects.create(
                task=self, 
                celery_task_id=_launch_task.delay(self.id, continue_mode).id
            )
            celery_id.save()
            
        
        
    def purge(self):
        """
        Deletes task logs associated with this task.
        """
        delete_task_logs(self)
            
    def restart(self):
        """
        Restarts the task by resetting and relaunching it.
        """
        if self.status == Task.Status.RUNNING:
            self.kill_current_celery_task()
        
        # reset milestones
        self.step = 1
        self.started_at = timezone.now()
        self.finished_at = None
        self.save()
        self.purge()
        self.launch()
                
    def cancel(self):
        """
        Cancels the task by revoking the Celery task and updating the status.
        """
        # stop celery task
        self.kill_current_celery_task()
        
        self.status = Task.Status.CANCELED
        self.finished_at = timezone.now()
        self.save()

    
    def pause(self):
        if self.status == Task.Status.RUNNING:
            # stop celery task
            self.kill_current_celery_task()

            
            self.paused_at = timezone.now()
            self.status = Task.Status.PAUSED
            self.save()

        
    def resume(self):
        
        if self.status == Task.Status.PAUSED:

            self.resumed_at = timezone.now()
            self.save()
            self.launch(continue_mode=True)
    
    def kill_current_celery_task(self):
        """
        Kills the task by revoking the Celery task
        """
        # stop celery task
        result = AsyncResult(self.celery_tasks.last().celery_task_id, app=app)
        result.revoke(terminate=True)
    
            
class CeleryTask(models.Model):
    """
    Celery task ID model.
    """
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True, related_name='celery_tasks')
    
    def __str__(self):
        return f"Celery Task ID: {self.celery_task_id}"