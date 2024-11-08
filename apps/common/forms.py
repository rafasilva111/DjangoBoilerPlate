
###
#       General imports
##


##
#   Default
#

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm,SetPasswordForm,  authenticate, get_user_model, password_validation
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone

##
#   Extras
#

from datetime import datetime



###
#       App specific imports
##


##
#   Models
#




##
#   Contants
#
from apps.user_app.constants import REGISTER_MINIMUM_AGE

from apps.user_app.models import User







class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.TextInput(attrs={
        'placeholder': 'Enter your email or username',
        'class': 'form-control'
    }))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={
        'placeholder': '********************',
        'class': 'form-control'
    }))
    remember_me = forms.BooleanField(label='Remember Me', required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))


        

class RegisterForm(UserCreationForm):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Name",
                "class": "form-control"
            }
        ))
    
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    
    
    birth_date = forms.DateField(
        label="Birthdate",
        widget=forms.DateInput(
            attrs={
                "placeholder": "YYYY-MM-DD",
                "class": "form-control",
                "type": "date"  # This adds the date picker
            }
        ))
    
    

    email = forms.CharField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        ))
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))
    
    password2= forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm Password",
                "class": "form-control"
            }
        ))
    

    class Meta:
        model = User
        fields = ['name', 'email','birth_date', 'username', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()

        birth_date = cleaned_data.get("birth_date")
        if birth_date:
            birth_datetime = datetime.combine(birth_date, datetime.min.time())
            # Making birth_date aware
            birth_date_aware = timezone.make_aware(birth_datetime, timezone=timezone.get_current_timezone())
            # Update age in cleaned_data
            age = self.calculate_age(birth_date_aware)
            if age < REGISTER_MINIMUM_AGE:
                self.add_error('birth_date', "You must be at least 18 years old to register.")
    
    def calculate_age(self, birthdate):
        today = today = timezone.now().date()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age



class ResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email',
    }), label="Email Address")

class SetPasswordForm(SetPasswordForm):
    """A custom form for password reset confirmation."""
    
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class': 'form-control',"autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control',"autocomplete": "new-password"}),
    )
    
    class Meta:
        fields = ('new_password1', 'new_password2')

    
    def clean_confirm_password(self):
        """Ensure that the two password fields match."""
        password = self.cleaned_data.get('new_password1')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(("The two password fields didn’t match."))
        
        return confirm_password