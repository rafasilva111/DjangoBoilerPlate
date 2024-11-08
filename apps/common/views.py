
###
#       General imports
##


##
#   Default
#

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView,PasswordContextMixin,INTERNAL_RESET_SESSION_TOKEN
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.views.generic import TemplateView
import markdown
from django.contrib.auth.tokens import default_token_generator

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseRedirect
from django.utils.http import  urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _

from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import FormView
from django.urls import reverse

from django.contrib.auth import login as auth_login

##
#   Extras
#

from web_project import TemplateLayout, TemplateHelper


###
#       App specific imports
##


##
#   Models
#

from apps.user_app.models import User

##
#   Serializers
#


##
#   Forms
#

from apps.common.forms import LoginForm, RegisterForm, ResetForm, SetPasswordForm


##
#   Functions
#


##
#   Contants
#




###
#
#       Others Views 
#   
##

@method_decorator(login_required, name='dispatch')
class DashboardsView(TemplateView):
    template_name = 'dashboard_analytics.html' 
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context

## TODO For dev usege LoginRequiredMixin is not required

@method_decorator(login_required, name='dispatch')
class ReadMeView(TemplateView):
    template_name = 'readme.html' 

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        
        
        with open('README.md', 'r') as f:  # Adjust the file path as needed
            readme_content = f.read()
        html_content = markdown.markdown(readme_content)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            'html_content': html_content,
        })
        
    
        return context
