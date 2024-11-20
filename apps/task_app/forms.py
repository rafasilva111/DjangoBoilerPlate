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
        hour = cleaned_data.get('hour')

        if minute == '*':
            self.add_error('minute', 'Minute cannot be "*"')
        if hour == '*': 
            self.add_error('hour', 'Hour cannot be "*"')

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
        fields = ['name', 'type',  'starting_condition_type', 'stopping_condition_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the name of the job'}),
            'type': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'parent_task': forms.Select(attrs={'class': 'form-select form-select-lg'}),
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
    
    def save(self,starting_condition_form = None,stopping_condition_form = None, *args, **kwargs):
        
        
        # Create or update the Job instance
        job = super().save(commit=False)
        
        
        if starting_condition_form:
            job.starting_condition = starting_condition_form.save()
            
        if stopping_condition_form:
            job.stopping_condition = stopping_condition_form.save()  
        
        # Call the original save method
        job.save()
    
        return job