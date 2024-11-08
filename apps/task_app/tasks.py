###
# General Imports
##

## Django Utilities
from django.utils import timezone

## Celery App
from config.celery import app

## Standard Libraries
import time
import logging

### App-specific imports

## Functions
from apps.task_app.functions import configure_task_logging, configure_job_logging

# Set up main logger
main_logger = logging.getLogger('django')


###
# Job Task Functions
##

@app.task
def _init_job(job_id):
    """
    Initializes a job, creating or resuming associated tasks as needed.

    - If a job has no associated tasks, it will create a new one.
    - If the last task is paused, it resumes that task.
    - If the last task is finished, it creates a new task.
    
    Args:
        job_id (int): ID of the Job to initialize.
    """
    from apps.task_app.models import Job, MaxRecordsCondition, Task

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        main_logger.error(f'Job {job_id} does not exist')
        return

    job.last_run = timezone.now()
    job.save()

    # Configure job-specific logging
    job_logger, log_info_path = configure_task_logging(job)
    job.log_path = log_info_path

    # Determine the status of the last task
    job_logger.info(f'Job {job_id} was started.')
    current_task = job.tasks.order_by('-created_at').first()
    job_logger.info(f'Current Task: {current_task}')

    if current_task is None:
        job_logger.info(f'No existing task. Creating new task.')
    elif current_task.status == Task.Status.FINISHED:
        job_logger.info(f'Task {current_task.id} has finished. Creating new task.')
    elif current_task.status == Task.Status.PAUSED:
        current_task.resume()
        return
    else:
        main_logger.info(f'Job {job_id} was not started due to Task {current_task.id} with status {current_task.status}.')
        return

    # Check for a stopping condition
    stopping_condition_max_records = None
    if isinstance(job.starting_condition, MaxRecordsCondition):
        stopping_condition_max_records = job.starting_condition.max_records
        job_logger.info(f'Task has a stopping condition: {stopping_condition_max_records}')

    # Create a new task
    task = Task.objects.create(
        company=job.company,
        type=job.type,
        parent_task=job.parent_task,
        job=job,
        stopping_condition_max_records=stopping_condition_max_records
    )
    job_logger.info(f'Starting task {task.id}')
    task.start()


###
# Task Functions
##

@app.task
def _launch_task(task_id):
    """
    Launches a specific task, running a test task based on the task type.

    - Configures logging and updates task status to RUNNING.
    - Initiates a test task with varying counts based on task type.

    Args:
        task_id (int): ID of the Task to launch.
    """
    from apps.task_app.models import Task

    task = Task.objects.get(id=task_id)

    logger, log_info_path = configure_task_logging(task)
    task.log_path = log_info_path
    task.status = Task.Status.RUNNING
    task.save()

    # Determine task behavior based on task type
    if task.type == Task.TaskType.SMALL:
        logger.info('Starting small Task')
        test_task(logger, task, max_count=5)
    elif task.type == Task.TaskType.MEDIUM:
        logger.info('Starting medium Task')
        test_task(logger, task, max_count=1000)
    elif task.type == Task.TaskType.LARGE:
        logger.info('Starting large Task')
        test_task(logger, task, max_count=10000)
    elif task.type == Task.TaskType.EMPTY:
        logger.info('Starting empty Task')
        test_task(logger, task, max_count=1)
    elif task.type == Task.TaskType.FAILURE:
        logger.info('Starting failure Task')
        test_task(logger, task, max_count=-1)


###
# Helper Functions
##

def test_task(logger, task, max_count=10000):
    """
    A helper function to simulate task processing by counting to a max value.

    - Logs each count increment and the task start/completion.
    - If max_count < 0, raises an exception to simulate a failure.

    Args:
        logger (logging.Logger): The logger to use for logging task events.
        task (Task): The task instance associated with the counting.
        max_count (int): The maximum count for the test task. Defaults to 10000.
    
    Raises:
        Exception: If max_count is less than 0.
    """
    logger.info("Executing Task...")
    
    if max_count < 0:
        raise Exception("Max Count cannot be less than 0")

    counter = 1
    while counter <= max_count:
        logger.info(f"Counting at: {counter}")
        time.sleep(1)
        counter += 1

    # Update task status to finished
    task.finished_at = timezone.now()
    task.status = task.Status.FINISHED
    task.save()
    
    logger.info("Done...")
    print("Done")
