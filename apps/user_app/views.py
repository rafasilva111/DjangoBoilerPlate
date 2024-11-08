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
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.decorators.http import require_GET, require_POST
from django.views import View
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
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
from django.urls import reverse, reverse_lazy

from django.contrib.auth import login as auth_login
from django.contrib.auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView,PasswordResetView ,PasswordContextMixin,INTERNAL_RESET_SESSION_TOKEN

##
#   Api Swagger
#


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

from apps.user_app.models import User, Invitation

##
#   Serializers
#


##
#   Forms
#
from apps.user_app.forms import LoginForm, RegisterForm, ResetForm, SetPasswordForm,UserInviteForm,UserRegisterByInviteForm,UserEditForm
from apps.task_app.forms import TaskForm, JobForm,MaxRecordsConditionForm,TimeConditionForm

##
#   Filters
#

from apps.user_app.filters import UserFilter

##
#   Functions
#


##
#   Contants
#

from apps.common.constants import WEBSOCKET_HOST


###
#
#       Auth Views 
#   
##

class LoginView(TemplateView):
    template_name = 'common/auth/login.html'  # Assuming the login template path
    form = LoginForm()

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path']  = TemplateHelper.set_layout("layout_blank.html", context)
        context['form'] = self.form

        return context

    def post(self, request):
        self.form = LoginForm(request.POST)
        if self.form.is_valid():
            email = self.form.cleaned_data['email']
            password = self.form.cleaned_data['password']
            remember_me  = self.form.cleaned_data['remember_me']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)


                if remember_me:
                    # If remember_me is checked, set a longer session expiry time
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                else:
                    # If remember_me is not checked, use the default session expiry time
                    request.session.set_expiry(0)  # Expire at browser close
                
                next_url = request.GET.get('next', reverse('home'))
                return redirect(next_url)
            else:
                self.form.add_error("password", "Invalid email or password")
                
        # If form is invalid or authentication failed, pass form with errors back to template
        context = self.get_context_data(form=self.form)  
        return render(request, self.template_name, context)
     
class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            try:
                user = form.save()
                return redirect('login', {"msg": "User registered successfully, please login"})
            except Exception as e:
                error_message = str(e)
                if "EMAIL_EXISTS" in error_message:
                    form.add_error("email", "Email already exists.")
                else:
                    form.add_error("password2", error_message)
        return render(request, 'accounts/register.html', {'form': form})

class LogoutView(LoginRequiredMixin,PasswordContextMixin,View):

    def post(self, request):
        logout(request)
        # You can add additional logic for handling POST requests if needed
        return redirect('login')

##
#   Password Reset
#
class PasswordResetView(PasswordResetView):
    template_name = 'common/auth/reset_password/password_reset.html'  # Assuming your template path
    form_class = ResetForm
    success_url = reverse_lazy('password_reset_done')

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", context)
        context['form'] = self.form_class()

        return context

    def post(self, request, *args, **kwargs):
        self.form = self.form_class(request.POST)

        if self.form.is_valid():
            return super().post(request, *args, **kwargs)  # Let the default password reset logic run

        # If form is invalid, return the form with errors
        context = self.get_context_data(form=self.form)
        return render(request, self.template_name, context)

class PasswordResetDoneView(TemplateView):
    template_name = "common/unlogged/success_page.html"
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", context)
        context['title'] = 'Reset your password'
        context['message'] = 'We’ve emailed you instructions for setting your password, if an account exists with the email you entered. You should receive them shortly.'
        context['redirect_url'] = reverse('login')
        context['redirect_text'] = 'Back to Login'
        return context     

class PasswordResetConfirmView(PasswordContextMixin, FormView):
    form_class = SetPasswordForm
    post_reset_login = False
    post_reset_login_backend = None
    reset_url_token = "set-password"
    success_url = reverse_lazy("password_reset_complete")
    template_name = "common/auth/reset_password/password_reset_confirm.html"
    title = _("Enter new password")
    token_generator = default_token_generator

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)

            # Check the token validity
            if self.token_generator.check_token(self.user, session_token):
                self.validlink = True
                return super().dispatch(*args, **kwargs)
            elif self.token_generator.check_token(self.user, token):
                self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                redirect_url = self.request.path.replace(token, self.reset_url_token)
                return HttpResponseRedirect(redirect_url)

        # Render failure response
        return self.render_to_response(self.get_context_data())
    
    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        if self.post_reset_login:
            auth_login(self.request, user, self.post_reset_login_backend)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", context)
        
        if self.validlink:
            context["validlink"] = True
        else:
            context.update(
                {
                    "form": None,
                    "title": _("Password reset unsuccessful"),
                    "validlink": False,
                }                
            )
        return context

class PasswordResetCompleteView(TemplateView):
    template_name = "common/unlogged/success_page.html"
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", context)
        context['title'] = 'Password set!'
        context['message'] = 'Your password has been reset. You can log in now.'
        context['redirect_url'] = reverse('login')
        context['redirect_text'] = 'Back to Login'
        return context     

###
#
#       User Views 
#   
##

class UserTableView(LoginRequiredMixin, TemplateView):
    template_name = 'user_app/user/table.html'
    page_size = 10

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        
        records = User.objects.all().order_by('-id')
        filter = UserFilter(self.request.GET, queryset=records)
        filtered_records = filter.qs
    
        page_size = int(self.request.GET.get('page_size',self.page_size))
            
        paginator = Paginator(filtered_records, page_size)  # Show 10 tasks per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['filter'] = filter
        context['page_obj'] = page_obj
        
        return context

class UserDetailView(PermissionRequiredMixin, TemplateView):
    template_name = 'user_app/user/detail.html'
    permission_required = 'auth.add_user' # todo
    def get_context_data(self, **kwargs):
        
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['record'] = User.objects.get(id=kwargs['id'])           
        
        return context
    
class UserEditView(PermissionRequiredMixin,TemplateView):
    template_name = 'user_app/user/edit.html'
    permission_required = 'auth.change_user'
    form_class = UserEditForm
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        id = self.kwargs.get('id', None)
        
        try:
            record = User.objects.get(id=id)
        except User.DoesNotExist:
            raise SuspiciousOperation("User does not exist")
        
        context['form'] = UserEditForm(instance=record, user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        job_form = UserEditForm(request.POST)
        starting_time_condition_form = TimeConditionForm(request.POST, prefix='starting_condition_time_form')
        stopping_time_condition_form = TimeConditionForm(request.POST, prefix='stopping_condition_time_form')
        stopping_condition_max_records_form = MaxRecordsConditionForm(request.POST, prefix='stopping_condition_max_records_form')

        if job_form.is_valid() :
            starting_condition_form = None
            stopping_condition_form = None
            
            
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

##
#     User Invite
#

class UserInviteView(PermissionRequiredMixin,TemplateView):
    template_name = 'user_app/user/invite.html'
    permission_required = 'auth.add_user'
    form_class = UserInviteForm
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['form'] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        instance_form = self.form_class(request.POST)
        if instance_form.is_valid():
            user_email = instance_form.cleaned_data.get('email')
            company = instance_form.cleaned_data.get('company')

            # Generate and save the invite with token
            invitation = Invitation.objects.create(company=company,email=user_email, invited_by=request.user)


            # Send tokenized invite email
            self.send_invitation_email(invitation, request)

            return redirect('user_invite_success')
        
        # Collect all errors if any form is invalid
        context = self.get_context_data()
        context['form'] = instance_form
        
        return self.render_to_response(context)
    
    def send_invitation_email(self, invitation, request):
        subject = 'You are invited to join the app!'
        invite_link = f'{settings.BASE_URL}{reverse("user_register", args=[invitation.token])}'  # Tokenized link

        # Render the email template
        message = render_to_string('user_app/emails/invite_email.html', {
            'invite_link': invite_link,
            'sender_email':invitation.invited_by.email,
            'sender_name': invitation.invited_by.name,
            'company_name': invitation.company.name if invitation.company else 'LiveView',
        })

        # Send the email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # From email
            [invitation.email],  # To email
            fail_silently=False,
        )

class UserInviteSuccessView(PermissionRequiredMixin, TemplateView):
    template_name = 'common/logged/success_page.html'
    #permission_required = 'auth.add_user'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['title'] = 'Success!'
        context['message'] = 'Invitation sent successfully!'
        context['tab'] = 'User / Invite User /'
        context['current_tab'] = 'Success'
        context['redirect_url'] = reverse('user')
        context['redirect_text'] = 'Back to User Table'
        return context

class UserRegisterView(TemplateView):
    template_name = 'user_app/auth/invite_register.html'
    #permission_required = 'auth.add_user'
    form_class = UserRegisterByInviteForm
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path']  = TemplateHelper.set_layout("layout_blank.html", context)
        
        token = self.kwargs.get('token', None)
        
        if not token:
            raise SuspiciousOperation("Token not provided")
        
        # Get Invitation
        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            
            # Check if user is already registered
            try:
                user = User.objects.get(email=invitation.email)
                # todo: User is already registered. Show message and redirect to login
                
            except User.DoesNotExist:
                raise SuspiciousOperation("Token is Invalid")
            
        form = self.form_class(email=invitation.email,company=invitation.company)
        context['form'] = form

        return context

    def post(self, request, *args, **kwargs):
        instance_form = self.form_class(request.POST)
        
        if instance_form.is_valid():
            
            instance_form.save()
            print(reverse('user_register_success'))
            return redirect(reverse('user_register_success'))

        context = self.get_context_data()
        context['form'] = instance_form
        
        return self.render_to_response(context)

class UserRegisterSuccessView(TemplateView):
    template_name = 'common/unlogged/success_page.html'
    #permission_required = 'auth.add_user'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['layout_path']  = TemplateHelper.set_layout("layout_blank.html", context)
        context['title'] = 'Success!'
        context['message'] = 'Your account is created successfully!'
        context['redirect_url'] = reverse('login')
        return context


###
#
#   Actions
#
## 

@login_required
@require_GET
@permission_required('auth.change_user', raise_exception=True)
def user_enable_disable(request, id):
    instance = get_object_or_404(User, id=id)
    instance.is_active = not instance.is_active
    instance.save()
    
    next_url = request.GET.get('next', reverse('user'))
    
    return redirect(next_url)

@login_required
@require_GET
@permission_required('auth.delete_user', raise_exception=True)
def user_delete(request, id):
    instance = get_object_or_404(User, id=id)
    instance.delete()
    
    return redirect(request.get_full_path())