
###
#       General imports
##


##
#   Default
#

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

##
#   Extras
#

import inspect


###
#       App specific imports
##


##
#   Models
#

from apps.user_app.models import User
from apps.task_app.models import Task



##
#   Serializers
#


##
#   Forms
#


##
#   Functions
#

from apps.common.tests.functions import print_prologue


##
#   Contants
#





###
#
#       Login Views 
#   
##

USER_EMAIL = "test@example.com"
USER_PASSWORD = "securepassword"


class TaskTableViewTest(TestCase):
    def setUp(self):
        """Set up a user for testing."""

        self.user = User.objects.create_user(
            email=USER_EMAIL,
            password=USER_PASSWORD,
            birth_date=timezone.now(),  
        )
        
        self.url = reverse('task')
        self.login_url = reverse('login')  # Assuming the URL name for login is 'login'
        self.logout_url = reverse('logout')  # Assuming the URL name for logout is 'logout'
        
        # Log in the user and check if login was successful
        login_success = self.client.login(email=USER_EMAIL, password=USER_PASSWORD)
        self.assertTrue(login_success, "Login should be successful")

        # Check if the user is authenticated
        response = self.client.get(self.login_url)  # Fetching the login page to check authentication
        self.assertTrue(response.wsgi_request.user.is_authenticated, "User should be authenticated")

    ##
    #   Testing View load
    #
    
    def test_view_load_succeds_when_user_authenticated(self):
        """Test that the login page loads and returns a 200 status when User authenticated."""
        
        print_prologue()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_app/task/table.html')
        
        print("\n")
        
    def test_view_load_fails_when_user_unauthenticated(self):
        """Test that the login page redirects to login view if not logged in."""
        
        print_prologue()
        
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}", status_code=302, target_status_code=200)
        
        print("\n")
        
    
    
    ##
    #   Testing View pagination
    #
    
    def test_pagination(self):
        """Test that pagination returns the correct page of results."""
        
        print_prologue()
        
        # Create test data with enough items to require multiple pages
        for i in range(25):
            Task.objects.create(type = Task.TaskType.EMPTY)          
        
        response = self.client.get(self.url, {'page': 2, 'page_size': 5})
        self.assertEqual(response.status_code, 200)
        # Check that the response contains only the users for page 2
        self.assertEqual(len(response.context['page_obj']), 5)
        
        print("\n")
        

class TaskCreateViewTest(TestCase):
    def setUp(self):
        """Set up a user for testing."""

        self.user = User.objects.create_user(
            email=USER_EMAIL,
            password=USER_PASSWORD,
            birth_date=timezone.now(),  
        )
        
        self.url = reverse('task')
        self.login_url = reverse('login')  # Assuming the URL name for login is 'login'
        self.logout_url = reverse('logout')  # Assuming the URL name for logout is 'logout'
        
        # Log in the user and check if login was successful
        login_success = self.client.login(email=USER_EMAIL, password=USER_PASSWORD)
        self.assertTrue(login_success, "Login should be successful")

        # Check if the user is authenticated
        response = self.client.get(self.login_url)  # Fetching the login page to check authentication
        self.assertTrue(response.wsgi_request.user.is_authenticated, "User should be authenticated")

    ##
    #   Testing View load
    #
    
    def test_view_load_succeds_when_user_authenticated(self):
        """Test that the login page loads and returns a 200 status when User authenticated."""
        
        print_prologue()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_app/task/table.html')
        
        print("\n")
        
    def test_view_load_fails_when_user_unauthenticated(self):
        """Test that the login page redirects to login view if not logged in."""
        
        print_prologue()
        
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}", status_code=302, target_status_code=200)
        
        print("\n")
    
    
    ##
    #   Testing View form
    #
    def test_create_task(self):
        """Test that the creation of a Task."""
        
        print_prologue()
        
        # Define the data to be submitted in the form
        form_data = {
            'type': Task.TaskType.EMPTY,       # or any other valid type value
            'debug_mode': False    # The checkbox can be True or False
        }
        
        # Perform a POST request to the view handling task creation
        response = self.client.post(reverse('task_create'), data=form_data)
                
        # Verify that the task was created in the database
        task = Task.objects.get(type=Task.TaskType.EMPTY)
        
        # Check the task fields
        self.assertEqual(task.type, form_data['type'])
        self.assertEqual(task.debug_mode, form_data['debug_mode'])
        
        # Check if the response redirects (assuming successful form submission redirects)
        self.assertRedirects(
            response, 
            reverse('task_detail', args=[task.id]),  # URL with task ID as argument
            status_code=302,
            target_status_code=200
        )
        
        print("\n")
        
        
        