from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SurgeryHours


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Clinical Info', {'fields': ('role', 'phone_number', 'date_of_birth', 'nhs_number', 'postal_code')}),
    )


@admin.register(SurgeryHours)
class SurgeryHoursAdmin(admin.ModelAdmin):
    list_display = ['day_of_week', 'open_time', 'close_time', 'is_closed']
    ordering = ['day_of_week']
