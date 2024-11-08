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


from django.shortcuts import render,redirect,get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views import View
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.generic import TemplateView

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

from apps.task_app.forms import TaskForm, JobForm,MaxRecordsConditionForm,TimeConditionForm

##
#   Filters
#

from apps.task_app.filters import JobFilter,TaskFilter

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

@method_decorator(login_required, name='dispatch')
class JobTableView(TemplateView):
    template_name = 'task_app/job/table.html'
    page_size = 10

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        
        records = Job.objects.all().order_by('-id')
        filter = JobFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs
        
        #

        page_size = int(self.request.GET.get('page_size',self.page_size))
            
        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['filter'] = filter
        context['page_obj'] = page_obj
        
        return context
    
#@method_decorator(login_required, name='dispatch')
class JobCreateView(TemplateView):
    template_name = 'task_app/job/create.html'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['form'] = JobForm()
        context['starting_condition_time_form'] = TimeConditionForm(prefix='starting_condition_time_form')
        context['stopping_condition_time_form'] = TimeConditionForm(prefix='stopping_condition_time_form')
        context['stopping_condition_max_records_form'] = MaxRecordsConditionForm(prefix='stopping_condition_max_records_form')
        return context

    def post(self, request, *args, **kwargs):
        job_form = JobForm(request.POST)
        starting_time_condition_form = TimeConditionForm(request.POST, prefix='starting_condition_time_form')
        stopping_time_condition_form = TimeConditionForm(request.POST, prefix='stopping_condition_time_form')
        stopping_condition_max_records_form = MaxRecordsConditionForm(request.POST, prefix='stopping_condition_max_records_form')

        if job_form.is_valid() :
            starting_condition_form = None
            stopping_condition_form = None
            
            teste = job_form.instance
            
            # Save the starting condition
            
            if job_form.instance.starting_condition_type and job_form.instance.starting_condition_type.name =='time condition': 
                if starting_time_condition_form.is_valid():
                
                    starting_condition_form = starting_time_condition_form
                else:
                    # Collect all errors if any form is invalid
                    context = self.get_context_data()
                    context['form'] = job_form
                    context['starting_condition_time_form'] = starting_time_condition_form
                    context['stopping_condition_time_form'] = stopping_time_condition_form
                    context['stopping_condition_max_records_form'] = stopping_condition_max_records_form
                    
                    return self.render_to_response(context)
                
            # Save the stopping time condition
            
            if job_form.instance.stopping_condition_type: 
                
                if job_form.instance.stopping_condition_type.name =='time condition':
                    if stopping_time_condition_form.is_valid():
                        stopping_condition_form = stopping_time_condition_form
                    else:
                        # Collect all errors if any form is invalid
                        context = self.get_context_data()
                        context['form'] = job_form
                        context['starting_condition_time_form'] = starting_time_condition_form
                        context['stopping_condition_time_form'] = stopping_time_condition_form
                        context['stopping_condition_max_records_form'] = stopping_condition_max_records_form
                        
                        return self.render_to_response(context)
                
                elif job_form.instance.stopping_condition_type.name =='max records condition':
                    stopping_condition_form = MaxRecordsConditionForm(request.POST, prefix='stopping_condition_max_records_form')
                    
                    if stopping_condition_max_records_form.is_valid():
                        stopping_condition_form = stopping_condition_max_records_form
                    # Collect all errors if any form is invalid
                    else:
                        context = self.get_context_data()
                        context['form'] = job_form
                        context['starting_condition_time_form'] = starting_time_condition_form
                        context['stopping_condition_time_form'] = stopping_time_condition_form
                        context['stopping_condition_max_records_form'] = stopping_condition_max_records_form
                        
                        return self.render_to_response(context)

                
            job = job_form.save(starting_condition_form,stopping_condition_form)
            
            return redirect(reverse('job_detail', args=[job.id]))

        # Collect all errors if any form is invalid
        context = self.get_context_data()
        context['form'] = job_form
        context['starting_condition_time_form'] = starting_time_condition_form
        context['stopping_condition_time_form'] = stopping_time_condition_form
        context['stopping_condition_max_records_form'] = stopping_condition_max_records_form

        return self.render_to_response(context)
    

#@method_decorator(login_required, name='dispatch')
class JobDetailView(TemplateView):
    template_name = 'task_app/job/detail.html'
    page_size = 10

    def get_context_data(self, **kwargs):
        
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['record'] = Job.objects.get(id=kwargs['id'])


        records = context['record'].tasks.all().order_by('-started_at')
        filter = TaskFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs
        
        #

        page_size = int(self.request.GET.get('page_size',self.page_size))
            
        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['filter'] = filter
        context['page_obj'] = page_obj
        
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

    return redirect(reverse('job_detail', args=[job.id]))


@require_GET
def job_pause(request, id):
    job = get_object_or_404(Job, id=id)
    job.pause_task()

    return redirect(reverse('job_detail', args=[job.id]))

@login_required
@require_GET
def job_delete(request, id):
    instance = get_object_or_404(Job, id=id)
    instance.delete()
    
    return redirect('job')


###
#
#   Tasks
#
##

@method_decorator(login_required, name='dispatch')
class TaskTableView(TemplateView):
    template_name = 'task_app/task/table.html'
    page_size = 10

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        
        records = Task.objects.all().order_by('-id')
        filter = TaskFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs
        
        #

        page_size = int(self.request.GET.get('page_size',self.page_size))
            
        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['filter'] = filter
        context['page_obj'] = page_obj
        
        return context
    
@method_decorator(login_required, name='dispatch')
class TaskDetailView(TemplateView):
    template_name = 'task_app/task/detail.html'
    page_size = 10

    def get_context_data(self, **kwargs):
        
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['task'] = Task.objects.get(id=kwargs['id'])
        
        log_path = context['task'].log_path

        if log_path and path.isfile(log_path):
            with open(log_path, 'r') as log_file:
                context['log'] = log_file.read()  # Read the entire content of the log file

        
        context['WEBSOCKET_HOST'] =  WEBSOCKET_HOST
        
        return context
    
    
@method_decorator(login_required, name='dispatch')
class TaskCreateView(TemplateView):
    template_name = 'task_app/task/create.html'

    
    
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['form'] = TaskForm()
        
        return context

    def post(self, request, *args, **kwargs):
        
        form = TaskForm(request.POST)

        if form.is_valid():
            instance = form.save()
            return redirect(reverse('task_detail', args=[instance.id]))
        
        # Use get_context_data to include layout_path and other context variables
        context = self.get_context_data(**kwargs)
        context['form'] = form

        return render(request, self.template_name, context)
 



###
#
#   Actions
#
##

@login_required
@require_GET
def task_restart(request, id):
    instance = get_object_or_404(Task, id=id)
    
    instance.restart()
    
    return redirect(reverse('task_detail', args=[instance.id])) 

@login_required
@require_GET
def task_pause(request, id):
    instance = get_object_or_404(Task, id=id)
    
    instance.pause()
    
    return redirect(reverse('task_detail', args=[instance.id])) 

@login_required
@require_GET
def task_resume(request, id):
    instance = get_object_or_404(Task, id=id)
    
    instance.resume()
    
    return redirect(reverse('task_detail', args=[instance.id])) 

@login_required
@require_GET
def task_cancel(request, id):
    instance = get_object_or_404(Task, id=id)
    
    instance.cancel()
    
    return redirect(reverse('task_detail', args=[instance.id])) 

@login_required
@require_GET
def task_delete(request, id):
    instance = get_object_or_404(Task, id=id)
    
    instance.delete()
    
    return redirect('tasks')
