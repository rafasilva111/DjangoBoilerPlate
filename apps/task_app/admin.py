###
# General imports
##

## Django Admin
from django.contrib import admin

### App-specific imports

## Models
from apps.task_app.models import Task, Job

# Register your models here.

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Task model.

    - Displays task type, status, and timing information.
    - Provides an action to duplicate selected tasks.

    Attributes:
        list_display (tuple): Fields to display in the list view.
        actions (list): List of custom actions for TaskAdmin.
    """
    list_display = ('type', 'status', 'started_at', 'finished_at')
    actions = ['duplicate_tasks']

    def duplicate_tasks(self, request, queryset):
        """
        Duplicates selected Task instances.

        - For each task in the queryset, sets the primary key to None,
          saving it as a new instance.
          
        Args:
            request (HttpRequest): The current request object.
            queryset (QuerySet): The selected tasks to duplicate.
        """
        for task in queryset:
            task.pk = None  # Set primary key to None to create a new instance
            task.save()
    duplicate_tasks.short_description = 'Duplicate selected tasks'


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Job model.

    - Displays the last run time and allows filtering by it.
    - Sets last_run as a read-only field.

    Attributes:
        list_display (tuple): Fields to display in the list view.
        list_filter (tuple): Fields to filter by in the list view.
        readonly_fields (tuple): Fields to set as read-only.
    """
    list_display = ('last_run',)
    list_filter = ('last_run',)
    readonly_fields = ('last_run',)

    def save_model(self, request, obj, form, change):
        """
        Custom save logic for Job instances.

        - Saves the Job instance and performs additional handling if required.

        Args:
            request (HttpRequest): The current request object.
            obj (Job): The Job instance to be saved.
            form (ModelForm): The form used to change the object.
            change (bool): A flag indicating if the object is being changed.
        """
        obj.save()
