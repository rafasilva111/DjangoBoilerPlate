from django.contrib import admin
from apps.user_app.models import User, Invitation


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'birth_date', 'is_active', 'created_at', 'user_type')
    list_filter = ('is_active', 'user_type')
    search_fields = ('email',  'name')
    ordering = ('-created_at',)
    
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'token', 'invited_by', 'created_at')
    list_filter = ( 'created_at', 'invited_by')
    search_fields = ('email', 'token', 'invited_by__email')
    readonly_fields = ('token', 'created_at')



admin.site.register(User, UserAdmin)
admin.site.register(Invitation, InvitationAdmin)
