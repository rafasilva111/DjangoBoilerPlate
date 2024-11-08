from django.core.management.base import BaseCommand
from apps.user_app.models import Company,User
from apps.common.constants import FIREBASE_STORAGE_COMPANY_BUCKET,COMPANY_LIVE_VIEW,COMPANY_LIVE_VIEW,COMPANY_LIVE_VIEW_DEFAULT_USER_PASSWORD
from apps.common.functions import lower_and_underescore
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create the default company if it does not exist'

    def handle(self, *args, **kwargs):

        ## LiveView

        # Check for Company Model

        try:
            live_view_company = Company.objects.get(name=COMPANY_LIVE_VIEW)

        except Company.DoesNotExist:

            name = COMPANY_LIVE_VIEW
            live_view_company = Company.objects.create(
                name=COMPANY_LIVE_VIEW,
                email=f'{lower_and_underescore(name)}@example.com',
                imgs_bucket=f"{FIREBASE_STORAGE_COMPANY_BUCKET}/{lower_and_underescore(name)}"
                )
            self.stdout.write(self.style.SUCCESS(f'Successfully created the {COMPANY_LIVE_VIEW} company'))

        # Check for Company default User

        if not live_view_company.user_account:

            live_view_user, created = User.objects.get_or_create(
                email=f'{lower_and_underescore(COMPANY_LIVE_VIEW)}@example.com',
                user_type=User.UserType.COMPANY,
                defaults={
                    'name': COMPANY_LIVE_VIEW,
                    'password': COMPANY_LIVE_VIEW_DEFAULT_USER_PASSWORD,
                    'img_source':"images/company/live_view/profile_img.png",
                    'is_staff': True,
                    'birth_date': timezone.now(),
                }
            )
            
            live_view_company.user_account = live_view_user
            live_view_company.save()

            self.stdout.write(self.style.SUCCESS(f'Successfully created the {COMPANY_LIVE_VIEW} company default user'))
