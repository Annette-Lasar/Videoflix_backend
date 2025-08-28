from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User


admin.site.unregister(DjangoUser)


@admin.register(User)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for custom User model."""
    
    list_display = ('id', 'email', 'is_active', 'date_joined')
    search_fields = ['email']
