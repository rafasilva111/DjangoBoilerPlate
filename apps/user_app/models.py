from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
    Permission,
    Group,
)
from django.forms import TextInput, PasswordInput
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.utils.translation import gettext_lazy
from apps.common.models import BaseModel
import uuid


class UserManager(BaseUserManager):
    """
    Custom manager for handling user creation with email as the unique identifier
    instead of a username. This manager provides methods for creating regular users
    and superusers, with automatic group assignment to new users.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and returns a new user with the given email and password, and assigns
        the user to a default group. Raises a ValueError if the email is not provided.

        Args:
            email (str): The user's email address, used as a unique identifier.
            password (str): The user's password.
            **extra_fields: Additional fields to set on the user model.

        Returns:
            User: The created user instance.

        Raises:
            ValueError: If the email is not provided.
        """

        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and returns a new superuser with the given email and password,
        setting is_staff and is_superuser to True. If these values are not True,
        a ValueError is raised.

        Args:
            email (str): The superuser's email address, used as a unique identifier.
            password (str): The superuser's password.
            **extra_fields: Additional fields to set on the user model.

        Returns:
            User: The created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser are not True.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # Use create_user to create the superuser and assign any additional roles
        user = self.create_user(email, password, **extra_fields)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    User model that extends AbstractBaseUser and PermissionsMixin.

    Attributes:
        name (str): The name of the user.
        img_source (str): The source URL for the user's profile image.
        email (str): The email address of the user, used as the unique identifier.
        created_at (datetime): The date and time when the user was created.
        updated_at (datetime): The date and time when the user was last updated.
        is_active (bool): Indicates whether the user account is active.
        is_staff (bool): Indicates whether the user has staff privileges.
        is_superuser (bool): Indicates whether the user has superuser privileges.
        groups (ManyToManyField): The groups the user belongs to.
        user_permissions (ManyToManyField): The permissions the user has.
        user_type (str): The type of user, either 'Normal' or 'Admin'.
        sex (str): The sex of the user, either 'Male' or 'Female'.

    Properties:
        age (int): The age of the user calculated from the birth_date.

    Meta:
        permissions (list): Custom permissions for the User model.

    Methods:
        __str__: Returns a string representation of the user.
    """

    name = models.CharField(max_length=40, null=False)
    img_source = models.CharField(max_length=255, default="", blank=True)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Security
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name="user_set", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="user_set", blank=True
    )

    objects = UserManager()

    @property
    def age(self):
        today = timezone.now()
        age = (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )
        return age

    class UserType(models.TextChoices):
        NORMAL = "N", "Normal"
        ADMIN = "A", "Admin"

    user_type = models.CharField(
        max_length=1, choices=UserType.choices, default=UserType.NORMAL, null=False
    )

    class SexType(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    sex = models.CharField(
        max_length=1, choices=SexType.choices, default=None, null=True
    )

    class Meta:
        permissions = [
            (f"can_view_user", f"Can view a User"),
            (f"can_create_user", f"Can create a User"),
            (f"can_edit_user", f"Can edit a User"),
            (f"can_delete_user", f"Can delete a User"),
        ]

    USERNAME_FIELD = "email"

    def __str__(self):
        return f"{self.id} - {self.name}"


class Invitation(models.Model):
    """
    Invitation model represents an invitation sent to a user via email.

    Attributes:
        email (EmailField): The email address to which the invitation is sent.
        token (UUIDField): A unique token for the invitation, generated by default.
        invited_by (ForeignKey): The user who sent the invitation, linked to the User model.
        created_at (DateTimeField): The date and time when the invitation was created.

    Methods:
        __str__(): Returns a string representation of the invitation.
    """
    
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="invitations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite to {self.email}"
