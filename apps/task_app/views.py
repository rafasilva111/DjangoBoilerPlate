###
#       General imports
##


##
#   Default
#

from web_project import TemplateLayout

##
#   Django
#


from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views import View
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

##
#   Api Swagger
#


##
#   Extras
#


from os import path

###
#       App specific imports
##


##
#   Models
#

from apps.task_app.models import Job, Task

##
#   Serializers
#


##
#   Forms
#

from apps.task_app.forms import  TaskForm, JobForm, TimeConditionForm


##
#   Filters
#

from apps.task_app.filters import JobFilter, TaskFilter

##
#   Functions
#


##
#   Contants
#

from apps.common.constants import WEBSOCKET_HOST


###
#
#   Jobs
#
##


@method_decorator(login_required, name="dispatch")
class JobTableView(TemplateView):
    template_name = "task_app/job/table.html"
    page_size = 10

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        records = Job.objects.all().order_by("-id")
        filter = JobFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs

        #

        page_size = int(self.request.GET.get("page_size", self.page_size))

        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["filter"] = filter
        context["page_obj"] = page_obj

        return context


# @method_decorator(login_required, name='dispatch')
class JobCreateView(TemplateView):
    template_name = "task_app/job/create.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context["form"] = JobForm()
        context["starting_condition_time_form"] = TimeConditionForm(
            prefix="starting_condition_time_form"
        )
        context["stopping_condition_time_form"] = TimeConditionForm(
            prefix="stopping_condition_time_form"
        )
        return context

    def post(self, request, *args, **kwargs):
        job_form = JobForm(request.POST)
        starting_time_condition_form = TimeConditionForm(
            request.POST, prefix="starting_condition_time_form"
        )
        stopping_time_condition_form = TimeConditionForm(
            request.POST, prefix="stopping_condition_time_form"
        )
        

        if job_form.is_valid():
            starting_condition_form = None
            stopping_condition_form = None


            # Save the starting condition

            if job_form.instance.starting_condition_type:
                if job_form.instance.starting_condition_type.name == "time condition":
                

            
                    if starting_time_condition_form.is_valid():
                        starting_condition_form = starting_time_condition_form
                    else:
                        # Collect all errors if any form is invalid
                        context = self.get_context_data()
                        context["form"] = job_form
                        context["starting_condition_time_form"] = (
                            starting_time_condition_form
                        )
                        context["stopping_condition_time_form"] = (
                            stopping_time_condition_form
                        )

                        return self.render_to_response(context)

            # Save the stopping time condition

            if job_form.instance.stopping_condition_type:

                if job_form.instance.stopping_condition_type.name == "time condition":
                    if stopping_time_condition_form.is_valid():
                        stopping_condition_form = stopping_time_condition_form
                    else:
                        # Collect all errors if any form is invalid
                        context = self.get_context_data()
                        context["form"] = job_form
                        context["starting_condition_time_form"] = (
                            starting_time_condition_form
                        )
                        context["stopping_condition_time_form"] = (
                            stopping_time_condition_form
                        )
                        

                        return self.render_to_response(context)

                

            job = job_form.save(starting_condition_form, stopping_condition_form)

            return redirect(reverse("job_detail", args=[job.id]))

        # Collect all errors if any form is invalid
        context = self.get_context_data()
        context["form"] = job_form
        context["starting_condition_time_form"] = starting_time_condition_form
        context["stopping_condition_time_form"] = stopping_time_condition_form
        

        return self.render_to_response(context)


# @method_decorator(login_required, name='dispatch')
class JobDetailView(TemplateView):
    template_name = "task_app/job/detail.html"
    page_size = 10

    def get_context_data(self, **kwargs):

        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context["record"] = Job.objects.get(id=kwargs["id"])

        records = context["record"].tasks.all().order_by("-started_at")
        filter = TaskFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs

        #

        page_size = int(self.request.GET.get("page_size", self.page_size))

        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["filter"] = filter
        context["page_obj"] = page_obj

        return context


###
#
#   Actions
#
##


@require_GET
def job_resume(request, id):
    job = get_object_or_404(Job, id=id)
    job.resume_task()

    return redirect(reverse("job_detail", args=[job.id]))


@require_GET
def job_pause(request, id):
    job = get_object_or_404(Job, id=id)
    job.pause_task()

    return redirect(reverse("job_detail", args=[job.id]))


@login_required
@require_GET
def job_delete(request, id):
    instance = get_object_or_404(Job, id=id)
    instance.delete()

    return redirect("job")


###
#
#   Tasks
#
##


@method_decorator(login_required, name="dispatch")
class TaskTableView(PermissionRequiredMixin, TemplateView):
    """
    A view class that displays a paginated table of tasks with filtering capabilities.
    This view requires user authentication and specific permission to view tasks.
    It extends TemplateView and implements PermissionRequiredMixin for access control.
    Attributes:
        template_name (str): Path to the template used to render the task table
        page_size (int): Default number of items per page
        permission_required (str): Permission required to access this view
        raise_exception (bool): Whether to raise exception for unauthorized access
    Methods:
        get_context_data(**kwargs): Prepares and returns the context data for template rendering
            - Initializes template layout
            - Retrieves and orders all tasks
            - Applies filtering based on request parameters
            - Implements pagination
            - Adds create task permission check
    Returns:
        dict: Context containing:
            - filter: Filtered queryset of tasks
            - page_obj: Paginator object with task records
            - can_create_task: Boolean indicating if user can create tasks
    """

    template_name = "task_app/task/table.html"
    page_size = 10
    permission_required = "task_app.can_view_tasks"
    raise_exception = False

    def get_context_data(self, **kwargs):
        """
        Prepares and returns the context data for template rendering.
        - Initializes template layout
        - Retrieves and orders all tasks
        - Applies filtering based on request parameters
        - Implements pagination
        - Adds create task permission check

        Returns:
            dict: Context containing:
                - filter: Filtered queryset of tasks
                - page_obj: Paginator object with task records
                - can_create_task: Boolean indicating if user can create tasks
        """
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # Retrieve and order all tasks
        records = Task.objects.all().order_by('-id')
        
        # Apply filtering based on request parameters
        filter = TaskFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs
        
        # Implement pagination
        page_size = int(self.request.GET.get('page_size', self.page_size))
        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add create task permission check
        context.update(
            {
                "filter": filter,
                "page_obj": page_obj,
                "can_create_task": self.request.user.has_perm(
                    "task_app.can_create_task"
                ),
                "can_edit_task": self.request.user.has_perm(
                    "task_app.can_edit_task"
                ),
                "can_view_task": self.request.user.has_perm(
                    "task_app.can_view_task"
                ),
                "can_delete_task": self.request.user.has_perm(
                    "task_app.can_delete_task"
                ),
            }
        )
        
        return context


@method_decorator(login_required, name="dispatch")
class TaskDetailView(PermissionRequiredMixin,TemplateView):
    """
    A view class for displaying task details.

    This class handles the display of task-specific information and associated log files.
    Requires user authentication to access the view.

    Attributes:
        template_name (str): The template used for rendering the task detail view.
        page_size (int): Number of items to display per page.
        permission_required (str): The required permission to access this view.

    Methods:
        get_context_data(**kwargs): Prepares and returns the context data for template rendering.

    Parameters:
        kwargs["id"] (int): The ID of the task to be displayed.

    Returns:
        dict: Context dictionary containing:
            - task: Task object retrieved from database
            - log: Content of the task's log file (if exists)
            - WEBSOCKET_HOST: WebSocket host configuration
            - Additional template layout context data
    """
    template_name = "task_app/task/detail.html"
    page_size = 10

    permission_required = "task_app.can_view_task"

    def get_context_data(self, **kwargs):
        """
        Prepares and returns the context data for template rendering.
        - Initializes template layout
        - Retrieves the task by ID
        - Reads the task's log file if it exists
        - Adds WebSocket host configuration

        Returns:
            dict: Context dictionary containing:
                - task: Task object retrieved from database
                - log: Content of the task's log file (if exists)
                - WEBSOCKET_HOST: WebSocket host configuration
        """
        # Initialize template layout
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        
        # Retrieve the task by ID
        context["task"] = Task.objects.get(id=kwargs["id"])

        # Read the task's log file if it exists
        log_path = context["task"].log_path
        if log_path and path.isfile(log_path):
            with open(log_path, "r") as log_file:
                context["log"] = log_file.read()  # Read the entire content of the log file
        
        # Add create task permission check
        context.update(
            {
                "WEBSOCKET_HOST": WEBSOCKET_HOST,
                "can_cancel_task": self.request.user.has_perm(
                    "task_app.can_cancel_task"
                ),
                "can_restart_task": self.request.user.has_perm(
                    "task_app.can_restart_task"
                ),
                "can_resume_task": self.request.user.has_perm(
                    "task_app.can_resume_task"
                ),
                "can_pause_task": self.request.user.has_perm(
                    "task_app.can_pause_task"
                ),
                "can_delete_task": self.request.user.has_perm(
                    "task_app.can_delete_task"
                ),
            }
        )
        return context


@method_decorator(login_required, name="dispatch")
class TaskCreateView(PermissionRequiredMixin, TemplateView):
    """
    Class-based view for creating a new task.

    This view requires users to be authenticated and have the 'task_app.can_create_task' permission.
    It renders a form for task creation and handles both GET and POST requests.

    Attributes:
        template_name (str): Path to the template used for rendering the task creation form.
        permission_required (str): Permission required to access this view.

    Methods:
        get_context_data(**kwargs): Adds form and layout context to template context.
        post(request, *args, **kwargs): Handles form submission, saves task if valid, 
            and redirects to task detail view.

    Returns:
        GET: Rendered template with task creation form
        POST: Redirects to task detail view on success, or re-renders form with errors
    """
    
    template_name = "task_app/task/create.html"

    permission_required = "task_app.can_create_task"

    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context["form"] = TaskForm()

        return context

    def post(self, request, *args, **kwargs):

        form = TaskForm(request.POST)

        if form.is_valid():
            instance = form.save()
            return redirect(reverse("task_detail", args=[instance.id]))

        # Use get_context_data to include layout_path and other context variables
        context = self.get_context_data(**kwargs)
        context["form"] = form

        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class TaskUpdateView(PermissionRequiredMixin, TemplateView): #todo  
    """
    Class-based view for creating a new task.

    This view requires users to be authenticated and have the 'task_app.can_create_task' permission.
    It renders a form for task creation and handles both GET and POST requests.

    Attributes:
        template_name (str): Path to the template used for rendering the task creation form.
        permission_required (str): Permission required to access this view.

    Methods:
        get_context_data(**kwargs): Adds form and layout context to template context.
        post(request, *args, **kwargs): Handles form submission, saves task if valid, 
            and redirects to task detail view.

    Returns:
        GET: Rendered template with task creation form
        POST: Redirects to task detail view on success, or re-renders form with errors
    """
    
    template_name = "task_app/task/create.html"

    permission_required = "task_app.can_edit_task"

    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context["form"] = TaskForm()

        return context

    def post(self, request, *args, **kwargs):

        form = TaskForm(request.POST)

        if form.is_valid():
            instance = form.save()
            return redirect(reverse("task_detail", args=[instance.id]))

        # Use get_context_data to include layout_path and other context variables
        context = self.get_context_data(**kwargs)
        context["form"] = form

        return render(request, self.template_name, context)


###
#
#   Actions
#
##


@login_required
@require_GET
def task_restart(request, id):
    """
    Restart a task instance and redirect to task detail page.
    This view requires user authentication and 'can_restart_task' permission.
    It retrieves a task by ID, calls its restart method, and redirects to the task detail page.
    Args:
        request: The HTTP request object
        id (int): The ID of the task to restart
    Returns:
        HttpResponseRedirect: Redirects to the task detail page
    Raises:
        PermissionDenied: If user doesn't have 'can_restart_task' permission
        Http404: If task with given ID is not found
    Requires:
        - User must be logged in (@login_required)
        - Request method must be GET (@require_GET)
        - User must have 'task_app.can_restart_task' permission
    """

    if not request.user.has_perm("task_app.can_restart_task"):
        raise PermissionDenied

    instance = get_object_or_404(Task, id=id)
    instance.restart()

    
    return redirect(reverse("task_detail", args=[instance.id]))
    

@login_required
@require_GET
def task_cancel(request, id):
    """
    Cancel a task and redirect to task detail page.
    This view cancels a specific task and redirects to the task detail page. It requires login and GET method.
    Only users with 'can_cancel_task' permission can access this view.
    Args:
        request (HttpRequest): The HTTP request object
        id (int): The ID of the task to be cancelled
    Returns:
        HttpResponseRedirect: Redirects to the task detail page
    Raises:
        PermissionDenied: If user doesn't have required permission
        Http404: If task with given ID doesn't exist
    Required Permissions:
        - task_app.can_cancel_task
    Decorators:
        - @login_required
        - @require_GET
    """
    if not request.user.has_perm("task_app.can_cancel_task"):
        raise PermissionDenied

    instance = get_object_or_404(Task, id=id)
    instance.cancel()
    
    return redirect(reverse("task_detail", args=[instance.id]))
    

@login_required
@require_GET
def task_delete(request, id):
    """
    Delete a task instance.
    This view function handles the deletion of a Task object. It requires the user to be
    authenticated and to have the 'can_delete_task' permission. If the task with the given ID
    exists, it will be deleted and the user will be redirected to the tasks list page.
    Args:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the task to be deleted.
    Returns:
        HttpResponseRedirect: Redirects to the tasks list page after successful deletion.
    Raises:
        PermissionDenied: If the user doesn't have the required permission.
        Http404: If the task with the given ID doesn't exist.
    """
    if not request.user.has_perm("task_app.can_delete_task"):
        raise PermissionDenied

    instance = get_object_or_404(Task, id=id)
    instance.delete()
    return redirect("tasks")



@login_required
@require_GET
def task_pause(request, id):

    if not request.user.has_perm("task_app.can_pause_task"):
        raise PermissionDenied

    instance = get_object_or_404(Task, id=id)
    instance.pause()
    return redirect(reverse("task_detail", args=[instance.id]))

@login_required
@require_GET
def task_resume(request, id):

    if not request.user.has_perm("task_app.can_resume_task"):
        raise PermissionDenied

    instance = get_object_or_404(Task, id=id)
    instance.resume()
    return redirect(reverse("task_detail", args=[instance.id]))