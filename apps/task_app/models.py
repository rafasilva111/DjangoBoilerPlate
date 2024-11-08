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


class MaxRecordsCondition(Condition):
    """
    Condition based on a maximum number of records.

    Attributes:
        max_records (int): Maximum number of records to trigger this condition.
    """
    max_records = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.id} - Max Records: {self.max_records}"


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

    debug_mode = models.BooleanField(default=False) 
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
        stopping_condition_max_records (int): Max records for stopping condition.
        debug_mode (bool): Whether the task is in debug mode.
        status (str): Status of the task, e.g., STARTING, RUNNING, CANCELED.
    """
    started_at = models.DateTimeField(auto_now=True)
    paused_at = models.DateTimeField(null=True)
    resumed_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    log_path = models.CharField(max_length=255, null=True, blank=True)
    sql_file = models.CharField(max_length=255, null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, blank=True, null=True, related_name='tasks')
    stopping_condition_max_records = models.IntegerField(default=None, null=True, blank=True)
    debug_mode = models.BooleanField(default=False)
    
    class Status(models.TextChoices):
        STARTING = 'STARTING', 'Starting'
        RUNNING = 'RUNNING', 'Running'
        CANCELED = 'CANCELED', 'Canceled'
        FAILED = 'FAILED', 'Failed'
        FINISHED = 'FINISHED', 'Finished'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.STARTING,
    )
    
    def __str__(self):
        return f"Task: {self.id} - {self.type}"

    def launch(self):
        """
        Launches the task by setting its status and initiating a Celery task.
        """
        
        self.status = Task.Status.STARTING
        self.save()
        
        if self.debug_mode:
            _launch_task(self.id)
        else:
            self.celery_task_id = _launch_task.delay(self.id).id
            self.save()
            
        
        
    def purge(self):
        """
        Deletes task logs associated with this task.
        """
        delete_task_logs(self)
            
    def restart(self):
        """
        Restarts the task by resetting and relaunching it.
        """
        self.started_at = timezone.now()
        self.save()
        if self.status != Task.Status.CANCELED:
            self.purge()
        self.launch()
                
    def cancel(self):
        """
        Cancels the task by revoking the Celery task and updating the status.
        """
        result = AsyncResult(self.celery_task_id, app=app)
        result.revoke(terminate=True)
        self.status = Task.Status.CANCELED
        self.finished_at = timezone.now()
        self.save()
