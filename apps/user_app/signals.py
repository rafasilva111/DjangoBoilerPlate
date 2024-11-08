# signals.py

from django.db.models.signals import post_delete,pre_delete,post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
#from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

User = get_user_model()

@receiver(post_delete, sender=User)
def nullify_user_in_outstanding_tokens(sender, instance, **kwargs):
    #teste = OutstandingToken.objects.filter(user=instance)
    #teste.update(user=None)
    pass
