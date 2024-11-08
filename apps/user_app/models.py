from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.forms import TextInput, PasswordInput
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.utils.translation import  gettext_lazy
from apps.common.models import BaseModel
import uuid

  
    


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
    
        
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            birth_date = timezone.make_aware(datetime(2000, 3, 15), timezone.get_current_timezone()),
            is_staff = True
        )
        user.save(using=self._db)
        return user

class FloatChoices(models.TextChoices):
    @classmethod
    def values(cls):
        return [choice[0] for choice in cls.choices]

    @classmethod
    def labels(cls):
        return [choice[1] for choice in cls.choices]
        

class User(AbstractBaseUser):

    name = models.CharField(max_length=40, null=False)
    birth_date = models.DateTimeField(null=False)
    img_source = models.CharField(max_length=255, default='',blank=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()

    @property
    def age(self):
        today = timezone.now()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return age
    

    
    class UserType(models.TextChoices):
        NORMAL = 'N', 'Normal'
        COMPANY = 'C', 'Company'
        ADMIN = 'A', 'Admin'

    user_type = models.CharField(
        max_length=1,
        choices=UserType.choices,
        default=UserType.NORMAL,
        null=False
    )

    class SexType(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'

    sex = models.CharField(
        max_length=1,
        choices=SexType.choices,
        default=None,
        null=True
    )

    class Meta:
        permissions = [
            (f'can_view_user', f'Can view a User'),
            (f'can_create_user', f'Can create a User'),
            (f'can_edit_user', f'Can edit a User'),
            (f'can_delete_user', f'Can delete a User'),
        ]

    USERNAME_FIELD = 'email'

    def __str__(self):
        return f"{self.id} - {self.name}"
    
    def has_module_perms(self, app_label):
        return True  # or customize according to your needs

    def has_perms(self, perm, obj=None):
        return True  # or customize according to your needs
    
    def has_perm(self, perm, obj=None):
        return True  # or customize according to your needs

class MyModelQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

class GoalManager(models.Manager):
    def get_queryset(self):
        return MyModelQuerySet(self.model, using=self._db).filter(deleted_at=None)
        
class Invitation(models.Model):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Invite to {self.email}'