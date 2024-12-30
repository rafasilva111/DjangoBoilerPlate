###
#       General imports
##

## 
#   Default
##
import json


##
#   Django
##
from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django_celery_beat.models import CrontabSchedule, PeriodicTask


## 
#   Api Swagger
##


## 
#   Extras
##


###
#       App specific imports
##

##
#   Models
from apps.task_app.models import Task, Job, ContentType, TimeCondition
from apps.user_app.models import User



# Predefined options for cron fields

MINUTES_CHOICES = [('*', '*')] + [(str(i), str(i)) for i in range(60)]
HOURS_CHOICES = [('*', '*')] + [(str(i), str(i)) for i in range(24)]
DAY_OF_WEEK_CHOICES = [('*', '*')] + [(str(i), str(i)) for i in range(7)]
DAY_OF_MONTH_CHOICES = [('*', '*')] + [(str(i), str(i)) for i in range(1, 32)]
MONTH_OF_YEAR_CHOICES = [('*', '*')] + [(str(i), str(i)) for i in range(1, 13)]


class TimeConditionForm(forms.ModelForm):
    
    minute = forms.ChoiceField(
        choices=MINUTES_CHOICES, 
        initial='*', 
        required=False,
        help_text='Cron minute field', 
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    hour = forms.ChoiceField(
        choices=HOURS_CHOICES, 
        initial='*', 
        required=False,
        help_text='Cron hour field', 
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    day_of_week = forms.ChoiceField(
        choices=DAY_OF_WEEK_CHOICES, 
        initial='*', 
        required=False,
        help_text='Cron day of week field', 
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    day_of_month = forms.ChoiceField(
        choices=DAY_OF_MONTH_CHOICES, 
        initial='*', 
        required=False,
        help_text='Cron day of month field', 
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    month_of_year = forms.ChoiceField(
        choices=MONTH_OF_YEAR_CHOICES, 
        initial='*', 
        required=False,
        help_text='Cron month of year field', 
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    class Meta:
        model = TimeCondition
        fields = ['minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year']
        
    def clean(self):
        cleaned_data = super().clean()
        minute = cleaned_data.get('minute')

        if minute == '*':
            self.add_error('minute', 'Minute cannot be "*"')

        return cleaned_data
    
        
    def save(self, commit=True):
        instance = super().save(commit=False)

        # Create or get the crontab schedule
        crontab, created = CrontabSchedule.objects.get_or_create(
            minute=self.cleaned_data['minute'],
            hour=self.cleaned_data['hour'],
            day_of_week=self.cleaned_data['day_of_week'],
            day_of_month=self.cleaned_data['day_of_month'],
            month_of_year=self.cleaned_data['month_of_year'],
        )
        


        instance.crontab = crontab

        if commit:
            instance.save()
        return instance


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['type',  'debug_mode']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'debug_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users based on company type


class TaskEditForm(forms.ModelForm):
    
    job = forms.ModelChoiceField(
        queryset=Job.objects.all(),
        required=False,
        label='Job',
        help_text='Select the job.',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    class Meta:
        model = Task
        fields = ['log_path', 'job', 'debug_mode', 'step']
        widgets = {
            'log_path': forms.TextInput(attrs={'class': 'form-control'}),
            'debug_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'step': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pass the user object to the form
        
        if user is None:
            raise ValueError("User must not be None")
        
        super(TaskEditForm, self).__init__(*args, **kwargs)

        # Edit Permissions
        if not user.is_staff:
            self.fields['log_path'].widget.attrs['readonly'] = 'readonly'
            self.fields['debug_mode'].widget.attrs['readonly'] = 'readonly'
            self.fields['job'].widget.attrs['readonly'] = 'readonly'
    
    def clean(self):
        cleaned_data = super().clean() 

        if self.instance.status in [Task.Status.STARTING, Task.Status.RUNNING]:
            if self.instance.debug_mode != cleaned_data.get('debug_mode'):
                self.add_error('debug_mode', "Cannot change debug_mode if current status is STARTING or RUNNING. Please change it to STOPPED first.")
            
            job = cleaned_data.get('job')
            if job and self.instance.job_id != job.id: # use get to avoid keyerrors
                self.add_error('job', "Cannot change job if current status is STARTING or RUNNING. Please change it to STOPPED first.")
            if self.instance.step != cleaned_data.get('step'):
                self.add_error('step', "Cannot change step if current status is STARTING or RUNNING. Please change it to STOPPED first.")
            if self.instance.log_path != cleaned_data.get('log_path'):
                self.add_error('log_path', "Cannot change log_path if current status is STARTING or RUNNING. Please change it to STOPPED first.")

        return cleaned_data
    
    def save(self, commit=True):
        # Check if type has changed
        old_instance = Task.objects.get(pk=self.instance.pk)

        instance = super(TaskEditForm, self).save(commit=False)
        
        # Check if the status is STARTING or RUNNING
        if old_instance.status in [Task.Status.STARTING, Task.Status.RUNNING]:
            
            if old_instance.debug_mode != self.cleaned_data['debug_mode']:
                self.add_error('debug_mode', "Cannot change debug_mode if status is STARTING or RUNNING.")
            
            if old_instance.job_id != self.cleaned_data['job']:
                self.add_error('job', "Cannot change job if status is STARTING or RUNNING.")
            
            if old_instance.step != self.cleaned_data['step']:
                self.add_error('step', "Cannot change step if status is STARTING or RUNNING.")
            
            if old_instance.log_path != self.cleaned_data['log_path']:
                self.add_error('log_path', "Cannot change log_path if status is STARTING or RUNNING.")
            
            # Abort save if there are errors
            if self.errors:
                return old_instance
            
        # Commit the changes
        if commit:
            instance.save()
        
        # Change the status if it has changed, to reflect the new status
        if self.instance.status != old_instance.status:
            self.instance.change_status(self.instance.status)
            
        return instance




class JobForm(forms.ModelForm):
    
    starting_condition_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(
            Q(app_label='task_app', model='timecondition')
        ),
        required=False,
        label='Starting Condition Type',
        help_text='Select the type of condition for starting.',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    
    stopping_condition_type = forms.ModelChoiceField(
        queryset = ContentType.objects.filter(
            Q(app_label='task_app', model='timecondition')
        ),
        required=False,
        label='Stopping Condition Type',
        help_text='Select the type of condition for stopping.',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    

    class Meta:
        model = Job
        fields = ['name', 'type',  'starting_condition_type', 'stopping_condition_type','continue_mode']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the name of the job'}),
            'type': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'parent_task': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'continue_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtering the ContentType queryset to show only types related to conditions
        # Adjust this if you want to filter specific content types for conditions.

        self.fields['starting_condition_type'].queryset = ContentType.objects.filter(
            Q(app_label='task_app', model='timecondition')
        )
        self.fields['stopping_condition_type'].queryset = ContentType.objects.filter(
            Q(app_label='task_app', model='timecondition') 
        )
    
    def save(self,starting_condition_form = None,stopping_condition_form = None, created_by = None, *args, **kwargs):
        
        
        # Create or update the Job instance
        job = super().save(commit=False)
        
        job.created_by = created_by
        
        
        if starting_condition_form:
            job.starting_condition = starting_condition_form.save()
            
        if stopping_condition_form:
            job.stopping_condition = stopping_condition_form.save()
        
        # Call the original save method
        job.save()
    
        return job